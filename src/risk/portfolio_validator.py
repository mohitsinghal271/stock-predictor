import math
from typing import Dict, List, Any, Optional

class PortfolioRiskValidator:
    """
    Enforces portfolio-level risk constraints for Indian Cash Equity accounts:
    - Maximum single trade risk: 1.0% of portfolio equity (Default Rs 5,000 on Rs 500,000)
    - Maximum aggregate open risk: 3.0% of portfolio equity (Default Rs 15,000)
    - Maximum sector exposure: 30.0% of portfolio capital (Default Rs 150,000)
    - Maximum total capital deployment: 80.0% (Default Rs 400,000 with 20% safety cash reserve)
    - Maximum concurrent open positions: 5 slots
    - Single position slot cap: 20.0% of equity (Default Rs 100,000)
    """
    def __init__(
        self,
        initial_capital: float = 500000.0,
        max_risk_per_trade: float = 0.01,
        max_open_portfolio_risk: float = 0.03,
        max_sector_exposure: float = 0.30,
        max_capital_deployment: float = 0.80,
        max_concurrent_positions: int = 5
    ):
        self.initial_capital = initial_capital
        self.max_risk_per_trade = max_risk_per_trade
        self.max_open_portfolio_risk = max_open_portfolio_risk
        self.max_sector_exposure = max_sector_exposure
        self.max_capital_deployment = max_capital_deployment
        self.max_concurrent_positions = max_concurrent_positions

    def validate_and_size_candidate(
        self,
        current_equity: float,
        available_cash: float,
        existing_positions: List[Dict[str, Any]],
        candidate: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates a candidate signal against current portfolio state.
        If adding the position would breach sector, cash, or aggregate risk limits,
        it automatically resizes the position to fit within available capacity,
        or rejects if capacity is zero.
        """
        symbol = candidate["symbol"]
        sector = candidate.get("sector", "Diversified")
        entry_price = candidate["ltp"]
        stop_loss = candidate["stop_loss"]

        risk_per_share = round(abs(entry_price - stop_loss), 2)
        if risk_per_share < 0.01 or entry_price <= 0:
            return {
                "symbol": symbol,
                "decision": "REJECTED",
                "shares": 0,
                "allocated_capital": 0.0,
                "rupee_risk": 0.0,
                "reason": "Invalid entry price or stop loss"
            }

        # 1. Check open slots
        if len(existing_positions) >= self.max_concurrent_positions:
            return {
                "symbol": symbol,
                "decision": "REJECTED",
                "shares": 0,
                "allocated_capital": 0.0,
                "rupee_risk": 0.0,
                "reason": f"Maximum concurrent positions ({self.max_concurrent_positions}) reached"
            }

        # 2. Prevent duplicate symbol
        for pos in existing_positions:
            if pos["symbol"] == symbol:
                return {
                    "symbol": symbol,
                    "decision": "REJECTED",
                    "shares": 0,
                    "allocated_capital": 0.0,
                    "rupee_risk": 0.0,
                    "reason": f"Symbol {symbol} already active in portfolio"
                }

        # 3. Calculate current portfolio risk & sector allocations
        current_open_risk = sum(p.get("rupee_risk", 0.0) for p in existing_positions)
        current_sector_capital = sum(
            p.get("allocated_capital", 0.0) for p in existing_positions if p.get("sector") == sector
        )
        total_deployed_capital = sum(p.get("allocated_capital", 0.0) for p in existing_positions)

        # Limits in INR
        max_trade_risk_inr = current_equity * self.max_risk_per_trade
        max_portfolio_risk_inr = current_equity * self.max_open_portfolio_risk
        max_sector_capital_inr = current_equity * self.max_sector_exposure
        max_total_deployment_inr = current_equity * self.max_capital_deployment
        max_slot_capital_inr = current_equity / self.max_concurrent_positions

        # 4. Remaining capacity checks
        remaining_risk_budget = max(0.0, max_portfolio_risk_inr - current_open_risk)
        effective_trade_risk_budget = min(max_trade_risk_inr, remaining_risk_budget)

        remaining_sector_capacity = max(0.0, max_sector_capital_inr - current_sector_capital)
        remaining_deployment_capacity = max(0.0, max_total_deployment_inr - total_deployed_capital)
        usable_cash = max(0.0, available_cash - (current_equity * (1.0 - self.max_capital_deployment)))

        # Sizing bounds
        # A. By Planned Risk (1% risk or remaining open risk)
        qty_by_risk = math.floor(effective_trade_risk_budget / risk_per_share) if risk_per_share > 0 else 0

        # B. By Slot Capital (20% max single slot)
        qty_by_slot = math.floor(max_slot_capital_inr / entry_price)

        # C. By Sector Limit (30% max sector allocation)
        qty_by_sector = math.floor(remaining_sector_capacity / entry_price)

        # D. By Total Deployment Limit (80% max deployment)
        qty_by_deployment = math.floor(remaining_deployment_capacity / entry_price)

        # E. By Available Cash
        qty_by_cash = math.floor(usable_cash / entry_price)

        # Constrained Quantity is the strict minimum across all 5 risk dimensions
        final_qty = max(0, min(qty_by_risk, qty_by_slot, qty_by_sector, qty_by_deployment, qty_by_cash))
        allocated_capital = round(final_qty * entry_price, 2)
        actual_rupee_risk = round(final_qty * risk_per_share, 2)

        if final_qty <= 0:
            reasons = []
            if qty_by_sector <= 0: reasons.append(f"Sector limit reached ({sector}: Rs {current_sector_capital:,.2f} / Rs {max_sector_capital_inr:,.2f})")
            if qty_by_risk <= 0: reasons.append("Portfolio aggregate risk cap (3%) reached")
            if qty_by_cash <= 0: reasons.append("Insufficient available cash buffer")
            if qty_by_deployment <= 0: reasons.append("Total capital deployment cap (80%) reached")
            return {
                "symbol": symbol,
                "decision": "REJECTED",
                "shares": 0,
                "allocated_capital": 0.0,
                "rupee_risk": 0.0,
                "reason": " | ".join(reasons) or "Quantity constrained to zero"
            }

        # Check if resized
        is_resized = (final_qty < qty_by_risk)
        resize_reasons = []
        if final_qty == qty_by_sector and final_qty < qty_by_risk:
            resize_reasons.append(f"Resized by 30% Sector Cap ({sector}: headroom Rs {remaining_sector_capacity:,.2f})")
        if final_qty == qty_by_slot and final_qty < qty_by_risk:
            resize_reasons.append("Resized by 20% Single-Slot Cap")
        if final_qty == qty_by_cash and final_qty < qty_by_risk:
            resize_reasons.append("Resized by Available Cash")

        decision = "APPROVED (RESIZED)" if is_resized else "APPROVED"
        explanation = " | ".join(resize_reasons) if is_resized else "All portfolio risk checks passed"

        return {
            "symbol": symbol,
            "decision": decision,
            "shares": final_qty,
            "allocated_capital": allocated_capital,
            "rupee_risk": actual_rupee_risk,
            "sector": sector,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "risk_per_share": risk_per_share,
            "sector_exposure_after": round(current_sector_capital + allocated_capital, 2),
            "sector_pct_after": round((current_sector_capital + allocated_capital) / current_equity * 100, 2),
            "portfolio_risk_after": round(current_open_risk + actual_rupee_risk, 2),
            "portfolio_risk_pct_after": round((current_open_risk + actual_rupee_risk) / current_equity * 100, 2),
            "reason": explanation
        }
