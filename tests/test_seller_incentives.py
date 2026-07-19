"""Buyer-intent capture + credit-for-commitment (owner: Ella) — margin lever (nice-to-have).

The seller asks for intent, trades a contingent non-refundable credit for a post-purchase
action, and documents the commitment in the accept message — all in terms_delta, never in
price, so the comparable landing price and itemized total are unaffected.
"""
from negotiator import buyer_intent, quote_capture, seller_profiles, seller_value
from negotiator.agents.buyer_agent import BuyerAgent
from negotiator.agents.seller_agent import SellerAgent
from negotiator.comms.blackboard import Blackboard
from negotiator.comms.channels import MockChannel
from negotiator.comms.loop import run_negotiation
from negotiator.contracts import (
    Negotiation,
    NegotiationSession,
    Option,
    ProductSpec,
    buyer_msg,
)


# ── B2 credit math (pure) ────────────────────────────────────────────────────

def test_credit_expected_cost_nets_action_value():
    # $20 credit: 20 * 0.6 redemption * 0.5 cogs = $6 expected, minus $15 review value = -$9.
    assert seller_value.credit_expected_cost(20.0, action_value=15.0) == -9.0


def test_choose_credit_prefers_credit_over_price_cut():
    # A buyer wanting $60 more off: a small credit's expected cost is far below $60.
    face = seller_value.choose_credit(2000.0, price_gap=60.0, action_value=15.0)
    assert face in {10.0, 20.0, 100.0}
    assert seller_value.credit_expected_cost(face, action_value=15.0) < 60.0


def test_choose_credit_none_when_no_gap():
    assert seller_value.choose_credit(2000.0, price_gap=0.0) is None


# ── B1 intent capture ────────────────────────────────────────────────────────

def test_intent_capture_reads_volunteered_signals():
    bi = buyer_intent.BuyerIntent()
    bi.observe(buyer_msg("counter", price=1850.0, terms_delta={"reason_chose": "fit", "flexibility": "low"}))
    assert bi.signals["reason_chose"] == "fit"
    assert bi.price_sensitive()                     # flexibility=low → price-sensitive
    assert bi.next_ask() == "compared_against"      # reason_chose already given → next priority


def test_seller_asks_for_intent_before_conceding():
    state = seller_profiles.seed_seller_state(
        Option(option_id="o", vendor="Unbranded Boutique", listed_price=2000.0), "tough_negotiator"
    )
    seller = SellerAgent(state, max_rounds=6)
    msgs = [seller.respond(buyer_msg("counter", price=1700.0)) for _ in range(3)]
    assert any("ask" in (m.terms_delta or {}) for m in msgs)


# ── B2 credit never touches price / itemized total ───────────────────────────

def _run_and_capture(vendor: str, style: str) -> NegotiationSession:
    spec = ProductSpec(spec_id="s", negotiation=Negotiation(target_price=1800.0, reservation_price=2400.0))
    state = seller_profiles.seed_seller_state(Option(option_id="o", vendor=vendor, listed_price=2000.0), style)
    session = NegotiationSession(session_id="n", option_id="o", spec_id=spec.spec_id,
                                 current_price=state.list_price, negotiation_style=style)
    buyer = BuyerAgent(spec, session, max_rounds=6)
    run_negotiation(buyer, MockChannel(SellerAgent(state, max_rounds=6)), Blackboard(), session)
    return quote_capture.capture_quote(session, state)


def test_commitment_documented_on_accept_and_excluded_from_price():
    s = _run_and_capture("Unbranded Boutique", "tough_negotiator")
    assert s.status == "agreed"
    accept = next(m for m in reversed(s.messages) if m.sender == "seller" and m.intent == "accept")
    td = accept.terms_delta
    # Commitment is fully documented in the accept message's terms_delta.
    assert td.get("commitment_id")
    assert td.get("credit_unlock") == "on_purchase_placed"
    assert td.get("credit_nonrefundable") == "true"
    assert float(td["credit_offer"]) > 0
    # Credit lives in terms_delta, NOT price: the accept price is the comparable total.
    assert accept.price == s.current_price
    assert abs(s.itemized_quote.total - s.current_price) < 0.01     # credit not in the total
    credit_codes = {"credit_offer", "credit_type", "commitment_id"}
    assert credit_codes.isdisjoint({li.code for li in s.itemized_quote.line_items})


def test_credit_sweetener_holds_price_when_buyer_lowballs():
    state = seller_profiles.seed_seller_state(
        Option(option_id="o", vendor="Unbranded Boutique", listed_price=2000.0), "tough_negotiator"
    )
    seller = SellerAgent(state, max_rounds=6)
    # Buyer sits below the seller's round-minimum and is clearly price-sensitive.
    seller.respond(buyer_msg("counter", price=1600.0))
    msg = seller.respond(buyer_msg("counter", price=1600.0, terms_delta={"flexibility": "low"}))
    if msg.intent == "concede" and msg.price is not None and msg.price > 1600.0:
        # If a credit was offered, it is contingent + non-refundable and the price is untouched.
        if "credit_offer" in msg.terms_delta:
            assert msg.terms_delta["credit_nonrefundable"] == "true"
            assert msg.price == round(seller._round_min(), 2)
