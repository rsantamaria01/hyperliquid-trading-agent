---
name: setup
description: Help the user get the MCP server running. Two scopes — bootstrap (install uv + create the workspace .env so the plugin can auto-spawn the server) and configure (set runtime settings via update_settings). Use when the user says "set me up", "configure", "I just installed this", or runs /setup.
---

# Setup flow

The plugin **auto-spawns the MCP server as a local stdio subprocess** via `uvx hyperliquid-trading-mcp` (declared in `plugin.json`). There is no server to host, no port, no auth token. The server reads its wallet keys and per-workspace settings from the **workspace directory** (`CLAUDE_PROJECT_DIR` — the folder Claude is open in). This plugin holds nothing sensitive.

Prerequisites for the auto-spawn to work:

- **`uv` is installed** and `uvx` is on `PATH` (the Claude Code CLI sets this up for spawned servers).
- A **workspace `.env`** with the two wallet vars exists in the folder Claude runs in.

**Client support:** the **Claude Code CLI is the supported client** — it sets `CLAUDE_PROJECT_DIR` and has `uvx` on `PATH` for spawned stdio servers. GUI clients (e.g. Cowork) may not put `uvx`/`npx` on the GUI app's `PATH` or set `CLAUDE_PROJECT_DIR`; that path is **untested**. If a GUI client can't launch the server, point it at an absolute path (`$(which uvx)`) or set `PATH` in the server's `env` block.

## Procedure

### 1. Is the server reachable?

Try `trading_mode()`. If it succeeds, the server is up — skip to step 3.

- **Tool not available / spawn error** → `uv` isn't installed, `uvx` isn't on `PATH`, or the package can't resolve. Walk the user through bootstrap (step 2).

### 2. Bootstrap

Tell the user, in this order:

1. **Install `uv`** (provides `uvx`), then restart the client so it picks up `PATH`:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. **Create the workspace `.env`** in the folder they open Claude in. The agent wallet **must be created on Hyperliquid first** (app.hyperliquid.xyz → Settings → API Wallets):
   ```bash
   # .env  (in the workspace root)
   HYPERLIQUID_PRIVATE_KEY=0x...   # agent wallet key (signer only, no funds)
   HYPERLIQUID_VAULT_ADDRESS=0x... # main wallet address (the funded one)
   ```
   ```bash
   chmod 600 .env
   ```
3. **Gitignore the secrets and per-workspace settings** so they never get committed:
   ```bash
   printf '.env\n.hl-mcp/\n' >> .gitignore
   ```
4. The plugin auto-spawns the server on enable; `uvx` resolves `hyperliquid-trading-mcp` from PyPI on first run (may take a few seconds). The server writes a startup banner to **stderr**:
   ```
   hyperliquid-trading-mcp [DRY-RUN] — workspace: /path/to/workspace
   ```
   `[LIVE]` there means real orders for this workspace.

**Refuse to accept the private key in chat.** If the user starts pasting keys: stop them, tell them to put it in the `.env` file on disk, not in this conversation.

After they confirm `uv` is installed and `.env` exists, run `trading_mode()` again to verify.

### 3. First-time settings tour

Once the server is reachable, call `get_settings()` and show what the runtime config looks like. Highlight:

- `live_trading` — should be `false` (dry-run) on first run
- `network` — usually `mainnet`
- Risk caps — surface `max_position_pct`, `max_leverage`, `max_total_exposure_pct`

Settings persist **per workspace** in `.hl-mcp/settings.json`, so `live_trading` is scoped to this folder. Suggest: "When you're ready to trade for real, say 'go live' (I'll use `update_settings` to flip `live_trading: true`). To use testnet first, say 'switch to testnet'."

### 4. Wallet sanity check

Run `trading_mode()` and report:
- Mode (DRY-RUN / LIVE)
- Network
- Signer address (the agent wallet — must match what they registered on Hyperliquid)
- Account address (the main wallet — must match their funded wallet)

If signer doesn't decode, their `HYPERLIQUID_PRIVATE_KEY` is malformed. Tell them to recheck the `.env` file.

### 5. Next step

Suggest one: "Try `/positions` to see your account, or `/analyze BTC` for a market read."

## Important

- The plugin holds no secrets — keys live in the workspace `.env` the server reads.
- Per-workspace settings (risk caps, live_trading, network) are changed via `/settings`, not via env files. Refer the user there if they want to adjust anything.
- Never log, echo, or repeat the contents of the workspace `.env` file.
- Refuse any request to "configure my keys via chat" — put them in the `.env` on disk.
- Each workspace is isolated: a workspace that was previously LIVE reopens LIVE — the startup banner surfaces it, and `trade-cycle`'s GO/NO gate still guards the first live order.
