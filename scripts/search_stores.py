#!/usr/bin/env python3
"""
search_stores.py — prove the Caller searches Ella's 12-store inventory (not empty match).

Runs the pipeline end to end on mocks:
    buyer text  ->  Estimator (ProductSpec)  ->  Caller.search over data/market stores
                ->  ranked, matched options

Usage:
    python scripts/search_stores.py
    python scripts/search_stores.py "Ivory A-line Pronovias, US 8, wedding in 120 days, ~$1500 cap $2200"

No API keys needed. Add stores by editing data/market/wedding_stores.csv.
"""
from __future__ import annotations

import sys

from negotiator import store_catalog
from negotiator.caller import search
from negotiator.estimator import estimate

_DEMO_TEXT = (
    "Ivory A-line wedding dress, US 8, wedding in about 120 days, "
    "hoping around $1500, hard cap $2200; designer look matters most."
)


def main() -> int:
    text = sys.argv[1] if len(sys.argv) > 1 else _DEMO_TEXT
    stores = store_catalog.load_store_listings("wedding-dress")
    print(f"Inventory: {len(stores)} stores loaded from data/market/wedding_stores.csv\n")

    spec = estimate(text, vertical="wedding-dress")
    ranked = search(spec)

    print(f'Buyer wants: "{text}"')
    print(f"spec_id={spec.spec_id}  target=${spec.negotiation.target_price:.0f}  "
          f"cap=${spec.negotiation.reservation_price:.0f}\n")
    print(f"{len(ranked.options)} matching options (ranked):")
    for o in ranked.options:
        unmet = f"  (unmet: {', '.join(o.unmet_soft)})" if o.unmet_soft else ""
        print(f"  {o.match_score:>5.2f}  ${o.listed_price:>6.0f}  {o.vendor}{unmet}")

    if not ranked.options:
        print("  (no matches — check the spec's hard constraints vs inventory)")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
