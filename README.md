# Hyperliquid Trading Agent — Claude plugin

Cowork / Claude Code plugin for trading Hyperliquid perpetuals via natural language. Ships **skills, strategies, and slash commands** — connects to an MCP server running as a Docker container in a separate repo.

> **Two-repo architecture.**
> - **MCP server** (Docker, persistent settings, all the Hyperliquid logic): [rsantamaria01/hyperliquid-trading-mcp](https://github.com/rsantamaria01/hyperliquid-trading-mcp). Forked from [edkdev/hyperliquid-mcp](https://github.com/edkdev/hyperliquid-mcp), risk layer adapted from [sanketagarwal/hyperliquid-trading-agent](https://github.com/sanketagarwal/hyperliquid-trading-agent).
> - **This plugin**: just the Claude-facing layer. Skills, strategies, slash commands. **Holds no secrets.** Connects over Streamable HTTP to `http://localhost:8000/mcp` by default; remote URL + auth are set per client (see install).

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
# edit .env — fill in HYPERLIQUID_PRIVATE_KEY + HYPERLIQUID_VAULT_ADDRESS + MCP_AUTH_TOKEN
#   MCP_AUTH_TOKEN: a long random string, e.g. `openssl rand -hex 32`
chmod 600 .env
docker compose up -d
```

Verify: `curl -sf http://<host-ip>:8000/health` → `ok`.

### 2. Install this plugin

**Claude Code (CLI)** — install from a release tag via the marketplace:

```
/plugin marketplace add rsantamaria01/hyperliquid-trading-agent@v0.6.0
/plugin install hyperliquid-trading-agent@hyperliquid-trading
```

The `@v0.6.0` pins the install to that release tag — bump it to install a newer version. Browse tags on the [Releases](https://github.com/rsantamaria01/hyperliquid-trading-agent/releases) page.

**Cowork** — download the `.zip` asset from the matching release and drag it into the install dialog.

The plugin defaults to `http://localhost:8000/mcp`. Pointing it at a **remote** server or sending an **auth token** is done per client (the plugin ships no URL override or token — `${VAR}` expansion is not applied to plugin MCP configs):

- **Claude Code (CLI)** — register your server (same name overrides the plugin's localhost default):
  ```bash
  claude mcp add --transport http --scope user \
    hyperliquid-trading-agent https://your-domain/mcp \
    --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
  ```
  Drop `--header` for a token-less local server; for an OAuth server omit it and run `/mcp` to log in.
- **Cowork (desktop)** — **Add custom connector** (name `hyperliquid-trading-agent`, URL e.g. `https://your-domain/mcp`). The UI is **OAuth-only — no static bearer token / custom headers** — so Cowork can't send `Authorization: Bearer`. For a token-protected server, the token must come from elsewhere:
  - **Reverse proxy injects it** (best if you already serve over HTTPS): Cowork hits `https://your-domain/mcp` with no auth header; the proxy adds the `Authorization` header upstream. Protect the public endpoint with Cloudflare Access / IP allowlist / proxy basic-auth.
  - **SSH tunnel + token off**: `ssh -N -L 8000:127.0.0.1:8000 user@server`, server bound to `127.0.0.1` with `MCP_AUTH_TOKEN` unset → default `localhost:8000/mcp` works.

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
