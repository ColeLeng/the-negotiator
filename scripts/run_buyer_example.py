#!/usr/bin/env python
"""
One buyer's negotiation session log (owner: Ella) — the `_demo_spec` scenario.

    python scripts/run_buyer_example.py [--data data/market] [--brand "Jenny Yoo"]

Builds a single BuyerAgent from data/market/buyer.csv (the ivory / US 8 / <=$1800 target,
$2400 reservation, 30-day scenario used in tests/test_a2a_styles.py) and runs it against the
brand market, printing the BUYER's turn-by-turn decisions — opens, Boulware counters, and the
accept/walk call — plus the deal it ultimately picks. Separate from run_market.py so the buyer
side is inspectable in isolation.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))   # repo root (for `negotiator`)
sys.path.insert(0, str(_HERE))          # scripts dir (for `run_market`)

from run_market import run_market  # noqa: E402
from negotiator import buyer_value  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Run one buyer against the brand market (buyer's-eye view).")
    ap.add_argument("--data", default="data/market")
    ap.add_argument("--brand", default=None, help="focus on one vendor (substring match); default: all")
    args = ap.parse_args()

    spec, results = run_market(args.data)
    n = spec.negotiation
    print(f"\n=== BUYER SESSION — {spec.spec_id} ===")
    print(f"Target ${n.target_price:.0f} · reservation ${n.reservation_price:.0f} · deadline {n.deadline_days}d")
    print("Wants: " + "; ".join(
        f"{a.name}={a.value}({a.constraint}" + (f",w={a.weight}" if a.weight else "") + ")"
        for a in spec.attributes))
    print("Policy: open at target → Boulware counters → accept if within walk-away & beats BATNA, else walk.\n")

    shown = 0
    for b, s in results:
        if args.brand and args.brand.lower() not in b["option"].vendor.lower():
            continue
        shown += 1
        print(f"--- vs {b['option'].vendor} ({b['state'].style}) → {s.status.upper()} ---")
        for m in s.messages:
            if m.sender == "buyer":
                price = f"${m.price:.0f}" if m.price is not None else "  —  "
                print(f"    buyer {m.intent:<7} {price:>7}  · {m.rationale}")
        if s.status == "agreed" and s.current_price is not None:
            u = buyer_value.utility(s.current_price, spec, offer_attrs=b["option"].matched_attributes)
            print(f"    → agreed ${s.current_price:.0f}   (buyer utility {u:.2f})")
        print()

    agreed = [(b, s) for b, s in results if s.status == "agreed" and s.current_price is not None]
    if agreed:
        b, s = min(agreed, key=lambda bs: bs[1].current_price)
        print(f"BUYER PICKS: {b['option'].vendor} at ${s.current_price:.0f} — lowest of {len(agreed)} agreed offers.")
    else:
        print("BUYER PICKS: nothing cleared — all sessions ended in callback/decline.")
    if shown == 0:
        print(f"(no brand matched --brand {args.brand!r})")


if __name__ == "__main__":
    main()
