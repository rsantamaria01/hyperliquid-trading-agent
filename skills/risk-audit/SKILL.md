---
name: risk-audit
description: Audit current portfolio against configured risk limits — flag positions over caps, missing stop-losses, excessive concentration, or approaching circuit breakers. Use when the user asks "am I within my risk limits?", "audit my risk", or before a high-stakes session.
---

# Risk audit

Uses `hyperliquid-trading-agent` MCP. Read-only.

## Steps

1. `get_risk_limits()` — pull the configured caps.
2. `get_account_state()` — balance, equity, positions.
3. `get_open_orders()` — to detect positions missing protective triggers.
4. `check_losing_positions()` — any position over the loss cap.

## Checks (run all, report each)

For each, output PASS / WARN / FAIL with a one-line explanation.

| Check | Logic |
|---|---|
| Concurrent positions | `len(positions) < max_concurrent_positions` |
| Position size | every position notional < `max_position_pct` of total_value |
| Total exposure | sum of notional < `max_total_exposure_pct` of total_value |
| Leverage | each position notional / balance < `max_leverage` |
| Daily drawdown | not within striking distance of `daily_loss_circuit_breaker_pct` |
| Balance reserve | balance >= `min_balance_reserve_pct` of initial |
| Stop-loss coverage | every long has an SL trigger; every short has an SL trigger |
| Force-close queue | `check_losing_positions()` empty |

## Output

Lead with overall status: GREEN / YELLOW / RED.
Then the table.
Then a punch list of recommended actions in priority order.

If any FAIL, ask the user whether they want you to remediate (close, resize, or attach missing SL).
