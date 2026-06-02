---
name: settings
user-invocable: false
description: View or change the MCP server's persistent runtime settings — risk caps, live_trading mode, network. Settings persist per workspace in .hl-mcp/settings.json and survive restarts. Use when the user says "show settings", "change max leverage", "go live", "switch to testnet", or runs /hta-settings.
---

# Settings management

The MCP server keeps its runtime config in a per-workspace JSON file (`CLAUDE_PROJECT_DIR/.hl-mcp/settings.json`). You change it via two MCP tools: `get_settings` and `update_settings`. Changes persist across restarts and are scoped to the workspace folder.

**Only these fields are configurable here.** Wallet keys (`HYPERLIQUID_PRIVATE_KEY`, `HYPERLIQUID_VAULT_ADDRESS`) are secrets — they live in the workspace `.env` file and CANNOT be changed via MCP tools.

## Editable settings

| Key | Type | Default | Notes |
|---|---|---|---|
| `live_trading` | bool | `false` | Set true to send real orders. Set false to dry-run. |
| `network` | string | `"mainnet"` | Or `"testnet"`. Changing this triggers an internal client rebuild. |
| `max_position_pct` | float | 10.0 | Single position cap as % of equity |
| `max_loss_per_position_pct` | float | 20.0 | Force-close threshold |
| `max_leverage` | int | 10 | Per-asset leverage cap (set on Hyperliquid before each entry) |
| `max_total_exposure_pct` | float | 50.0 | Sum of position notionals cap |
| `daily_loss_circuit_breaker_pct` | float | 10.0 | Halt new trades at this daily drawdown |
| `mandatory_sl_pct` | float | 5.0 | Auto-SL distance if user/strategy doesn't set one |
| `max_concurrent_positions` | int | 10 | |
| `min_balance_reserve_pct` | float | 20.0 | Stop trading below this % of starting balance |

## Procedure

### Showing settings (default `/hta-settings`)

1. Call `get_settings()`.
2. Show a compact table of current values, marking which differ from defaults.
3. Mention `live_trading` and `network` prominently — those are the safety-relevant ones.

### Changing settings

- If the user says "set max_leverage to 5" or similar: call `update_settings({"max_leverage": 5})`.
- If the user says "go live": **confirm first** (one short sentence), then `update_settings({"live_trading": true})`.
- If they want to switch to testnet: `update_settings({"network": "testnet"})` — warn that this requires the next tool call to use a fresh client (transparent to the user).
- Multiple keys at once: pass them all in one `update_settings` call.

### Reset

If the user says "reset settings" or "back to defaults":
1. Call `get_settings()` to show what's about to change.
2. Confirm.
3. Call `reset_settings()`.

## Important

- **Never assume the user wants live trading on.** Confirm explicitly before setting `live_trading: true`.
- The risk manager's hard checks are configured here, but they're still hard-coded — a strategy cannot bypass them by changing settings mid-cycle.
- If `update_settings` returns `{"status": "error", ...}`, the user passed an unknown key or invalid value. Report the error and the list of editable keys.
