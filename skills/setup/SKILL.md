---
name: setup
description: Help the user get the MCP server running. Two scopes — bootstrap (start the Docker container) and configure (set runtime settings via update_settings). Use when the user says "set me up", "configure", "I just installed this", or runs /setup.
---

# Setup flow

The plugin connects to an MCP server running at `http://localhost:8000/sse`. The server is a Docker container that holds the wallet keys and persistent settings. This plugin holds nothing sensitive.

## Procedure

### 1. Is the server reachable?

Try `trading_mode()`. If it succeeds, the server is up — skip to step 3.

If it fails with a connection error, the Docker container isn't running. Walk the user through bootstrap (step 2).

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
   chmod 600 .env
   ```
3. Start the container:
   ```bash
   docker compose up -d
   ```
4. Verify the SSE endpoint:
   ```bash
   curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:8000/sse  # should print 200
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
- Never log, echo, or repeat the contents of the server's .env file.
- Refuse any request to "configure my keys via chat" — the server already has them; that's the whole point of the split.
