# STRATEGY ROBUSTNESS & OVERFIT FILTERING REPORT

## Evaluation Criteria
1. Out-of-Sample Profit Factor >= 1.25.
2. Parameter Sensitivity: +/- 20% parameter perturbation maintains >= 80% of original Sharpe.
3. Maximum Permitted Drawdown: <= 20% on Portfolio basis.
4. Monte Carlo 10,000 P95 Drawdown <= 35%.

## Status
* **DualEMAMomentum(20/50 & 50/100):** **ROBUST (Passed all walk-forward tests)**
* **DonchianBreakout(50/20):** **ROBUST (Passed)**
* **VCPRocketStrategy:** **ROBUST (Passed)**
* **Unconstrained Fast EMA (5/15):** **REJECTED (High fee friction and whipsaw)**
