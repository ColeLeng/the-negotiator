"""Agent-to-agent: ≥3 styles + structured itemized endings (Caller ↔ Ella scaffold)."""
from negotiator import orchestrator
from negotiator.caller import search
from negotiator.contracts import Attribute, Negotiation, ProductSpec
from negotiator.seller_profiles import DEMO_STYLES, build_states_for_ranked


def _demo_spec() -> ProductSpec:
    return ProductSpec(
        spec_id="spec_a2a",
        category="WeddingDress",
        attributes=[
            Attribute(name="color", value="ivory", constraint="soft", weight=0.15,
                      substitutions=["champagne", "off-white"]),
            Attribute(name="size", value="US 8", constraint="hard"),
            Attribute(name="brand", value="Pronovias", constraint="soft", weight=0.2,
                      substitutions=["Vera Wang", "comparable designer"]),
        ],
        negotiation=Negotiation(target_price=1800.0, reservation_price=2400.0, deadline_days=30),
    )


def test_three_styles_run_with_structured_endings():
    spec = _demo_spec()
    ranked = search(spec)
    result = orchestrator.run(ranked, spec, top_n=3)
    sessions = result["sessions"]
    assert len(sessions) == 3

    styles = {s.negotiation_style for s in sessions}
    assert styles == set(DEMO_STYLES)

    for s in sessions:
        assert s.call_ending in {"itemized_quote", "callback_commitment", "declined"}
        if s.call_ending == "itemized_quote":
            assert s.itemized_quote is not None
            assert s.itemized_quote.total > 0
            codes = {li.code for li in s.itemized_quote.line_items}
            assert "base" in codes
            # Comparable: total matches sum of non-deposit lines.
            non_dep = sum(li.amount for li in s.itemized_quote.line_items if li.code != "deposit")
            assert abs(non_dep - s.itemized_quote.total) < 0.01


def test_seller_seeds_differ_by_style():
    ranked = search(_demo_spec())
    states = build_states_for_ranked(ranked, top_n=3)
    by_style = {st.style: st for st in states.values()}
    assert set(by_style) == set(DEMO_STYLES)
    # Tough holds more margin / less aged stock than upseller.
    tough = by_style["tough_negotiator"]
    upsell = by_style["hard_sell_upseller"]
    assert tough.inventory.stock_age_days < upsell.inventory.stock_age_days
    assert len(upsell.catalog_addons) > len(tough.catalog_addons)
    assert by_style["stonewaller_no_prices_by_phone"].capacity.at_capacity is True


def test_at_least_one_priced_quote_or_callback():
    """Demo must show real style diversity — not three identical accepts."""
    spec = _demo_spec()
    ranked = search(spec)
    result = orchestrator.run(ranked, spec, top_n=3)
    endings = {s.call_ending for s in result["sessions"]}
    assert endings & {"itemized_quote", "callback_commitment", "declined"}
    # Trajectories should not be identical message intent sequences.
    trajectories = [
        tuple((m.sender, m.intent) for m in s.messages) for s in result["sessions"]
    ]
    assert len(set(trajectories)) >= 2
