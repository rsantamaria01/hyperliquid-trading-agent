---
name: market-analysis
user-invocable: false
description: Analyze one or more Hyperliquid markets and produce a buy/sell/hold recommendation with allocation, stop-loss, and take-profit. Use when the user asks "should I go long/short on X?", "what's the setup on BTC?", or asks for a market read on an asset.
---

# Market analysis

You have access to the `hyperliquid-trading-agent` MCP server. Use these tools (do NOT make any market data assumptions from memory):

1. **`get_market_context(asset, interval, count=200)`** — one-shot bundle of price + latest indicators + open interest + funding + last 20 candles.
2. **`get_account_state()`** — only if the user wants a size recommendation (you need the balance).
3. **`get_risk_limits()`** — to ground any allocation suggestion in the configured caps.

## Procedure

For each asset the user mentions:

1. Call `get_market_context` with the user's interval (default `5m` for scalping, `1h` for swing, `4h`/`1d` for longer holds).
2. Read the indicator block: trend (EMA20 vs EMA50, ADX), momentum (RSI7/14, MACD), volatility (ATR14, BBands width), volume (OBV trend, VWAP location).
3. Note funding rate and open interest — extreme funding or rising OI can flip a setup.
4. Produce a **structured recommendation** with these fields:
   - `signal`: buy / sell / hold
   - `confidence`: low / medium / high (and why)
   - `entry`: market price now, or a limit price
   - `stop_loss`: price level (be specific — use ATR or recent swing)
   - `take_profit`: price level (or multiple, R-multiples)
   - `allocation_usd`: suggested size, capped by `get_risk_limits()`
   - `reasoning`: 2–4 bullets on the actual signal

## Output style

- Lead with the verdict, then the levels, then the reasoning. The user reads top-down.
- If multiple assets, output a compact table.
- If conditions are mixed, say `hold` — do not invent a thesis.
- Never recommend an allocation > `max_position_pct` of total_value.

## Do NOT

- Place any orders here — analysis only. Use `trade-cycle` for execution.
- Guess prices or indicator values without calling the tool.
- Skip the stop-loss field. Every recommendation has one.
