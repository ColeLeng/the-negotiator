"""Buyer value/ZOPA model — the '§7 done when' checks (owner: Cole)."""
from negotiator import buyer_value
from negotiator.contracts import Attribute, Negotiation, NegotiationSession, ProductSpec


def _spec(target=1800.0, reservation=2400.0, attrs=None) -> ProductSpec:
    return ProductSpec(
        spec_id="s",
        negotiation=Negotiation(target_price=target, reservation_price=reservation),
        attributes=attrs or [],
    )


def _demo_attrs() -> list[Attribute]:
    return [
        Attribute(name="color", value="ivory", constraint="soft", weight=0.15,
                  substitutions=["champagne", "off-white"]),
        Attribute(name="size", value="US 8", constraint="hard"),
        Attribute(name="brand", value="Pronovias", constraint="soft", weight=0.2,
                  substitutions=["Vera Wang", "comparable designer"]),
    ]


def test_utility_bounds_and_monotonicity():
    spec = _spec()
    assert buyer_value.utility(1800, spec) == 1.0
    assert buyer_value.utility(2400, spec) == 0.0
    assert 0.0 < buyer_value.utility(2100, spec) < 1.0
    assert buyer_value.utility(1900, spec) > buyer_value.utility(2200, spec)


def test_feasibility_at_walkaway():
    spec = _spec()
    assert buyer_value.is_feasible(2400, spec)
    assert not buyer_value.is_feasible(2400.01, spec)


def test_should_accept_walks_when_batna_high():
    spec = _spec()
    session = NegotiationSession(session_id="n", option_id="o", spec_id="s", batna_utility=0.9)
    # A $2400 offer (utility 0) is below the BATNA → walk.
    assert not buyer_value.should_accept(2400, session, spec)
    # A target-price offer beats the BATNA → accept.
    assert buyer_value.should_accept(1800, session, spec)


def test_concession_curve_rises_from_target_to_reservation():
    spec = _spec()
    session = NegotiationSession(session_id="n", option_id="o", spec_id="s")
    early = buyer_value.next_concession(session, spec, round_idx=1, max_rounds=6)
    late = buyer_value.next_concession(session, spec, round_idx=6, max_rounds=6)
    assert spec.negotiation.target_price <= early < late <= spec.negotiation.reservation_price


def test_hard_attribute_miss_is_infeasible():
    spec = _spec(attrs=_demo_attrs())
    ok = {"color": "ivory", "size": "US 8", "brand": "Pronovias"}
    bad = {"color": "ivory", "size": "US 12", "brand": "Pronovias"}
    assert buyer_value.is_feasible(2000, spec, ok)
    assert not buyer_value.is_feasible(2000, spec, bad)
    assert buyer_value.utility(1800, spec, offer_attrs=bad) == 0.0


def test_soft_substitution_scores_below_preferred():
    spec = _spec(attrs=_demo_attrs())
    preferred = {"color": "ivory", "size": "US 8", "brand": "Pronovias"}
    substituted = {"color": "champagne", "size": "US 8", "brand": "comparable designer"}
    u_pref = buyer_value.utility(1900, spec, offer_attrs=preferred)
    u_sub = buyer_value.utility(1900, spec, offer_attrs=substituted)
    assert u_pref > u_sub > 0.0


def test_unmet_soft_lists_non_preferred():
    spec = _spec(attrs=_demo_attrs())
    attrs = {"color": "champagne", "size": "US 8", "brand": "Pronovias"}
    assert buyer_value.unmet_soft_attributes(spec, attrs) == ["color"]
