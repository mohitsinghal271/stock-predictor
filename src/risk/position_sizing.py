import math
from src.config.research_profiles import CAPITAL_CONFIG

class RiskBasedPositionSizer:
    """
    Computes strict risk-based position sizing for Indian cash equity trades.
    Formula:
        risk_amount = current_equity * risk_pct (Default 1.0% = Rs 5,000 on Rs 5L)
        risk_per_share = abs(entry_price - stop_loss)
        raw_quantity = floor(risk_amount / risk_per_share)
    Enforces available cash ceiling, max single position ceiling (20% of equity),
    and capital deployment constraints (80% max deployed).
    """
    def __init__(self, config=None):
        self.c = config or CAPITAL_CONFIG

    def calculate_quantity(self, current_equity: float, available_cash: float, entry_price: float, stop_loss: float) -> dict:
        if entry_price <= 0 or stop_loss <= 0:
            return {"quantity": 0, "allocated_capital": 0.0, "risk_amount": 0.0, "reason": "Invalid price levels"}

        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share < 0.01:
            return {"quantity": 0, "allocated_capital": 0.0, "risk_amount": 0.0, "reason": "Stop loss too close to entry"}

        # 1. Planned Risk Amount (1% of equity)
        planned_risk = current_equity * self.c["max_risk_per_trade"]
        raw_qty = math.floor(planned_risk / risk_per_share)

        if raw_qty <= 0:
            return {"quantity": 0, "allocated_capital": 0.0, "risk_amount": 0.0, "reason": "Calculated quantity is zero"}

        # 2. Maximum Single Position Allocation constraint (20% of total equity)
        max_slot_capital = current_equity / self.c["max_concurrent_positions"]
        qty_by_slot = math.floor(max_slot_capital / entry_price)

        # 3. Available Cash constraint (accounting for 20% safety cash buffer)
        usable_cash = max(0.0, available_cash - (current_equity * (1.0 - self.c["max_capital_deployment"])))
        qty_by_cash = math.floor(usable_cash / entry_price)

        # Final Quantity is the minimum of risk-sized, slot-capped, and cash-limited
        final_qty = max(0, min(raw_qty, qty_by_slot, qty_by_cash))
        allocated_capital = round(final_qty * entry_price, 2)
        actual_risk_amount = round(final_qty * risk_per_share, 2)

        return {
            "quantity": final_qty,
            "allocated_capital": allocated_capital,
            "risk_amount": actual_risk_amount,
            "risk_per_share": round(risk_per_share, 2),
            "planned_risk": round(planned_risk, 2),
            "allocation_pct": round(allocated_capital / current_equity, 4) if current_equity > 0 else 0.0,
            "reason": "OK" if final_qty > 0 else "Insufficient cash or slot capital"
        }
