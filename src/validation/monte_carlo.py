import numpy as np

class MonteCarloSimulator:
    """
    Performs bootstrap resampling of trade returns to stress-test drawdowns
    and compute confidence intervals for strategy equity paths.
    """
    @staticmethod
    def run(trade_returns: list, iterations: int = 10000, initial_capital: float = 1000000.0) -> dict:
        """
        Fully vectorized bootstrap resampling of trade return sequences.
        Simulates 10,000 iterations in milliseconds using numpy.
        """
        if not trade_returns or len(trade_returns) < 5:
            return {
                "p50_max_dd": 0.0,
                "p95_max_dd": 0.0,
                "p99_max_dd": 0.0,
                "risk_of_ruin_pct": 0.0
            }

        returns_arr = np.array(trade_returns)
        # Cap max trades sampled to 2,000 to keep statistical validity while fast
        sample_size = min(len(returns_arr), 2000)

        # Generate matrix of shape (iterations, sample_size)
        sampled_matrix = np.random.choice(returns_arr, size=(iterations, sample_size), replace=True)
        equity_matrix = initial_capital * np.cumprod(1.0 + sampled_matrix, axis=1)
        peaks = np.maximum.accumulate(equity_matrix, axis=1)
        drawdowns = (equity_matrix - peaks) / peaks
        max_dds = np.abs(np.min(drawdowns, axis=1))

        ruin_count = np.sum(max_dds >= 0.50)

        return {
            "p50_max_dd": round(float(np.percentile(max_dds, 50)), 4),
            "p95_max_dd": round(float(np.percentile(max_dds, 95)), 4),
            "p99_max_dd": round(float(np.percentile(max_dds, 99)), 4),
            "risk_of_ruin_pct": round(float((ruin_count / iterations) * 100.0), 2)
        }
