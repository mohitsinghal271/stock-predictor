import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data_store"
PARQUET_DIR = DATA_DIR / "parquet"
REPORTS_DIR = BASE_DIR / "reports"
DB_PATH = DATA_DIR / "research_store.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
PARQUET_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# NSE Indian Market Transaction Costs (Delivery & Swing Equity)
# Matches actual NSE & SEBI statutory charges for retail / HNI accounts
TRANSACTION_COSTS = {
    "brokerage_pct": 0.0003,       # 0.03% or max Rs 20 per order
    "brokerage_max_inr": 20.0,
    "stt_buy_pct": 0.001,          # 0.1% Securities Transaction Tax on Buy
    "stt_sell_pct": 0.001,         # 0.1% Securities Transaction Tax on Sell
    "exchange_turnover_pct": 0.0000325, # 0.00325% NSE turnover charge
    "sebi_turnover_pct": 0.000001,      # Rs 10 per Crore (0.0001%)
    "stamp_duty_buy_pct": 0.00015,     # 0.015% Stamp duty on Buy only
    "gst_pct": 0.18,                   # 18% GST on (Brokerage + Exchange turnover)
    "slippage_pct": 0.0010             # 0.10% conservative slippage per leg
}

# Validation Splits
DATA_SPLIT = {
    "train_pct": 0.60,      # In-Sample training & parameter discovery
    "val_pct": 0.20,        # Validation tuning
    "test_pct": 0.20        # Untouched Out-of-Sample evaluation
}

# Universe Definition: Core Liquid NSE Momentum & Quality Universe
DEFAULT_UNIVERSE = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBIN",
    "LICI", "ITC", "HINDUNILVR", "LT", "BAJFINANCE", "HCLTECH", "MARUTI",
    "SUNPHARMA", "ONGC", "TATAMOTORS", "NTPC", "KOTAKBANK", "TITAN",
    "BSE", "CDSL", "CAMS", "DIXON", "BEML", "MIDHANI", "BDL", "PNB", "IREDA",
    "POLYCAB", "POWERINDIA", "HAL", "BEL", "TRENT", "CHOLAFIN", "MCX"
]

# Benchmark Index Symbol
BENCHMARK_SYMBOL = "NIFTY 50"

# Target Acceptance Criteria for Production Strategies
ACCEPTANCE_CRITERIA = {
    "min_oos_sharpe": 1.0,
    "min_oos_profit_factor": 1.30,
    "max_drawdown_pct": 0.22,
    "min_trades": 30,
    "min_win_rate": 0.40,
    "min_expectancy_pct": 0.005
}
