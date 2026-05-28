---
name: strategy
description: List, inspect, or select a trading strategy from the strategies/ folder. Strategies define entry/exit/stop/take-profit rules that /trade-cycle follows. Use when the user says "what strategies are available", "show me the breakout strategy", "use the trend-pullback strategy", or runs /strategy.
---

# Strategy selector

Each strategy lives in `strategies/*.md` in the plugin folder. Strategies tell `/trade-cycle` how to act instead of using the generic default heuristics.

## Procedure

### If no argument: list strategies

1. List the files in the plugin's `strategies/` directory (use Glob or Read).
2. For each file, parse the YAML frontmatter to extract `name`, `description`, `timeframes`, `direction`, `entry_type`.
3. Present as a compact table:

```
| Name | Style | Timeframes | Direction | Entry |
|---|---|---|---|---|
| breakout-bb | Volatility breakout out of Bollinger Bands | 15m, 1h | long, short | market |
| trend-pullback | Pullback to EMA20 in strong trend | 1h, 4h | long, short | limit |
| mean-reversion-rsi | Fade RSI extremes | 5m, 15m | long, short | both |
| range-fade | Fade Bollinger extremes in a range | 5m, 15m, 1h | long, short | limit |
```

4. End by suggesting one of:
   - "Tell me which one to use, or say `details <name>` for the full rules."
   - "Use a strategy in trade-cycle: `/trade-cycle BTC ETH --strategy <name>`."

### If argument looks like a strategy name: show details

Read the file `strategies/<name>.md`. Print the full content (or a clean summary if the user asks for a summary). Highlight: setup, entry conditions, SL/TP rules, sizing override, when NOT to use.

### If argument is "create" or "add"

Show the user the template structure from `strategies/README.md` and offer to draft a new strategy file based on a verbal description. Save it to `strategies/<their-name>.md` only after they confirm.

## Important

- Strategy files are **prose for Claude**, not executable code. When `/trade-cycle` runs with a strategy, you read the strategy file fresh, hold its rules in working memory, and apply them literally.
- Never modify a strategy file without explicit user permission.
- If a strategy says "limit at EMA20" and you don't have EMA20 in the market context, compute it from the candles before placing.
- Override rules from a strategy file ALWAYS lose to the hard-coded risk manager (position cap, leverage cap, mandatory SL). A strategy can say "20% position size" but the risk manager will still cap at `MAX_POSITION_PCT`.
