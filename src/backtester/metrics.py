import numpy as np
import pandas as pd

class PerformanceMetrics:
    """
    Computes professional quantitative performance, risk, and drawdown statistics
    for strategy evaluation and ranking.
    """
    @staticmethod
    def calculate(equity_curve: pd.Series, trade_returns: list, risk_free_rate: float = 0.07) -> dict:
        """
        Calculates all risk-adjusted and trade distribution metrics.
        equity_curve: Daily portfolio equity series indexed by datetime.
        trade_returns: List of net percentage returns per closed trade.
        risk_free_rate: Annualized risk-free rate (7% for Indian RBI 10Y G-Sec).
        """
        if equity_curve.empty or len(equity_curve) < 2:
            return PerformanceMetrics.empty_metrics()

        # 1. Total Return & CAGR
        initial_equity = equity_curve.iloc[0]
        final_equity = equity_curve.iloc[-1]
        total_return = (final_equity - initial_equity) / initial_equity if initial_equity > 0 else 0.0

        n_days = len(equity_curve)
        years = n_days / 252.0
        if years > 0 and final_equity > 0:
            cagr = (final_equity / initial_equity) ** (1.0 / years) - 1.0
        else:
            cagr = 0.0

        # 2. Daily Returns & Volatility
        daily_returns = equity_curve.pct_change().dropna()
        daily_rf = (1.0 + risk_free_rate) ** (1.0 / 252.0) - 1.0
        excess_daily_returns = daily_returns - daily_rf

        ann_vol = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0.0

        # 3. Sharpe Ratio
        if ann_vol > 0:
            sharpe = (cagr - risk_free_rate) / ann_vol
        else:
            sharpe = 0.0

        # 4. Sortino Ratio (Downside deviation only)
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 1 else 0.0
        sortino = (cagr - risk_free_rate) / downside_std if downside_std > 0 else 0.0

        # 5. Drawdown & Calmar Ratio
        rolling_max = equity_curve.cummax()
        drawdown_series = (equity_curve - rolling_max) / rolling_max
        max_drawdown = abs(drawdown_series.min()) if not drawdown_series.empty else 0.0
        calmar = cagr / max_drawdown if max_drawdown > 0 else 0.0

        # 6. Trade Distribution Statistics
        n_trades = len(trade_returns)
        if n_trades > 0:
            tr_array = np.array(trade_returns)
            wins = tr_array[tr_array > 0]
            losses = tr_array[tr_array < 0]

            win_rate = len(wins) / n_trades
            avg_win = float(wins.mean()) if len(wins) > 0 else 0.0
            avg_loss = float(abs(losses.mean())) if len(losses) > 0 else 0.0

            gross_profit = float(wins.sum()) if len(wins) > 0 else 0.0
            gross_loss = float(abs(losses.sum())) if len(losses) > 0 else 0.0

            if gross_loss > 0:
                profit_factor = gross_profit / gross_loss
            elif gross_profit > 0:
                profit_factor = 99.0
            else:
                profit_factor = 0.0

            expectancy = (win_rate * avg_win) - ((1.0 - win_rate) * avg_loss)
            win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0.0
        else:
            win_rate = 0.0
            avg_win = 0.0
            avg_loss = 0.0
            profit_factor = 0.0
            expectancy = 0.0
            win_loss_ratio = 0.0

        # 7. Recovery Factor
        recovery_factor = total_return / max_drawdown if max_drawdown > 0 else 0.0

        return {
            "cagr": round(cagr, 4),
            "total_return": round(total_return, 4),
            "annualized_volatility": round(ann_vol, 4),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "calmar_ratio": round(calmar, 2),
            "max_drawdown": round(max_drawdown, 4),
            "profit_factor": round(profit_factor, 2),
            "win_rate": round(win_rate, 4),
            "avg_win": round(avg_win, 4),
            "avg_loss": round(avg_loss, 4),
            "win_loss_ratio": round(win_loss_ratio, 2),
            "expectancy": round(expectancy, 4),
            "trade_count": n_trades,
            "recovery_factor": round(recovery_factor, 2)
        }

    @staticmethod
    def empty_metrics() -> dict:
        return {
            "cagr": 0.0,
            "total_return": 0.0,
            "annualized_volatility": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "calmar_ratio": 0.0,
            "max_drawdown": 0.0,
            "profit_factor": 0.0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "win_loss_ratio": 0.0,
            "expectancy": 0.0,
            "trade_count": 0,
            "recovery_factor": 0.0
        }
