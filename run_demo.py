"""
End-to-end MOCK demo — no API keys, no network.

    python run_demo.py

Runs intake → call-list + search → parallel negotiations (3 styles) → itemized quotes
→ ranked recommendation. Price movement is emergent from each seller's private
inventory-driven floor vs the buyer's Boulware curve — not a script.
"""
from __future__ import annotations

from negotiator import orchestrator
from negotiator.caller import search
from negotiator.estimator import estimate
from negotiator.quote_capture import ending_label


def main() -> None:
    spec = estimate(
        "Ivory Pronovias wedding dress, US 8, ideally under $1800, hard cap $2400, within 30 days."
    )
    print(
        f"\n[Estimator] spec {spec.spec_id}: target ${spec.negotiation.target_price:.0f} · "
        f"reservation ${spec.negotiation.reservation_price:.0f}"
    )

    ranked = search(spec)
    prov = ranked.call_list_provenance
    print(f"[Caller] {len(ranked.options)} ranked options "
          f"(call list: {prov.provider if prov else '—'})")
    if prov and prov.note:
        print(f"    provenance: {prov.note}")
    for o in ranked.options[:5]:
        style = o.negotiation_style or "—"
        phone = o.phone or "—"
        print(
            f"    {o.option_id}  {o.vendor:<22} list ${o.listed_price:>7.0f}  "
            f"match {o.match_score:.2f}  style={style}  phone={phone}"
        )

    result = orchestrator.run(ranked, spec, top_n=3)
    states = result["seller_states"]

    print("\n[Negotiations] ≥3 styles · moving price · structured endings:")
    for s in result["sessions"]:
        state = states[s.option_id]
        prices = [m.price for m in s.messages if m.price is not None]
        trail = " → ".join(f"${p:.0f}" for p in prices) if prices else "(no phone price)"
        print(
            f"\n  {s.option_id} ({state.vendor}) — style={state.style} — "
            f"{s.status.upper()} — ending={ending_label(s.call_ending)}"
        )
        print(f"    price: {trail}")
        if s.itemized_quote:
            print(f"    itemized total ${s.itemized_quote.total:.0f}:")
            for li in s.itemized_quote.line_items:
                opt = " (optional)" if li.optional else ""
                print(f"      - {li.code:<14} ${li.amount:>7.0f}  {li.label}{opt}")
        for m in s.messages:
            price = f"${m.price:.0f}" if m.price is not None else "  —  "
            print(f"      {m.sender:<6} {m.intent:<8} {price:>7}  · {m.rationale}")

    rec = result["recommendation"]
    print("\n[Recommendation]")
    if rec:
        state = states[rec.option_id]
        saved = state.list_price - (rec.current_price or state.list_price)
        print(
            f"    Best deal: {state.vendor} at ${rec.current_price:.0f} "
            f"(list ${state.list_price:.0f}, saved ${saved:.0f}) — "
            f"style={state.style} — session {rec.session_id}"
        )
    else:
        print("    No deal cleared all constraints; sessions ended in callback/decline.")
    print()


if __name__ == "__main__":
    main()
