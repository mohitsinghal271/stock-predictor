import pandas as pd
import numpy as np
from src.strategies.base import BaseStrategy

class VCPRocketStrategy(BaseStrategy):
    """
    Mark Minervini style Volatility Contraction Pattern (VCP) with Rocket Volume Thrust:
    1. Trend: Price > 50 EMA and 50 EMA > 200 EMA (Stage 2 Uptrend).
    2. Contraction: ATR(10) is lower than ATR(30) (Volatility has compressed).
    3. Trigger: Price breaks out of 10-day range with Volume > 1.8x 20-day Average Volume.
    4. Exit: Trailing stop below 20-day EMA or 8% fixed stop loss.
    """
    def __init__(self, atr_fast: int = 10, atr_slow: int = 30, vol_mult: float = 1.8, stop_loss_pct: float = 0.08):
        super().__init__("VCPRocketStrategy", {
            "atr_fast": atr_fast,
            "atr_slow": atr_slow,
            "vol_mult": vol_mult,
            "stop_loss_pct": stop_loss_pct
        })

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # 1. Trend Filter
        ema50 = close.ewm(span=50, adjust=False).mean()
        ema200 = close.ewm(span=200, adjust=False).mean()

        # 2. True Range & ATR
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr_fast = tr.rolling(window=self.params["atr_fast"]).mean()
        atr_slow = tr.rolling(window=self.params["atr_slow"]).mean()

        # 3. Volume & Range
        avg_vol = volume.shift(1).rolling(window=20).mean()
        high_10 = high.shift(1).rolling(window=10).max()
        exit_ema = close.ewm(span=20, adjust=False).mean()

        signals = pd.Series(0, index=df.index)
        is_long = False
        entry_price = 0.0

        for i in range(len(df)):
            c = close.iloc[i]
            v = volume.iloc[i]
            e50 = ema50.iloc[i]
            e200 = ema200.iloc[i]
            af = atr_fast.iloc[i]
            asl = atr_slow.iloc[i]
            av = avg_vol.iloc[i]
            h10 = high_10.iloc[i]
            ee = exit_ema.iloc[i]

            if not is_long:
                if (c > e50 and e50 > e200 and af < asl and
                    not np.isnan(h10) and c > h10 and
                    not np.isnan(av) and v >= av * self.params["vol_mult"]):
                    is_long = True
                    entry_price = c
            else:
                # Stop loss or trailing EMA exit
                if c < entry_price * (1.0 - self.params["stop_loss_pct"]) or c < ee:
                    is_long = False
                    entry_price = 0.0

            signals.iloc[i] = 1 if is_long else 0

        return signals
