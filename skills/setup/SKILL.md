---
name: setup
description: Help the user get the MCP server running. Two scopes — bootstrap (start the Docker container) and configure (set runtime settings via update_settings). Use when the user says "set me up", "configure", "I just installed this", or runs /setup.
---

# Setup flow

The plugin connects to the MCP server over **Streamable HTTP at `/mcp`**. It defaults to `http://localhost:8000/mcp`; two env vars (read from the shell where Claude Code / Cowork launches) override the connection:

- `HL_MCP_URL` — full server URL. Set this to `http://<host-ip>:8000/mcp` when the server runs on another machine.
- `HL_MCP_TOKEN` — bearer token sent as `Authorization: Bearer <token>`. **Must equal the server's `MCP_AUTH_TOKEN`.** Leave it unset only when the server runs without a token (local-only).

The server is a Docker container that holds the wallet keys and persistent settings. This plugin holds nothing sensitive — including the token, which lives in the user's shell env, not in the plugin.

## Procedure

### 1. Is the server reachable?

Try `trading_mode()`. If it succeeds, the server is up — skip to step 3.

- **Connection error / refused** → the Docker container isn't running (or `HL_MCP_URL` points at the wrong host). Walk the user through bootstrap (step 2).
- **401 / unauthorized** → the server requires a token but `HL_MCP_TOKEN` is unset or doesn't match the server's `MCP_AUTH_TOKEN`. Have them export the correct token (step 2.4) and relaunch.

### 2. Bootstrap (Docker)

Tell the user, in this order:

1. Clone the MCP repo (or update it):
   ```bash
   git clone https://github.com/rsantamaria01/hyperliquid-trading-mcp.git
   cd hyperliquid-trading-mcp
   ```
2. Create the `.env` file with their wallet keys. The agent wallet **must be created on Hyperliquid first** (app.hyperliquid.xyz → Settings → API Wallets), then:
   ```bash
   cp .env.example .env
   # edit .env — fill in:
   #   HYPERLIQUID_PRIVATE_KEY=0x... (agent wallet key)
   #   HYPERLIQUID_VAULT_ADDRESS=0x... (main wallet address)
   #   MCP_AUTH_TOKEN=...            (a long random string; see note below)
   chmod 600 .env
   ```
   For `MCP_AUTH_TOKEN`, generate a strong value with `openssl rand -hex 32`. The port is exposed on all interfaces, so this token is the access guard — required unless the server is bound to localhost only.
3. Start the container:
   ```bash
   docker compose up -d
   ```
4. **Point the plugin at the server.** In the shell where Claude Code / Cowork runs, export the matching token (and the URL if the server is remote), then relaunch:
   ```bash
   export HL_MCP_TOKEN=<same value as MCP_AUTH_TOKEN>
   export HL_MCP_URL=http://<host-ip>:8000/mcp   # omit for a local server (defaults to localhost)
   ```
5. Verify the server is healthy (no token needed for `/health`):
   ```bash
   curl -sf http://<host-ip>:8000/health  # should print "ok"
   ```

**Refuse to accept the private key in chat.** If the user starts pasting keys: stop them, tell them to put it in the `.env` file on disk, not in this conversation.

After they confirm the container is up, run `trading_mode()` again to verify.

### 3. First-time settings tour

Once the server is reachable, call `get_settings()` and show what the runtime config looks like. Highlight:

- `live_trading` — should be `false` (dry-run) on first run
- `network` — usually `mainnet`
- Risk caps — surface `max_position_pct`, `max_leverage`, `max_total_exposure_pct`

Suggest: "When you're ready to trade for real, say 'go live' (I'll use `update_settings` to flip `live_trading: true`). To use testnet first, say 'switch to testnet'."

### 4. Wallet sanity check

Run `trading_mode()` and report:
- Mode (DRY-RUN / LIVE)
- Network
- Signer address (the agent wallet — must match what they registered on Hyperliquid)
- Account address (the main wallet — must match their funded wallet)

If signer doesn't decode, their `HYPERLIQUID_PRIVATE_KEY` is malformed. Tell them to recheck the .env file.

### 5. Next step

Suggest one: "Try `/positions` to see your account, or `/analyze BTC` for a market read."

## Important

- The plugin no longer manages env files itself — that's the server's responsibility.
- Per-user settings (risk caps, live_trading, network) are now changed via `/settings`, not via env files. Refer the user there if they want to adjust anything.
- Never log, echo, or repeat the contents of the server's .env file, or the value of `HL_MCP_TOKEN` / `MCP_AUTH_TOKEN`.
- Refuse any request to "configure my keys via chat" — the server already has them; that's the whole point of the split.
- `HL_MCP_URL` / `HL_MCP_TOKEN` are client-side shell env vars (where Claude Code / Cowork launches), read by `plugin.json`. They are the one thing the user sets outside the server's `.env`.
