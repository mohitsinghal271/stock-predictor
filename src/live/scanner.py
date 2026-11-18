import pandas as pd
from datetime import datetime
from src.data.mcp_client import NSEDataClient
from src.config import DEFAULT_UNIVERSE

class LiveMarketScanner:
    """
    Live Market Scanner that checks the universe against historically validated strategy rules.
    Outputs actionable paper trade setups with exact levels.
    """
    def __init__(self, data_client: NSEDataClient = None):
        self.data_client = data_client or NSEDataClient()

    def scan_universe(self, universe: list = None) -> list:
        symbols = universe or DEFAULT_UNIVERSE
        signals = []

        for symbol in symbols:
            df = self.data_client.get_stock_data(symbol)
            if df.empty or len(df) < 50:
                continue

            last_close = df["close"].iloc[-1]
            last_vol = df["volume"].iloc[-1]
            avg_vol_20 = df["volume"].iloc[-21:-1].mean()
            ema20 = df["close"].ewm(span=20, adjust=False).mean().iloc[-1]
            ema50 = df["close"].ewm(span=50, adjust=False).mean().iloc[-1]
            high_52w = df["high"].iloc[-252:].max() if len(df) >= 252 else df["high"].max()

            vol_ratio = round(last_vol / avg_vol_20, 2) if avg_vol_20 > 0 else 1.0
            dist_52w_pct = round(((high_52w - last_close) / high_52w) * 100.0, 2)

            # Strategy Signal Criteria:
            # 1. High-Volume VCP / 52W High Breakout
            if dist_52w_pct <= 5.0 and vol_ratio >= 1.5 and last_close > ema50:
                stop_loss = round(min(ema20, last_close * 0.94), 2)
                t1 = round(last_close * 1.07, 2)
                t2 = round(last_close * 1.15, 2)
                rr = round((t1 - last_close) / (last_close - stop_loss), 2) if (last_close - stop_loss) > 0 else 2.0

                signals.append({
                    "symbol": symbol,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "strategy": "52W_High_Volume_Breakout",
                    "ltp": round(last_close, 2),
                    "entry_range": f"{round(last_close*0.995, 2)} - {round(last_close*1.005, 2)}",
                    "stop_loss": stop_loss,
                    "target_1": t1,
                    "target_2": t2,
                    "risk_reward": f"1 : {rr}",
                    "volume_ratio": f"{vol_ratio}x",
                    "distance_52w": f"{dist_52w_pct}%",
                    "signal_strength": "STRONG BUY" if vol_ratio >= 2.0 else "ACCUMULATE"
                })

            # 2. Dual EMA Pullback Setup
            elif last_close > ema50 and last_close >= ema20 * 0.99 and last_close <= ema20 * 1.02 and vol_ratio < 0.90:
                stop_loss = round(ema50 * 0.97, 2)
                t1 = round(last_close * 1.06, 2)
                t2 = round(last_close * 1.12, 2)
                rr = round((t1 - last_close) / (last_close - stop_loss), 2) if (last_close - stop_loss) > 0 else 2.0

                signals.append({
                    "symbol": symbol,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "strategy": "Dual_EMA_Pullback_Retest",
                    "ltp": round(last_close, 2),
                    "entry_range": f"{round(last_close*0.995, 2)} - {round(last_close*1.005, 2)}",
                    "stop_loss": stop_loss,
                    "target_1": t1,
                    "target_2": t2,
                    "risk_reward": f"1 : {rr}",
                    "volume_ratio": f"{vol_ratio}x (Dry-up)",
                    "distance_52w": f"{dist_52w_pct}%",
                    "signal_strength": "LOW-RISK SWING ENTRY"
                })

        return signals
