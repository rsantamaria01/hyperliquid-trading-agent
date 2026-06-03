---
description: Start a looping trade cycle on the given assets (fan-out analysis + auto-repeat), or `close` to stop and flatten
argument-hint: <asset1> [asset2 ...] [--interval 5m|15m|1h|4h|1d] [--strategy a[,b]] | close
---

Dispatch to the `trade-loop` skill with `$ARGUMENTS`.

- **`hta-trade-cycle <assets> [...]`** — start the loop. It runs one fan-out trade-cycle iteration, then repeats every cadence interval in this chat session. If no assets are given, ask the user for a watchlist (don't start an empty loop).
- **`hta-trade-cycle close`** — stop the loop and flatten **all** positions regardless of PnL. A normal stop (ending the session, or "stop") leaves positions open under their exchange-side SL/TP brackets — only `close` flattens.

Defaults and args:

- **`--interval`** — the loop **cadence** (how often it runs). Default `5m`. This is not the analysis timeframe — each strategy is analyzed on a timeframe it declares valid.
- **`--strategy a[,b]`** — strategies to run. Default is a single curated strategy (`trend-pullback`). Multiple are opt-in; mixing trend and counter-trend strategies often aggregates to HOLD by design.
- Add the phrase **"execute approved trades automatically"** to authorize autonomous LIVE entries; otherwise each new entry pauses for GO/NO in LIVE (risk-reducing actions always auto-run).

Always print the trading mode (DRY-RUN vs LIVE) at the top of your response.
