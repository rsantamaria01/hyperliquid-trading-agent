# Hyperliquid Trading Agent — Claude plugin

Claude Code plugin for trading Hyperliquid perpetuals via natural language. Ships **skills, strategies, and slash commands** — and auto-spawns the MCP server (a separate repo) as a local stdio subprocess.

> **Two-repo architecture.**
> - **MCP server** (per-workspace settings, all the Hyperliquid logic): [rsantamaria01/hyperliquid-trading-mcp](https://github.com/rsantamaria01/hyperliquid-trading-mcp), installed straight from git via `uvx`. Forked from [edkdev/hyperliquid-mcp](https://github.com/edkdev/hyperliquid-mcp), risk layer adapted from [sanketagarwal/hyperliquid-trading-agent](https://github.com/sanketagarwal/hyperliquid-trading-agent).
> - **This plugin**: just the Claude-facing layer. Skills, strategies, slash commands. **Holds no secrets.** Launches the server locally via `uvx --from git+...`; keys live in the workspace `.env` the server reads.

> ⚠️ **Live exchange. Real money.** Not audited. Default mode is dry-run.

## What's in this plugin

```
.claude-plugin/plugin.json    # registers the uvx launch command + skills + commands
skills/
  setup/                       # /setup — install uv + create the workspace .env
  settings/                    # /settings — view/change per-workspace runtime config
  strategy/                    # /strategy — pick or describe a strategy
  market-analysis/             # /analyze — read setups
  trade-cycle/                 # /trade-cycle — one full loop iteration
  portfolio-review/            # /positions
  risk-audit/                  # /risk-audit
commands/                      # slash-command entry points
strategies/                    # pluggable .md strategy definitions
```

## Install — 3 steps

### 1. Install `uv` + create the workspace `.env`

The plugin auto-spawns the server via `uvx`, so you just need `uv` on `PATH` and a `.env` in the folder you open Claude in:

```bash
# install uv (provides uvx), then restart the client
curl -LsSf https://astral.sh/uv/install.sh | sh

# in your workspace root, create .env with your wallet keys
cat > .env <<'EOF'
HYPERLIQUID_PRIVATE_KEY=0x...   # agent wallet key (signer only, no funds)
HYPERLIQUID_VAULT_ADDRESS=0x... # main wallet address (the funded one)
EOF
chmod 600 .env

# never commit secrets or per-workspace settings
printf '.env\n.hl-mcp/\n' >> .gitignore
```

The agent wallet must be created on Hyperliquid first (app.hyperliquid.xyz → Settings → API Wallets). `uvx` clones and builds the server from git on first run (so `git` must be on `PATH`).

### 2. Install this plugin

**Claude Code (CLI)** — install from a release tag via the marketplace:

```
/plugin marketplace add rsantamaria01/hyperliquid-trading-agent@v0.8.0
/plugin install hyperliquid-trading-agent@hyperliquid-trading
```

The `@v0.8.0` pins the install to that release tag — bump it to install a newer version. Browse tags on the [Releases](https://github.com/rsantamaria01/hyperliquid-trading-agent/releases) page.

On enable, the plugin spawns `uvx --from git+https://github.com/rsantamaria01/hyperliquid-trading-mcp@v3.0.0 hyperliquid-trading-mcp` automatically. The server writes a startup banner to **stderr**:

```
hyperliquid-trading-mcp [DRY-RUN] — workspace: /path/to/workspace
```

`[LIVE]` there means real orders for this workspace.

**Client support:** the **Claude Code CLI is the supported client** — it sets `CLAUDE_PROJECT_DIR` and has `uvx` on `PATH` for spawned servers. GUI clients (e.g. Cowork) may not put `uvx`/`npx` on the GUI app's `PATH` or set `CLAUDE_PROJECT_DIR`; that path is **untested**. If a GUI client can't launch the server, point it at an absolute path (`$(which uvx)`) or set `PATH` in the server's `env` block.

### 3. Sanity check + configure

In Claude:
```
/setup                                # walks first-time setup; verifies server
/settings                             # see per-workspace config
/trading-mode                         # confirms mode + wallet
```

## Use

```
/strategy                             # list strategies
/analyze BTC ETH --interval 1h
/trade-cycle BTC ETH --strategy breakout-bb
/positions
/risk-audit
/cancel BTC
/settings set max_leverage=5
/settings go-live                     # flips live_trading: true after confirm
```

## Configuration model

| Where | What | How to change |
|---|---|---|
| Workspace `.env` | Only secrets: `HYPERLIQUID_PRIVATE_KEY`, `HYPERLIQUID_VAULT_ADDRESS` | Edit file, re-spawn the server |
| Workspace `.hl-mcp/settings.json` | `live_trading`, `network`, risk caps | `/settings` slash command |
| Plugin `strategies/*.md` | Trading strategies | Add `.md` files; `/strategy create` walks you through one |

Secrets and settings are **per workspace** — read from the folder Claude is open in (`CLAUDE_PROJECT_DIR`), so `live_trading` is scoped to that folder. Risk caps are read on every tool call — change them with `/settings` and they take effect immediately, no restart needed.

## Going live

1. Run several cycles with `live_trading: false`. Verify trades look right.
2. `/settings go-live` (asks for confirmation, then calls `update_settings({"live_trading": true})`).
3. Start conservative: `/settings set max_position_pct=5 max_leverage=3` until you trust it.

A workspace that was previously LIVE reopens LIVE — the startup banner surfaces it, and `trade-cycle`'s GO/NO gate guards the first live order each interactive cycle.

## Autonomous mode (scheduled tasks)

```
cron: */15 * * * *
prompt: Run trade-cycle on BTC ETH SOL using the breakout-bb strategy. Execute approved trades automatically. Report what you did.
```

## License

MIT.
