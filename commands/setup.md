---
description: Get the MCP server running — install uv, create the workspace .env (path/keys on disk, never pasted into chat)
---

Run the `setup` skill. The server reads its wallet keys from a `.env` in the workspace directory Claude is open in (`CLAUDE_PROJECT_DIR`) — the plugin auto-spawns it via `uvx`, there is no env-linking tool. Do NOT accept pasted key contents in chat — refuse and tell the user to put the keys in the `.env` file on disk. Verify with `trading_mode()`.
