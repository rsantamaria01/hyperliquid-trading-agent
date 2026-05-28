# Hyperliquid Trading Agent — Claude plugin

Cowork / Claude Code plugin for trading Hyperliquid perpetuals via natural language. Ships **skills, strategies, and slash commands** — connects to an MCP server running as a Docker container in a separate repo.

> **Two-repo architecture.**
> - **MCP server** (Docker, persistent settings, all the Hyperliquid logic): [rsantamaria01/hyperliquid-trading-mcp](https://github.com/rsantamaria01/hyperliquid-trading-mcp). Forked from [edkdev/hyperliquid-mcp](https://github.com/edkdev/hyperliquid-mcp), risk layer adapted from [sanketagarwal/hyperliquid-trading-agent](https://github.com/sanketagarwal/hyperliquid-trading-agent).
> - **This plugin**: just the Claude-facing layer. Skills, strategies, slash commands. **Holds no secrets.** Connects to `http://localhost:8000/sse`.

> ⚠️ **Live exchange. Real money.** Not audited. Default mode is dry-run.

## What's in this plugin

```
.claude-plugin/plugin.json    # registers the MCP URL + skills + commands
skills/
  setup/                       # /setup — bootstrap the Docker server
  settings/                    # /settings — view/change persistent runtime config
  strategy/                    # /strategy — pick or describe a strategy
  market-analysis/             # /analyze — read setups
  trade-cycle/                 # /trade-cycle — one full loop iteration
  portfolio-review/            # /positions
  risk-audit/                  # /risk-audit
commands/                      # slash-command entry points
strategies/                    # pluggable .md strategy definitions
```

## Install — 3 steps

### 1. Start the MCP server (Docker)

```bash
git clone https://github.com/rsantamaria01/hyperliquid-trading-mcp.git
cd hyperliquid-trading-mcp
cp .env.example .env
# edit .env — fill in HYPERLIQUID_PRIVATE_KEY + HYPERLIQUID_VAULT_ADDRESS
chmod 600 .env
docker compose up -d
```

Verify: `curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8000/sse` → `200`.

### 2. Install this plugin

Download the latest `hyperliquid-trading-agent.plugin` from [Releases](https://github.com/rsantamaria01/hyperliquid-trading-agent/releases) and open it (or drag into Cowork's install dialog). Restart Cowork.

### 3. Sanity check + configure

In Claude:
```
/setup                                # walks first-time setup; verifies server
/settings                             # see persistent config
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
| Server `.env` | Only secrets: `HYPERLIQUID_PRIVATE_KEY`, `HYPERLIQUID_VAULT_ADDRESS` | Edit file, `docker compose up -d` |
| Server `/data/settings.json` (named volume) | `live_trading`, `network`, risk caps | `/settings` slash command |
| Plugin `strategies/*.md` | Trading strategies | Add `.md` files; `/strategy create` walks you through one |

The settings file persists across container restarts via a Docker named volume (`hyperliquid-mcp-data`). Risk caps are read on every tool call — change them with `/settings` and they take effect immediately, no restart needed.

## Going live

1. Run several cycles with `live_trading: false`. Verify trades look right.
2. `/settings go-live` (asks for confirmation, then calls `update_settings({"live_trading": true})`).
3. Start conservative: `/settings set max_position_pct=5 max_leverage=3` until you trust it.

## Autonomous mode (Cowork scheduled tasks)

```
cron: */15 * * * *
prompt: Run trade-cycle on BTC ETH SOL using the breakout-bb strategy. Execute approved trades automatically. Report what you did.
```

## License

MIT.
