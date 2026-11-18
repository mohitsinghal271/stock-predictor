import pandas as pd
import numpy as np
from src.strategies.base import BaseStrategy

class DonchianBreakoutStrategy(BaseStrategy):
    """
    Classic Turtle Trend / Donchian Breakout:
    Entry: Close breaks above the N-day highest high.
    Exit: Close drops below the M-day lowest low or trailing stop.
    """
    def __init__(self, entry_period: int = 20, exit_period: int = 10):
        super().__init__("DonchianBreakout", {
            "entry_period": entry_period,
            "exit_period": exit_period
        })

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        high = df["high"]
        low = df["low"]
        close = df["close"]

        upper_channel = high.shift(1).rolling(window=self.params["entry_period"]).max()
        lower_channel = low.shift(1).rolling(window=self.params["exit_period"]).min()

        signals = pd.Series(0, index=df.index)
        is_long = False

        for i in range(len(df)):
            c = close.iloc[i]
            u = upper_channel.iloc[i]
            l = lower_channel.iloc[i]

            if not is_long:
                if not np.isnan(u) and c > u:
                    is_long = True
            else:
                if not np.isnan(l) and c < l:
                    is_long = False

            signals.iloc[i] = 1 if is_long else 0

        return signals


class VolumeConfirmedBreakoutStrategy(BaseStrategy):
    """
    Breakout confirmed by institutional volume:
    Entry: 20-day high breakout + Volume >= 1.75x 20-day Volume Average.
    Exit: Close drops below 20-day EMA or trailing stop.
    """
    def __init__(self, lookback: int = 20, volume_factor: float = 1.75, exit_ema: int = 20):
        super().__init__("VolumeConfirmedBreakout", {
            "lookback": lookback,
            "volume_factor": volume_factor,
            "exit_ema": exit_ema
        })

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        high = df["high"]
        close = df["close"]
        volume = df["volume"]

        prior_high = high.shift(1).rolling(window=self.params["lookback"]).max()
        avg_vol = volume.shift(1).rolling(window=self.params["lookback"]).mean()
        exit_ema = close.ewm(span=self.params["exit_ema"], adjust=False).mean()

        signals = pd.Series(0, index=df.index)
        is_long = False

        for i in range(len(df)):
            c = close.iloc[i]
            v = volume.iloc[i]
            ph = prior_high.iloc[i]
            av = avg_vol.iloc[i]
            ee = exit_ema.iloc[i]

            if not is_long:
                if not np.isnan(ph) and not np.isnan(av) and c > ph and v >= (av * self.params["volume_factor"]):
                    is_long = True
            else:
                if c < ee:
                    is_long = False

            signals.iloc[i] = 1 if is_long else 0

        return signals
