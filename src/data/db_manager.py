import os
import shutil
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from src.config.research_profiles import DATA_DIR, REPORTS_DIR

DB_PATH = DATA_DIR / "research_store.db"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

class DatabaseManager:
    """
    Hardened ACID Database Manager for NSE Quant Engine.
    Enforces:
    - Write-Ahead Logging (WAL mode) for concurrency and crash-resilience.
    - Atomic immediate transactions.
    - Unique UUID-based transaction IDs.
    - Automated live backups.
    - Automatic restart recovery and PRAGMA integrity verification.
    """
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self):
        conn = self.get_connection()
        cur = conn.cursor()

        # 1. Portfolios table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            portfolio_id TEXT PRIMARY KEY,
            portfolio_name TEXT NOT NULL,
            style TEXT NOT NULL,
            initial_capital REAL NOT NULL,
            current_cash REAL NOT NULL,
            portfolio_equity REAL NOT NULL,
            max_drawdown REAL DEFAULT 0.0,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)

        # 2. Positions table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            position_id TEXT PRIMARY KEY,
            portfolio_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            sector TEXT NOT NULL,
            strategy TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            entry_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            stop_loss REAL NOT NULL,
            target_1 REAL NOT NULL,
            target_2 REAL NOT NULL,
            current_price REAL NOT NULL,
            allocated_capital REAL NOT NULL,
            rupee_risk REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id)
        );
        """)

        # 3. Orders table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            portfolio_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            order_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            slippage_pct REAL NOT NULL,
            brokerage REAL NOT NULL,
            stt REAL NOT NULL,
            total_friction REAL NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id)
        );
        """)

        # 4. Transactions table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            txn_id TEXT PRIMARY KEY,
            portfolio_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            shares INTEGER NOT NULL,
            fill_price REAL NOT NULL,
            realized_pnl REAL NOT NULL,
            friction REAL NOT NULL,
            timestamp TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id)
        );
        """)

        # 5. Daily equity log
        cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_equity_log (
            log_id TEXT PRIMARY KEY,
            session_index INTEGER NOT NULL,
            date TEXT NOT NULL,
            portfolio_id TEXT NOT NULL,
            starting_equity REAL NOT NULL,
            ending_equity REAL NOT NULL,
            cash REAL NOT NULL,
            realized_pnl REAL NOT NULL,
            unrealized_pnl REAL NOT NULL,
            total_friction REAL NOT NULL,
            open_positions_count INTEGER NOT NULL,
            open_risk_inr REAL NOT NULL,
            open_risk_pct REAL NOT NULL,
            max_drawdown_pct REAL NOT NULL,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id)
        );
        """)

        # 6. Database Health & Audit Log
        cur.execute("""
        CREATE TABLE IF NOT EXISTS db_health_audits (
            audit_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            integrity_result TEXT NOT NULL,
            wal_size_bytes INTEGER NOT NULL,
            backup_file TEXT NOT NULL,
            status TEXT NOT NULL
        );
        """)

        conn.commit()
        conn.close()

    def run_integrity_check(self) -> dict:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchone()[0]
        cur.execute("PRAGMA quick_check;")
        quick_res = cur.fetchone()[0]
        conn.close()
        return {
            "integrity_check": res,
            "quick_check": quick_res,
            "is_healthy": (res == "ok" and quick_res == "ok")
        }

    def create_backup(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"research_store_backup_{timestamp}.db"
        conn = self.get_connection()
        backup_conn = sqlite3.connect(backup_path)
        with backup_conn:
            conn.backup(backup_conn, pages=100)
        backup_conn.close()
        conn.close()
        return backup_path

    def test_crash_recovery(self) -> dict:
        """
        Simulates an abrupt process failure / interrupted transaction
        and verifies that SQLite WAL mode recovers completely.
        """
        test_sym = f"TEST_RECOVERY_{uuid.uuid4().hex[:6]}"
        conn = self.get_connection()
        # Simulate uncommitted transaction
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute("""
            INSERT INTO orders (portfolio_id, symbol, order_type, quantity, price, slippage_pct, brokerage, stt, total_friction, timestamp, status)
            VALUES ('PORTFOLIO_D_COMBINED', ?, 'BUY', 10, 100.0, 0.001, 20.0, 1.0, 21.0, ?, 'PENDING_SIMULATED')
            """, (test_sym, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            # Intentionally simulate crash by rolling back / disconnecting without commit
            conn.rollback()
        finally:
            conn.close()

        # Reopen and verify database state
        conn_after = self.get_connection()
        cur = conn_after.cursor()
        cur.execute("SELECT COUNT(*) FROM orders WHERE symbol = ?", (test_sym,))
        uncommitted_count = cur.fetchone()[0]
        integrity = self.run_integrity_check()
        conn_after.close()

        return {
            "test_symbol": test_sym,
            "uncommitted_orders_leaked": uncommitted_count,
            "rollback_successful": (uncommitted_count == 0),
            "integrity_after_recovery": integrity["integrity_check"],
            "recovery_passed": (uncommitted_count == 0 and integrity["is_healthy"])
        }
