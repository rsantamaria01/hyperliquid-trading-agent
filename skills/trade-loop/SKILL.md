---
name: trade-loop
user-invocable: false
description: Drive a recurring scheduled trading loop — arm a cron that runs one trade-cycle iteration every cadence interval — and handle the `close` keyword (stop the loop and flatten all positions). Dispatched by the hta-trade-cycle command. Use when the user starts a looping trade cycle or sends `hta-trade-cycle close`.
---

# Trade loop (orchestrator + background job)

This chat session is an **orchestrator / control panel** — it arms, inspects, modifies, and stops the loop, but it does **not** run trades itself. The trading runs in the **background**: a recurring scheduled job (cron) fires **one `trade-cycle` iteration every cadence interval, each in its own headless session**, independent of this chat. The per-tick trading logic (fan-out, guards, consensus, execute, log) lives in the `trade-cycle` skill. Leaf and log field names: `skills/trade-loop/leaf-contract.md`, `LOG-SCHEMA.md`.

Control surface from this chat:
- **Arm** — `hta-trade-cycle <assets> [...]` → create the background job.
- **Status** — `hta-trade-cycle status` (or "how's the loop?") → show the job + recent results from the log.
- **Modify** — `hta-trade-cycle <new assets/strategies/cadence>` while a job is running → re-arm with new params.
- **Stop** — `hta-trade-cycle close` (stop + flatten) or "stop" (stop, leave positions open).

> **Background job — survives this chat.** The cron keeps firing after you close this chat. In LIVE + autonomous that means **real orders continue with no one watching**. The only ways to stop it are `hta-trade-cycle close` (stop + flatten) or deleting the cron job (`CronDelete <id>`). Closing the chat does **not** stop trading.

## Inputs

Parse `$ARGUMENTS`:

- **`close`** — if the args are exactly the `close` keyword (see "close branch") → run the **close branch**. Otherwise → **arm branch**.
- **Assets** — required for the arm branch. e.g. "BTC ETH SOL".
- **Strategies** — default = one curated strategy (`trend-pullback`); multiple opt-in via `--strategy a,b`.
- **Cadence interval** — how often the job fires (default `5m`). Distinct from per-strategy analysis timeframes (handled inside `trade-cycle`).
- **Autonomous flag** — true if the args contain the phrase "execute approved trades automatically". Authorizes autonomous LIVE entries; carried into the cron prompt.

## Arm branch

The orchestrator session does **not** run trading ticks itself — all ticks run in the background job. Arming only validates and schedules.

### 1. Validate (and optional DRY-RUN preview)
- Resolve assets, strategies (default `trend-pullback`; "all" → enumerate `strategies/*.md`), cadence, and the autonomous flag. Check the account is reachable (`trading_mode()` / `get_account_state()`) so a broken setup fails here, not silently in the background.
- Offer (do not force) a **one-off DRY-RUN preview tick** so the user can see what a tick produces before scheduling LIVE. A preview runs `trade-cycle` once in DRY-RUN (simulated, no real orders) — never run a LIVE trading tick in the orchestrator.

### 2. Arm the recurring job (R9)
Create **one** cron job that fires every cadence. **The cron prompt is a natural-language instruction that triggers the `trade-cycle` skill for one tick — NOT a slash command and NOT this `trade-loop` skill.** Slash commands do not resolve in scheduled/headless runs (`/hta-trade-cycle` → "Unknown command"), and pointing the cron at `trade-loop` would make it arm another cron. Use `CronCreate` with the cadence mapped to a cron expression:

| Cadence | Cron expression |
| --- | --- |
| `5m` | `*/5 * * * *` |
| `15m` | `*/15 * * * *` |
| `1h` | `0 * * * *` |
| `4h` | `0 */4 * * *` |
| `1d` | `0 0 * * *` |

Cron **prompt** template (fill in the parsed values):

> Run one `trade-cycle` iteration on <ASSETS> using strategies <STRATEGIES>, cadence <CADENCE>. This is a single tick of an existing scheduled loop — run exactly one iteration and do **not** create or modify any schedule. [If autonomous:] Execute approved trades automatically. Report what you did.

- Arm **exactly one** job. Before creating, `CronList` and delete any existing trade-cycle job for the same assets so duplicates can't stack.
- Note the returned job id and its auto-expiry (the harness expires cron jobs after a fixed window, e.g. 7 days) in the arm summary.

### 3. Arm summary (LIVE guardrails)
Print a summary table (job id, cron expr, assets, strategies, cadence, autonomous on/off, expiry) and, in LIVE, these warnings prominently:
- **This is a background job. It keeps trading after you close this chat.** Stop it with `hta-trade-cycle close` (stop + flatten) or by deleting the job (`CronDelete <id>`).
- If autonomous is ON: **every new entry fires real orders with no confirmation.** Each tick still runs force-close + the circuit-breaker gate + `validate_trade`, and positions open with exchange-side SL/TP brackets — but direction/thesis are not human-reviewed.
- Worst-case `close`-to-flatten latency is up to one cadence interval (the job only stops cleanly at a tick boundary / when you delete it).
- Recommend starting with DRY-RUN and a small asset set.

## Status branch (view results)

When the user asks for status (`hta-trade-cycle status`, "how's the loop?", "show results"):
- `CronList` → is a trade-cycle job alive? Show its id, cron expression, assets, autonomous on/off, and expiry.
- Read the `log.jsonl` tail and present a compact per-asset summary of recent ticks: last decision, strategies pass count, any open position + PnL, and the latest `iteration_id`/timestamp. Pull live position PnL from `get_account_state()`.
- This is read-only — it never places or cancels orders and never touches the job.

## Modify branch (change a running loop)

When the user changes params while a job is running (different assets, strategies, cadence, or toggling autonomous):
- `CronList` → find the existing trade-cycle job, `CronDelete` it, then arm a fresh job with the new params (the Arm branch). Keep **one** job — never leave two.
- Confirm the old job was removed and show the new arm summary. Do not flatten positions on a modify (use `close` for that).

## Circuit-breaker behavior (per tick, R12)

Each scheduled tick re-checks the breaker itself (inside `trade-cycle`). On an active breaker the tick places no new entries. **Conservative stop:** when a tick reports the breaker active, it should also **delete the cron job** and tell the user the loop stopped on a daily-loss breaker and must be manually re-armed after they review the drawdown — an unattended LIVE job must not silently resume trading across the day boundary without a human ack.

## Close branch (R10, R13, R14)

Trigger only when the user's input is the **explicit `close` command** — `hta-trade-cycle close` (or args that are exactly the bare keyword `close`). A message that merely *contains* "close" in prose (e.g. "should I close BTC?") does **not** flatten; if intent is ambiguous, ask first.

Then:
1. **Delete the cron job first** so no tick fires during/after the flatten. `CronList`, find the trade-cycle job (match by the prompt/assets), `CronDelete <id>`. Do this **before** flattening so a scheduled fire cannot race the close. If you cannot positively identify the job, list the candidates and ask — do not leave an unknown LIVE job running.
2. **Flatten all open positions regardless of PnL.** Read positions via `get_account_state()`; for each, `close_position(asset)`, retrying each failure up to **3 times** with a short backoff.
3. **Honest reporting (R13):** list each position closed (asset, exit, realized PnL). For any that failed after retries, report it explicitly with size + unrealized PnL and that it is **still open** and needs manual intervention. **Never print "account is flat" unless every position is confirmed closed.**
4. Append a `close`/`derisk` log line per affected crypto.
5. Confirm the job is deleted and the loop is stopped.

## Stop without flatten (R11)

If the user says "stop"/"pause" (not `close`): **delete the cron job** and leave open positions in place, protected by their resting exchange-side SL/TP brackets. Confirm positions are left open and that `close` is how to also flatten. (Closing the chat alone does **not** stop the job — it must be deleted.)

## Mid-loop questions (R14)

For any other message while the loop is armed: answer it (e.g. "how is BTC?" → report from `get_account_state()`) without flattening and without touching the job. Only `close`/`stop` change the job.

## Loop-state hygiene (R15)

Each scheduled tick is a fresh context. The tick rebuilds what it needs from its cron prompt args, the **log** (`log.jsonl` tail for prior decisions/positions + the next `iteration_id`), and live `get_account_state()` — never from accumulated chat reasoning. There is no growing chat context across ticks because each fire is independent.

## Mode

DRY-RUN is the default and the required pre-LIVE validation path. Validate the full loop — arm, a few ticks, and a `close` — in DRY-RUN before any LIVE use. Keep this skill `user-invocable: false` so it does not add a second slash entry alongside the `hta-trade-cycle` command.
