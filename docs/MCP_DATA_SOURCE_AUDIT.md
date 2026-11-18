# MCP DATA SOURCE AUDIT & CAPABILITY MATRIX
**Connected Servers:** `nse-bhavcopy` & `cm-market`  
**Endpoint URLs:** 
* `https://mcp.nseindia.in/bhavcopy/cm/mcp`
* `https://mcp.nseindia.in/cmmkt/mcp`  
**Transport:** Remote HTTP/SSE

---

## 1. Tool Capability Matrix

| MCP Server | Tool Name | Data Returned | Historical Depth | Intraday Support | Real-Time Live | Primary Research Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`nse-bhavcopy`** | `get_stock_history` | Daily OHLCV, Traded Value, Volume, Date | Up to 5+ yrs (3 mo chunks with pagination) | No (Daily Only) | Previous Day Close | Ingestion of raw daily OHLCV series |
| **`nse-bhavcopy`** | `get_corporate_actions` | Splits, Bonuses, Dividends, Rights, Ex-Dates | Multi-year | N/A | Current Actions | Price adjustment pipeline (splits/bonuses) |
| **`nse-bhavcopy`** | `get_volume_analysis` | Avg volume, Volume spikes (>2x), 5-day trend | 5 to 252 days | No | Real-Time Aggregated | Institutional accumulation detection |
| **`nse-bhavcopy`** | `get_index_history` | Index OHLCV (NIFTY 50, NIFTY BANK, etc.) | Multi-year | No | Previous Day Close | Market regime & benchmark comparison |
| **`nse-bhavcopy`** | `get_index_snapshot` | Current valuation, PE, PB, Div Yield | Point-in-time | N/A | Live | Macro market valuation filter |
| **`nse-bhavcopy`** | `get_market_breadth` | Advances, Declines, Unchanged counts | Point-in-time | N/A | Live | Market regime classifier (Bullish/Bearish) |
| **`nse-bhavcopy`** | `get_52_week_high_low` | 52-week High/Low dates & values | 1 Year | N/A | Live | Breakout strategy filter |
| **`cm-market`** | `cm_get_stock_quote` | LTP, Day OHLC, Volume, Turnover, 52W H/L | Intraday Snap | Live tick | Live (Real-Time) | Live signal trigger & paper trading |
| **`cm-market`** | `cm_get_live_gainers` | Segment Gainers (NIFTY, F&O, Midcap, All) | Intraday Snap | Live tick | Live (Real-Time) | Top relative strength scanner |
| **`cm-market`** | `cm_get_live_indices` | Real-time index movements & performance | Intraday Snap | Live tick | Live (Real-Time) | Sector rotation & index strength |
| **`cm-market`** | `cm_get_equity_stocks` | List of all actively traded equity symbols | N/A | N/A | Live | Point-in-time universe generator |

---

## 2. Critical Constraints & Engineering Protections
1. **Unadjusted Bhavcopy Data:**
   * Raw OHLCV from `get_stock_history` does **not** adjust for splits or bonuses automatically.
   * *Protection:* The data pipeline must query `get_corporate_actions(symbol)` and apply a backward adjustment multiplier for splits (e.g. 1:1 split multiplies pre-split volume by 2 and divides pre-split price by 2) to eliminate false 50% drops.
2. **Chunked Pagination:**
   * `get_stock_history` yields a maximum of 3 months per request and returns `next_end_date`.
   * *Protection:* The ingestion engine implements an automatic cursor-based crawler with checkpoints stored in SQLite to resume interrupted downloads.
3. **Rate Limits & Backoff:**
   * Remote NSE servers throttle on burst requests.
   * *Protection:* Requests are paced with a token-bucket rate limiter (500ms delay between symbol queries) and exponential backoff retry.
4. **Intraday Data Availability:**
   * Neither MCP server provides multi-year 1-minute or 5-minute ticks (only daily OHLCV and live real-time snapshots are served).
   * *Engineering Decision:* In strict compliance with guidelines, **backtesting will strictly run on Daily timeframe data** (and intraday simulated execution at next day's Open/VWAP). No fake intraday candles will be hallucinated.
