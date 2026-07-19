"""Brand/policy/SLA config (owner: Ella) — margin lever (nice-to-have).

A brand profile raises the landing price (concession dampening), enriches the upsell
catalog with accessories, and is loaded purely into the seller's own state — no change to
the shared NegotiationMessage schema.
"""
from negotiator import brand_profiles, seller_value
from negotiator.agents.buyer_agent import BuyerAgent
from negotiator.agents.seller_agent import SellerAgent
from negotiator.comms.blackboard import Blackboard
from negotiator.comms.channels import MockChannel
from negotiator.comms.loop import run_negotiation
from negotiator.contracts import (
    Capacity,
    Inventory,
    Negotiation,
    NegotiationSession,
    ProductSpec,
    SellerState,
)


def _tough_state(vendor: str) -> SellerState:
    return SellerState(vendor=vendor, cost_floor=1400.0, list_price=2000.0, min_margin=440.0,
                       inventory=Inventory(sku_units=2, stock_age_days=14),
                       capacity=Capacity(lead_time_days=28, at_capacity=False),
                       style="tough_negotiator")


def _run(state: SellerState) -> NegotiationSession:
    spec = ProductSpec(spec_id="s", negotiation=Negotiation(target_price=1800.0, reservation_price=2400.0))
    session = NegotiationSession(session_id="n", option_id="o", spec_id=spec.spec_id,
                                 current_price=state.list_price, negotiation_style=state.style)
    buyer = BuyerAgent(spec, session, max_rounds=6)
    run_negotiation(buyer, MockChannel(SellerAgent(state, max_rounds=6)), Blackboard(), session)
    return session


def test_value_hold_only_raises_toward_list():
    assert seller_value.value_hold(1500.0, 2000.0, 0.0) == 1500.0        # no brand → unchanged
    held = seller_value.value_hold(1500.0, 2000.0, 0.8)
    assert 1500.0 < held <= 2000.0                                       # raised, never above list


def test_known_brand_loads_and_scores():
    brand = brand_profiles.load_brand("Kleinfeld Bridal")
    assert brand is not None
    assert 0.0 < brand_profiles.value_score(brand) <= 1.0
    assert brand_profiles.load_brand("No Such Vendor 123") is None       # graceful miss


def test_brand_holds_price_higher_under_identical_pressure():
    branded = _run(_tough_state("Kleinfeld Bridal"))     # high value_score → concede less
    plain = _run(_tough_state("Unbranded Boutique"))     # no config → value_score 0
    if branded.status == "agreed" and plain.status == "agreed":
        assert branded.current_price >= plain.current_price


def test_accessories_merge_into_catalog_and_fees():
    state = _tough_state("Kleinfeld Bridal")
    agent = SellerAgent(state, max_rounds=6)
    names = {a.name.lower() for a in agent.state.catalog_addons}
    codes = {f.code for f in agent.state.fee_template}
    assert "bridal cape" in names and "watteau train" in names
    assert "cape" in codes and "watteau_train" in codes
    # Accessory fee lines are optional (strippable), so they never distort the base total.
    assert all(f.optional for f in agent.state.fee_template if f.code in {"cape", "watteau_train", "gloves"})


def test_earned_credits_marked_non_refundable_in_policy():
    brand = brand_profiles.load_brand("Kleinfeld Bridal")
    assert "NOT refunded" in brand["returns_refunds"]["notes"]
