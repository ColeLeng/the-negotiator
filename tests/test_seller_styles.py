"""Seller styles (owner: Ella) — §4/§11.

Three styles → three distinct trajectories under identical buyer pressure; an aging-stock
upseller concedes further than a fresh-stock tough; the stonewaller ends as a callback
commitment when the buyer never books (Done-when #1 and #2).
"""
from negotiator.agents.buyer_agent import BuyerAgent
from negotiator.agents.seller_agent import SellerAgent
from negotiator.comms.blackboard import Blackboard
from negotiator.comms.channels import MockChannel
from negotiator.comms.loop import run_negotiation
from negotiator.contracts import (
    AddOn,
    Capacity,
    Inventory,
    Negotiation,
    NegotiationSession,
    ProductSpec,
    SellerState,
    buyer_msg,
)

LIST = 2000.0


def _spec() -> ProductSpec:
    return ProductSpec(spec_id="s", negotiation=Negotiation(target_price=1800.0, reservation_price=2400.0))


def _tough() -> SellerState:
    return SellerState(vendor="Tough", cost_floor=LIST * 0.72, list_price=LIST, min_margin=LIST * 0.22,
                       inventory=Inventory(sku_units=2, stock_age_days=14),
                       capacity=Capacity(lead_time_days=28, at_capacity=False),
                       style="tough_negotiator")


def _stonewaller() -> SellerState:
    return SellerState(vendor="Stone", cost_floor=LIST * 0.65, list_price=LIST, min_margin=LIST * 0.18,
                       inventory=Inventory(sku_units=6, stock_age_days=60),
                       capacity=Capacity(lead_time_days=45, at_capacity=True),
                       style="stonewaller_no_prices_by_phone")


def _upseller() -> SellerState:
    return SellerState(vendor="Upsell", cost_floor=LIST * 0.55, list_price=LIST, min_margin=LIST * 0.12,
                       inventory=Inventory(sku_units=18, stock_age_days=240),
                       capacity=Capacity(lead_time_days=21, at_capacity=False),
                       catalog_addons=[AddOn(name="veil", price=120.0), AddOn(name="alterations", price=350.0),
                                       AddOn(name="rush", price=200.0)],
                       style="hard_sell_upseller")


def _run(state: SellerState) -> NegotiationSession:
    spec = _spec()
    session = NegotiationSession(session_id="n", option_id="o", spec_id=spec.spec_id,
                                 current_price=state.list_price, negotiation_style=state.style)
    buyer = BuyerAgent(spec, session, max_rounds=6)
    run_negotiation(buyer, MockChannel(SellerAgent(state, max_rounds=6)), Blackboard(), session)
    return session


def _intents(s: NegotiationSession):
    return tuple((m.sender, m.intent) for m in s.messages)


def _prices(s: NegotiationSession):
    return tuple(m.price for m in s.messages if m.price is not None)


def test_three_styles_distinct_trajectories():
    sessions = [_run(_tough()), _run(_stonewaller()), _run(_upseller())]
    # Stonewaller's "no prices by phone" opening makes its intent sequence unlike the others.
    assert _intents(sessions[1]) != _intents(sessions[0])
    assert _intents(sessions[1]) != _intents(sessions[2])
    # All three walk a genuinely different price path (not one scripted number).
    assert len({_prices(s) for s in sessions}) == 3


def _drive_lowball(state: SellerState, rounds: int = 6, lowball: float = 100.0):
    """Drive a seller with a buyer that never accepts, exposing its full concession depth
    (independent of when a cooperative buyer would have said yes)."""
    seller = SellerAgent(state, max_rounds=rounds)
    inbound = buyer_msg("open", price=lowball)
    prices = []
    for _ in range(rounds * 2):
        msg = seller.respond(inbound)
        if msg.price is not None:
            prices.append(msg.price)
        if msg.intent in ("accept", "reject", "hangup"):
            break
        inbound = buyer_msg("counter", price=lowball)
    return prices


def test_aging_upseller_concedes_further_than_fresh_tough():
    from negotiator import seller_value
    tough, upsell = _tough(), _upseller()
    assert seller_value.dynamic_floor(upsell) < seller_value.dynamic_floor(tough)
    # Under identical (never-accepting) buyer pressure, the aging upseller reaches a
    # strictly lower price than the fresh-stock tough (Done-when #1).
    assert min(_drive_lowball(upsell)) < min(_drive_lowball(tough))


def test_stonewaller_callback_when_buyer_wont_book():
    # A buyer that only ever low-balls and never books → structured callback commitment.
    seller = SellerAgent(_stonewaller(), max_rounds=3)
    inbound = buyer_msg("open", price=100.0)
    out = []
    for _ in range(10):
        msg = seller.respond(inbound)
        out.append(msg)
        if msg.intent in ("accept", "reject", "hangup"):
            break
        inbound = buyer_msg("counter", price=100.0)
    terminal = out[-1]
    assert terminal.intent == "reject"
    assert terminal.price is None                       # never a vague phone number
    assert terminal.terms_delta.get("callback")         # documented callback commitment
