---
name: trade-cycle
description: Run one full trading-loop iteration — sync account, force-close losers, analyze each asset against a strategy (or default heuristics), validate proposed trades against risk limits, execute. Use when the user says "run the trading loop", "do a trade cycle", "check the watchlist and trade", or sets up a scheduled task that invokes this skill.
---

# Trade cycle (one iteration)

This skill executes one full trading iteration. Same flow as the upstream repo's main loop, with Claude replacing the LLM call.

## Inputs

Parse from the user's message or command args:

- **Assets** — required. e.g. "BTC ETH SOL", or a watchlist they've mentioned before.
- **Interval** — candle timeframe. Default `5m`. Examples: `5m`, `15m`, `1h`, `4h`, `1d`.
- **Strategy** — optional. e.g. `--strategy breakout-bb` or "use the trend-pullback strategy". If provided, **read `strategies/<name>.md` BEFORE step 4** and apply its rules. If absent, use the default heuristics in step 5b.

Ask if assets are missing. Don't ask about interval or strategy — defaults are fine.

## Procedure — execute in order, do not skip

### 1. Mode check
- Call `trading_mode()`. Print one line: "Mode: DRY-RUN" or "Mode: LIVE — placing real orders."

### 2. Strategy load (if specified)
- If a strategy name was given, read `strategies/<name>.md` from the plugin folder.
- Hold the entry conditions, SL/TP rules, and "when NOT to use" guidance in working memory.
- If the strategy file doesn't exist, list available strategies via the `strategy` skill and ask the user to pick.

### 3. Account snapshot
- Call `get_account_state()` and `get_risk_limits()` in parallel.
- Note `balance`, `total_value`, current positions, available exposure budget.

### 4. Force-close losers (non-negotiable safety net)
- Call `check_losing_positions()`. If anything is returned, call `force_close_losing_positions()`.
- Even with a strategy loaded, this runs every cycle — it mirrors the hard-coded guard in the original loop.

### 5. Gather context for each asset (parallel)
- For each asset: `get_market_context(asset, interval)`.

### 5b. Apply the decision logic

**If a strategy is loaded** — follow its rules literally:
- Check the strategy's "When NOT to use" first. If any condition matches, mark the asset HOLD with a reason and skip.
- Check the strategy's "Entry conditions" — does the current market context satisfy them? If not, HOLD.
- If conditions pass:
  - Determine direction per the strategy's `direction` field.
  - Compute SL per the strategy's stop-loss rules.
  - Compute TP per the strategy's take-profit rules.
  - Choose entry execution per the strategy's `entry_type`.

**If no strategy is loaded** — use the default heuristics:
- Trend alignment (EMA20 vs EMA50, ADX > 20)
- Momentum (RSI not extreme, MACD direction)
- Volatility-sized stop (1 × ATR from entry)
- TP at 2R (2× SL distance)
- Default to market entry

For each asset already with an open position:
- Long + signal still aligned → HOLD (don't pyramid by default)
- Long + signal flipped → propose `close_position(asset)`
- No position + clean setup → propose `buy` or `sell`

### 6. Pre-flight validation
- For each non-hold trade, call `validate_trade(asset, action, allocation_usd, sl_price, tp_price)`.
- Capture rejections and the adjusted trade (the risk manager may cap allocation or auto-set SL).

### 7. Show the validated plan
Present a compact table BEFORE executing:

| Asset | Side | Entry type | Entry price | Allocation | SL | TP | R:R | Reason |
|---|---|---|---|---|---|---|---|---|

If in LIVE mode, pause for explicit user confirmation (GO / NO / adjust) unless the user has already pre-authorized this cycle (e.g. in a scheduled task prompt: "execute approved trades automatically").

### 8. Execute
For each approved trade, choose the right tool based on entry type:

**Market entry:**
```
place_market_order(
  asset=...,
  side="buy"|"sell",
  allocation_usd=<notional>,
  sl_price=<computed>,
  tp_price=<computed>,
  slippage=0.01
)
```
Returns the entry fill plus the SL and TP resting brackets.

**Limit entry (with brackets):**
```
place_limit_order(
  asset=...,
  side="buy"|"sell",
  allocation_usd=<notional>,
  limit_price=<from strategy>,
  sl_price=<computed from strategy>,
  tp_price=<computed from strategy>,
  tif="Gtc"
)
```
The SL and TP are submitted alongside the limit as a `normalTpsl` bracket group. They stay dormant until the limit fills, then activate as reduce-only triggers. The position is protected the moment it opens — no window of unbracketed exposure.

If the strategy says "limit at EMA20" and EMA20 is e.g. $73,500, place the limit there. If price runs away by more than 1 × ATR without filling, cancel the resting limit (next cycle will detect and re-place if conditions still hold).

### 9. Summary
Report:
- Trades opened (asset, side, entry type, fill price, brackets)
- Trades closed (asset, exit price, realized PnL)
- Limit orders placed (resting)
- Rejected trades and why
- Current net exposure vs. cap
- Reminder of mode (DRY-RUN / LIVE)

## Guardrails

- Never pyramid more than `max_position_pct` notional into a single asset.
- Never override a `validate_trade` rejection by retrying with smaller params unless the rejection was specifically about size — and only once.
- If `circuit_breaker_active` is true in the risk summary, STOP. Tell the user no new trades until UTC day boundary.
- Strategy sizing instructions (e.g. "use 60% of MAX_POSITION_PCT") are advisory — the risk manager's hard cap always wins.
- If LIVE mode and the cycle is being run interactively (not via scheduled task), pause for user confirm before executing.

## Scheduled-task usage

For autonomous mode, the cron prompt should look like:
> Run trade-cycle on BTC ETH SOL with interval 5m using the breakout-bb strategy. Execute approved trades automatically. Report what you did.

The phrase "Execute approved trades automatically" tells the cycle to skip the GO/NO confirmation step.
