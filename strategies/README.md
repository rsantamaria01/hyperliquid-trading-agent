# Strategies

Each `.md` file in this folder defines a trading strategy that `/hta-trade-cycle` can use.

## Selecting one

```
/hta-strategy                          # list available strategies
/hta-strategy breakout-bb              # show full rules for a strategy
/hta-trade-cycle BTC ETH --strategy breakout-bb --interval 1h
```

Without `--strategy`, `/hta-trade-cycle` runs a single curated default strategy (`trend-pullback`). Pass `--strategy a,b` to run several — mixing trend and counter-trend strategies often aggregates to HOLD by design (conservative consensus).

## Adding your own

Create a new `.md` file in this folder with this structure:

```markdown
---
name: my-strategy
description: One-line summary used when listing strategies
timeframes: [5m, 15m, 1h]      # which candle intervals this works on
direction: [long, short]        # or just [long] or just [short]
entry_type: market | limit | both
---

# My Strategy

## Setup
What kind of market regime / conditions this strategy is designed for.

## Entry conditions
The rules that must be true to take a trade. Be specific — Claude will follow these literally.

- Condition 1 (e.g. "EMA20 > EMA50 on the analysis timeframe")
- Condition 2 (e.g. "RSI14 between 40 and 60 — we want pullbacks, not extremes")
- ...

## Entry execution
How to place the entry:
- **Market** if the signal is happening right now and we want fill certainty.
- **Limit** if we want a better price — specify where (e.g. "limit at EMA20 ± 0.25 × ATR").

## Stop-loss
Where the stop goes. Be specific — Claude will compute the price from candles.
- e.g. "Below the most recent swing low minus 0.5 × ATR14"
- e.g. "2 × ATR14 from entry"

## Take-profit
Where TP goes.
- e.g. "At 2× the SL distance from entry (2R)"
- e.g. "At the upper Bollinger band"

## Exit conditions (manual)
Conditions that should trigger closing even before SL/TP. Optional.
- e.g. "Close if MACD crosses bearish before TP hits"
- e.g. "Close at end of session (UTC 20:00)"

## Position sizing
Optional override to the default MAX_POSITION_PCT.
- e.g. "Use 5% of equity per position regardless of MAX_POSITION_PCT"

## When NOT to use
Market conditions where this strategy should be skipped.
- e.g. "ADX < 20 — no trend"
- e.g. "Funding rate above 0.03% — over-extended"
```

## Built-in strategies

| File | Style | Direction | Timeframes |
|---|---|---|---|
| `breakout-bb.md` | Volatility breakout out of Bollinger Bands | long, short | 15m, 1h |
| `trend-pullback.md` | Pullback to EMA20 in strong trend | long, short | 1h, 4h |
| `mean-reversion-rsi.md` | RSI extreme reversion | long, short | 5m, 15m |
| `range-fade.md` | Fade Bollinger extremes in a range | long, short | 5m, 15m, 1h |
