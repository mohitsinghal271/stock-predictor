from src.config.research_profiles import DELIVERY_COSTS

class DeliveryCostModel:
    """
    Statutory NSE Delivery Equity Friction Model (Swing & Positional).
    STT: 0.10% on Buy AND 0.10% on Sell.
    Stamp Duty: 0.015% on Buy only.
    Brokerage: 0.03% capped at Rs 20.
    Exchange turnover: 0.00325%.
    GST: 18% on (Brokerage + Exchange turnover).
    SEBI charges: Rs 10 / Crore.
    Slippage: 0.10% per leg.
    """
    def __init__(self, config=None):
        self.c = config or DELIVERY_COSTS

    def calculate_buy_cost(self, trade_value: float) -> dict:
        brokerage = min(trade_value * self.c["brokerage_pct"], self.c["brokerage_max_inr"])
        stt = trade_value * self.c["stt_buy_pct"]
        exchange = trade_value * self.c["exchange_turnover_pct"]
        gst = (brokerage + exchange) * self.c["gst_pct"]
        sebi = trade_value * self.c["sebi_turnover_pct"]
        stamp_duty = trade_value * self.c["stamp_duty_buy_pct"]
        slippage = trade_value * self.c["slippage_pct"]

        total = brokerage + stt + exchange + gst + sebi + stamp_duty + slippage
        return {
            "brokerage": brokerage, "stt": stt, "exchange": exchange,
            "gst": gst, "sebi": sebi, "stamp_duty": stamp_duty,
            "slippage": slippage, "total_cost": total
        }

    def calculate_sell_cost(self, trade_value: float) -> dict:
        brokerage = min(trade_value * self.c["brokerage_pct"], self.c["brokerage_max_inr"])
        stt = trade_value * self.c["stt_sell_pct"]
        exchange = trade_value * self.c["exchange_turnover_pct"]
        gst = (brokerage + exchange) * self.c["gst_pct"]
        sebi = trade_value * self.c["sebi_turnover_pct"]
        stamp_duty = 0.0
        slippage = trade_value * self.c["slippage_pct"]

        total = brokerage + stt + exchange + gst + sebi + stamp_duty + slippage
        return {
            "brokerage": brokerage, "stt": stt, "exchange": exchange,
            "gst": gst, "sebi": sebi, "stamp_duty": stamp_duty,
            "slippage": slippage, "total_cost": total
        }

    def round_trip_cost(self, buy_val: float, sell_val: float) -> float:
        b = self.calculate_buy_cost(buy_val)["total_cost"]
        s = self.calculate_sell_cost(sell_val)["total_cost"]
        return b + s
