# Changelog

## 0.10.3 — Pin server v3.0.3 (read_concurrency is a setting)

- Bump the server pin `v3.0.2` → `v3.0.3`. The read-concurrency knob added in v3.0.2 was wrongly an env var; it's now a proper per-workspace **setting**. Tune it with `/hta-settings set read_concurrency=3` (lower it if a heavy fan-out hits rate-limits/502s) — no new env var, no restart. `.env` stays secrets-only.

## 0.10.2 — Log in the workspace; survive bursty fan-out

First LIVE loop test surfaced two issues.

- **Bug: the log was written to the plugin folder, not the user's workspace.** `LOG-SCHEMA.md` and `trade-cycle` said `hl-plugin/log.jsonl`, so the tick wrote into the plugin's directory (on the test machine, a dev clone) instead of where the user ran the chat. Fixed: the log is written to **`log.jsonl` in the workspace** (`CLAUDE_PROJECT_DIR`, next to `.env`/`.hl-mcp/`), never a plugin path. `/hta-setup` now git-ignores `log.jsonl`.
- **Bug: `get_market_context` `IndexError` blinded most leaves under heavy fan-out.** A tick fired 36 leaves at once; the burst self-inflicted rate-limits/502s and the SDK raised `IndexError` on truncated bodies, so every asset HOLDed. Fixed in the **MCP server (bumped pin `v3.0.1` → `v3.0.2`)**: read calls now use bounded concurrency + backoff retry, the lazy meta fetch is serialized (no stampede), and candle/price fetches degrade gracefully instead of crashing the tool. README now warns to start with a modest watchlist.

## 0.10.1 — Fix the loop: background orchestrator model

First live test of 0.10.0 surfaced two breakages and a clarified design. The loop is now an **orchestrator + background job**, not a same-chat loop.

- **Bug: scheduled re-fire failed with `Unknown command: /hta-trade-cycle`.** The loop re-fired a slash command, which does not resolve in a scheduled/headless run. Fixed: the cron runs a **natural-language instruction that triggers the `trade-cycle` skill** for exactly one tick — never a slash command, and never `trade-loop` (which would arm another cron).
- **Bug: `/loop 5m` created a detached background cron while the docs claimed "same-chat".** Reconciled: the loop **is** a background scheduled job by design now. `trade-loop` arms one `CronCreate` job (cadence → cron expression); each fire runs one `trade-cycle` tick in its own headless session.
- **Orchestrator model.** The chat where you start the loop is a **control panel** — arm / `status` / modify / `close` — and does **not** run trading ticks itself. The heavy per-tick fan-out runs in the background, so the main session's context stays lean (the original context-pressure goal).
- **Headless entry safety.** A background tick has no human to confirm, so without `execute approved trades automatically` it now **skips** new entries (monitor + de-risk only) instead of hanging on a GO/NO it can never receive.
- **Stop semantics updated for a background job.** Closing the chat no longer stops trading — `close` (stop + flatten) or a plain "stop" both **delete the cron job**; `close` also flattens. A tripped circuit breaker deletes the job and requires manual re-arm.
- New `status` control: shows the running job + recent per-asset results from the log (read-only).

## 0.10.0 — Looping trade cycle with subagent fan-out

`/hta-trade-cycle <assets>` now starts a **persistent same-chat loop** instead of running a single iteration, and each iteration fans its per-asset analysis out to **parallel leaf subagents** (one per crypto × strategy).

- **New `trade-loop` skill** owns the loop: run one `trade-cycle` tick → schedule the next wake after the cadence interval (via `ScheduleWakeup`, re-firing the command to carry state) → repeat. Per-tick state is rebuilt from args + the log + live account state, so the main context does not grow unbounded across ticks.
- **`trade-cycle` refactored** from serial per-asset analysis to a parallel (crypto × strategy) leaf fan-out per `skills/trade-loop/leaf-contract.md`. Each leaf fetches its own market context in isolation and returns only a compact verdict; the main agent aggregates by **conservative consensus** (open only if strategies agree on direction; conflict → HOLD), validates, executes, and logs.
- **`hta-trade-cycle close`** stops the loop and flattens all positions regardless of PnL (bounded retry, honest reporting — never claims "flat" unconfirmed). A normal stop leaves positions open under their exchange-side SL/TP brackets.
- **LIVE = confirm-on-new-entry**: risk-reducing actions auto-run; new entries pause for GO/NO unless `execute approved trades automatically` is supplied. Per-tick `trading_mode()` overrides any session flag. The **circuit-breaker hard stop** is preserved as an explicit per-tick guard (no new trades, no next wake when active).
- **Cadence vs analysis timeframe** decoupled: `--interval` is the run cadence; each strategy is analyzed on a timeframe it declares valid. Default strategy set is a single coherent strategy (not all) to avoid a consensus deadlock.
  - **Breaking (behavior):** `--interval` previously set the analysis candle timeframe fed to `get_market_context`; it now sets the loop **cadence**. Analysis timeframe now comes from each strategy's `timeframes` frontmatter. Existing one-shot invocations that relied on `--interval` to pick the analysis timeframe will analyze on the strategy's declared timeframe instead.
- **Loop driver:** repetition runs on the `/loop` skill (same-chat, self-paced) — `/hta-trade-cycle` executes one tick per firing. No background/cron scheduler (out of scope).
- **New append-only log**: `log.json` (an unused template) replaced by **git-ignored `log.jsonl`** (JSON Lines, one event per crypto per tick) documented in `LOG-SCHEMA.md`. It holds financial data and is local-only — never committed.

## 0.9.2 — One slash surface: hide skills from the menu

The 7 skills were surfacing as their own slash entries (e.g. bare `/setup`, `/settings`, `/strategy`) **alongside** the `hta-*` commands — duplicate, inconsistently-named entries, since each `hta-*` command is a thin wrapper that runs its skill.

- Add `user-invocable: false` to all 7 skills (`setup`, `settings`, `strategy`, `market-analysis`, `trade-cycle`, `portfolio-review`, `risk-audit`). They no longer appear in the `/` menu.
- The slash menu now shows only the 9 `/hyperliquid-trading-agent:hta-*` commands — one consistent surface.
- Skills still run: the commands invoke them, Claude still auto-triggers them by description, and scheduled tasks still work (`user-invocable: false` only hides the menu entry; unlike `disable-model-invocation` it does not block model/scheduled invocation).

## 0.9.1 — Fix stale go-live instructions

- **`commands/hta-trading-mode.md`** told users to flip to LIVE by setting `LIVE_TRADING=true` in the MCP env. That's wrong for the current model — `live_trading` is a per-workspace persisted setting. Corrected to `/hta-settings go-live` (`update_settings`), and clarified that `LIVE_TRADING` env is only an emergency kill-switch override.
- `skills/settings/SKILL.md` description: `LIVE_TRADING mode` → `live_trading mode` to match the setting key.

## 0.9.0 — Consistent `hta-` slash-command names

All slash commands are renamed with an `hta-` prefix so they share one namespace under the plugin: `/hyperliquid-trading-agent:hta-<name>`.

- `setup → hta-setup`, `settings → hta-settings`, `analyze → hta-analyze`, `trade-cycle → hta-trade-cycle`, `positions → hta-positions`, `risk-audit → hta-risk-audit`, `strategy → hta-strategy`, `cancel → hta-cancel`, `trading-mode → hta-trading-mode`.
- **Breaking (muscle memory):** the old bare names (`/setup`, etc.) no longer exist — use the `hta-` forms. Skill names and MCP tool names are unchanged.
- Docs, skills, and strategy README updated to the new command names.

## 0.8.2 — Pin server v3.0.1 (SDK spot-meta crash fix)

- Bump the spawned server pin to `hyperliquid-trading-mcp@v3.0.1`, which fixes an `IndexError: list index out of range` that crashed client init (every wallet-dependent tool) against current Hyperliquid mainnet spot meta. No plugin behavior change beyond the pin.

## 0.8.1 — Fix stale skill/command references

Cleanup that 0.8.0 missed — two files still described the old Docker/HTTP model:

- **`commands/setup.md`** referenced the removed `link_env_file` MCP tool. Rewritten: the server reads the workspace `.env` (`CLAUDE_PROJECT_DIR`) and the plugin auto-spawns it via `uvx` — no env-linking tool. Keys go in the `.env` on disk, never pasted into chat.
- **`skills/settings/SKILL.md`** said settings live in a "Docker named volume" that "survives container restarts". Corrected to the per-workspace `CLAUDE_PROJECT_DIR/.hl-mcp/settings.json`.

No behavior change in the server; tool surface unchanged.

## 0.8.0 — Local stdio via uvx, per-workspace config

Drops the hosted-server model entirely. The plugin now **auto-spawns the MCP server as a local stdio subprocess** instead of connecting to an HTTP endpoint.

- **`plugin.json`** server entry is now `{ "command": "uvx", "args": ["--from", "git+https://github.com/rsantamaria01/hyperliquid-trading-mcp@v3.0.0", "hyperliquid-trading-mcp"] }` — no `url`, `type`, or auth header. Claude launches the server on enable; `uvx` clones and builds it from git (no registry account).
- **No HTTP, no port, no bearer token.** The Cowork reverse-proxy / SSH-tunnel / OAuth-connector workarounds are gone — there's nothing to tunnel to.
- **Per-workspace config.** The server reads secrets from `CLAUDE_PROJECT_DIR/.env` and settings from `CLAUDE_PROJECT_DIR/.hl-mcp/settings.json`. `live_trading` is scoped to the workspace folder.
- **Setup skill + README rewritten:** install `uv` (+ `git`), create the workspace `.env` (two wallet vars), gitignore `.env` + `.hl-mcp/`, read the stderr LIVE/DRY-RUN banner. GUI PATH caveat documented; Claude Code CLI is the supported client (Cowork untested).
- Requires MCP server **v3.0.0** (stdio transport, installed from git at the tag).

## 0.7.0 — Connection config moved to the client

Fixes a broken assumption in 0.6.0: `${VAR}` expansion is **not** applied to plugin-bundled MCP configs (neither Cowork nor the CLI honor it for `plugin.json`), so the templated URL/header shipped as a literal string.

- **`plugin.json`** now ships a plain default `url: http://localhost:8000/mcp` and **no auth header** — the plugin carries no deployment URL or token. The server URL is interchangeable per client; nothing deployment-specific lives in the repo.
- **Per-client connection** documented:
  - Claude Code (CLI/Desktop): override in `~/.claude.json` (same-named server wins; static `Authorization` header supported).
  - Cowork: Add custom connector with your URL. The UI is OAuth-only, so a token-protected server needs the token supplied outside Cowork — a reverse proxy that injects `Authorization` (ideal behind an HTTPS domain), or an SSH tunnel with the server's token disabled.
- `HL_MCP_URL` / `HL_MCP_TOKEN` env vars removed (they never worked for plugin-bundled servers).

## 0.6.0 — Streamable HTTP + bearer-token auth

- **Transport is now Streamable HTTP** at `/mcp` (`"type": "http"`); the legacy SSE endpoint (`/sse`) is gone. Matches MCP server's HTTP-only rewrite.
- **Configurable, authenticated connection.** `plugin.json` reads two shell env vars: `HL_MCP_URL` (defaults to `http://localhost:8000/mcp`; set to `http://<host-ip>:8000/mcp` for a remote server) and `HL_MCP_TOKEN` (sent as `Authorization: Bearer …`, must match the server's `MCP_AUTH_TOKEN`).
- **Setup skill + README** updated: server `.env` now includes `MCP_AUTH_TOKEN`; client exports `HL_MCP_TOKEN` / `HL_MCP_URL`; 401 troubleshooting added.
- Requires MCP server with the Streamable-HTTP `/mcp` endpoint and optional `MCP_AUTH_TOKEN`.

## 0.5.0 — URL transport, persistent settings via MCP

- **Plugin connects via URL** (`http://localhost:8000/sse`). No more spawning the server process from `plugin.json`. The MCP server runs as a long-lived Docker container.
- **Plugin holds zero secrets and zero config.** Only the URL.
- **Server-side persistent settings** in a Docker named volume (`hyperliquid-mcp-data`) at `/data/settings.json`. `live_trading`, `network`, and all risk caps are stored here and editable via two new MCP tools: `get_settings` and `update_settings`.
- **New `/settings` slash command + skill** for viewing/changing runtime config (`go-live`, `set max_leverage=5`, etc.).
- **Setup skill rewritten** to walk the user through bootstrapping the Docker container (instead of managing a plugin-side .env file).
- Requires MCP server **v0.2.0** which adds the new tools and SSE transport.

## 0.4.0 — Repo split

- **The MCP server moved to its own repo:** [rsantamaria01/hyperliquid-trading-mcp](https://github.com/rsantamaria01/hyperliquid-trading-mcp). Forked from edkdev/hyperliquid-mcp with our risk-management layer on top. Ships with Dockerfile + docker-compose.yml for standalone use.
- This plugin now contains **only** the Claude-facing layer: skills, strategies, slash commands.
- `plugin.json` references the external MCP via `uvx --from git+...` (default) or `docker run` (alternative).
- No more `mcp_server/` folder, no more `bootstrap.py` — install path is much cleaner.

## 0.3.4

- **Atomic limit-with-brackets** — borrowed the pattern from [edkdev/hyperliquid-mcp](https://github.com/edkdev/hyperliquid-mcp): submit entry + SL + TP as one `bulk_orders([...])` call with default grouping. Reduce-only triggers can't fire before the entry fills, so we get the same effective protection as `grouping="normalTpsl"` without needing the kwarg (which doesn't exist in SDK 0.20.x). One HTTP request, one signature.

## 0.3.3

- Hotfix for v0.3.2: `bulk_orders` in the pinned SDK version (0.20.x) doesn't expose the `grouping` kwarg needed for atomic `normalTpsl` brackets. Switched limit orders to a 3-step sequential placement (entry, then reduce-only SL trigger, then reduce-only TP trigger). The SL and TP land within ~1 second of the entry — not perfectly atomic, but reliable across SDK versions and well below any meaningful price-movement window.

## 0.3.2

- Hotfix for v0.3.1: `place_limit_order` was passing `grouping` as a positional argument to the SDK's `bulk_orders`, which actually mapped to `builder`. Result was `"string indices must be integers, not 'str'"` at order time. Now passed as a kwarg, which is what the SDK expects.

## 0.3.1

- **Limit orders now ship with SL/TP brackets atomically.** `place_limit_order` accepts `sl_price` and `tp_price` and submits all three orders as one `normalTpsl` group via Hyperliquid's `bulk_orders`. The SL/TP triggers stay dormant until the limit fills, then activate as reduce-only. No window of unbracketed exposure between fill and bracket attachment.
- Updated `trade-cycle` skill to pass SL/TP into `place_limit_order` for limit-entry strategies.

## 0.3.0

- **Strategies system.** New `strategies/` folder with pluggable `.md` strategy definitions. Ship with four built-ins: `breakout-bb`, `trend-pullback`, `mean-reversion-rsi`, `range-fade`. Each defines setup, entry conditions, SL/TP rules, sizing, and "when NOT to use." Users can add their own by dropping new `.md` files in the folder.
- **`/strategy` slash command** + `strategy` skill — lists available strategies, shows full rules for one, helps draft new ones.
- **Limit-entry support in `/trade-cycle`**. Strategies declare `entry_type: market | limit | both` in frontmatter. The trade-cycle skill uses `place_limit_order` when the strategy says limit, including computing the limit price from indicators (e.g. "limit at EMA20"). The hard-coded risk manager still applies.
- **`/trade-cycle` now accepts `--strategy <name>`** to apply a strategy's rules instead of the default heuristics.

## 0.2.2

- Enforce `MAX_LEVERAGE` on the exchange before opening positions. The plugin now calls `update_leverage(MAX_LEVERAGE, asset)` before every entry so the actual position respects the configured cap. Previously `MAX_LEVERAGE` was only a notional/balance math check and Hyperliquid used the account default (often 20x on majors).
- Round SL/TP trigger prices to Hyperliquid's perp tick rule (max 5 significant figures, max `6 - szDecimals` decimal places). Fixes "Invalid TP/SL price. asset=N" rejections on assets like ETH.
- New tool `set_leverage` for manual per-asset overrides.

## 0.2.1

- Normalize action strings — `validate_trade`, `place_market_order`, `place_limit_order` now accept `buy`/`long`/`sell`/`short` in any case. Fixes a bug where `"long"` made the validator compute SL on the *short* side of entry (i.e. 5% above current for a long position), an immediate stop-out trap.

## 0.2.0

- Self-installing bootstrap. Plugin now ships with `mcp_server/bootstrap.py` which creates a local `.venv` on first run and installs deps. No more `uv` or manual `pip install`.
- Path-only setup. The `link_env_file` MCP tool accepts a filesystem path to your `.env` and symlinks it. Pasted secrets in chat are rejected — the conversation log can't see them.
- New `set_leverage`, `unlink_env_file`, `get_setup_status` tools.

## 0.1.0

- Initial release. MCP server with 18 tools exposing market data, account state, risk validation, and order execution. Skills for market analysis, trade cycle, portfolio review, risk audit. Dry-run by default.
