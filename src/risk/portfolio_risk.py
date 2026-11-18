from src.config.research_profiles import CAPITAL_CONFIG, STOCK_SECTORS

class PortfolioRiskManager:
    """
    Guarantees aggregate portfolio safety:
    1. Maximum concurrent open positions <= 5.
    2. Total planned open risk across all positions <= 3.0% of portfolio.
    3. Maximum capital deployment <= 80%.
    4. Sector exposure <= 30%.
    """
    def __init__(self, config=None, sector_map=None):
        self.c = config or CAPITAL_CONFIG
        self.sector_map = sector_map or STOCK_SECTORS

    def can_open_position(self, current_equity: float, current_positions: list, candidate_symbol: str, candidate_risk: float, candidate_capital: float) -> dict:
        # Check 1: Max Concurrent Positions
        if len(current_positions) >= self.c["max_concurrent_positions"]:
            return {"allowed": False, "reason": f"Max concurrent positions ({self.c['max_concurrent_positions']}) reached"}

        # Check 2: No duplicate symbol
        for pos in current_positions:
            if pos["symbol"] == candidate_symbol:
                return {"allowed": False, "reason": f"Position already open in {candidate_symbol}"}

        # Check 3: Aggregate Open Risk Limit (Max 3%)
        current_open_risk = sum(p.get("risk_amount", 0.0) for p in current_positions)
        new_total_risk = current_open_risk + candidate_risk
        max_allowed_risk = current_equity * self.c["max_portfolio_open_risk"]
        if new_total_risk > max_allowed_risk:
            return {"allowed": False, "reason": f"Total portfolio open risk ({new_total_risk:.2f}) would exceed limit ({max_allowed_risk:.2f})"}

        # Check 4: Capital Deployment Limit (Max 80%)
        current_deployed = sum(p.get("allocated_capital", 0.0) for p in current_positions)
        new_total_deployed = current_deployed + candidate_capital
        max_allowed_deployed = current_equity * self.c["max_capital_deployment"]
        if new_total_deployed > max_allowed_deployed:
            return {"allowed": False, "reason": f"Capital deployment ({new_total_deployed:.2f}) would exceed 80% ceiling"}

        # Check 5: Sector Concentration Limit (Max 30%)
        cand_sector = self.sector_map.get(candidate_symbol, "Other")
        current_sector_capital = sum(p.get("allocated_capital", 0.0) for p in current_positions if self.sector_map.get(p["symbol"]) == cand_sector)
        new_sector_capital = current_sector_capital + candidate_capital
        max_sector_capital = current_equity * self.c["max_sector_exposure"]
        if new_sector_capital > max_sector_capital:
            return {"allowed": False, "reason": f"Sector exposure in {cand_sector} ({new_sector_capital:.2f}) would exceed 30% limit"}

        return {"allowed": True, "reason": "Approved by Portfolio Risk Manager"}
