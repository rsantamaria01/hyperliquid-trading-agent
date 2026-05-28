# Changelog

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
