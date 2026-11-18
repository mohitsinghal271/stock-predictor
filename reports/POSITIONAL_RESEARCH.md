# TRACK C: POSITIONAL TRADING RESEARCH REPORT
**Initial Capital:** INR 500,000 | **Holding Period:** 20–120 Days | **Cost Model:** Statutory Delivery STT

## Performance Matrix
| Strategy | CAGR | Sharpe | Max DD | Profit Factor | Win Rate | Trades | P95 DD |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| DualEMAMomentum(fast_span=50, slow_span=100, trend_span=200) | 54.40% | 2.52 | 10.72% | 2.01 | 37.90% | 562 | 79.66% |
| DualEMAMomentum(fast_span=50, slow_span=200, trend_span=200) | 46.70% | 2.10 | 9.58% | 1.88 | 38.10% | 609 | 82.60% |
| DonchianBreakout(entry_period=50, exit_period=20) | 83.14% | 3.42 | 8.72% | 2.21 | 39.82% | 329 | 74.06% |
| VolumeConfirmedBreakout(lookback=50, volume_factor=1.5, exit_ema=50) | 89.69% | 3.80 | 8.75% | 2.15 | 40.84% | 191 | 67.20% |
| RSIMomentumTrend(rsi_period=14, rsi_buy=60.0, rsi_sell=40.0, ema_trend=100) | 58.23% | 2.78 | 10.00% | 2.07 | 40.40% | 500 | 75.17% |
