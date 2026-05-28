---
description: Run one full trading-loop iteration on the given assets
argument-hint: [asset1 asset2 ...] [--interval 5m|1h|...]
---

Run the `trade-cycle` skill on the assets in $ARGUMENTS (space-separated). If no assets are given, ask the user for a watchlist.

Default interval is `5m` unless the user passes `--interval`.

Always print the trading mode (DRY-RUN vs LIVE) at the top of your response.
