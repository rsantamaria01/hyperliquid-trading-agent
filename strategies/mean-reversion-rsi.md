---
name: mean-reversion-rsi
description: Fade extreme RSI prints back toward the mean — counter-trend, fast timeframes, tight stops.
timeframes: [5m, 15m]
direction: [long, short]
entry_type: both
---

# RSI Mean Reversion

## Setup
On fast timeframes inside a range or weak trend, RSI extremes tend to revert. We buy oversold dips and sell overbought rips, expecting a bounce back to the middle Bollinger Band (the 20-SMA).

## Entry conditions

**For a long (oversold bounce):**
- RSI7 < 20 OR (RSI14 < 30 AND RSI7 < 25)
- ADX < 25 — we want range/weak trend, not strong trend (don't catch falling knives in a downtrend)
- Price within or below `bb_lower`
- Most recent candle shows reversal: close > open (a bullish candle) OR a long lower wick (low more than 1 × ATR below close)
- EMA20 and EMA50 not aggressively diverging (within 0.5 × ATR of each other)

**For a short (overbought fade):** mirror — RSI7 > 80, price near or above `bb_upper`, ADX < 25.

## Entry execution
**Both supported:**
- **Market** if the reversal candle just closed and you want to enter immediately.
- **Limit** at the lower band (`bb_lower`) for longs / upper band (`bb_upper`) for shorts if price is still approaching the extreme.

Default: limit at the band — only use market if the candle has already shown clear rejection.

## Stop-loss
- Long SL: 0.5 × ATR14 below the entry candle's low
- Short SL: 0.5 × ATR14 above the entry candle's high

Mean reversion stops should be **tight**. If wrong, get out fast.

## Take-profit
The middle Bollinger Band (`bb_middle`, which is the 20-SMA). That's the "mean" we're reverting to.

Don't target the opposite band — it rarely runs all the way through.

## Exit conditions (manual)
- Close immediately if a candle closes further beyond the entry band (the "extreme" became more extreme — your thesis is broken)
- Close if RSI hasn't recovered above 30 (longs) / below 70 (shorts) within 3 candles after entry — momentum isn't bouncing
- Close on contact with `bb_middle` regardless of how it looks

## Position sizing
**Half the default `MAX_POSITION_PCT`.** Mean reversion has lower hit rate than trend strategies, and the asymmetric "I'm wrong" case (catching a real breakdown) can be ugly.

## When NOT to use
- ADX > 25 — there's a real trend; don't fight it
- BTC funding rate > 0.05% or < −0.05% — leverage is unbalanced, the extreme might extend
- During the first hour after a major news event
- If RSI has been in the extreme zone for more than 3 consecutive candles — momentum is the trade now, not reversion
