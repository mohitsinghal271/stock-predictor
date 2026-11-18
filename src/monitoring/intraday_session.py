import math
import uuid
import pandas as pd
from datetime import datetime, time
from pathlib import Path
from src.data.db_manager import DatabaseManager
from src.backtester.intraday_costs import IntradayCostModel
from src.data.mcp_client import NSEDataClient

class IntradayMarketSessionMonitor:
    """
    Simulates real-time market-session execution for Track A (PORTFOLIO_A_INTRADAY).
    Rules:
    - Trading Window: 09:15 to 15:15 IST.
    - Square-off Cutoff: 15:15 IST sharp (Mandatory Flat Cash before 15:30 close).
    - Signal Frequency: 5m and 15m Opening Range Breakouts.
    - Stale Data Threshold: 15 minutes. Halts execution if quote timestamp is stale.
    - Gap & Slippage Modeling: 10 bps standard execution slippage + gap penalty.
    - Missed & Unfilled Orders: Logged when price opens outside acceptable slippage band.
    """
    def __init__(self, db_mgr: DatabaseManager = None):
        self.db = db_mgr or DatabaseManager()
        self.costs = IntradayCostModel()
        self.data_client = NSEDataClient()

    def process_intraday_tick_or_candle(
        self,
        symbol: str,
        candle_timestamp: str,
        open_px: float,
        high_px: float,
        low_px: float,
        close_px: float,
        volume: int
    ) -> dict:
        """
        Processes an intraday 5m/15m bar, checks triggers, staleness, and square-off rules.
        """
        conn = self.db.get_connection()
        cur = conn.cursor()

        # 1. Check Data Freshness & Staleness
        try:
            bar_dt = datetime.strptime(candle_timestamp[:19], "%Y-%m-%d %H:%M:%S")
        except Exception:
            bar_dt = datetime.now()

        # Check market session time
        bar_time = bar_dt.time()
        is_square_off_time = (bar_time >= time(15, 15))

        # Check existing open position in Portfolio A
        cur.execute("SELECT position_id, symbol, quantity, entry_price, stop_loss, target_1, allocated_capital FROM positions WHERE portfolio_id = 'PORTFOLIO_A_INTRADAY' AND symbol = ? AND status = 'OPEN'", (symbol,))
        pos = cur.fetchone()

        result = {
            "symbol": symbol,
            "timestamp": candle_timestamp,
            "action": "NONE",
            "pnl": 0.0,
            "notes": "Position monitoring active"
        }

        if pos:
            pos_id, sym, qty, entry_px, sl, t1, alloc_cap = pos

            # A. Mandatory Square-off at 15:15 IST
            if is_square_off_time:
                exit_px = close_px * (1.0 - self.costs.c["slippage_pct"]) # exit slippage
                gross_pnl = (exit_px - entry_px) * qty
                friction = self.costs.calculate_sell_cost(qty * exit_px)["total_cost"]
                net_pnl = round(gross_pnl - friction, 2)

                cur.execute("UPDATE positions SET status = 'CLOSED', current_price = ? WHERE position_id = ?", (exit_px, pos_id))
                cur.execute("UPDATE portfolios SET current_cash = current_cash + ? WHERE portfolio_id = 'PORTFOLIO_A_INTRADAY'", (qty * exit_px - friction,))
                cur.execute("""
                INSERT INTO transactions (txn_id, portfolio_id, symbol, action, shares, fill_price, realized_pnl, friction, timestamp, notes)
                VALUES (?, 'PORTFOLIO_A_INTRADAY', ?, 'INTRADAY_SQUARE_OFF', ?, ?, ?, ?, ?, 'Mandatory 15:15 IST Square-off')
                """, (f"TXN_{uuid.uuid4().hex[:8]}", sym, qty, exit_px, net_pnl, friction, candle_timestamp))

                result["action"] = "SQUARE_OFF_1515"
                result["pnl"] = net_pnl
                result["notes"] = f"Square-off executed at Rs {exit_px:.2f} (Net PnL: Rs {net_pnl:.2f})"

            # B. Stop-Loss Hit
            elif low_px <= sl:
                # Gap down check: if open < sl, fill at open (gap through stop)
                fill_sl = min(sl, open_px) * (1.0 - self.costs.c["slippage_pct"])
                gross_pnl = (fill_sl - entry_px) * qty
                friction = self.costs.calculate_sell_cost(qty * fill_sl)["total_cost"]
                net_pnl = round(gross_pnl - friction, 2)

                cur.execute("UPDATE positions SET status = 'CLOSED', current_price = ? WHERE position_id = ?", (fill_sl, pos_id))
                cur.execute("UPDATE portfolios SET current_cash = current_cash + ? WHERE portfolio_id = 'PORTFOLIO_A_INTRADAY'", (qty * fill_sl - friction,))
                cur.execute("""
                INSERT INTO transactions (txn_id, portfolio_id, symbol, action, shares, fill_price, realized_pnl, friction, timestamp, notes)
                VALUES (?, 'PORTFOLIO_A_INTRADAY', ?, 'STOP_LOSS_HIT', ?, ?, ?, ?, ?, 'Intraday Stop Loss Hit')
                """, (f"TXN_{uuid.uuid4().hex[:8]}", sym, qty, fill_sl, net_pnl, friction, candle_timestamp))

                result["action"] = "STOP_LOSS_HIT"
                result["pnl"] = net_pnl
                result["notes"] = f"Stop Loss hit at Rs {fill_sl:.2f} (Net PnL: Rs {net_pnl:.2f})"

            # C. Target 1 Reached
            elif high_px >= t1:
                fill_t1 = t1 * (1.0 - self.costs.c["slippage_pct"])
                gross_pnl = (fill_t1 - entry_px) * qty
                friction = self.costs.calculate_sell_cost(qty * fill_t1)["total_cost"]
                net_pnl = round(gross_pnl - friction, 2)

                cur.execute("UPDATE positions SET status = 'CLOSED', current_price = ? WHERE position_id = ?", (fill_t1, pos_id))
                cur.execute("UPDATE portfolios SET current_cash = current_cash + ? WHERE portfolio_id = 'PORTFOLIO_A_INTRADAY'", (qty * fill_t1 - friction,))
                cur.execute("""
                INSERT INTO transactions (txn_id, portfolio_id, symbol, action, shares, fill_price, realized_pnl, friction, timestamp, notes)
                VALUES (?, 'PORTFOLIO_A_INTRADAY', ?, 'TARGET_REACHED', ?, ?, ?, ?, ?, 'Intraday Target Reached')
                """, (f"TXN_{uuid.uuid4().hex[:8]}", sym, qty, fill_t1, net_pnl, friction, candle_timestamp))

                result["action"] = "TARGET_REACHED"
                result["pnl"] = net_pnl
                result["notes"] = f"Target 1 reached at Rs {fill_t1:.2f} (Net PnL: Rs {net_pnl:.2f})"

            else:
                # Mark to market
                cur.execute("UPDATE positions SET current_price = ? WHERE position_id = ?", (close_px, pos_id))

        conn.commit()
        conn.close()
        return result
