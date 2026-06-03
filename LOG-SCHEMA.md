# Trade-loop event log schema (`log.jsonl`)

The looping trade cycle (`trade-loop` skill, driving `trade-cycle`) appends to **`log.jsonl` in the workspace directory** — the folder the user is running the chat in (the current working directory / `CLAUDE_PROJECT_DIR`), next to their `.env` and `.hl-mcp/`. **Not** in the plugin's install/cache directory. This keeps the log where the user can find it and scopes it per workspace (like settings).

**Format:** [JSON Lines](https://jsonlines.org/) — one JSON object per line, append-only. One line is written **per crypto, per iteration**. The file is created on first append; nothing reads it at runtime (it is a record for later analysis).

**Local-only.** The log holds financial data (order sizes, SL/TP prices, PnL). Add `log.jsonl` to the workspace `.gitignore` (`/hta-setup` does this) — never commit or share it. There is no seed file.

> Field-level names for the per-strategy results and the order block are the **single source of truth in `skills/trade-loop/leaf-contract.md`** (the leaf verdict contract), which pins them. This doc owns the top-level event structure; `leaf-contract.md` owns the inner field names. The verdict→log mapping is: verdict `strategy`→`strategies[].name`, `proposed_sl`/`proposed_tp`→`order.sl`/`order.tp`; `passed`/`score`/`signal` carry through unchanged.

## Top-level event structure

Each line is one object with these top-level keys:

| Key | Type | Meaning |
|---|---|---|
| `ts` | string (ISO 8601) | When the event was written. |
| `session_id` | string | The chat session that ran the loop. Distinguishes concurrent loops sharing the file. |
| `iteration_id` | integer | Monotonic per session; which loop tick produced this event. |
| `crypto` | string | Asset shortname, e.g. `BTC`. One line per crypto per iteration. |
| `mode` | string | `LIVE` or `DRY-RUN` — the mode this iteration actually ran in (per-tick `trading_mode()`). |
| `strategies` | array | Per-strategy results for this crypto this iteration (see below). |
| `decision` | string enum | One of `open`, `close`, `dca`, `derisk`, `hold` — the aggregated decision. |
| `order` | object \| null | The resulting order, or `null` when no order was placed (e.g. `hold`). |
| `position` | object \| null | Position snapshot after the decision, or `null` if no position. |
| `decision_audit` | object | **Reserved for v2.** Empty `{}` in v1. The v2 per-crypto decision/audit subagents add their fields here so existing v1 lines never need reshaping. |

### `strategies[]` (directional — names finalized in `leaf-contract.md`)

Flat array, one entry per strategy evaluated for this crypto:

| Field | Type | Meaning |
|---|---|---|
| `name` | string | Strategy slug, e.g. `trend-pullback`. |
| `passed` | boolean | Did the crypto pass this strategy's parameter checks. |
| `score` | number | Conviction score (scale pinned in `leaf-contract.md`). |
| `signal` | string enum | `long`, `short`, or `none`. |

### `order` (directional — names finalized in `leaf-contract.md`)

`null` when no order placed; otherwise:

| Field | Type | Meaning |
|---|---|---|
| `side` | string | `buy` / `sell`. |
| `allocation_usd` | number | Notional allocated. |
| `entry` | number | Entry / limit price. |
| `sl` | number | Stop-loss trigger. |
| `tp` | number | Take-profit trigger. |
| `oid` | string \| number | Exchange order id (or simulated id in DRY-RUN). |

### `position`

`null` when no open position; otherwise:

| Field | Type | Meaning |
|---|---|---|
| `pnl` | number | Unrealized PnL. |
| `return_pct` | number | Unrealized return %. |

## Example line

```json
{"ts":"2026-06-03T14:05:00Z","session_id":"abc123","iteration_id":7,"crypto":"BTC","mode":"DRY-RUN","strategies":[{"name":"trend-pullback","passed":true,"score":0.78,"signal":"long"}],"decision":"open","order":{"side":"buy","allocation_usd":50,"entry":104250,"sl":102100,"tp":108500,"oid":"sim-7-BTC"},"position":{"pnl":0,"return_pct":0},"decision_audit":{}}
```

Example of a `hold` with no order and an existing position:

```json
{"ts":"2026-06-03T14:10:00Z","session_id":"abc123","iteration_id":8,"crypto":"ETH","mode":"DRY-RUN","strategies":[{"name":"trend-pullback","passed":false,"score":0.31,"signal":"none"}],"decision":"hold","order":null,"position":{"pnl":-2.4,"return_pct":-1.1},"decision_audit":{}}
```

## v2 forward-compatibility

When decision/audit move into dedicated subagents (origin steps 4.2–4.4), their output goes into `decision_audit`. Readers of v1 lines see `decision_audit: {}` and tolerate it; no v1 line is rewritten. Adding new top-level keys in v2 is allowed (readers ignore unknown keys); renaming or removing the keys above is not.
