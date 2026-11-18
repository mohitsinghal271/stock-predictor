import pandas as pd
import numpy as np
from src.config.research_profiles import CAPITAL_CONFIG, STOCK_SECTORS
from src.backtester.delivery_costs import DeliveryCostModel
from src.risk.position_sizing import RiskBasedPositionSizer
from src.risk.portfolio_risk import PortfolioRiskManager
from src.backtester.metrics import PerformanceMetrics

class CombinedPortfolioEngine:
    """
    Mode 2: Combined Multi-Style Shared Portfolio Engine.
    Single shared capital pool of INR 500,000.
    Enforces:
    - Max 5 concurrent open positions.
    - Max 3% aggregate open portfolio risk.
    - Max 80% total capital deployment.
    - Max 30% sector exposure ceiling.
    - Zero duplicate symbol positions.
    """
    def __init__(self, initial_capital: float = 500000.0):
        self.initial_capital = initial_capital
        self.cost_model = DeliveryCostModel()
        self.sizer = RiskBasedPositionSizer()
        self.risk_mgr = PortfolioRiskManager()

    def run_combined_simulation(self, universe_dfs: dict, swing_strat, positional_strat) -> dict:
        symbols = list(universe_dfs.keys())
        all_dates = list(universe_dfs[symbols[0]].index)

        # Precompute strategy signals once (Vectorized O(N) instead of O(N^2))
        swing_signals = {sym: swing_strat.generate_signals(universe_dfs[sym]) for sym in symbols}
        pos_signals = {sym: positional_strat.generate_signals(universe_dfs[sym]) for sym in symbols}

        cash = self.initial_capital
        positions = {} # sym -> {shares, entry_price, stop_loss, style, sector, risk_amount, allocated_capital}
        equity_curve = []
        trade_log = []

        for d in all_dates:
            mtm_cur = sum(pos["shares"] * (universe_dfs[sym]["close"].loc[d] if d in universe_dfs[sym].index else pos["entry_price"]) for sym, pos in positions.items())
            curr_equity = cash + mtm_pos if 'mtm_pos' in locals() else cash + mtm_cur

            # 1. Process Exits First
            for sym in list(positions.keys()):
                df = universe_dfs[sym]
                if d not in df.index: continue
                loc = df.index.get_loc(d)
                if loc == 0: continue
                c_low = df["low"].iloc[loc]
                c_open = df["open"].iloc[loc]
                pos = positions[sym]

                # Check Stop Loss
                if c_low <= pos["stop_loss"]:
                    exit_price = pos["stop_loss"]
                    reason = "STOP_LOSS"
                    del_pos = True
                else:
                    # Check precomputed strategy exit signal on prior close
                    prior_sig = swing_signals[sym].iloc[loc - 1] if pos["style"] == "SWING" else pos_signals[sym].iloc[loc - 1]
                    if prior_sig == 0:
                        exit_price = c_open * (1.0 - self.cost_model.c["slippage_pct"])
                        reason = "SIGNAL_EXIT"
                        del_pos = True
                    else:
                        del_pos = False

                if del_pos:
                    sh = pos["shares"]
                    sell_val = sh * exit_price
                    sell_costs = self.cost_model.calculate_sell_cost(sell_val)["total_cost"]
                    net_pnl = (exit_price - pos["entry_price"]) * sh - (self.cost_model.calculate_buy_cost(sh * pos["entry_price"])["total_cost"] + sell_costs)

                    cash += (sell_val - sell_costs)
                    trade_log.append({
                        "symbol": sym,
                        "style": pos["style"],
                        "entry_date": str(pos["entry_date"]),
                        "exit_date": str(d.date()) if hasattr(d, "date") else str(d),
                        "entry_price": pos["entry_price"],
                        "exit_price": exit_price,
                        "shares": sh,
                        "net_pnl": net_pnl,
                        "return_pct": net_pnl / (sh * pos["entry_price"]),
                        "reason": reason
                    })
                    del positions[sym]

            # 2. Process Entries (Positional & Swing)
            for sym in symbols:
                if len(positions) >= CAPITAL_CONFIG["max_concurrent_positions"]:
                    break
                if sym in positions:
                    continue

                df = universe_dfs[sym]
                if d not in df.index: continue
                loc = df.index.get_loc(d)
                if loc == 0: continue

                # Check Signals: Positional takes precedence over swing
                pos_sig = pos_signals[sym].iloc[loc - 1]
                sw_sig = swing_signals[sym].iloc[loc - 1]

                chosen_style = None
                sl_pct = 0.05
                if pos_sig == 1:
                    chosen_style = "POSITIONAL"
                    sl_pct = 0.08
                elif sw_sig == 1:
                    chosen_style = "SWING"
                    sl_pct = 0.05

                if chosen_style is not None and cash > 20000:
                    c_open = df["open"].iloc[loc]
                    entry_price = c_open * (1.0 + self.cost_model.c["slippage_pct"])
                    stop_loss = entry_price * (1.0 - sl_pct)

                    sizing = self.sizer.calculate_quantity(curr_equity, cash, entry_price, stop_loss)
                    qty = sizing["quantity"]

                    if qty > 0:
                        risk_amt = sizing["risk_amount"]
                        alloc_cap = sizing["allocated_capital"]

                        # Check with Portfolio Risk Manager
                        curr_pos_list = list(positions.values())
                        approval = self.risk_mgr.can_open_position(curr_equity, curr_pos_list, sym, risk_amt, alloc_cap)

                        if approval["allowed"]:
                            buy_costs = self.cost_model.calculate_buy_cost(alloc_cap)["total_cost"]
                            cash -= (alloc_cap + buy_costs)
                            positions[sym] = {
                                "symbol": sym,
                                "shares": qty,
                                "entry_price": entry_price,
                                "stop_loss": stop_loss,
                                "entry_date": d.date() if hasattr(d, "date") else d,
                                "style": chosen_style,
                                "risk_amount": risk_amt,
                                "allocated_capital": alloc_cap
                            }

            # 3. Mark to Market Equity
            mtm_pos = sum(p["shares"] * (universe_dfs[s]["close"].loc[d] if d in universe_dfs[s].index else p["entry_price"]) for s, p in positions.items())
            equity_curve.append(cash + mtm_pos)

        eq_series = pd.Series(equity_curve, index=all_dates)
        trade_returns = [t["return_pct"] for t in trade_log]
        metrics = PerformanceMetrics.calculate(eq_series, trade_returns)

        return {
            "initial_capital": self.initial_capital,
            "final_equity": round(equity_curve[-1], 2),
            "metrics": metrics,
            "equity_curve": eq_series,
            "trade_log": trade_log
        }
