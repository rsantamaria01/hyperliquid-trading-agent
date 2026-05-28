---
name: trend-pullback
description: Buy the dip in an uptrend, sell the rip in a downtrend — enter on a pullback to EMA20 when the larger trend is intact.
timeframes: [1h, 4h]
direction: [long, short]
entry_type: limit
---

# Trend Pullback (EMA20)

## Setup
A clean trend is established. We're not chasing — we wait for price to come back to a dynamic support (EMA20) and enter there with a tight stop.

## Entry conditions

**For a long:**
- EMA20 > EMA50 > EMA200-equivalent (use EMA50 as proxy if EMA200 not computed)
- ADX > 20 — trend has strength
- Last close > EMA50 (still in trend)
- Current price within 0.5 × ATR14 of EMA20 (the pullback is reaching the entry zone — or place a limit at EMA20)
- RSI14 dipped to 40–50 range on the pullback (cooled off, ready to resume)
- MACD histogram still positive OR turning positive after a small dip

**For a short:** mirror — EMA20 < EMA50, RSI14 between 50 and 60 on the bounce, MACD histogram negative or turning negative.

## Entry execution
**Limit order at EMA20.** Place the order and let price come to you.

- Long entry price = `ema20`
- Short entry price = `ema20`

If price runs away (closes 1 ATR away from EMA20 without a pullback), cancel and wait for the next pullback opportunity. Don't chase.

## Stop-loss
Below the EMA50 minus a small buffer (longs), above EMA50 plus buffer (shorts).
- Long SL ≈ `ema50 - 0.25 × atr14`
- Short SL ≈ `ema50 + 0.25 × atr14`

## Take-profit
The previous swing high (for longs) or swing low (for shorts) — look at the last 20 candles.

Alternative: 3R fixed target.

## Exit conditions (manual)
- Close if a candle closes back below EMA50 (for longs) — trend may be ending
- Close if EMA20 crosses EMA50 against the trade
- Close if RSI14 reaches 75+ before TP — overextended, take what you have

## Position sizing
Standard `MAX_POSITION_PCT`. Pullbacks are higher-probability than breakouts so the default cap is fine.

## When NOT to use
- ADX < 20 (no trend — pullback could just be range structure)
- Inside the first 1–2 candles after a major breakout (let the breakout retest properly)
- When EMA20 and EMA50 are within 0.25 × ATR of each other (trend isn't well-defined)
