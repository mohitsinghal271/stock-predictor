# REPOSITORY & SYSTEM ARCHITECTURE AUDIT
**Project:** Autonomous NSE Quantitative Research & Strategy Discovery Engine  
**Target Path:** `c:\Users\idea\OneDrive\Desktop\projects\stcks_predictor`  
**Audit Date:** November 17, 2026  
**Environment:** Windows (Development & Verification) -> Render/Railway + Vercel + GitHub (Production Cloud)

---

## 1. Directory & Codebase Status
* **Location:** `c:\Users\idea\OneDrive\Desktop\projects\stcks_predictor`
* **Initial State:** Clean/empty project workspace directory.
* **Sibling Projects:** 
  * `REA\swingexploder`: Web dashboard with local Vite server running on port 5050.
* **Preservation Policy:** All existing files in sibling directories are isolated and untouched.

---

## 2. Runtime Environment & Dependencies
* **Python Runtime:** Python 3.12 (64-bit)
* **Available Data Science Libraries:**
  * `pandas` (3.1.0)
  * `numpy` (2.5.4)
  * `SQLAlchemy` (2.0.51) & `aiosqlite` (0.22.1)
  * `pillow` (11.3.0) — High-res PDF & visual report generation
  * `fastapi` (0.139.0) & `uvicorn` (0.51.0) — Lightweight REST API
  * `rich` (15.0.0) — Terminal visual logging & progress tracking
  * `pydantic` (2.13.4) — Typed schema validation
  * `requests` & `httpx` — HTTP clients for remote MCP and REST endpoints
* **Storage Options:**
  * Local Development: SQLite (`research_store.db`) with WAL mode + Parquet storage for OHLCV datasets.
  * Cloud Production: Managed PostgreSQL (Render/Railway/Supabase) + Object storage (S3/R2/Cloudflare).

---

## 3. Cloud Deployment Compatibility Audit
* **Antigravity Context vs. Cloud Worker:**
  * Local execution runs inside Antigravity sandbox (governed by execution policies).
  * Production cloud execution requires a persistent, headless background worker (Render / Railway) capable of running scheduled cron cycles (Daily data sync, Weekly walk-forward, Monthly strategy search).
* **MCP Transport Verification:**
  * Verified MCP connections: **Remote HTTP/SSE** endpoints hosted at `https://mcp.nseindia.in`.
  * Because these are remote HTTP endpoints (and not local stdio pipes), the cloud worker can directly reach the MCP server endpoints over HTTPS without needing local desktop processes.
