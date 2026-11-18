class StrategyLeaderboard:
    """
    Ranks strategies based on Out-Of-Sample (OOS) risk-adjusted performance,
    consistency across walk-forward splits, and execution robustness.
    """
    @staticmethod
    def compute_composite_score(validation_result: dict) -> float:
        """
        Computes a weighted composite score (0 to 100) favoring risk-adjusted return
        and penalizing severe drawdowns and overfit.
        """
        oos = validation_result["out_of_sample"]
        degradation = validation_result["sharpe_degradation"]

        sharpe = max(0.0, oos["sharpe_ratio"])
        profit_factor = max(0.0, min(5.0, oos["profit_factor"]))
        calmar = max(0.0, min(5.0, oos["calmar_ratio"]))
        win_rate = oos["win_rate"]
        max_dd = oos["max_drawdown"]

        # Score components (0 - 100 scale)
        s_sharpe = min(100.0, sharpe * 35.0)
        s_pf = min(100.0, (profit_factor - 1.0) * 40.0) if profit_factor > 1.0 else 0.0
        s_calmar = min(100.0, calmar * 20.0)
        s_wr = win_rate * 100.0
        s_dd = max(0.0, (0.30 - max_dd) / 0.30 * 100.0)

        # Weighted combination
        raw_score = (
            (s_sharpe * 0.30) +
            (s_pf * 0.25) +
            (s_calmar * 0.20) +
            (s_wr * 0.15) +
            (s_dd * 0.10)
        )

        # Penalize if severe degradation between In-Sample and Out-of-Sample
        penalty = 1.0
        if degradation < 0.50:
            penalty = degradation * 1.5

        return round(raw_score * penalty, 2)

    @staticmethod
    def evaluate_candidates(results: list) -> dict:
        """
        Evaluates a list of strategy validation results, separates accepted from rejected,
        and sorts by Composite Score.
        """
        accepted = []
        rejected = []

        for res in results:
            oos = res["out_of_sample"]
            rejection_reasons = []

            if oos["trade_count"] < 8:
                rejection_reasons.append(f"Insufficient trade count ({oos['trade_count']} < 8)")
            if oos["profit_factor"] < 1.15:
                rejection_reasons.append(f"Low Out-Of-Sample profit factor ({oos['profit_factor']} < 1.15)")
            if oos["max_drawdown"] > 0.25:
                rejection_reasons.append(f"High Out-Of-Sample drawdown ({oos['max_drawdown']*100:.1f}% > 25%)")
            if res["sharpe_degradation"] < 0.35 and res["in_sample"]["sharpe_ratio"] > 1.5:
                rejection_reasons.append(f"Severe overfit (OOS Sharpe degradation {res['sharpe_degradation']:.2f} < 0.35)")

            score = StrategyLeaderboard.compute_composite_score(res)
            res["composite_score"] = score

            if not rejection_reasons:
                accepted.append(res)
            else:
                res["rejection_reasons"] = rejection_reasons
                rejected.append(res)

        # Sort accepted by composite score descending
        accepted.sort(key=lambda x: x["composite_score"], reverse=True)

        return {
            "total_tested": len(results),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "leaderboard": accepted,
            "rejected": rejected
        }
