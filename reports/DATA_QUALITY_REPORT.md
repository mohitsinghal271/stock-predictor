# DATA QUALITY & HISTORICAL INTEGRITY REPORT
**Phase 12 Independent Audit** | Date: 2026-11-17 10:47:18

## 1. Executive Summary
* **Total NSE Symbols Audited:** 36
* **Total Daily Candles Analyzed:** 46,944
* **OHLC Logic Violations (`Low > Open/Close` or `High < Open/Close`):** **0 (Zero Defect)**
* **Duplicate Timestamp Records:** **0 (Zero Defect)**
* **Historical Date Span:** 5.0 Years (Nov 2021 to Nov 2026)
* **Sampling Frequency:** Daily Trading Sessions (1,304 trading bars per symbol)

## 2. Integrity Verification Findings
1. **Candle Construction Validity (`VERIFIED`):**
   * Every recorded candle strictly satisfies `Low <= min(Open, Close)` and `High >= max(Open, Close)`.
   * Zero negative prices or infinite ratios exist in the datastore.
2. **Survivorship Bias Disclosure (`IMPORTANT LIMITATION`):**
   * The current datastore uses the top surviving liquid NSE equities (Nifty 50, Next 50, and leading midcaps).
   * **Limitation:** Historical delisted stocks (e.g. DHFL, Reliance Comm, Sintex) from 2018-2020 are not present in this surviving cohort. Strategies backtested strictly on this cohort benefit from a slight positive survival drift.
3. **Corporate Action Adjustments (`VERIFIED`):**
   * Historical prices are adjusted for stock splits and bonus issues (e.g. Reliance 1:1 bonus, Tata Motors split) to eliminate artificial 50% price gap anomalies.

## 3. Sample Symbol Audit Log
| Symbol | Records | Start Date | End Date | OHLC Violations | Duplicates | Quality Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BAJFINANCE | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| BDL | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| BEL | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| BEML | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| BHARTIARTL | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| BSE | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| CAMS | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| CDSL | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| CHOLAFIN | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| DIXON | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| HAL | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| HCLTECH | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| HDFCBANK | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| HINDUNILVR | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
| ICICIBANK | 1304 | 2021-11-18 | 2026-11-17 | 0 | 0 | **PASS** |
