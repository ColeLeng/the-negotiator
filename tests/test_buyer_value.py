"""Buyer value/ZOPA model — the '§7 done when' checks (owner: Cole + Kazi)."""
from negotiator import buyer_value
from negotiator.contracts import Negotiation, NegotiationSession, ProductSpec


def _spec(target=1800.0, reservation=2400.0) -> ProductSpec:
    return ProductSpec(spec_id="s", negotiation=Negotiation(target_price=target, reservation_price=reservation))


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
