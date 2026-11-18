import pandas as pd
import numpy as np
from src.strategies.base import BaseStrategy

class BollingerMeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion using Bollinger Bands & RSI:
    Entry: Price closes below the Lower Bollinger Band AND RSI < 35 (Oversold).
    Exit: Price reaches the Middle Band (20 SMA) or RSI > 60.
    """
    def __init__(self, bb_period: int = 20, num_std: float = 2.0, rsi_entry: float = 35.0, rsi_exit: float = 60.0):
        super().__init__("BollingerMeanReversion", {
            "bb_period": bb_period,
            "num_std": num_std,
            "rsi_entry": rsi_entry,
            "rsi_exit": rsi_exit
        })

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        sma = close.rolling(window=self.params["bb_period"]).mean()
        std = close.rolling(window=self.params["bb_period"]).std()
        lower_band = sma - (self.params["num_std"] * std)

        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss.replace(0, np.nan))
        rsi = 100 - (100 / (1 + rs))

        signals = pd.Series(0, index=df.index)
        is_long = False

        for i in range(len(df)):
            c = close.iloc[i]
            lb = lower_band.iloc[i]
            mb = sma.iloc[i]
            r = rsi.iloc[i]

            if not is_long:
                if not np.isnan(lb) and c < lb and r < self.params["rsi_entry"]:
                    is_long = True
            else:
                if (not np.isnan(mb) and c >= mb) or r >= self.params["rsi_exit"]:
                    is_long = False

            signals.iloc[i] = 1 if is_long else 0

        return signals
