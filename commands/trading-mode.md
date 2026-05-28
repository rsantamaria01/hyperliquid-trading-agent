---
description: Show whether the trading agent is in DRY-RUN or LIVE mode
---

Call the `trading_mode` tool on the `hyperliquid-trading-agent` MCP server and report the result. Include signer address, account address, network, and the LIVE_TRADING env value.

If LIVE, remind the user that real orders will execute. If DRY-RUN, tell them how to flip (set `LIVE_TRADING=true` in the MCP env).
