---
name: portfolio-review
description: Review the current Hyperliquid portfolio — open positions, PnL, exposure, recent fills. Use when the user asks "how are my positions doing?", "what's my PnL?", "show me my open trades", or wants a daily/weekly portfolio check.
---

# Portfolio review

Uses the `hyperliquid-trading-agent` MCP server. Read-only — does not place or close anything unless the user explicitly asks.

## Steps

1. `trading_mode()` — confirm DRY-RUN vs LIVE in one line at the top.
2. `get_account_state()` — balance, total_value, positions with PnL.
3. `get_open_orders()` — any resting limit or trigger orders (TP/SL).
4. `get_recent_fills(limit=20)` — last 20 fills for context.
5. `get_risk_limits()` — current caps and whether the daily circuit breaker is active.

## Output format

Lead with the headline numbers:

- **Equity**: $X (balance $Y + unrealized $Z)
- **Daily**: ±Z% vs daily high
- **Exposure**: X% of cap used

Then a compact table of open positions:

| Asset | Side | Size | Entry | Mark | PnL | PnL % | SL | TP |

Then any open orders. Then recent fills if interesting.

Close with one line on risk posture: are any positions close to the loss-cap? Is exposure near the limit?

## When to suggest action

- If any position has `loss_pct >= 0.8 * max_loss_per_position_pct`, flag it and ask if the user wants to close.
- If `circuit_breaker_active`, surface that prominently.
- If positions exist without stop-loss orders (no SL in open_orders for that asset), offer to set them via `set_stop_loss`.
