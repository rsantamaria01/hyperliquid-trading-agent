---
description: Show whether the trading agent is in DRY-RUN or LIVE mode
---

Call the `trading_mode` tool on the `hyperliquid-trading-agent` MCP server and report the result. Include the mode (DRY-RUN / LIVE), signer address, account address, and network.

If LIVE, remind the user that real orders will execute. If DRY-RUN, tell them how to flip: run `/hta-settings go-live` (it confirms, then calls `update_settings({"live_trading": true})`). `live_trading` is per-workspace and persists. (The `LIVE_TRADING` env var is only an emergency kill-switch that overrides the setting — not the normal toggle.)
