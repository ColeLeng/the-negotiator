"""Seller itemization (owner: Ella) — §7/§11.

The accept path must yield fee lines that cover the comparable final price: a `base`
line is always present, the deposit is a payment-schedule line (excluded from total),
and the non-deposit lines sum to the itemized total (apples-to-apples comparability).
"""
from negotiator import quote_capture, seller_profiles
from negotiator.agents.buyer_agent import BuyerAgent
from negotiator.agents.seller_agent import SellerAgent
from negotiator.comms.blackboard import Blackboard
from negotiator.comms.channels import MockChannel
from negotiator.comms.loop import run_negotiation
from negotiator.contracts import Negotiation, NegotiationSession, Option, ProductSpec


def _state_for(style: str):
    opt = Option(option_id="o", vendor="V", listed_price=2000.0, negotiation_style=style)
    return seller_profiles.seed_seller_state(opt, style)


def _run_and_capture(style: str) -> NegotiationSession:
    spec = ProductSpec(spec_id="s", negotiation=Negotiation(target_price=1800.0, reservation_price=2400.0))
    state = _state_for(style)
    session = NegotiationSession(session_id="n", option_id="o", spec_id=spec.spec_id,
                                 current_price=state.list_price, negotiation_style=style)
    buyer = BuyerAgent(spec, session, max_rounds=6)
    run_negotiation(buyer, MockChannel(SellerAgent(state, max_rounds=6)), Blackboard(), session)
    return quote_capture.capture_quote(session, state)


def test_accept_path_is_fee_itemized():
    for style in ("tough_negotiator", "hard_sell_upseller"):
        s = _run_and_capture(style)
        assert s.status == "agreed"
        assert s.call_ending == "itemized_quote"
        assert s.itemized_quote is not None
        codes = {li.code for li in s.itemized_quote.line_items}
        assert "base" in codes                                   # never a single opaque lump
        non_deposit = sum(li.amount for li in s.itemized_quote.line_items if li.code != "deposit")
        assert abs(non_deposit - s.itemized_quote.total) < 0.01  # comparable total
        # The itemized total reflects the comparable price the buyer pays for the gown deal.
        assert abs(s.itemized_quote.total - s.current_price) < 0.01


def test_deposit_is_schedule_line_not_extra_charge():
    s = _run_and_capture("tough_negotiator")
    deposits = [li for li in s.itemized_quote.line_items if li.code == "deposit"]
    assert deposits, "deposit line should be present"
    # Deposit is a slice of the price (a payment schedule), not added on top of the total.
    assert sum(li.amount for li in deposits) not in {s.itemized_quote.total}
    assert all(li.amount < s.itemized_quote.total for li in deposits)
