---
name: trade-cycle
description: Run one full trading-loop iteration — sync account, force-close losers, analyze each asset, validate proposed trades against risk limits, execute. Use when the user says "run the trading loop", "do a trade cycle", "check the watchlist and trade", or sets up a scheduled task that invokes this skill.
---

# Trade cycle (one iteration)

This skill replicates what the upstream repo's main loop does each interval, with you (Claude) replacing the LLM call. It uses the `hyperliquid-trading-agent` MCP server.

## Inputs

Either the user names the assets (e.g. "trade BTC ETH SOL"), or you read a default watchlist from env / prior conversation. Ask once if unclear.

## Procedure — perform in order, do not skip steps

### 1. Mode check
- Call `trading_mode()` and tell the user whether you're in DRY-RUN or LIVE. If LIVE, confirm with one short line: "Executing live trades."

### 2. Account snapshot
- Call `get_account_state()`. Note `balance`, `total_value`, and current `positions`.
- Call `get_risk_limits()` so you have caps in working memory.

### 3. Force-close excessive losers (safety first)
- Call `check_losing_positions()`. If anything is returned, call `force_close_losing_positions()` immediately.
- This is non-negotiable — it mirrors the hard-coded guard in the original loop.

### 4. Gather context for each asset on the watchlist
- For each asset, call `get_market_context(asset, interval)`.
- Do this in **parallel** (multiple tool uses in one message) when more than one asset.

### 5. Propose trades
For each asset, decide buy / sell / hold using the same heuristics as `market-analysis`:
- Trend alignment (EMA20 vs EMA50, ADX > 20)
- Momentum (RSI not extreme, MACD direction)
- Volatility-sized stop (ATR-based)
- Funding / OI not screaming reversal

If the asset already has an open position:
- Long position + still bullish → consider `hold` (don't pyramid by default)
- Long position + bearish flip → propose `close_position(asset)`
- No position + clean setup → propose `buy` or `sell`

Build a draft list of trades with: asset, action, allocation_usd, sl_price, tp_price.

### 6. Pre-flight validation
- For each non-hold trade, call `validate_trade(...)`. Capture any rejections or adjusted allocations.
- Show the user the validated plan as a compact table before execution.

### 7. Execute
- For each approved trade call `place_market_order(asset, side, allocation_usd, sl_price, tp_price)`.
- If `trading_mode` reports DRY-RUN, every order returns a simulated response — that's expected and safe.
- If LIVE, the tool places the entry + stop-loss + (optional) take-profit brackets automatically.

### 8. Summary
- Report: positions opened/closed, allocations, stops, current PnL, cash deployed.
- Note any rejected trades and the reason.

## Guardrails

- Never pyramid more than `max_position_pct` notional into a single asset.
- Never override a `validate_trade` rejection by re-calling with smaller params unless the rejection reason was specifically about size — and even then only once.
- If `circuit_breaker_active` is true in the risk summary, STOP. Tell the user no new trades until UTC day boundary.

## When the user wants this scheduled

Tell them to set up a Cowork scheduled task with prompt: "Run the trade-cycle skill on BTC ETH SOL" and a cron like `*/15 * * * *`. Make sure `LIVE_TRADING=true` is set in the MCP server env first — and that they understand the risk.
