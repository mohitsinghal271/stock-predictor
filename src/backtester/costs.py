from src.config import TRANSACTION_COSTS

class IndianTransactionCostModel:
    """
    Computes exact, realistic transaction costs for Indian cash equity swing trades.
    Includes Brokerage, STT, Exchange Turnover Charges, GST, SEBI fee, Stamp Duty, and Slippage.
    """
    def __init__(self, config=None):
        self.c = config or TRANSACTION_COSTS

    def calculate_buy_cost(self, trade_value: float) -> dict:
        """Computes all friction costs on entry (Buy)."""
        brokerage = min(trade_value * self.c["brokerage_pct"], self.c["brokerage_max_inr"])
        stt = trade_value * self.c["stt_buy_pct"]
        exchange_turnover = trade_value * self.c["exchange_turnover_pct"]
        gst = (brokerage + exchange_turnover) * self.c["gst_pct"]
        sebi = trade_value * self.c["sebi_turnover_pct"]
        stamp_duty = trade_value * self.c["stamp_duty_buy_pct"]
        slippage = trade_value * self.c["slippage_pct"]

        total = brokerage + stt + exchange_turnover + gst + sebi + stamp_duty + slippage
        return {
            "brokerage": brokerage,
            "stt": stt,
            "exchange": exchange_turnover,
            "gst": gst,
            "sebi": sebi,
            "stamp_duty": stamp_duty,
            "slippage": slippage,
            "total_buy_cost": total,
            "cost_pct": total / trade_value if trade_value > 0 else 0.0
        }

    def calculate_sell_cost(self, trade_value: float) -> dict:
        """Computes all friction costs on exit (Sell)."""
        brokerage = min(trade_value * self.c["brokerage_pct"], self.c["brokerage_max_inr"])
        stt = trade_value * self.c["stt_sell_pct"]
        exchange_turnover = trade_value * self.c["exchange_turnover_pct"]
        gst = (brokerage + exchange_turnover) * self.c["gst_pct"]
        sebi = trade_value * self.c["sebi_turnover_pct"]
        stamp_duty = 0.0  # Stamp duty applies to buy side only
        slippage = trade_value * self.c["slippage_pct"]

        total = brokerage + stt + exchange_turnover + gst + sebi + stamp_duty + slippage
        return {
            "brokerage": brokerage,
            "stt": stt,
            "exchange": exchange_turnover,
            "gst": gst,
            "sebi": sebi,
            "stamp_duty": stamp_duty,
            "slippage": slippage,
            "total_sell_cost": total,
            "cost_pct": total / trade_value if trade_value > 0 else 0.0
        }

    def calculate_round_trip_friction(self, buy_value: float, sell_value: float) -> float:
        """Returns total INR cost deducted for a complete buy-then-sell trade."""
        b = self.calculate_buy_cost(buy_value)["total_buy_cost"]
        s = self.calculate_sell_cost(sell_value)["total_sell_cost"]
        return b + s
