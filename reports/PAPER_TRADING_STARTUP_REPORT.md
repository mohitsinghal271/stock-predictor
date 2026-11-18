# PAPER TRADING INCUBATION STARTUP REPORT (30-DAY PROGRAMME)
**Project:** `stcks_predictor` | **Phase 13C Live Paper Incubation**  
**Startup Timestamp:** 2026-11-17 11:57:40  
**Database Storage:** `data_store/research_store.db` (SQLite Persistent ACID Storage)  
**Real-Money Trading:** **STRICTLY DISABLED (RESEARCH & PAPER TRADING ONLY)**

---

## 1. Portfolio Initialization Status

| Portfolio ID | Description | Base Capital | Current Cash | Capital Deployed | Open Risk | Active Slots | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`PORTFOLIO_A_INTRADAY`** | Track A: Independent Intraday (5m/15m ORB) | ₹5,00,000.00 | ₹5,00,000.00 | ₹0.00 (0.0%) | ₹0.00 (0.0%) | 0 / 5 | **`ACTIVE`** |
| **`PORTFOLIO_B_SWING`** | Track B: Independent Swing (2–20 days) | ₹5,00,000.00 | ₹2,52,236.60 | ₹2,47,763.40 (49.5%) | ₹12,388.17 (2.48%) | 3 / 5 | **`ACTIVE`** |
| **`PORTFOLIO_C_POSITIONAL`** | Track C: Independent Positional (20–120 days) | ₹5,00,000.00 | ₹2,52,236.60 | ₹2,47,763.40 (49.5%) | ₹12,388.17 (2.48%) | 3 / 5 | **`ACTIVE`** |
| **`PORTFOLIO_D_COMBINED`** | Mode 2: Multi-Style Shared Capital Pool | ₹5,00,000.00 | ₹2,52,236.60 | ₹2,47,763.40 (49.5%) | ₹12,388.17 (2.48%) | 3 / 5 | **`ACTIVE`** |

---

## 2. Seeded Verified & Resized Initial Positions

| **`KOTAKBANK`** | Financials | APPROVED | 201 sh | ₹496.40 | ₹471.58 | ₹99,776.40 | ₹4,988.82 (1.0%) |
| **`BEML`** | Defense_Rail | APPROVED | 47 sh | ₹2,087.00 | ₹1,982.65 | ₹98,089.00 | ₹4,904.45 (0.98%) |
| **`HDFCBANK`** | Financials | APPROVED (RESIZED) | 61 sh | ₹818.00 | ₹777.10 | ₹49,898.00 | ₹2,494.90 (0.5%) |


### Sector Compliance Verification:
* **Financials (Banking):** `KOTAKBANK` (₹99,776.40) + `HDFCBANK` (₹49,898.00) = **`₹1,49,674.40`** (**29.93%** of capital <= 30.0% cap). **PASS.**
* **Defense / Rail:** `BEML` = **`₹98,089.00`** (**19.62%** of capital <= 30.0% cap). **PASS.**
* **Total Portfolio Open Risk:** **`₹12,388.17`** (**2.48%** of capital <= 3.0% cap). **PASS.**
* **Total Capital Deployed:** **`₹2,47,763.40`** (**49.55%** of capital <= 80.0% cap). **PASS.**

---

## 3. Automated Monitoring Schedule & Daily Routines

1. **Daily Market Close (15:35 IST):**
   * Stream live closing prices from NSE MCP server.
   * Mark-to-market all open positions in SQLite `positions` table.
   * Check stop-loss hits (trigger EXIT if `low <= stop_loss`).
   * Check target hits (trigger partial scale-out if `high >= target_1`).
   * Square off all intraday positions for `PORTFOLIO_A_INTRADAY` at 15:15 IST.
   * Log daily equity, cash, open risk, and sector exposure in `daily_equity_log`.
2. **Weekly Performance Audit (Every Friday 18:00 IST):**
   * Compute rolling weekly returns, maximum drawdown, Sharpe, and Sortino across all 4 portfolios.
   * Compare execution slippage against the 10 bps model.
   * Audit rejected candidate setups and record explanations.
3. **Day 30 Final Incubation Verdict:**
   * Evaluate whether any strategy breached risk criteria.
   * Generate `PAPER_TRADING_FINAL_REPORT.md` and full trade ledger CSVs.
