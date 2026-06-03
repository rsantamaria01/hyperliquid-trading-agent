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
  setup/                       # /hta-setup — install uv + create the workspace .env
  settings/                    # /hta-settings — view/change per-workspace runtime config
  strategy/                    # /hta-strategy — pick or describe a strategy
  market-analysis/             # /hta-analyze — read setups
  trade-cycle/                 # one fan-out iteration (called per tick by trade-loop)
  trade-loop/                  # the loop: repeat trade-cycle on a cadence + `close`
    leaf-contract.md           # (crypto × strategy) leaf verdict contract
  portfolio-review/            # /hta-positions
  risk-audit/                  # /hta-risk-audit
commands/                      # slash-command entry points
strategies/                    # pluggable .md strategy definitions
LOG-SCHEMA.md                  # append-only log.jsonl event schema (local-only)
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

On enable, the plugin spawns `uvx --from git+https://github.com/rsantamaria01/hyperliquid-trading-mcp@v3.0.1 hyperliquid-trading-mcp` automatically. The server writes a startup banner to **stderr**:

```
hyperliquid-trading-mcp [DRY-RUN] — workspace: /path/to/workspace
```

`[LIVE]` there means real orders for this workspace.

**Client support:** the **Claude Code CLI is the supported client** — it sets `CLAUDE_PROJECT_DIR` and has `uvx` on `PATH` for spawned servers. GUI clients (e.g. Cowork) may not put `uvx`/`npx` on the GUI app's `PATH` or set `CLAUDE_PROJECT_DIR`; that path is **untested**. If a GUI client can't launch the server, point it at an absolute path (`$(which uvx)`) or set `PATH` in the server's `env` block.

### 3. Sanity check + configure

In Claude:
```
/hta-setup                                # walks first-time setup; verifies server
/hta-settings                             # see per-workspace config
/hta-trading-mode                         # confirms mode + wallet
```

## Use

```
/hta-strategy                             # list strategies
/hta-analyze BTC ETH --interval 1h
/hta-trade-cycle BTC ETH --strategy breakout-bb
/hta-positions
/hta-risk-audit
/hta-cancel BTC
/hta-settings set max_leverage=5
/hta-settings go-live                     # flips live_trading: true after confirm
```

## Looping trade cycle (orchestrator + background job)

`/hta-trade-cycle <assets>` arms a **background loop**: a scheduled job (cron) fires one trade-cycle iteration every cadence interval, **each in its own headless session**. **This chat is the orchestrator** — you arm, inspect, modify, and stop the loop here, but the heavy per-tick work runs in the background. That keeps this session lean: the fan-out (N assets × M strategies) never lands in your chat context; you only see compact summaries from the log.

```
/hta-trade-cycle BTC ETH SOL --interval 5m --strategy trend-pullback execute approved trades automatically
/hta-trade-cycle status                   # show the running job + recent per-asset results
/hta-trade-cycle close                    # stop the loop AND flatten everything
```

Each background tick: mode check → account snapshot + risk audit → circuit-breaker gate → force-close losers → **fan out one subagent per (crypto × strategy)** in parallel (each analyzes in its own context, returns a compact pass/fail + score + signal) → aggregate per crypto → `validate_trade` → execute → append a log line.

- **Background — survives this chat.** The job keeps firing after you close the chat. Stop it with `hta-trade-cycle close` (stop + flatten) or `CronDelete <id>`. Closing the chat does **not** stop trading.
- **Autonomous required for unattended entries.** A background tick has no human to confirm, so without the phrase `execute approved trades automatically` it **skips** new entries (runs as monitor + de-risk only). With it, LIVE entries fire unattended — every tick still runs force-close, the circuit-breaker gate, and `validate_trade`, and positions open with exchange-side SL/TP brackets.
- **Cadence ≠ timeframe.** `--interval` is how often a tick fires. Each strategy is analyzed on a timeframe **it** declares valid (its `timeframes` frontmatter), independent of the cadence.
- **Default strategy is a single coherent one** (`trend-pullback`). Multiple are opt-in (`--strategy a,b`) — mixing trend and counter-trend often aggregates to HOLD by design (conservative consensus).
- **Circuit breaker** trips → the job is deleted and the loop stops; re-arm manually after reviewing the drawdown.
- **Stopping.** `close` deletes the job and flattens all positions (bounded retry; never claims "flat" unless every close is confirmed). A plain "stop" deletes the job but leaves positions open under their exchange-side brackets. Emergency-exit latency is up to one cadence interval; for a faster stop, delete the job or close on the exchange directly.
- **Log.** Each tick appends to `log.jsonl` (JSON Lines: per crypto, per tick — strategy results, decision, order, PnL). Financial data, git-ignored, **local-only** — never commit or share. Schema: `LOG-SCHEMA.md`.

## Configuration model

| Where | What | How to change |
|---|---|---|
| Workspace `.env` | Only secrets: `HYPERLIQUID_PRIVATE_KEY`, `HYPERLIQUID_VAULT_ADDRESS` | Edit file, re-spawn the server |
| Workspace `.hl-mcp/settings.json` | `live_trading`, `network`, risk caps | `/hta-settings` slash command |
| Plugin `strategies/*.md` | Trading strategies | Add `.md` files; `/hta-strategy create` walks you through one |

Secrets and settings are **per workspace** — read from the folder Claude is open in (`CLAUDE_PROJECT_DIR`), so `live_trading` is scoped to that folder. Risk caps are read on every tool call — change them with `/hta-settings` and they take effect immediately, no restart needed.

## Going live

1. Run several cycles with `live_trading: false`. Verify trades look right.
2. `/hta-settings go-live` (asks for confirmation, then calls `update_settings({"live_trading": true})`).
3. Start conservative: `/hta-settings set max_position_pct=5 max_leverage=3` until you trust it.

A workspace that was previously LIVE reopens LIVE — the startup banner surfaces it, and the loop's confirm-on-new-entry gate guards every new live entry (unless you authorized autonomous entries with `execute approved trades automatically`).

## Autonomous mode (scheduled tasks)

```
cron: */15 * * * *
prompt: Run trade-cycle on BTC ETH SOL using the breakout-bb strategy. Execute approved trades automatically. Report what you did.
```

## License

MIT.
