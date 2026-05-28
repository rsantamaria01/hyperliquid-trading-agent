# Changelog

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
