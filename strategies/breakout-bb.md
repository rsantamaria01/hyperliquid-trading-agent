---
name: breakout-bb
description: Volatility breakout — enter when price closes outside the Bollinger Band with rising ADX. Trend-continuation play.
timeframes: [15m, 1h]
direction: [long, short]
entry_type: market
---

# Bollinger Breakout

## Setup
Markets that have been compressing (BB narrowing) and then break out with conviction. We want the breakout candle to close *outside* the band — not just wick through — and we want trend strength to be increasing.

## Entry conditions

**For a long:**
- Last close > `bb_upper` (close, not high — wicks don't count)
- ADX > 25 and rising (compare against ADX 3 candles ago)
- Volume on the breakout candle > 1.5× recent average (check the recent_candles `volume` field)
- RSI14 between 55 and 75 — confirming momentum but not exhausted
- EMA20 > EMA50 — trend already aligned

**For a short:** mirror — close < `bb_lower`, RSI14 between 25 and 45, EMA20 < EMA50.

## Entry execution
**Market.** Breakouts move fast — chasing with a limit usually means missing the trade.

## Stop-loss
Below the previous swing low (for longs) or above the previous swing high (for shorts). Use the lowest low of the last 6 candles minus 0.25 × ATR14 buffer.

Sanity check: SL distance shouldn't exceed 1.5 × ATR14. If it does, the structure is too far away — skip the trade.

## Take-profit
2R minimum. Compute: `tp = entry + 2 × (entry − sl)` for longs.

If the move is exceptionally strong (ADX > 40), consider 3R.

## Exit conditions (manual)
- Close if price closes back inside the band on the analysis timeframe (failed breakout)
- Close if ADX falls below its value at entry by more than 5 points

## Position sizing
Use the configured `MAX_POSITION_PCT` — breakouts have decent edge so full allocation is appropriate.

## When NOT to use
- ADX < 20 (no trend yet — likely a fakeout)
- Inside a known range without confirmation of regime change
- After 3+ consecutive bars in the same direction outside the band (mean reversion risk)
- Within 15 minutes of major macro news (CPI, FOMC, etc.)
