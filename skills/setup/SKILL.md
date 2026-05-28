---
name: setup
description: Connect the plugin to a user-owned .env file. The user creates the file on disk OUTSIDE Claude (so the private key never enters chat) and gives Claude the path. Use when the user says "set up the plugin", "configure my keys", "I just installed this", "where do I put my keys?", or runs /setup.
---

# Setup flow — path-only (secret-safe)

The plugin's setup is intentionally restricted to one path:

> The user creates a `.env` file on their own disk, then gives Claude its absolute path.

**Pasting a private key into chat is rejected.** Anything typed into the conversation persists in the session log — that's a leak risk. The `.env` lives on the user's disk, only the path travels through chat.

## Procedure

### 1. Status check

Call `get_setup_status()`. It returns:
- `env_path` — where the plugin expects to find its env file
- `env_file_exists` — whether one is already linked
- `missing_required` — `HYPERLIQUID_PRIVATE_KEY` and/or `HYPERLIQUID_VAULT_ADDRESS` if unset

If `configured` is true, ask if they want to relink to a different file. Otherwise continue.

### 2. Show the template, ask for a path

Tell the user, in this exact order:

1. Create a file somewhere on their disk (e.g. `~/.config/hyperliquid-agent.env`) — outside any synced folder, not in chat.
2. Copy this template into it and fill in their values:

```
HYPERLIQUID_PRIVATE_KEY=0x...           # agent wallet, signer only
HYPERLIQUID_VAULT_ADDRESS=0x...         # main wallet
HYPERLIQUID_NETWORK=mainnet             # or testnet
LIVE_TRADING=false                      # start in dry-run
MAX_POSITION_PCT=10
MAX_LEVERAGE=10
MAX_TOTAL_EXPOSURE_PCT=50
DAILY_LOSS_CIRCUIT_BREAKER_PCT=10
MANDATORY_SL_PCT=5
MAX_CONCURRENT_POSITIONS=10
MIN_BALANCE_RESERVE_PCT=20
MAX_LOSS_PER_POSITION_PCT=20
```

3. Save with permissions `600` (owner-read-only): `chmod 600 ~/.config/hyperliquid-agent.env` on macOS/Linux.
4. Reply with **only the path** — e.g. `/Users/raul/.config/hyperliquid-agent.env`.

If the user starts pasting key contents into chat, **stop them immediately**: "Don't paste your key here — it would land in the conversation log. Save it to a file and give me the path instead."

### 3. Link the file

Once they give you a path:

```
link_env_file(path="<their path>", mode="symlink")
```

Default `symlink` mode keeps the secret in their file — the plugin folder just points at it. If symlinks aren't supported (some Windows setups), retry with `mode="copy"`.

The tool returns which recognized keys are in the file and which were ignored. It does **not** echo the secret values — confirm only the keys are present, not their contents.

### 4. Verify

Call `trading_mode()`. Report:
- Mode (DRY-RUN / LIVE)
- Network
- Signer address (derived from the private key — useful confirmation, not a leak)
- Account address

If signer doesn't decode, something's wrong with the key format in their file. Ask them to recheck their `.env`.

### 5. Next step

Suggest one: "Try `/positions` or `/analyze BTC`."

## Important

- **NEVER ask the user to paste their private key, address, or any .env value into chat.** Even pasted "for verification" — refuse and ask for a path.
- **NEVER call any tool with a private key in the arguments.** The only credential-touching tool is `link_env_file`, which only accepts a *path*.
- Never log, echo, or repeat the contents of the linked file.
- If they want to change one value (like flipping LIVE_TRADING), tell them to edit their .env directly and restart Claude — don't try to rewrite it from chat.
