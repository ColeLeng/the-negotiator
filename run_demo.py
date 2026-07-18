"""
End-to-end MOCK demo — no API keys, no network.

    python run_demo.py

Runs intake → search → parallel negotiations → ranked recommendation, and prints a
genuinely MOVING price for each session. The movement is emergent: it comes from each
seller's private inventory-driven floor vs the buyer's Boulware concession curve, not a
script. Sellers with aging stock have a lower dynamic floor and concede further — exactly
the "real moving price" criterion.
"""
from __future__ import annotations

from negotiator import orchestrator
from negotiator.caller import search
from negotiator.contracts import Capacity, Inventory, SellerState
from negotiator.estimator import estimate


def _seller_profiles(ranked):
    """Distinct inventory economics per option so behaviour visibly differs."""
    # (stock_age_days, sku_units, at_capacity) — aging + plentiful → concedes hardest
    profiles = [(240, 18, False), (20, 3, False), (120, 9, True)]
    states = {}
    for opt, (age, units, at_cap) in zip(ranked.options, profiles):
        listed = opt.listed_price
        states[opt.option_id] = SellerState(
            vendor=opt.vendor,
            cost_floor=round(listed * 0.60, 2),
            list_price=listed,
            min_margin=round(listed * 0.18, 2),
            inventory=Inventory(sku_units=units, stock_age_days=age),
            capacity=Capacity(lead_time_days=21, at_capacity=at_cap),
        )
    return states


def main() -> None:
    spec = estimate("Ivory Pronovias wedding dress, US 8, ideally under $1800, hard cap $2400, within 30 days.")
    print(f"\n[Estimator] spec {spec.spec_id}: target ${spec.negotiation.target_price:.0f} · "
          f"reservation ${spec.negotiation.reservation_price:.0f}")

    ranked = search(spec)
    print(f"[Caller] {len(ranked.options)} ranked options:")
    for o in ranked.options:
        print(f"    {o.option_id}  {o.vendor:<20} list ${o.listed_price:>7.0f}  match {o.match_score:.2f}")

    states = _seller_profiles(ranked)
    result = orchestrator.run(ranked, spec, seller_states=states, top_n=3)

    print("\n[Negotiations] moving price per session:")
    for s in result["sessions"]:
        state = states[s.option_id]
        prices = [m.price for m in s.messages if m.price is not None]
        trail = " → ".join(f"${p:.0f}" for p in prices)
        print(f"\n  {s.option_id} ({state.vendor}) — stock_age {state.inventory.stock_age_days}d — {s.status.upper()}")
        print(f"    price: {trail}")
        for m in s.messages:
            price = f"${m.price:.0f}" if m.price is not None else "  —  "
            print(f"      {m.sender:<6} {m.intent:<8} {price:>7}  · {m.rationale}")

    rec = result["recommendation"]
    print("\n[Recommendation]")
    if rec:
        state = states[rec.option_id]
        saved = state.list_price - (rec.current_price or state.list_price)
        print(f"    Best deal: {state.vendor} at ${rec.current_price:.0f} "
              f"(list ${state.list_price:.0f}, saved ${saved:.0f}) — session {rec.session_id}")
    else:
        print("    No deal cleared all constraints; every session walked to its BATNA.")
    print()


if __name__ == "__main__":
    main()
