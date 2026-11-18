from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    """
    Abstract base class for all parameterized quantitative trading strategies.
    Every strategy takes a price DataFrame and returns a Series of position signals:
    1 = Long, 0 = Flat/Cash.
    """
    def __init__(self, name: str, params: dict = None):
        self.name = name
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Takes cleaned OHLCV DataFrame (sorted chronologically).
        Must return a pd.Series of signals (1 or 0) aligned with df.index.
        STRICT RULE: Signal on bar i can only use information available at or before bar i.
        Execution occurs on bar i+1 Open.
        """
        pass

    def get_description(self) -> str:
        param_str = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name}({param_str})"
