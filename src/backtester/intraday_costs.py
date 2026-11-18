from src.config.research_profiles import INTRADAY_COSTS

class IntradayCostModel:
    """
    Statutory NSE Intraday Equity Friction Model.
    STT: 0.025% on Sell only (Zero on Buy).
    Stamp Duty: 0.003% on Buy only.
    Brokerage: 0.03% capped at Rs 20.
    Exchange turnover: 0.00325%.
    GST: 18% on (Brokerage + Exchange turnover).
    SEBI charges: Rs 10 / Crore.
    Slippage: 0.05% per leg.
    """
    def __init__(self, config=None):
        self.c = config or INTRADAY_COSTS

    def calculate_buy_cost(self, trade_value: float) -> dict:
        brokerage = min(trade_value * self.c["brokerage_pct"], self.c["brokerage_max_inr"])
        stt = 0.0 # Zero STT on intraday buy
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
        stt = trade_value * self.c["stt_sell_pct"] # 0.025% on intraday sell
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
