import time
import signal
import sys
from datetime import datetime, date
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.engine.session_manager import PaperTradingSessionManager
from src.data.db_manager import DatabaseManager

class AutonomousResearchWorker:
    """
    Continuous Cloud Background Research & Paper-Trading Worker.
    Executes automated daily market scans, position monitoring, risk checks,
    and daily/weekly reporting independently without requiring laptop to remain open.
    """
    def __init__(self, run_interval_seconds: int = 3600):
        self.interval = run_interval_seconds
        self.is_running = True
        self.session_mgr = PaperTradingSessionManager()
        self.db_mgr = DatabaseManager()

        signal.signal(signal.SIGTERM, self._graceful_shutdown)
        signal.signal(signal.SIGINT, self._graceful_shutdown)

    def _graceful_shutdown(self, signum, frame):
        print(f"\n[WORKER] Caught signal {signum}. Shutting down worker gracefully...")
        self.is_running = False

    def start(self):
        print("=" * 70)
        print("  PHASE 14 AUTONOMOUS CLOUD RESEARCH & PAPER TRADING WORKER")
        print(f"  Experiment ID: {self.session_mgr.experiment_id}")
        print(f"  Check Cadence: Every {self.interval} seconds (1 Hour)")
        print(f"  Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        print("  Real-Money Trading: STRICTLY DISABLED")
        print("=" * 70)

        # Execute immediate session on startup
        self.run_cycle()

        while self.is_running:
            slept = 0
            while self.is_running and slept < self.interval:
                time.sleep(5)
                slept += 5

            if self.is_running:
                self.run_cycle()

        print("[WORKER] Worker terminated cleanly.")

    def run_cycle(self):
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            print(f"\n[WORKER] Running Paper Trading Cycle for Date: {today_str}...")
            res = self.session_mgr.execute_daily_session(today_str)
            print(f"[WORKER RESULT] Status: {res.get('status')} | Message: {res.get('message', 'Cycle processed successfully')}")
            if res.get("status") == "SUCCESS":
                print(f"  Session: {res.get('session_number')}/30 | Equity: Rs {res.get('portfolio_equity', 0.0):,.2f} | Net PnL Today: Rs {res.get('net_pnl_today', 0.0):,.2f}")
        except Exception as e:
            print(f"[WORKER ERROR] Cycle failed with exception: {e}")

if __name__ == "__main__":
    if "--once" in sys.argv:
        mgr = PaperTradingSessionManager()
        today = datetime.now().strftime("%Y-%m-%d")
        res = mgr.execute_daily_session(today)
        print("Single Cycle Result:", res)
    else:
        worker = AutonomousResearchWorker(run_interval_seconds=3600)
        worker.start()
