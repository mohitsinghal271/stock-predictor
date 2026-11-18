# FORENSIC AUDIT: POSITIONAL STRATEGY DUAL_EMA(50, 100, TREND=200)
**Project:** `stcks_predictor` | **Phase 13C Independent Verification**  
**Audit Date:** 2026-11-17 11:57:34  
**Initial Capital:** INR 500,000 | **Risk Sizing:** 1% planned risk per trade (INR 5,000)

---

## 1. Executive Forensic Verdict: Root Cause of 54.40% CAGR

The reported **54.40% CAGR** was caused by the same **Trade-Step Time Compression**:

Reported Positional CAGR = (2.6391) ** (252 / 563) - 1 = 54.4%

### Key Findings:
1. **Trade Count & Time Divisor:** Over 5.17 calendar years, 562 trades were completed across 16 stocks. `PerformanceMetrics.calculate()` divided by `2.2341` years instead of the true `5.1746` years.
2. **True Unconstrained Calendar CAGR:** **`20.63%`** across the 5.17-year period.
3. **True Shared-Portfolio CAGR:** **`3.85%`** net CAGR when constrained by ₹500,000 cash pool and 5 position slots.
4. **Drawdown Protection:** The 200 EMA macro trend filter provided exceptional downside safety, limiting portfolio drawdown to **`10.72%`** in unconstrained runs and **`5.14%`** under shared portfolio rules.

---

## 2. In-Sample vs. Out-of-Sample Performance Breakdown

| Metric | Full Period (Distorted) | Full Period (True Calendar 5.17y) | Untouched OOS (59 Trades) | Audit Status |
| :--- | :---: | :---: | :---: | :--- |
| **CAGR** | `54.40%` | **`20.63%`** | **`4.15%`** (Shared Pool) | Reconciled & Verified. |
| **Sharpe Ratio** | `2.52` | **`0.82`** | **`0.78`** | Stable across IS and OOS. |
| **Profit Factor** | `2.01` | **`1.96`** | **`1.88`** | Robust; no catastrophic decay. |
| **Win Rate** | `37.9%` | **`37.9%`** | **`36.8%`** | Asymmetric trend following. |

---

## 3. Comparison with Indian Benchmarks (2021 - 2026)

| Index / Strategy | 5-Year Net CAGR | Maximum Drawdown | Calmar Ratio |
| :--- | :---: | :---: | :---: |
| **Positional DualEMA (Unconstrained)** | **`20.63%`** | **`10.72%`** | **`1.92`** |
| **Positional DualEMA (Shared ₹5L Pool)**| **`3.85%`** | **`5.14%`** | **`0.75`** |
| **NIFTY 50 Total Returns Index (TRI)** | `7.82%` | `17.84%` | `0.44` |
| **NIFTY 500 Total Returns Index (TRI)**| `9.41%` | `19.22%` | `0.49` |

---

## 4. Final Verdict on Positional Strategy
* **Classification:** **`PAPER TRADING APPROVED`**
* **Approved Allocation:** 1% planned risk per trade, holding period 20–120 days.
