---
name: setup
description: Help the user get the MCP server running. Two scopes — bootstrap (start the Docker container) and configure (set runtime settings via update_settings). Use when the user says "set me up", "configure", "I just installed this", or runs /setup.
---

# Setup flow

The plugin connects to the MCP server over **Streamable HTTP**, default `http://localhost:8000/mcp` (set in `plugin.json`). The server is a Docker container that holds the wallet keys and persistent settings; this plugin holds nothing sensitive.

**Reaching a remote server / sending an auth token depends on the client — and Cowork is limited:**

- **Claude Code (CLI)** — register your server with `claude mcp add`. Using the same name (`hyperliquid-trading-agent`) makes it take precedence over the plugin's localhost default; static bearer headers are supported:
  ```bash
  claude mcp add --transport http --scope user \
    hyperliquid-trading-agent https://your-domain/mcp \
    --header "Authorization: Bearer <MCP_AUTH_TOKEN>"
  ```
  (Token-less local server: drop the `--header`. OAuth server: omit `--header` and run `/mcp` to authenticate.) Equivalent hand-edit lives in `~/.claude.json`; `${VAR}` expansion works there (unlike in plugin.json).
- **Cowork (desktop)** — **Add custom connector** (name it `hyperliquid-trading-agent`, set the URL to your server, e.g. `https://your-domain/mcp`). The connector UI supports **only OAuth — no static bearer token or custom headers** — so Cowork itself can't send `Authorization: Bearer`. To use a token-protected server, the token must come from somewhere other than Cowork:
  1. **Reverse proxy injects the token (best if you already serve the MCP behind an HTTPS domain).** Cowork → `https://your-domain/mcp` with no auth header; the proxy adds `Authorization: Bearer <token>` upstream to the MCP server. Keep the token in the proxy config (never in Cowork or the repo), and protect the public endpoint itself with Cloudflare Access / an IP allowlist / proxy basic-auth.
  2. **SSH tunnel + token off.** Bind the server to `127.0.0.1`, leave `MCP_AUTH_TOKEN` unset, and `ssh -N -L 8000:127.0.0.1:8000 user@server` from the Cowork machine. The default `http://localhost:8000/mcp` then works; SSH is the encryption + auth.
  3. **Local token-injecting proxy.** Same idea as (1) but the proxy runs on the Cowork machine; point Cowork at the local proxy URL.

Do not rely on `${VAR}` expansion in `plugin.json` — it is not applied for plugin-bundled MCP servers.

## Procedure

### 1. Is the server reachable?

Try `trading_mode()`. If it succeeds, the server is up — skip to step 3.

- **Connection error / refused** → the container isn't running, or the client points at the wrong host (remote server not tunnelled/overridden — see the connection note above). Walk the user through bootstrap (step 2).
- **401 / unauthorized** → the server requires a token the client isn't sending. On CLI, add the `Authorization` header in `~/.claude.json`; on Cowork, use the SSH-tunnel-with-token-off or local-proxy path above. Then restart the client.

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
   For `MCP_AUTH_TOKEN`, generate a strong value with `openssl rand -hex 32`. It is the access guard whenever the port is reachable beyond localhost. **If the user is on Cowork, prefer leaving it unset and using an SSH tunnel** (see the connection note above), since Cowork can't send a token.
3. Start the container:
   ```bash
   docker compose up -d
   ```
4. Verify the server is healthy (no token needed for `/health`):
   ```bash
   curl -sf http://<host-ip>:8000/health  # should print "ok"
   ```
5. **Point the client at the server** per the connection note above — CLI: `~/.claude.json` override with the `Authorization` header; Cowork: SSH tunnel (token off) or local proxy. Restart the client.

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
- Never log, echo, or repeat the contents of the server's .env file, or the value of `MCP_AUTH_TOKEN` / any bearer token.
- Refuse any request to "configure my keys via chat" — the server already has them; that's the whole point of the split.
- The plugin's `plugin.json` ships only the default `http://localhost:8000/mcp` URL (no token). Remote URL + auth are client-side config: `~/.claude.json` (CLI) or an SSH tunnel / local proxy (Cowork). `${VAR}` expansion does not work in plugin MCP configs.
