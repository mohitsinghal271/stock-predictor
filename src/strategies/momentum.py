import pandas as pd
import numpy as np
from src.strategies.base import BaseStrategy

class DualEMAMomentumStrategy(BaseStrategy):
    """
    Momentum Strategy based on Fast EMA > Slow EMA with optional Long-Term Trend Filter.
    Parameters:
      fast_span: Fast EMA window (e.g. 10, 20)
      slow_span: Slow EMA window (e.g. 50, 100)
      trend_span: 200 EMA macro filter (optional, 0 to disable)
    """
    def __init__(self, fast_span: int = 20, slow_span: int = 50, trend_span: int = 200):
        super().__init__("DualEMAMomentum", {
            "fast_span": fast_span,
            "slow_span": slow_span,
            "trend_span": trend_span
        })

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        fast_ema = close.ewm(span=self.params["fast_span"], adjust=False).mean()
        slow_ema = close.ewm(span=self.params["slow_span"], adjust=False).mean()

        condition = fast_ema > slow_ema

        if self.params["trend_span"] > 0:
            trend_ema = close.ewm(span=self.params["trend_span"], adjust=False).mean()
            condition = condition & (close > trend_ema)

        signals = pd.Series(0, index=df.index)
        signals[condition] = 1
        return signals


class RSIMomentumTrendStrategy(BaseStrategy):
    """
    RSI Bullish Regime Strategy: Holds long when RSI > rsi_buy and price is above 50 EMA.
    Exits when RSI drops below rsi_sell.
    """
    def __init__(self, rsi_period: int = 14, rsi_buy: float = 55.0, rsi_sell: float = 45.0, ema_trend: int = 50):
        super().__init__("RSIMomentumTrend", {
            "rsi_period": rsi_period,
            "rsi_buy": rsi_buy,
            "rsi_sell": rsi_sell,
            "ema_trend": ema_trend
        })

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params["rsi_period"]).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params["rsi_period"]).mean()
        rs = gain / (loss.replace(0, np.nan))
        rsi = 100 - (100 / (1 + rs))

        ema = close.ewm(span=self.params["ema_trend"], adjust=False).mean()

        signals = pd.Series(0, index=df.index)
        is_long = False
        for i in range(len(df)):
            curr_rsi = rsi.iloc[i]
            curr_close = close.iloc[i]
            curr_ema = ema.iloc[i]

            if not is_long:
                if curr_rsi > self.params["rsi_buy"] and curr_close > curr_ema:
                    is_long = True
            else:
                if curr_rsi < self.params["rsi_sell"] or curr_close < curr_ema * 0.98:
                    is_long = False

            signals.iloc[i] = 1 if is_long else 0

        return signals
