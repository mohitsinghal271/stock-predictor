# PHASE 13B: REPORT ACCURACY RECONCILIATION
**Audit of PDF Discrepancy & Forensic Metric Verification**

---

## 1. Discrepancy Identified
* The previous PDF report showed:
  * Strategy: `DualEMAMomentum(50, 100, 200)`
  * Profit Factor: **`28.49`**
  * P95 Monte Carlo DD: **`58.5%`**
  * Risk of Ruin: **`14.4%`**
* Meanwhile, the Phase 12 forensic audit reported an aggregate profit factor of **`2.72`**.

---

## 2. Root Cause Discovery
* **The Culprit:** In `run_research.py`, `generate_pdf_research_report()` directly loaded `research_summary.json`. 
* That JSON file had stored the **unweighted arithmetic mean of individual stock profit factors** (`np.mean([m['profit_factor']...])`).
* When single stocks in the test basket had 0 losing trades in the test slice, division by zero was capped at `99.0`, artificially inflating the mean to `28.49`.
* The forensic audit had correctly calculated the **true portfolio aggregate**:
  $$	ext{True Profit Factor} = rac{\sum 	ext{Gross Net Profits}}{\sum |	ext{Gross Net Losses}|} = rac{₹26,92,093.97}{₹9,88,323.03} = \mathbf{2.72}$$
* **Fix Applied:** `run_phase13b.py` directly overrides the report rendering pipeline to enforce true aggregate dollar profit factor accounting. The regenerated PDF now strictly states **`2.72`**.
