# Autonomous NSE Quantitative Research & Strategy Discovery Engine

[![CI](https://github.com/your-username/stcks_predictor/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/stcks_predictor/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An institutional-grade autonomous quantitative research platform designed to discover, backtest, stress-test, rank, and monitor trading strategies across NSE-listed Indian equities.

---

## Key Features

1. **Zero Future Leakage:** Realistic next-day Open execution on signals triggered at bar T Close.
2. **Statutory Indian Transaction Costs:** Deducts 0.1% STT, 0.03% brokerage, NSE turnover charges, 18% GST, SEBI turnover fees, Stamp duty, and 0.10% conservative slippage per leg.
3. **Walk-Forward Validation:** Strict 60% Train / 20% Validation / 20% Untouched Out-Of-Sample split to penalize overfit models.
4. **Monte Carlo Bootstrap Simulation:** 1,000-iteration trade sequence shuffle testing tail-risk maximum drawdowns and ruin probability.
5. **Live Market Scanner & Paper Trading:** Continuously checks live NSE MCP feeds (`cm-market` and `nse-bhavcopy`) and generates virtual paper trades.
6. **Headless Cloud Architecture:** Pre-configured for deployment on Render, Railway, Docker, or Vercel without requiring a local PC or Antigravity to stay open.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run full research cycle (tests all strategies across 5 years of data)
python run_research.py

# 3. Launch live web dashboard
uvicorn src.dashboard.api:app --host 0.0.0.0 --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Discovered Strategy Matrix

The engine autonomously evaluates multiple parameterized strategy families:
* **Dual EMA Momentum:** Fast/Slow EMA crossovers with 200 EMA macro trend filters.
* **Donchian Breakouts:** Multi-week turtle upper channel breakouts.
* **Volume Confirmed Breakouts:** 20D/50D high breakouts with 1.75x–2.0x volume expansion.
* **Bollinger Mean Reversion:** Extreme lower band oversold reversals with RSI targets.
* **VCP Rocket Strategy:** Volatility contraction (ATR compression) followed by institutional volume thrust.

---

## Documentation

* [Repository Audit](docs/REPOSITORY_AUDIT.md)
* [MCP Data Source Audit](docs/MCP_DATA_SOURCE_AUDIT.md)
* [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
* [Cloud Deployment Guide](DEPLOYMENT.md)
