import pandas as pd
import numpy as np
from src.backtester.costs import IndianTransactionCostModel
from src.backtester.metrics import PerformanceMetrics
from src.strategies.base import BaseStrategy

class BacktestEngine:
    """
    Production-grade Vectorized & Trade-by-Trade Backtesting Engine.
    Executes next-day Open on signals generated at Day T Close.
    Deducts exact statutory Indian transaction costs & slippage on every trade.
    """
    def __init__(self, initial_capital: float = 1000000.0, cost_model=None):
        self.initial_capital = initial_capital
        self.cost_model = cost_model or IndianTransactionCostModel()

    def run(self, df: pd.DataFrame, strategy: BaseStrategy, position_size_pct: float = 1.0) -> dict:
        """
        Executes backtest for a single stock price series.
        df must have: ['open', 'high', 'low', 'close', 'volume'] indexed by datetime or sequential dates.
        """
        if df.empty or len(df) < 50:
            return {
                "metrics": PerformanceMetrics.empty_metrics(),
                "equity_curve": pd.Series([self.initial_capital]),
                "trades": []
            }

        # 1. Generate signals (at Bar T Close)
        raw_signals = strategy.generate_signals(df)

        # 2. Shift signals by 1 bar to simulate realistic execution on Next Day (Bar T+1)
        # Position taken at Bar T+1 Open, held until exit signal
        exec_signals = raw_signals.shift(1).fillna(0)

        # 3. Simulate Trade Logs & Equity
        dates = df.index
        opens = df["open"].values
        closes = df["close"].values

        capital = self.initial_capital
        equity_history = []
        trades = []

        in_trade = False
        entry_idx = 0
        entry_price = 0.0
        shares = 0
        allocated_cash = 0.0

        for i in range(len(df)):
            curr_signal = exec_signals.iloc[i]
            curr_open = opens[i]
            curr_close = closes[i]
            curr_date = dates[i]

            # Signal changed from 0 to 1 -> BUY at today's OPEN
            if curr_signal == 1 and not in_trade:
                in_trade = True
                entry_idx = i
                # Entry price includes slippage
                entry_price = curr_open * (1.0 + self.cost_model.c["slippage_pct"])
                allocated_cash = capital * position_size_pct
                shares = int(allocated_cash / entry_price)

                if shares > 0:
                    buy_val = shares * entry_price
                    buy_costs = self.cost_model.calculate_buy_cost(buy_val)["total_buy_cost"]
                    capital -= buy_costs
                else:
                    in_trade = False

            # Signal changed from 1 to 0 -> SELL at today's OPEN
            elif curr_signal == 0 and in_trade:
                exit_price = curr_open * (1.0 - self.cost_model.c["slippage_pct"])
                sell_val = shares * exit_price
                sell_costs = self.cost_model.calculate_sell_cost(sell_val)["total_sell_cost"]

                gross_pnl = (exit_price - entry_price) * shares
                net_pnl = gross_pnl - (self.cost_model.calculate_buy_cost(shares * entry_price)["total_buy_cost"] + sell_costs)
                pct_return = net_pnl / (shares * entry_price) if entry_price > 0 else 0.0

                capital += net_pnl

                trades.append({
                    "entry_date": str(dates[entry_idx]),
                    "exit_date": str(curr_date),
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "shares": shares,
                    "duration_days": i - entry_idx,
                    "gross_pnl": round(gross_pnl, 2),
                    "net_pnl": round(net_pnl, 2),
                    "return_pct": round(pct_return, 4)
                })

                in_trade = False
                shares = 0

            # Daily Mark-to-Market Equity
            if in_trade:
                curr_mtm = capital + (shares * (curr_close - entry_price))
            else:
                curr_mtm = capital

            equity_history.append(curr_mtm)

        # Close any lingering trade on last bar for complete accounting
        if in_trade and shares > 0:
            last_close = closes[-1]
            exit_price = last_close * (1.0 - self.cost_model.c["slippage_pct"])
            gross_pnl = (exit_price - entry_price) * shares
            sell_costs = self.cost_model.calculate_sell_cost(shares * exit_price)["total_sell_cost"]
            net_pnl = gross_pnl - sell_costs
            pct_return = net_pnl / (shares * entry_price) if entry_price > 0 else 0.0

            trades.append({
                "entry_date": str(dates[entry_idx]),
                "exit_date": str(dates[-1]),
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "shares": shares,
                "duration_days": len(df) - 1 - entry_idx,
                "gross_pnl": round(gross_pnl, 2),
                "net_pnl": round(net_pnl, 2),
                "return_pct": round(pct_return, 4)
            })

        equity_curve = pd.Series(equity_history, index=df.index)
        trade_returns = [t["return_pct"] for t in trades]

        metrics = PerformanceMetrics.calculate(equity_curve, trade_returns)

        return {
            "strategy": strategy.get_description(),
            "initial_capital": self.initial_capital,
            "final_equity": round(equity_history[-1] if equity_history else self.initial_capital, 2),
            "metrics": metrics,
            "equity_curve": equity_curve,
            "trades": trades
        }
