"""
Scenario 2 demo — the buyer's quote-gathering agent process (no keys, no network).

    python run_scenario2.py

Takes the buyer's requirements (a JSON ProductSpec), runs the buyer inquiry agent
against the 12 seller agents — each with a distinct disclosure persona — builds the
verified evidence pool, prunes the obviously-bad quotes, and shortlists the top 3–5
vendors for Scenario 3 (negotiation). Prints every inquiry turn and pruning decision.
"""
from __future__ import annotations

import json
from pathlib import Path

from negotiator.contracts import ProductSpec
from negotiator.inquiry import gather_quotes, shortlist
from negotiator.seller_market import load_market, spec_from_csv

_SPEC_JSON = Path(__file__).parent / "fixtures" / "wedding_market_spec.json"

_PERSONA_TAG = {
    "transparent": "itemizes up front",
    "guarded": "base only until pressed",
    "stonewaller": "no prices by phone",
    "upseller": "inflates a bundle",
    "lowball_teaser": "dangles a fake-low base",
}


def _load_spec() -> ProductSpec:
    if _SPEC_JSON.exists():
        return ProductSpec.model_validate(json.loads(_SPEC_JSON.read_text()))
    return spec_from_csv()


def main() -> None:
    spec = _load_spec()
    print(f"\n[Requirements] {spec.spec_id}: target ${spec.negotiation.target_price:,.0f} · "
          f"reservation ${spec.negotiation.reservation_price:,.0f} · "
          f"{spec.negotiation.must_have_summary or ''}")

    sellers = load_market()
    print(f"\n[Market] contacting {len(sellers)} seller agents:")
    for s in sellers:
        print(f"    {s.vendor:<22} {s.persona:<15} — {_PERSONA_TAG.get(s.persona, '')}")

    pool = gather_quotes(spec, sellers)

    print("\n[Evidence pool] verified & itemized quotes the buyer trusts:")
    print(f"    {'vendor':<22} {'persona':<15} {'status':<11} {'all-in':>8}  {'util':>5}  flags")
    for q in pool.quotes:
        allin = f"${q.comparable_total:,.0f}" if q.comparable_total is not None else "—"
        flags = ", ".join(q.red_flags or q.verification_flags) or "-"
        print(f"    {q.vendor:<22} {q.persona:<15} {q.status:<11} {allin:>8}  {q.utility:>5.2f}  {flags}")

    summ = pool.summary()
    print(f"\n    → {summ['contacted']} contacted · {summ['firm_quotes']} firm quotes · "
          f"{summ['verified']} verified · median all-in ${summ['median_comparable'] or 0:,.0f}")

    ranked = shortlist(pool, spec, keep=5)
    dropped = [q for q in pool.quotes if q.option_id not in {o.option_id for o in ranked.options}]

    print("\n[Pruned] removed from negotiation set:")
    for q in dropped:
        print(f"    {q.vendor:<22} {q.status:<11} — {q.notes}")

    print(f"\n[Shortlist] top {len(ranked.options)} vendors handed to Scenario 3 (negotiation):")
    for i, o in enumerate(ranked.options, start=1):
        print(f"    {i}. {o.vendor:<22} all-in ${o.listed_price:,.0f}  match {o.match_score:.2f}  {o.source_url or ''}")
    print()


if __name__ == "__main__":
    main()
