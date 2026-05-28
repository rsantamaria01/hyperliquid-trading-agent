---
name: range-fade
description: Fade Bollinger Band extremes inside a confirmed range — buy lower band, sell upper band, only when trend is absent.
timeframes: [5m, 15m, 1h]
direction: [long, short]
entry_type: limit
---

# Range Fade (Bollinger Edges)

## Setup
Range conditions only. We identify the range by ADX < 20 and a flat EMA structure, then fade touches of the band edges. The trade is "this band will hold."

## Entry conditions

**For a long (fade lower band):**
- ADX < 20 — confirms range
- `|ema20 − ema50| < 0.3 × atr14` — EMAs are flat and close together
- Price within 0.25 × ATR of `bb_lower` (or has just touched it)
- RSI14 between 25 and 40 — not deeply oversold (those tend to break the range)
- The previous 10 candles have respected both bands at least once each (true range behavior)

**For a short (fade upper band):** mirror — price near `bb_upper`, RSI14 between 60 and 75.

## Entry execution
**Limit only.** Put the limit AT the band, not chasing into it. If price overshoots and we don't get filled at the band, we don't take the trade — that's a sign the range is breaking.

## Stop-loss
Just outside the band, by 0.5 × ATR14.
- Long SL: `bb_lower − 0.5 × atr14`
- Short SL: `bb_upper + 0.5 × atr14`

If price closes outside the band, the range is broken and we want to be out anyway.

## Take-profit
The middle Bollinger Band (`bb_middle`). That's the typical reversion target.

Alternative: opposite band, but only take half size to that target — full mean reversion to the opposite extreme is rare in a true range.

## Exit conditions (manual)
- Close immediately if a candle closes outside the entry band — range is breaking
- Close if ADX rises above 25 — the range is converting into a trend
- Close on contact with `bb_middle` (the safe TP)
- Close if a candle closes on the opposite side of EMA20 from your entry — momentum has shifted

## Position sizing
**60% of default `MAX_POSITION_PCT`.** Range plays have decent edge but the "range broke" case can be a sharp loss. Smaller size keeps the asymmetry manageable.

## When NOT to use
- ADX > 20 (no range, there's a trend)
- After a strong directional candle (>1.5 × ATR body) — wait for the range to re-establish
- When the band width has been expanding for 5+ candles (volatility regime change)
- BTC dominance or correlations are extreme (cross-market trend day, individual ranges break)
