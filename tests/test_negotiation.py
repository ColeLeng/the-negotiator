"""Negotiation engine — the '§8 done when' checks: real, terminating, inventory-driven price."""
from negotiator import seller_value
from negotiator.agents.buyer_agent import BuyerAgent
from negotiator.agents.seller_agent import SellerAgent
from negotiator.comms.blackboard import Blackboard
from negotiator.comms.channels import MockChannel
from negotiator.comms.loop import run_negotiation
from negotiator.contracts import (
    Inventory,
    Negotiation,
    NegotiationSession,
    ProductSpec,
    SellerState,
)


def _spec(target=1800.0, reservation=2400.0) -> ProductSpec:
    return ProductSpec(spec_id="s", negotiation=Negotiation(target_price=target, reservation_price=reservation))


def _run(state: SellerState, spec=None, batna=0.0) -> NegotiationSession:
    spec = spec or _spec()
    session = NegotiationSession(
        session_id="n1", option_id="o1", spec_id=spec.spec_id,
        batna_utility=batna, current_price=state.list_price,
    )
    buyer = BuyerAgent(spec, session, max_rounds=6)
    seller = SellerAgent(state, max_rounds=6)
    run_negotiation(buyer, MockChannel(seller), Blackboard(), session)
    return session


def test_zopa_reaches_agreement_within_bounds():
    spec = _spec()
    state = SellerState(vendor="V", cost_floor=1200, list_price=2200, min_margin=200,
                        inventory=Inventory(sku_units=10, stock_age_days=120))
    s = _run(state, spec)
    assert s.status == "agreed"
    floor = seller_value.dynamic_floor(state)
    assert floor - 1 <= s.current_price <= spec.negotiation.reservation_price + 1
    # every message is logged with a price/ rationale = transcript evidence
    assert len(s.messages) >= 2 and s.messages[0].sender == "buyer"


def test_price_actually_moves():
    spec = _spec()
    state = SellerState(vendor="V", cost_floor=1200, list_price=2200, min_margin=200,
                        inventory=Inventory(sku_units=10, stock_age_days=120))
    s = _run(state, spec)
    prices = [m.price for m in s.messages if m.price is not None]
    assert len(set(prices)) >= 3   # the number genuinely moves, not a single scripted value


def test_aging_stock_closes_no_higher_than_fresh():
    spec = _spec()
    fresh = SellerState(vendor="Fresh", cost_floor=1500, list_price=2200, min_margin=300,
                        inventory=Inventory(sku_units=2, stock_age_days=10))
    aging = SellerState(vendor="Aging", cost_floor=1500, list_price=2200, min_margin=300,
                        inventory=Inventory(sku_units=20, stock_age_days=300))
    assert seller_value.dynamic_floor(aging) < seller_value.dynamic_floor(fresh)
    s_fresh, s_aging = _run(fresh, spec), _run(aging, spec)
    if s_fresh.status == "agreed" and s_aging.status == "agreed":
        assert s_aging.current_price <= s_fresh.current_price + 1e-6


def test_no_zopa_walks_gracefully():
    spec = _spec()
    # Floor above the buyer's reservation → no overlap → graceful walk, not a crash or bad deal.
    state = SellerState(vendor="Pricey", cost_floor=2350, list_price=2600, min_margin=100,
                        inventory=Inventory(sku_units=1, stock_age_days=5))
    s = _run(state, spec, batna=0.95)
    assert s.status in ("walked_away", "refused")
    assert s.current_price is None or s.current_price >= seller_value.dynamic_floor(state) - 1
