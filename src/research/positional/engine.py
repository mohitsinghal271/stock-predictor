import pandas as pd
import numpy as np
from src.backtester.delivery_costs import DeliveryCostModel
from src.risk.position_sizing import RiskBasedPositionSizer
from src.backtester.metrics import PerformanceMetrics
from src.strategies.base import BaseStrategy

class PositionalResearchEngine:
    """
    Track C: Positional Trading Engine.
    Rules:
    - Holding period: 20 to 120 trading days.
    - Captures major multi-month institutional bull trends.
    - Delivery friction model.
    - Trailing 50-day EMA or 8% trailing stop exit.
    - Initial virtual capital: INR 500,000. Max 1% planned risk per trade.
    """
    def __init__(self, initial_capital: float = 500000.0):
        self.initial_capital = initial_capital
        self.cost_model = DeliveryCostModel()
        self.sizer = RiskBasedPositionSizer()

    def run(self, df: pd.DataFrame, strategy: BaseStrategy, trailing_stop_pct: float = 0.08) -> dict:
        if len(df) < 100:
            return {"metrics": PerformanceMetrics.empty_metrics(), "equity_curve": pd.Series([self.initial_capital]), "trades": []}

        signals = strategy.generate_signals(df).shift(1).fillna(0)
        dates = df.index
        opens = df["open"].values
        highs = df["high"].values
        lows = df["low"].values
        closes = df["close"].values

        capital = self.initial_capital
        equity_history = []
        trades = []

        in_trade = False
        entry_idx = 0
        entry_price = 0.0
        trailing_peak = 0.0
        stop_loss = 0.0
        qty = 0

        for i in range(len(df)):
            sig = signals.iloc[i]
            c_open = opens[i]
            c_high = highs[i]
            c_low = lows[i]
            c_close = closes[i]

            # Entry
            if sig == 1 and not in_trade:
                entry_price = c_open * (1.0 + self.cost_model.c["slippage_pct"])
                trailing_peak = entry_price
                stop_loss = entry_price * (1.0 - trailing_stop_pct)
                sizing = self.sizer.calculate_quantity(capital, capital * 0.80, entry_price, stop_loss)
                qty = sizing["quantity"]

                if qty > 0:
                    in_trade = True
                    entry_idx = i
                    buy_val = qty * entry_price
                    buy_costs = self.cost_model.calculate_buy_cost(buy_val)["total_cost"]
                    capital -= buy_costs

            # Positional In-Trade: Trailing Stop Logic
            elif in_trade:
                trailing_peak = max(trailing_peak, c_high)
                trailing_stop = trailing_peak * (1.0 - trailing_stop_pct)

                if c_low <= trailing_stop:
                    exit_price = trailing_stop
                    in_trade = False
                    reason = "TRAILING_STOP_HIT"
                elif sig == 0:
                    exit_price = c_open * (1.0 - self.cost_model.c["slippage_pct"])
                    in_trade = False
                    reason = "STRATEGY_EXIT"
                else:
                    exit_price = None

                if not in_trade and exit_price is not None:
                    sell_val = qty * exit_price
                    sell_costs = self.cost_model.calculate_sell_cost(sell_val)["total_cost"]
                    gross_pnl = (exit_price - entry_price) * qty
                    net_pnl = gross_pnl - (self.cost_model.calculate_buy_cost(qty * entry_price)["total_cost"] + sell_costs)
                    capital += net_pnl

                    trades.append({
                        "entry_date": str(dates[entry_idx].date()) if hasattr(dates[entry_idx], "date") else str(dates[entry_idx]),
                        "exit_date": str(dates[i].date()) if hasattr(dates[i], "date") else str(dates[i]),
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "shares": qty,
                        "holding_days": i - entry_idx,
                        "gross_pnl": round(gross_pnl, 2),
                        "net_pnl": round(net_pnl, 2),
                        "return_pct": round(net_pnl / (qty * entry_price), 4),
                        "reason": reason
                    })
                    qty = 0

            # Daily Mark-to-Market Equity
            mtm = capital + (qty * (c_close - entry_price)) if in_trade else capital
            equity_history.append(mtm)

        eq_series = pd.Series(equity_history, index=dates)
        trade_returns = [t["return_pct"] for t in trades]
        metrics = PerformanceMetrics.calculate(eq_series, trade_returns)

        return {
            "strategy": strategy.get_description(),
            "style": "POSITIONAL",
            "initial_capital": self.initial_capital,
            "final_equity": round(equity_history[-1] if equity_history else capital, 2),
            "metrics": metrics,
            "equity_curve": eq_series,
            "trades": trades
        }
