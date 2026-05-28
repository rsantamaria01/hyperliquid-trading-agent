# Hyperliquid Trading Agent — Claude plugin

Trade Hyperliquid perpetuals directly from a Claude conversation, in Cowork or Claude Code. Get market reads, run a full trade cycle, review your portfolio, audit your risk — all via slash commands. No standalone Python loop, no `ANTHROPIC_API_KEY` required.

> **Credits:** trading logic, indicators, and risk-guard design adapted from [sanketagarwal/hyperliquid-trading-agent](https://github.com/sanketagarwal/hyperliquid-trading-agent) (MIT). Architecture inverted into an MCP server + skills so Claude drives the loop instead of being called from one.

> ⚠️ **Live exchange. Real money.** Not audited. Use at your own risk. Start in dry-run mode (default). See `LICENSE`.

## Quick install — 2 steps

The plugin self-installs its Python dependencies the first time it runs into a venv inside its own folder. **You don't need `pip`, `uv`, or any extra setup** — just Python 3.10+, which is already on macOS and Linux. On Debian/Ubuntu, also make sure `python3-venv` is installed (`sudo apt install python3-venv`).

### 1. Install the plugin

Download the latest `hyperliquid-trading-agent.plugin` from the [releases page](https://github.com/rsantamaria01/hyperliquid-trading-agent/releases).

**Cowork:** open the `.plugin` file (or drag it into the Cowork install dialog). Cowork drops it into your plugins directory.

**Claude Code:** unzip the `.plugin` file into a directory and add it to your plugin path, or place it under `~/.claude/plugins/hyperliquid-trading-agent/`.

### 2. Configure — `/setup`

**Your private key never goes through chat.** Setup is path-only:

1. Create `.env` somewhere on your disk (e.g. `~/.config/hyperliquid-agent.env`) using `.env.example` as a template. Fill in your keys.
2. Lock it down: `chmod 600 ~/.config/hyperliquid-agent.env`
3. In Claude, run `/setup` and give it the path. Claude will symlink the plugin to your file via the `link_env_file` MCP tool and verify the connection with `trading_mode`.

That's it. The plugin reads from your file each time it starts. To change settings, edit your `.env` directly and restart Claude.

Pasting key contents into chat is rejected — the conversation log is a leak vector. The path is the only thing that travels through chat.

**First-run note:** the very first MCP call after install takes ~30 seconds — the plugin is creating a venv and installing Python deps. After that it's instant. Check `~/.config/Claude/plugins/hyperliquid-trading-agent/mcp_server/.venv/` to confirm the cache built.

That's it. The first time the MCP server runs, `uvx` installs Python deps in an isolated cache — takes ~20 seconds. After that it's instant.

## Where is "the root of the installed plugin folder"?

After install, the plugin lives at one of these paths:

- **Cowork (macOS):** `~/Library/Application Support/Claude/plugins/hyperliquid-trading-agent/`
- **Cowork (Linux):** `~/.config/Claude/plugins/hyperliquid-trading-agent/`
- **Cowork (Windows):** `%APPDATA%\Claude\plugins\hyperliquid-trading-agent\`
- **Claude Code:** wherever you placed the unzipped folder (e.g. `~/.claude/plugins/hyperliquid-trading-agent/`)

The `.env` file goes directly inside that folder — at the same level as `.claude-plugin/` and `mcp_server/`. You can also point to a different `.env` location by setting `HYPERLIQUID_PLUGIN_ENV=/path/to/your.env` in your shell.

## How to get a Hyperliquid agent wallet

1. Go to [app.hyperliquid.xyz](https://app.hyperliquid.xyz) → Settings → API Wallets
2. Add a new API wallet — save the private key (this becomes `HYPERLIQUID_PRIVATE_KEY`)
3. Your main wallet address is `HYPERLIQUID_VAULT_ADDRESS`

The agent wallet **signs trades** on behalf of the main wallet. It cannot withdraw funds.

## Use

After install, in Claude:

```
/trading-mode                              # confirm DRY-RUN vs LIVE + which wallet
/analyze BTC ETH SOL --interval 1h         # market read
/positions                                 # portfolio review
/risk-audit                                # risk check
/trade-cycle BTC ETH SOL                   # one full loop iteration
```

Or natural language: "analyze BTC on the 4h", "what's my PnL?", "close my ETH position".

## Going live

1. Run several `/trade-cycle` iterations with `LIVE_TRADING=false`. Verify the trades look right.
2. Edit `.env`: `LIVE_TRADING=true`.
3. Restart Claude so the MCP server reloads.
4. `/trading-mode` should now report `LIVE`.
5. Start conservative — `MAX_POSITION_PCT=5`, `MAX_LEVERAGE=3` — until you trust it.

## Autonomous mode (Cowork only)

To replicate the upstream's interval loop:

1. Set `LIVE_TRADING=true` in `.env`.
2. Create a Cowork scheduled task with cron `*/15 * * * *` and prompt:
   > Run the trade-cycle skill on BTC ETH SOL with interval 5m. Report what you did.

## What the plugin exposes

**Market data**: `get_current_price`, `get_candles`, `get_market_context`
**Account**: `get_account_state`, `get_open_orders`, `get_recent_fills`
**Risk**: `get_risk_limits`, `check_losing_positions`, `validate_trade`
**Orders**: `place_market_order`, `place_limit_order`, `close_position`, `force_close_losing_positions`, `set_stop_loss`, `set_take_profit`, `cancel_order`, `cancel_all_orders`
**Meta**: `trading_mode`

Every order tool checks `LIVE_TRADING`. Dry-run returns a simulated response — safe for testing.

## Safety

- Risk guards (position size, leverage, exposure, daily drawdown, mandatory SL) are enforced in code before any SDK call. The LLM cannot override them.
- Private key never leaves your machine. The MCP server runs locally.
- Not audited. Trade at your own risk.

## Troubleshooting

**Plugin tools don't appear after restart:**
- Check that `python3` is reachable. In a terminal: `python3 --version`. If missing, install it.
- On Debian/Ubuntu, also need `sudo apt install python3-venv` for the bootstrap to create its venv.
- Inspect bootstrap output: tail Cowork's log (typically `~/.config/Claude/logs/`) for lines tagged `[hyperliquid-mcp bootstrap]`.

**Wipe the cache and reinstall deps:**
```bash
rm -rf ~/.config/Claude/plugins/hyperliquid-trading-agent/mcp_server/.venv
```
Next restart, the bootstrap recreates it.

## License

MIT.
