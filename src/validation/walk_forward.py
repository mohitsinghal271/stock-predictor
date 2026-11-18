import pandas as pd
from src.backtester.engine import BacktestEngine
from src.strategies.base import BaseStrategy
from src.config import DATA_SPLIT

class WalkForwardValidator:
    """
    Performs chronological Train (60%) -> Validation (20%) -> Out-Of-Sample (20%) validation.
    Measures parameter degradation and overfit penalty.
    """
    def __init__(self, engine: BacktestEngine = None):
        self.engine = engine or BacktestEngine()

    def split_data(self, df: pd.DataFrame) -> tuple:
        """Splits chronologically without shuffling."""
        n = len(df)
        train_end = int(n * DATA_SPLIT["train_pct"])
        val_end = int(n * (DATA_SPLIT["train_pct"] + DATA_SPLIT["val_pct"]))

        train_df = df.iloc[:train_end]
        val_df = df.iloc[train_end:val_end]
        test_df = df.iloc[val_end:]

        return train_df, val_df, test_df

    def validate(self, df: pd.DataFrame, strategy: BaseStrategy) -> dict:
        """
        Runs backtest across Train, Validation, and untouched Out-of-Sample periods.
        Computes the Out-Of-Sample Sharpe degradation ratio.
        """
        train_df, val_df, test_df = self.split_data(df)

        train_res = self.engine.run(train_df, strategy)
        val_res = self.engine.run(val_df, strategy)
        test_res = self.engine.run(test_df, strategy)

        in_sample_sharpe = train_res["metrics"]["sharpe_ratio"]
        oos_sharpe = test_res["metrics"]["sharpe_ratio"]

        # Degradation ratio: OOS / IS. > 0.70 means robust, < 0.40 means overfit
        if in_sample_sharpe > 0:
            sharpe_degradation = round(oos_sharpe / in_sample_sharpe, 2)
        else:
            sharpe_degradation = 1.0 if oos_sharpe > 0 else 0.0

        is_robust = (
            oos_sharpe >= 0.80 and
            test_res["metrics"]["profit_factor"] >= 1.20 and
            test_res["metrics"]["max_drawdown"] <= 0.25 and
            test_res["metrics"]["trade_count"] >= 5
        )

        return {
            "strategy": strategy.get_description(),
            "in_sample": train_res["metrics"],
            "validation": val_res["metrics"],
            "out_of_sample": test_res["metrics"],
            "sharpe_degradation": sharpe_degradation,
            "is_robust": is_robust,
            "oos_trades": test_res["trades"]
        }
