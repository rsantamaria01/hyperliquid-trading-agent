---
description: Arm/inspect/stop a background looping trade cycle (fan-out analysis on a schedule). This chat is the orchestrator; ticks run in the background.
argument-hint: <asset1> [asset2 ...] [--interval 5m|15m|1h|4h|1d] [--strategy a[,b]] | status | close
---

Dispatch to the `trade-loop` skill with `$ARGUMENTS`. **This chat is the orchestrator / control panel** — it arms, inspects, modifies, and stops the loop, but the trading **ticks run in the background** (a cron job fires one `trade-cycle` iteration every cadence interval, each in its own headless session). That keeps this session's context lean: the heavy per-tick fan-out (N assets × M strategies) stays out of this chat; here you only see compact summaries from the log.

- **`hta-trade-cycle <assets> [...]`** — arm the background loop. If no assets are given, ask for a watchlist (don't arm an empty loop).
- **`hta-trade-cycle status`** — show the running job + recent per-asset results from the log (read-only).
- **`hta-trade-cycle <new assets/strategies/cadence>`** while running — modify: re-arm with new params (one job only).
- **`hta-trade-cycle close`** — stop the loop and flatten **all** positions regardless of PnL. A plain "stop" stops the job but leaves positions open under their exchange-side SL/TP brackets — only `close` flattens.

Defaults and args:

- **`--interval`** — the loop **cadence** (how often a tick fires). Default `5m`. Not the analysis timeframe — each strategy is analyzed on a timeframe it declares valid.
- **`--strategy a[,b]`** — strategies to run. Default is a single curated strategy (`trend-pullback`). Multiple are opt-in; mixing trend and counter-trend strategies often aggregates to HOLD by design.
- Add the phrase **"execute approved trades automatically"** to authorize autonomous LIVE entries (required for a background loop to open new positions unattended; without it, entries that need confirmation are skipped). Risk-reducing actions always auto-run.

> **Background job — keeps running after you close this chat.** Stop it with `hta-trade-cycle close` or by deleting the cron job. In LIVE + autonomous, ticks place real orders unattended.

Always print the trading mode (DRY-RUN vs LIVE) at the top of your response.
