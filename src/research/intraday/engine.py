import pandas as pd
import numpy as np
from src.backtester.intraday_costs import IntradayCostModel
from src.risk.position_sizing import RiskBasedPositionSizer
from src.backtester.metrics import PerformanceMetrics

class IntradayResearchEngine:
    """
    Track A: Pure Intraday Trading Engine.
    Rules:
    - Same-session entries (Opening Range Breakout / Prev Day High Breakout).
    - Mandatory square-off at session close (15:15 IST). Zero overnight risk.
    - Statutory Intraday STT (0.025% on sell only).
    - Initial virtual capital: INR 500,000. Max 1% planned risk per trade.
    """
    def __init__(self, initial_capital: float = 500000.0):
        self.initial_capital = initial_capital
        self.cost_model = IntradayCostModel()
        self.sizer = RiskBasedPositionSizer()

    def run_orb_breakout(self, df: pd.DataFrame, orb_window: int = 15, stop_loss_atr: float = 1.5) -> dict:
        """
        Simulates Daily Opening Range Breakout:
        Entry: If Day High breaks above yesterday's High + small buffer.
        Exit: Force square-off at today's Close.
        """
        if len(df) < 50:
            return {"metrics": PerformanceMetrics.empty_metrics(), "equity_curve": pd.Series([self.initial_capital]), "trades": []}

        highs = df["high"].values
        lows = df["low"].values
        opens = df["open"].values
        closes = df["close"].values
        dates = df.index

        # ATR calculation
        tr = np.maximum(highs - lows, np.maximum(np.abs(highs - np.roll(closes, 1)), np.abs(lows - np.roll(closes, 1))))
        tr[0] = highs[0] - lows[0]
        atr = pd.Series(tr).rolling(14).mean().bfill().values

        capital = self.initial_capital
        equity_history = []
        trades = []

        for i in range(1, len(df)):
            prev_high = highs[i-1]
            prev_low = lows[i-1]
            curr_open = opens[i]
            curr_high = highs[i]
            curr_low = lows[i]
            curr_close = closes[i]
            curr_atr = atr[i-1]

            # Intraday Breakout Condition: Day High breaks above Previous Day High
            if curr_high > prev_high:
                # Simulated entry at breakout price (prev_high * 1.001)
                entry_price = prev_high * 1.001
                # Stop loss based on ATR below entry
                stop_loss = max(curr_open * 0.98, entry_price - (curr_atr * stop_loss_atr))

                sizing = self.sizer.calculate_quantity(capital, capital * 0.80, entry_price, stop_loss)
                qty = sizing["quantity"]

                if qty > 0:
                    # Intraday Execution: Did price hit Stop Loss intraday or close?
                    if curr_low <= stop_loss:
                        exit_price = stop_loss
                        reason = "SL_HIT"
                    else:
                        exit_price = curr_close # Mandatory square-off at close
                        reason = "MARKET_CLOSE_SQUAREOFF"

                    buy_val = qty * entry_price
                    sell_val = qty * exit_price
                    friction = self.cost_model.round_trip_cost(buy_val, sell_val)

                    gross_pnl = (exit_price - entry_price) * qty
                    net_pnl = gross_pnl - friction
                    ret_pct = net_pnl / buy_val if buy_val > 0 else 0.0

                    capital += net_pnl
                    trades.append({
                        "date": str(dates[i].date()) if hasattr(dates[i], "date") else str(dates[i]),
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "stop_loss": round(stop_loss, 2),
                        "shares": qty,
                        "gross_pnl": round(gross_pnl, 2),
                        "net_pnl": round(net_pnl, 2),
                        "friction": round(friction, 2),
                        "return_pct": round(ret_pct, 4),
                        "exit_reason": reason
                    })

            equity_history.append(capital)

        eq_series = pd.Series(equity_history, index=dates[1:])
        trade_returns = [t["return_pct"] for t in trades]
        metrics = PerformanceMetrics.calculate(eq_series, trade_returns)

        return {
            "strategy": f"Intraday_ORB_Breakout(ATR={stop_loss_atr})",
            "style": "INTRADAY",
            "initial_capital": self.initial_capital,
            "final_equity": round(capital, 2),
            "metrics": metrics,
            "equity_curve": eq_series,
            "trades": trades
        }
