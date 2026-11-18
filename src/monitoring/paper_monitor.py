import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from src.config.research_profiles import DATA_DIR, REPORTS_DIR
from src.data.mcp_client import NSEDataClient
from src.backtester.delivery_costs import DeliveryCostModel

DB_PATH = DATA_DIR / "research_store.db"

class PaperTradingMonitor:
    """
    Automated Daily and Weekly Monitoring Engine for the 30-Session Paper Trading Programme.
    Tracks all 4 Independent Portfolios:
      - PORTFOLIO_A_INTRADAY
      - PORTFOLIO_B_SWING
      - PORTFOLIO_C_POSITIONAL
      - PORTFOLIO_D_COMBINED
    """
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.data_client = NSEDataClient()
        self.cost_model = DeliveryCostModel()

    def run_daily_monitoring_session(self, current_date_str: str = None) -> dict:
        """
        Executes daily session processing:
        1. Refreshes live prices for all active symbols.
        2. Evaluates stop loss and target conditions.
        3. Updates mark-to-market valuations and portfolio equity.
        4. Logs snapshot in daily_equity_log.
        """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        date_str = current_date_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Fetch distinct symbols
        cur.execute("SELECT DISTINCT symbol FROM positions WHERE status = 'OPEN'")
        symbols = [r[0] for r in cur.fetchall()]

        # 2. Get latest quotes
        latest_quotes = {}
        for sym in symbols:
            try:
                quote = self.data_client.get_live_quote(sym)
                latest_quotes[sym] = quote.get("ltp") or quote.get("close") or 0.0
            except Exception:
                # Fallback to last recorded close in historical dataframe
                df = self.data_client.get_stock_data(sym)
                latest_quotes[sym] = float(df["close"].iloc[-1]) if not df.empty else 0.0

        # 3. Update Open Positions & Check Triggers
        cur.execute("SELECT position_id, portfolio_id, symbol, quantity, entry_price, stop_loss, target_1, allocated_capital FROM positions WHERE status = 'OPEN'")
        open_pos = cur.fetchall()

        events = []
        for pos_id, pid, sym, qty, entry_px, sl, t1, alloc_cap in open_pos:
            cur_px = latest_quotes.get(sym, entry_px)
            if cur_px <= 0: continue

            # Check stop loss hit
            if cur_px <= sl:
                # Exit at stop loss
                realized_pnl = (sl - entry_px) * qty
                friction = self.cost_model.calculate_sell_cost(qty * sl)["total_cost"]
                net_pnl = realized_pnl - friction
                cur.execute("UPDATE positions SET status = 'CLOSED', current_price = ? WHERE position_id = ?", (sl, pos_id))
                cur.execute("UPDATE portfolios SET current_cash = current_cash + ? WHERE portfolio_id = ?", (qty * sl - friction, pid))
                cur.execute("INSERT INTO transactions (portfolio_id, symbol, action, shares, fill_price, realized_pnl, friction, timestamp, notes) VALUES (?, ?, 'STOP_LOSS_EXIT', ?, ?, ?, ?, ?, 'Stop Loss Hit')",
                            (pid, sym, qty, sl, net_pnl, friction, date_str))
                events.append(f"{pid} {sym} STOP_LOSS_HIT at Rs {sl}")
            elif cur_px >= t1:
                # Target 1 hit: take profit
                realized_pnl = (t1 - entry_px) * qty
                friction = self.cost_model.calculate_sell_cost(qty * t1)["total_cost"]
                net_pnl = realized_pnl - friction
                cur.execute("UPDATE positions SET status = 'CLOSED', current_price = ? WHERE position_id = ?", (t1, pos_id))
                cur.execute("UPDATE portfolios SET current_cash = current_cash + ? WHERE portfolio_id = ?", (qty * t1 - friction, pid))
                cur.execute("INSERT INTO transactions (portfolio_id, symbol, action, shares, fill_price, realized_pnl, friction, timestamp, notes) VALUES (?, ?, 'TARGET_EXIT', ?, ?, ?, ?, ?, 'Target 1 Reached')",
                            (pid, sym, qty, t1, net_pnl, friction, date_str))
                events.append(f"{pid} {sym} TARGET_REACHED at Rs {t1}")
            else:
                # Mark to market
                cur.execute("UPDATE positions SET current_price = ? WHERE position_id = ?", (cur_px, pos_id))

        # 4. Update Portfolio Equities
        cur.execute("SELECT portfolio_id, current_cash, initial_capital FROM portfolios")
        all_ports = cur.fetchall()

        daily_summary = []
        for pid, cash, init_cap in all_ports:
            cur.execute("SELECT SUM(quantity * current_price), SUM(rupee_risk), COUNT(*) FROM positions WHERE portfolio_id = ? AND status = 'OPEN'", (pid,))
            mtm_val, tot_risk, open_cnt = cur.fetchone()
            mtm_val = mtm_val or 0.0
            tot_risk = tot_risk or 0.0
            open_cnt = open_cnt or 0
            equity = cash + mtm_val

            cur.execute("UPDATE portfolios SET portfolio_equity = ? WHERE portfolio_id = ?", (equity, pid))
            cur.execute("""
            INSERT INTO daily_equity_log (date, portfolio_id, equity, cash, open_positions_count, open_risk_inr, open_risk_pct, sector_exposure_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (date_str, pid, equity, cash, open_cnt, tot_risk, round(tot_risk / equity * 100, 2), "{}"))

            daily_summary.append({
                "portfolio_id": pid,
                "equity": round(equity, 2),
                "cash": round(cash, 2),
                "open_positions": open_cnt,
                "open_risk": round(tot_risk, 2)
            })

        conn.commit()
        conn.close()

        return {
            "session_date": date_str,
            "events": events,
            "portfolios": daily_summary
        }

    def generate_weekly_status_csv(self) -> Path:
        """Exports current portfolios and positions to CSV for tracking."""
        conn = sqlite3.connect(self.db_path)
        ports_df = pd.read_sql("SELECT * FROM portfolios", conn)
        pos_df = pd.read_sql("SELECT * FROM positions", conn)
        tx_df = pd.read_sql("SELECT * FROM transactions", conn)
        conn.close()

        out_path = REPORTS_DIR / "WEEKLY_PORTFOLIO_SNAPSHOT.csv"
        ports_df.to_csv(out_path, index=False)
        return out_path
