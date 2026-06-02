---
description: Cancel an order by ID, or cancel all orders for an asset
argument-hint: <asset> [oid] | all <asset>
---

Parse $ARGUMENTS:

- `<asset> <oid>` → call `cancel_order(asset, oid)` for a single order
- `all <asset>` or just `<asset>` → call `cancel_all_orders(asset)` to wipe every resting order on that asset (entries + SL + TP triggers)
- No argument → ask the user. First call `get_open_orders()` and show what's resting; let them pick.

Print the cancelled count or order ID. Confirm DRY-RUN vs LIVE in the response.
