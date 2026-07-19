#!/usr/bin/env python
"""
Market harness (owner: Ella) — ONE buyer vs MANY brand Seller Agents.

    python scripts/run_market.py --data data/market [--out market_results.csv]

Loads a CSV market (buyer + brands + upsells + deals), spawns one SellerAgent per brand
(each injected with its own brand dict: SLA/value_score + upsell catalog + credit deals),
and runs each Buyer <-> Seller session over a shared Blackboard so the single buyer persona
gains real cross-brand BATNA leverage. Prints a per-brand comparison and writes a results CSV.

Mirrors the ~15-line orchestrator.run loop but injects brand data (no edit to the orchestrator).
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from negotiator import buyer_value, market_dataset  # noqa: E402
from negotiator.agents.buyer_agent import BuyerAgent  # noqa: E402
from negotiator.agents.seller_agent import SellerAgent  # noqa: E402
from negotiator.comms.blackboard import Blackboard  # noqa: E402
from negotiator.comms.channels import MockChannel  # noqa: E402
from negotiator.comms.loop import run_negotiation  # noqa: E402
from negotiator.contracts import NegotiationSession  # noqa: E402
from negotiator.quote_capture import capture_quote, ending_label  # noqa: E402


def run_market(data_dir: str, max_rounds: int = 6):
    """Run one buyer against every brand. Returns (spec, [(brand, session), ...])."""
    spec, brands = market_dataset.load_market(data_dir)
    blackboard = Blackboard()
    results = []
    for i, b in enumerate(brands):
        opt, state, brand = b["option"], b["state"], b["brand"]
        # BATNA seed = utility of the next brand's listed option (a real fallback).
        if i + 1 < len(brands):
            nxt = brands[i + 1]["option"]
            batna = buyer_value.utility(nxt.listed_price, spec, offer_attrs=nxt.matched_attributes)
        else:
            batna = 0.0
        session = NegotiationSession(
            session_id=f"neg_{opt.option_id}", option_id=opt.option_id, spec_id=spec.spec_id,
            batna_utility=batna, current_price=opt.listed_price, negotiation_style=opt.negotiation_style,
        )
        buyer = BuyerAgent(spec, session, max_rounds=max_rounds)
        seller = SellerAgent(state, max_rounds=max_rounds, brand=brand)  # <- brand injected
        run_negotiation(buyer, MockChannel(seller), blackboard, session)
        capture_quote(session, state)
        results.append((b, session))
    return spec, results


def _deal_terms(session: NegotiationSession) -> dict:
    """The credit commitment attached to the final deal — whether it rode on the seller's
    accept, or on the concede the buyer accepted. Last seller message carrying a credit wins."""
    for m in reversed(session.messages):
        if m.sender == "seller" and (m.terms_delta or {}).get("credit_offer"):
            return m.terms_delta
    return {}


def _kept_upsells(session: NegotiationSession) -> str:
    if not session.itemized_quote:
        return ""
    return ";".join(li.label for li in session.itemized_quote.line_items if li.optional)


def _row(brand: dict, session: NegotiationSession) -> dict:
    opt, state = brand["option"], brand["state"]
    td = _deal_terms(session)
    agreed = session.status == "agreed" and session.current_price is not None
    final = session.current_price if agreed else None
    return {
        "vendor": opt.vendor,
        "product": brand["row"].get("product_name", ""),
        "style": state.style,
        "list_price": f"{state.list_price:.0f}",
        "final_price": f"{final:.0f}" if final is not None else "",
        "saved": f"{state.list_price - final:.0f}" if final is not None else "",
        "ending": session.call_ending or "",
        "upsells_kept": _kept_upsells(session),
        "credit_offer": td.get("credit_offer", ""),
        "credit_type": td.get("credit_type", ""),
        "credit_conditions": td.get("credit_conditions", ""),
        "commitment_id": td.get("commitment_id", ""),
    }


_FIELDS = ["vendor", "product", "style", "list_price", "final_price", "saved",
           "ending", "upsells_kept", "credit_offer", "credit_type", "credit_conditions", "commitment_id"]


def print_report(spec, results) -> None:
    print(f"\n[Buyer] {spec.spec_id}: target ${spec.negotiation.target_price:.0f} · "
          f"reservation ${spec.negotiation.reservation_price:.0f} · "
          f"wants {', '.join(a.name+'='+(a.value or '?') for a in spec.attributes)}")
    print(f"\n[Market] one buyer vs {len(results)} brand agents (shared blackboard = cross-brand BATNA):")
    for brand, s in results:
        state = brand["state"]
        prices = [m.price for m in s.messages if m.price is not None]
        trail = " → ".join(f"${p:.0f}" for p in prices) if prices else "(no phone price)"
        print(f"\n  {brand['option'].vendor} — {brand['row'].get('product_name','')} — "
              f"style={state.style} — {s.status.upper()} — ending={ending_label(s.call_ending)}")
        print(f"    price: {trail}")
        if s.itemized_quote:
            print(f"    itemized total ${s.itemized_quote.total:.0f}: "
                  + ", ".join(f"{li.code}=${li.amount:.0f}" for li in s.itemized_quote.line_items))
        td = _deal_terms(s)
        if td.get("credit_offer"):
            print(f"    deal: ${td['credit_offer']} {td.get('credit_type','')} for "
                  f"{td.get('credit_conditions','')} (non-refundable) [{td.get('commitment_id','')}]")

    agreed = [(b, s) for b, s in results if s.status == "agreed" and s.current_price is not None]
    print("\n[Recommendation]")
    if agreed:
        b, s = min(agreed, key=lambda bs: bs[1].current_price)
        st = b["state"]
        print(f"    Best deal: {b['option'].vendor} ({b['row'].get('product_name','')}) at "
              f"${s.current_price:.0f} (list ${st.list_price:.0f}, saved ${st.list_price - s.current_price:.0f}) "
              f"— style={st.style}")
    else:
        print("    No deal cleared; sessions ended in callback/decline.")


def write_csv(results, out_path: str) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_FIELDS)
        w.writeheader()
        for brand, s in results:
            w.writerow(_row(brand, s))


def main() -> None:
    ap = argparse.ArgumentParser(description="One buyer vs many brand Seller Agents (CSV-driven).")
    ap.add_argument("--data", default="data/market", help="dir with buyer/brands/upsells/deals CSVs")
    ap.add_argument("--out", default="market_results.csv", help="results CSV output path")
    ap.add_argument("--max-rounds", type=int, default=6)
    args = ap.parse_args()

    spec, results = run_market(args.data, max_rounds=args.max_rounds)
    print_report(spec, results)
    write_csv(results, args.out)
    print(f"\n    Wrote {len(results)} rows → {args.out}\n")


if __name__ == "__main__":
    main()
