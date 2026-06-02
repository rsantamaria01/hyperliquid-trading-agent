---
description: View or change the MCP server's persistent runtime settings
argument-hint: [show | set <key>=<value> | reset | go-live | go-dry-run | testnet | mainnet]
---

Run the `settings` skill with the argument in $ARGUMENTS.

- No argument or `show` → `get_settings()` and print a compact table
- `set <key>=<value>` → `update_settings({"<key>": <value>})`
- `reset` → `reset_settings()` after confirming
- `go-live` → confirm, then `update_settings({"live_trading": true})`
- `go-dry-run` → `update_settings({"live_trading": false})`
- `testnet` / `mainnet` → `update_settings({"network": "..."})`
