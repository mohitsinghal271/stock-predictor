import json
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.config import DATA_DIR, REPORTS_DIR

app = FastAPI(title="Autonomous NSE Quant Engine", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "research_store.db"

def load_research_data() -> dict:
    json_path = DATA_DIR / "research_summary.json"
    if json_path.exists():
        with open(json_path, "r") as f:
            return json.load(f)
    return {}

@app.get("/health")
@app.get("/api/health")
def health_check():
    db_ok = False
    active_portfolios = 0
    active_positions = 0
    db_integrity = "UNKNOWN"
    
    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("PRAGMA integrity_check")
            db_integrity = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM portfolios WHERE status = 'ACTIVE_INCUBATION'")
            active_portfolios = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM positions WHERE status = 'OPEN'")
            active_positions = cur.fetchone()[0]
            conn.close()
            db_ok = (db_integrity == "ok")
        except Exception as e:
            db_integrity = str(e)

    return {
        "status": "HEALTHY" if db_ok else "DEGRADED",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "database": {
            "connected": db_ok,
            "path": str(DB_PATH),
            "integrity": db_integrity,
            "active_portfolios": active_portfolios,
            "active_positions": active_positions
        },
        "engine_mode": "RESEARCH_AND_PAPER_TRADING",
        "real_money_trading": "DISABLED"
    }

@app.get("/api/experiment")
def get_experiment_details():
    config_path = Path(__file__).resolve().parent.parent.parent / "config" / "experiment_config.json"
    cfg = {}
    config_hash = "N/A"
    if config_path.exists():
        with open(config_path, "r") as f:
            cfg = json.load(f)
        import hashlib
        with open(config_path, "rb") as f:
            config_hash = hashlib.sha256(f.read()).hexdigest()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM daily_sessions WHERE status = 'COMPLETED'")
    completed_sessions = cur.fetchone()[0]
    cur.execute("SELECT session_date, portfolio_equity, net_pnl FROM daily_sessions ORDER BY session_number DESC LIMIT 1")
    last_session = cur.fetchone()
    conn.close()

    return {
        "experiment_id": cfg.get("experiment_id", "EXP-NSE-2026-001"),
        "name": cfg.get("name", "Phase 14 Autonomous 30-Session Paper Trading"),
        "config_sha256": config_hash,
        "completed_sessions": completed_sessions,
        "total_planned_sessions": 30,
        "progress_pct": round(completed_sessions / 30.0 * 100, 1),
        "status": "INCUBATION_ACTIVE" if completed_sessions < 30 else "EXPERIMENT_COMPLETE",
        "last_session_date": last_session[0] if last_session else "N/A",
        "current_equity_combined": last_session[1] if last_session else 500000.0,
        "worker_health": "ONLINE_24_7",
        "real_money_trading": "DISABLED",
        "mcp_status": "ONLINE"
    }

@app.get("/api/sessions")
def get_daily_sessions():
    if not DB_PATH.exists():
        return {"sessions": []}
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM daily_sessions ORDER BY session_number ASC", conn)
        conn.close()
        return {"sessions": df.to_dict(orient="records")}
    except Exception:
        conn.close()
        return {"sessions": []}

@app.get("/api/live-portfolios")
def get_live_portfolios():
    if not DB_PATH.exists():
        return {"portfolios": []}
    conn = sqlite3.connect(DB_PATH)
    try:
        ports_df = pd.read_sql("SELECT * FROM portfolios", conn)
        pos_df = pd.read_sql("SELECT * FROM positions WHERE status = 'OPEN'", conn)
        conn.close()
        return {
            "portfolios": ports_df.to_dict(orient="records"),
            "open_positions": pos_df.to_dict(orient="records")
        }
    except Exception:
        conn.close()
        return {"portfolios": [], "open_positions": []}

@app.get("/api/styles")
def get_styles_data():
    results = {}
    csv_map = {
        "intraday": REPORTS_DIR / "INTRADAY_LEADERBOARD.csv",
        "swing": REPORTS_DIR / "SWING_LEADERBOARD.csv",
        "positional": REPORTS_DIR / "POSITIONAL_LEADERBOARD.csv",
        "combined": REPORTS_DIR / "COMBINED_PORTFOLIO_RESULTS.csv",
        "live_signals": REPORTS_DIR / "LIVE_PAPER_SIGNALS.csv",
        "sizing_audit": REPORTS_DIR / "POSITION_SIZING_AUDIT.csv"
    }
    for key, path in csv_map.items():
        if path.exists():
            try:
                df = pd.read_csv(path)
                results[key] = df.to_dict(orient="records")
            except Exception as e:
                results[key] = []
        else:
            results[key] = []
    return results

@app.get("/api/leaderboard")
def get_leaderboard():
    data = load_research_data()
    return {
        "leaderboard": data.get("leaderboard", []),
        "rejected": data.get("rejected", [])
    }

@app.get("/api/signals")
def get_signals():
    # Return audited live paper signals
    path = REPORTS_DIR / "LIVE_PAPER_SIGNALS.csv"
    if path.exists():
        df = pd.read_csv(path)
        return {"signals": df.to_dict(orient="records")}
    data = load_research_data()
    return {
        "signals": data.get("live_signals", [])
    }

@app.get("/api/paper-trades")
def get_paper_trades():
    ledger_file = DATA_DIR / "paper_trades.json"
    if ledger_file.exists():
        with open(ledger_file, "r") as f:
            return json.load(f)
    return {}

@app.get("/api/download-pdf")
def download_pdf():
    pdf_path = REPORTS_DIR / "Autonomous_NSE_Quant_Research_Report.pdf"
    if pdf_path.exists():
        return FileResponse(pdf_path, media_type="application/pdf", filename="Autonomous_NSE_Quant_Research_Report.pdf")
    return {"error": "PDF report not yet generated"}

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Quant Engine Dashboard Initializing...</h1>"
