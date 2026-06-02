---
description: Run one full trading-loop iteration on the given assets, optionally using a strategy
argument-hint: <asset1> [asset2 ...] [--interval 5m|15m|1h|4h|1d] [--strategy <name>]
---

Run the `trade-cycle` skill on the assets in $ARGUMENTS (space-separated). If no assets are given, ask the user for a watchlist.

Defaults: interval `5m`, no strategy (default heuristics).

If `--strategy <name>` is passed, load `strategies/<name>.md` from the plugin folder and follow its rules instead of the default heuristics.

Always print the trading mode (DRY-RUN vs LIVE) at the top of your response.
