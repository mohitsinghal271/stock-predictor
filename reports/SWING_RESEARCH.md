# TRACK B: SWING TRADING RESEARCH REPORT
**Initial Capital:** INR 500,000 | **Holding Period:** 2–20 Days | **Cost Model:** Statutory Delivery STT (0.10% buy & sell)

## Performance Matrix
| Strategy | CAGR | Sharpe | Max DD | Profit Factor | Win Rate | Trades | P95 DD |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DualEMAMomentum(fast_span=20, slow_span=50, trend_span=200) | 181.26% | 3.73 | 21.92% | 2.85 | 32.51% | 323 | 78.07% |
| DualEMAMomentum(fast_span=10, slow_span=30, trend_span=0) | 117.08% | 3.68 | 15.15% | 2.45 | 39.86% | 429 | 71.77% |
| DonchianBreakout(entry_period=20, exit_period=10) | 113.04% | 4.28 | 10.03% | 2.20 | 40.93% | 386 | 69.40% |
| VolumeConfirmedBreakout(lookback=20, volume_factor=1.75, exit_ema=20) | 170.93% | 6.14 | 7.84% | 2.42 | 44.52% | 155 | 50.74% |
| VCPRocketStrategy(atr_fast=10, atr_slow=30, vol_mult=1.8, stop_loss_pct=0.08) | 449.56% | 12.60 | 3.50% | 3.99 | 50.00% | 58 | 30.50% |
| RSIMomentumTrend(rsi_period=14, rsi_buy=55.0, rsi_sell=45.0, ema_trend=50) | 64.83% | 2.49 | 12.36% | 1.86 | 39.90% | 599 | 77.92% |
| BollingerMeanReversion(bb_period=20, num_std=2.0, rsi_entry=35.0, rsi_exit=60.0) | 2.11% | -0.34 | 23.51% | 1.02 | 54.10% | 366 | 88.76% |
