---
name: trade-loop
user-invocable: false
description: Drive a persistent same-chat trading loop — run one trade-cycle iteration, sleep the cadence interval, repeat — and handle the `close` keyword (stop the loop and flatten all positions). Dispatched by the hta-trade-cycle command. Use when the user starts a looping trade cycle or sends `hta-trade-cycle close`.
---

# Trade loop (lifecycle + close)

This skill owns the **loop**: it runs one `trade-cycle` iteration, schedules the next run after the cadence interval, and repeats — all in one live chat session. It also handles the `close` keyword. The per-iteration trading logic (fan-out, guards, consensus, execute, log) lives in the `trade-cycle` skill; this skill only sequences it and manages stop/flatten. Leaf and log field names: `skills/trade-loop/leaf-contract.md`, `LOG-SCHEMA.md`.

## Inputs

Parse `$ARGUMENTS`:

- **`close`** — if the args are exactly the `close` keyword (see "close branch" for the match rule) → run the **close branch**. Otherwise → **start/run branch**.
- **Assets** — required for the run branch. e.g. "BTC ETH SOL".
- **Strategies** — default = one curated strategy (`trend-pullback`); multiple opt-in via `--strategy a,b`.
- **Cadence interval** — how often the loop runs (default `5m`). Distinct from per-strategy analysis timeframes (handled inside `trade-cycle`).
- **Autonomous flag** — true if the args contain the phrase "execute approved trades automatically". Authorizes autonomous LIVE entries; passed through to each `trade-cycle` tick.

## Start / run branch

### 1. Start-of-loop notice (first invocation only)
- Print the cadence, assets, strategy set, and mode.
- **In LIVE**, warn explicitly: "Ending this chat session stops active management. Open positions are left in place, protected by their resting exchange-side SL/TP brackets, but no further loop ticks (force-close, circuit-breaker, re-evaluation) run until you start the loop again. Use `hta-trade-cycle close` to stop *and* flatten."
- If LIVE and the autonomous flag is **not** set, remind the user that each new entry will pause for GO/NO; if they want unattended entries they must restart with "execute approved trades automatically".

### 2. Run one iteration
- Invoke the `trade-cycle` skill with the assets, cadence interval, strategy set, and autonomous flag. It performs mode check → snapshot + risk audit → circuit-breaker gate → force-close → fan-out → consensus → validate → execute → log → summary.

### 3. Decide whether to continue
- If `trade-cycle` signaled a **circuit-breaker halt**: do **not** continue the loop (stop the driver below). Tell the user the loop is paused until the UTC day boundary and they can re-start it then. Stop.
- Otherwise keep the loop running (step 4).

### 4. Repeat on the cadence (R9)
The loop repeats by **re-firing the `hta-trade-cycle` command each cadence interval in the same chat session**. Use the harness's same-chat recurring mechanism — the **`/loop` skill** is the match (`/loop <cadence> /hta-trade-cycle <assets> [--strategy a,b] [execute approved trades automatically]`), which re-runs the slash command verbatim every interval and self-paces in one session.

- On a **fresh start**, run the first tick (step 2), then hand off to `/loop` so it re-fires the command each cadence. Each subsequent firing runs **exactly one tick** — it does not re-arm `/loop` (keep **one** driver only; never start a second).
- Re-firing the exact command string is what carries the loop's state (assets, strategy set, cadence, autonomous flag) across each repeat — there is no separately persisted state to manage.
- If the client does not provide `/loop`, fall back to the harness's own recurring/wake primitive, re-firing the same command string each cadence. Do not hard-code a specific tool name; what matters is "re-run this command every cadence in this session." (Background/cron schedulers are out of scope — same-chat only.)

### 5. Loop-state hygiene (R15)
- Each wake is effectively a fresh tick. Rebuild what the tick needs from (a) the re-fired command args, (b) the **log** (`log.jsonl` — last lines for prior decisions/positions), and (c) live `get_account_state()` — **not** from accumulated chat reasoning. Do not carry full prior-tick analysis forward in context; the durable record is the log. This keeps the main context from growing unbounded across many ticks.

## Close branch (R10, R13, R14)

Trigger only when the user's input is the **explicit `close` command** — `hta-trade-cycle close` (or args that are exactly the bare keyword `close`). A normal message that merely *contains* the word "close" in prose (e.g. "should I close BTC?") does **not** trigger a flatten; if intent is ambiguous, ask before flattening.

Then:
1. **Stop the loop driver first** so no tick re-fires after the flatten (no zombie iteration). End the active `/loop` (or whichever recurring mechanism is driving this session's loop) — identify it from the running session, do not rely on a remembered job id. Do this **before** flattening so a re-fire cannot race the close.
2. **Flatten all open positions regardless of PnL.** Read positions via `get_account_state()`; for each, call `close_position(asset)`. Retry each failed close up to **3 times** with a short backoff.
3. **Honest reporting (R13):** list each position closed (asset, exit, realized PnL). For any that still failed after retries, report it explicitly with current size + unrealized PnL and tell the user it is **still open** and needs manual intervention. **Never print "account is flat" unless every position is confirmed closed.**
4. Append a `close`/`derisk` log line per affected crypto.
5. Stop the loop. Do not schedule another wake.

## Mid-loop messages that are not `close` (R14)

If the user sends any other message while the loop is active:
- **Do not flatten** and **do not silently drop it.** Answer the question or handle the request (e.g. "how is BTC doing?" → report from `get_account_state()`), then continue the loop on its existing schedule.
- If the message is a stop intent other than `close` (e.g. "stop", "pause the loop"), treat it as a **normal stop (R11)**: stop the loop driver (end the `/loop`) and leave open positions untouched (they remain protected by their exchange-side brackets). Confirm that positions are left open and that `close` is the way to also flatten.

## Normal stop (R11)

A normal stop — the session ends, or the user asks to stop without `close` — ends the loop and **leaves open positions in place**, protected by their resting exchange-side SL/TP brackets. No further ticks run. Only the `close` keyword flattens.

## Worst-case close latency

While the loop is idle waiting for a scheduled wake, a `close` typed mid-sleep is acted on at the next opportunity; in the worst case that is up to **one cadence interval** away (5m by default, longer for larger cadences). For a faster emergency exit, use a short cadence or close positions directly on the exchange. This is documented in the README.

## Mode

DRY-RUN is the default and the required pre-LIVE validation path. Validate the full loop — including a mid-loop `close` — in DRY-RUN before any LIVE use. Keep this skill `user-invocable: false` so it does not add a second slash entry alongside the `hta-trade-cycle` command.
