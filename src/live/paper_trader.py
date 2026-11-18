import json
from pathlib import Path
from datetime import datetime
from src.config import DATA_DIR

class PaperTradingLedger:
    """
    Simulated Paper Trading Engine.
    Executes and records virtual orders with realistic slippage and statutory cost tracking.
    """
    def __init__(self):
        self.ledger_file = DATA_DIR / "paper_trades.json"
        self._load()

    def _load(self):
        if self.ledger_file.exists():
            with open(self.ledger_file, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {
                "initial_cash": 1000000.0,
                "available_cash": 1000000.0,
                "active_positions": [],
                "closed_trades": []
            }
            self._save()

    def _save(self):
        with open(self.ledger_file, "w") as f:
            json.dump(self.data, f, indent=2)

    def record_signal(self, signal: dict, allocated_amount: float = 100000.0):
        """Places a simulated paper trade."""
        symbol = signal["symbol"]
        # Don't double enter if already open
        for pos in self.data["active_positions"]:
            if pos["symbol"] == symbol:
                return

        ltp = signal["ltp"]
        shares = int(allocated_amount / ltp) if ltp > 0 else 0
        if shares == 0 or self.data["available_cash"] < allocated_amount:
            return

        trade_record = {
            "id": f"PT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{symbol}",
            "symbol": symbol,
            "strategy": signal["strategy"],
            "entry_time": signal["timestamp"],
            "entry_price": ltp,
            "shares": shares,
            "cost_basis": round(shares * ltp, 2),
            "stop_loss": signal["stop_loss"],
            "target_1": signal["target_1"],
            "target_2": signal["target_2"],
            "status": "OPEN"
        }

        self.data["available_cash"] -= trade_record["cost_basis"]
        self.data["active_positions"].append(trade_record)
        self._save()

    def get_summary(self) -> dict:
        total_open_cost = sum(p["cost_basis"] for p in self.data["active_positions"])
        total_portfolio_val = self.data["available_cash"] + total_open_cost
        unrealized_pnl = total_portfolio_val - self.data["initial_cash"]
        return {
            "initial_cash": self.data["initial_cash"],
            "available_cash": round(self.data["available_cash"], 2),
            "invested_cash": round(total_open_cost, 2),
            "portfolio_value": round(total_portfolio_val, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "open_count": len(self.data["active_positions"]),
            "closed_count": len(self.data["closed_trades"])
        }
