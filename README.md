# Hyperliquid Trading Agent — Claude plugin

A Cowork / Claude Code plugin for trading Hyperliquid perpetuals via natural language. Ships **skills, strategies, and slash commands** — the actual MCP server lives in a separate repo.

> **Architecture:** Two repos, clean split.
> - **MCP server** (Python, Docker-ready): [rsantamaria01/hyperliquid-trading-mcp](https://github.com/rsantamaria01/hyperliquid-trading-mcp) — generic Hyperliquid interface with hard-coded risk guards. Forked from [edkdev/hyperliquid-mcp](https://github.com/edkdev/hyperliquid-mcp), risk layer adapted from [sanketagarwal/hyperliquid-trading-agent](https://github.com/sanketagarwal/hyperliquid-trading-agent).
> - **This plugin**: Claude-specific layer — skills, strategies, slash commands.

> ⚠️ **Live exchange. Real money.** Not audited. Use at your own risk. Default is dry-run.

## What's in this plugin

```
.claude-plugin/plugin.json    # registers the external MCP + skills + commands
skills/
  setup/                       # /setup — link your .env file
  strategy/                    # /strategy — pick or describe a strategy
  market-analysis/             # /analyze — read setups on assets
  trade-cycle/                 # /trade-cycle — one full loop iteration
  portfolio-review/            # /positions — review open positions
  risk-audit/                  # /risk-audit — check risk posture
commands/                     # slash command shells that invoke the skills
strategies/                   # pluggable .md strategy definitions
  breakout-bb.md
  trend-pullback.md
  mean-reversion-rsi.md
  range-fade.md
```

## Install

### 1. Install `uv` (one-time)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

The plugin uses `uvx` to launch the MCP server. `uvx` clones and installs the server on first run; subsequent runs are instant.

### 2. Configure your `.env`

```bash
mkdir -p ~/.config/hyperliquid-mcp
cp <wherever you have your .env> ~/.config/hyperliquid-mcp/.env
chmod 600 ~/.config/hyperliquid-mcp/.env
```

See [hyperliquid-trading-mcp/.env.example](https://github.com/rsantamaria01/hyperliquid-trading-mcp/blob/main/.env.example) for the full field list.

The minimum:
```
HYPERLIQUID_PRIVATE_KEY=0x...     # agent wallet private key (signer)
HYPERLIQUID_VAULT_ADDRESS=0x...   # main wallet address (funded)
LIVE_TRADING=false
```

### 3. Install the plugin in Cowork

Download `hyperliquid-trading-agent.plugin` from the [releases page](https://github.com/rsantamaria01/hyperliquid-trading-agent/releases) and open it (or drag into Cowork's install dialog).

Restart Cowork after install so the MCP server registers.

## Alternative: Docker for the MCP

If you'd rather run the MCP server as a Docker container instead of via `uvx`:

```bash
git clone https://github.com/rsantamaria01/hyperliquid-trading-mcp.git
cd hyperliquid-trading-mcp
cp .env.example .env  # fill in
docker compose build
```

Then edit `.claude-plugin/plugin.json` in the installed plugin folder, changing the `mcpServers` block to:

```json
"mcpServers": {
  "hyperliquid-trading-agent": {
    "command": "docker",
    "args": ["run", "--rm", "-i", "--env-file", "/absolute/path/to/.env", "rsantamaria01/hyperliquid-trading-mcp:latest"]
  }
}
```

## Use

```
/setup ~/.config/hyperliquid-mcp/.env      # link your env file
/trading-mode                              # confirm DRY-RUN vs LIVE
/strategy                                  # list available strategies
/analyze BTC ETH --interval 1h             # market read
/trade-cycle BTC ETH --interval 5m         # one loop iteration (default heuristics)
/trade-cycle BTC ETH --strategy breakout-bb  # use a specific strategy
/positions                                 # portfolio review
/risk-audit                                # risk posture
/cancel BTC                                # cancel all BTC orders
```

Or natural language: "analyze BTC on the 4h", "use the mean-reversion strategy on SOL", "close my ETH position".

## Adding strategies

Drop a new `.md` file in `strategies/` with the frontmatter and sections documented in [strategies/README.md](./strategies/README.md). Then `/trade-cycle ASSETS --strategy <your-name>`.

## Going live

1. Run a few cycles in dry-run. Verify the plan and execution flow look right.
2. Edit your `.env` and set `LIVE_TRADING=true`.
3. Restart Cowork.
4. `/trading-mode` should now report LIVE.
5. Start with conservative risk caps (`MAX_POSITION_PCT=5`, `MAX_LEVERAGE=3`) until you trust the setup.

## Autonomous mode (Cowork scheduled tasks)

```
cron: */15 * * * *
prompt: Run trade-cycle on BTC ETH SOL with interval 5m using the breakout-bb strategy. Execute approved trades automatically. Report what you did.
```

## License

MIT.
