from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data_store"
PARQUET_DIR = DATA_DIR / "parquet"
REPORTS_DIR = BASE_DIR / "reports"
DB_PATH = DATA_DIR / "research_store.db"

# Centralized Multi-Style Capital & Risk Profiles (Phase 13A)
CAPITAL_CONFIG = {
    "initial_capital": 500000.0,       # INR 500,000 Virtual Starting Capital
    "max_risk_per_trade": 0.01,        # 1% Account Risk per trade (Rs 5,000)
    "max_risk_amount": 5000.0,
    "max_concurrent_positions": 5,     # Max 5 Simultaneous Open Positions
    "max_portfolio_open_risk": 0.03,   # Max 3% Planned Aggregate Open Risk (Rs 15,000)
    "max_sector_exposure": 0.30,       # Max 30% Capital in any single sector
    "max_capital_deployment": 0.80,    # Max 80% Capital deployed (20% Cash buffer)
    "risk_free_rate": 0.07             # 7% RBI 10Y Benchmark G-Sec yield
}

# Cost Profiles
INTRADAY_COSTS = {
    "brokerage_pct": 0.0003,           # 0.03% or Rs 20/order
    "brokerage_max_inr": 20.0,
    "stt_buy_pct": 0.0,                # No STT on Intraday Buy
    "stt_sell_pct": 0.00025,           # 0.025% STT on Intraday Sell only
    "exchange_turnover_pct": 0.0000325,# 0.00325% NSE turnover
    "sebi_turnover_pct": 0.000001,      # Rs 10 / Crore
    "stamp_duty_buy_pct": 0.00003,     # 0.003% Intraday Stamp duty on Buy
    "gst_pct": 0.18,                   # 18% on (Brokerage + Exchange)
    "slippage_pct": 0.0005             # 0.05% Intraday liquid slippage
}

DELIVERY_COSTS = {
    "brokerage_pct": 0.0003,
    "brokerage_max_inr": 20.0,
    "stt_buy_pct": 0.001,              # 0.10% on Delivery Buy
    "stt_sell_pct": 0.001,             # 0.10% on Delivery Sell
    "exchange_turnover_pct": 0.0000325,
    "sebi_turnover_pct": 0.000001,
    "stamp_duty_buy_pct": 0.00015,     # 0.015% Delivery Stamp duty on Buy
    "gst_pct": 0.18,
    "slippage_pct": 0.0010             # 0.10% Delivery slippage
}

# Sectors Mapping for Sector Exposure Controls
STOCK_SECTORS = {
    # Banking & Financials
    "HDFCBANK": "Financials", "ICICIBANK": "Financials", "SBIN": "Financials",
    "KOTAKBANK": "Financials", "AXISBANK": "Financials", "PNB": "Financials",
    "CANBK": "Financials", "BANKBARODA": "Financials", "BAJFINANCE": "Financials",
    "BAJAJFINSV": "Financials", "CHOLAFIN": "Financials", "IREDA": "Financials",
    "BSE": "Financials", "CDSL": "Financials", "CAMS": "Financials", "MCX": "Financials",
    # IT & Tech
    "TCS": "IT", "INFY": "IT", "HCLTECH": "IT", "WIPRO": "IT", "TECHM": "IT",
    # Energy, Oil & Utilities
    "RELIANCE": "Energy", "ONGC": "Energy", "NTPC": "Utilities", "POWERGRID": "Utilities",
    "BPCL": "Energy", "IOC": "Energy", "COALINDIA": "Energy",
    # Capital Goods, Power & Defense
    "BEML": "Defense_Rail", "MIDHANI": "Defense_Rail", "BDL": "Defense_Rail",
    "HAL": "Defense_Rail", "BEL": "Defense_Rail", "MAZDOCK": "Defense_Rail",
    "POWERINDIA": "Capital_Goods", "ABB": "Capital_Goods", "SIEMENS": "Capital_Goods",
    "POLYCAB": "Capital_Goods", "LT": "Capital_Goods", "DIXON": "Electronics",
    # Auto & Auto Ancillary
    "MARUTI": "Auto", "TATAMOTORS": "Auto", "M&M": "Auto", "EICHERMOT": "Auto",
    "BAJAJ-AUTO": "Auto", "MOTHERSON": "Auto",
    # Consumer & Retail
    "ITC": "FMCG", "HINDUNILVR": "FMCG", "TITAN": "Consumer", "TRENT": "Retail",
    "ASIANPAINT": "Consumer", "NESTLEIND": "FMCG", "BRITANNIA": "FMCG",
    # Metals & Commodities
    "TATASTEEL": "Metals", "JSWSTEEL": "Metals", "HINDALCO": "Metals", "VEDL": "Metals"
}

# Expanded Universe Cohorts (100+ Liquid NSE Equities)
UNIVERSE_COHORTS = {
    "NIFTY_50": [
        "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "BHARTIARTL", "SBIN",
        "ITC", "HINDUNILVR", "LT", "BAJFINANCE", "HCLTECH", "MARUTI", "SUNPHARMA",
        "ONGC", "TATAMOTORS", "NTPC", "KOTAKBANK", "TITAN", "AXISBANK", "ADANIENT",
        "ADANIPORTS", "COALINDIA", "POWERGRID", "M&M", "BAJAJFINSV", "TATASTEEL",
        "JSWSTEEL", "HINDALCO", "GRASIM", "TECHM", "WIPRO", "NESTLEIND", "BPCL",
        "EICHERMOT", "BAJAJ-AUTO", "CIPLA", "DRREDDY", "BRITANNIA", "ASIANPAINT"
    ],
    "NIFTY_NEXT_50": [
        "PNB", "CANBK", "BANKBARODA", "CHOLAFIN", "HDFCAMC", "DLF", "VAML", "AMBUJACEM",
        "IRFC", "HYUNDAI", "ABB", "MOTHERSON", "ZYDUSLIFE", "SOLARINDS", "BOSCHLTD",
        "PIDILITIND", "MAZDOCK", "HAL", "BEL", "TRENT", "SIEMENS", "TORNTPHARM"
    ],
    "MIDCAP_MOMENTUM_LEADERS": [
        "BSE", "CDSL", "CAMS", "DIXON", "BEML", "MIDHANI", "BDL", "IREDA", "POLYCAB",
        "POWERINDIA", "MCX", "KFINTECH", "ANGELONE", "PREMIERENE", "DELHIVERY"
    ]
}

# Flat list of all eligible equities
FULL_NSE_UNIVERSE = sorted(list(set(
    UNIVERSE_COHORTS["NIFTY_50"] +
    UNIVERSE_COHORTS["NIFTY_NEXT_50"] +
    UNIVERSE_COHORTS["MIDCAP_MOMENTUM_LEADERS"]
)))
