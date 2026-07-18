"""
Seller Agent (owner: Ella) — §8.3. Represents the vendor; asymmetric concerns vs the buyer:
protect margin, move the right inventory, land the customer.

Private state: SellerState (cost floor, list price, inventory, capacity, style, fee_template).
Cole's Caller stamps `style` + `fee_template`; Ella owns the full policy. This file is a
*runnable scaffold* so the agent-to-agent demo shows ≥3 distinct negotiation styles
without blocking on Ella — deepen behind the same NegotiationMessage interface.

Styles (challenge-required):
  · tough_negotiator              — hold near list, push deposit, concede slowly
  · stonewaller_no_prices_by_phone — refuse phone pricing early → callback / late range
  · hard_sell_upseller            — open with bundled fees; concede by stripping add-ons

Honesty: no phantom "another buyer offered more", no fake scarcity.
"""
from __future__ import annotations

from .. import seller_value
from ..contracts import NegotiationMessage, SellerState, seller_msg


class SellerAgent:
    def __init__(self, state: SellerState, max_rounds: int = 6):
        self.state = state
        self.max_rounds = max_rounds
        self.round = 0
        self.style = state.style or "tough_negotiator"

    def evaluate(self, offer_price: float) -> float:
        return seller_value.surplus(offer_price, self.state)

    def open(self) -> NegotiationMessage:
        if self.style == "hard_sell_upseller":
            bundled = seller_value.bundled_ask(self.state)
            return seller_msg(
                "open",
                price=bundled,
                terms_delta={"bundle": "gown+alterations+veil+rush"},
                rationale=(
                    f"Open at bundled ask ${bundled:.0f} (list ${self.state.list_price:.0f} "
                    f"+ add-ons) — upseller style."
                ),
            )
        if self.style == "stonewaller_no_prices_by_phone":
            return seller_msg(
                "open",
                price=None,
                terms_delta={"appointment": "required"},
                rationale="We only quote after an in-store appointment — stonewaller open.",
            )
        return seller_msg(
            "open",
            price=self.state.list_price,
            terms_delta={"deposit_pct": "20"},
            rationale="Open at list; deposit required to hold — tough negotiator.",
        )

    def respond(self, inbound: NegotiationMessage) -> NegotiationMessage:
        self.round += 1
        if self.style == "stonewaller_no_prices_by_phone":
            return self._respond_stonewaller(inbound)
        if self.style == "hard_sell_upseller":
            return self._respond_upseller(inbound)
        return self._respond_tough(inbound)

    # ── style policies (scaffold — Ella deepens) ─────────────────────────────

    def _respond_tough(self, inbound: NegotiationMessage) -> NegotiationMessage:
        buyer_price = inbound.price
        my_min = seller_value.next_seller_min(self.state, self.round, self.max_rounds)
        # Tough: concede slower (stretch the curve).
        floor = seller_value.dynamic_floor(self.state)
        my_min = max(my_min, floor + (self.state.list_price - floor) * 0.25 * (1 - self.round / self.max_rounds))

        if buyer_price is not None and buyer_price >= my_min:
            return seller_msg(
                "accept",
                price=buyer_price,
                terms_delta={"deposit_pct": "20"},
                rationale=f"Buyer ${buyer_price:.0f} clears tough floor ${floor:.0f}; deposit still required.",
            )
        if self.round >= self.max_rounds:
            if buyer_price is not None and buyer_price >= floor:
                return seller_msg(
                    "accept",
                    price=buyer_price,
                    terms_delta={"deposit_pct": "20"},
                    rationale=f"Final round; accept ${buyer_price:.0f} at floor ${floor:.0f}.",
                )
            return seller_msg(
                "reject",
                price=round(floor, 2),
                rationale=f"Below floor ${floor:.0f}; no deal without a serious deposit.",
            )
        return seller_msg(
            "concede",
            price=round(my_min, 2),
            terms_delta={"deposit_pct": "20"},
            rationale=f"Tough concede to ${my_min:.0f} (floor ${floor:.0f}).",
        )

    def _respond_stonewaller(self, inbound: NegotiationMessage) -> NegotiationMessage:
        # Early rounds: refuse phone pricing (non-terminal counter) → callback path.
        # Using reject would end the loop; counter+empty price models "someone will call you back".
        if self.round <= 2:
            return seller_msg(
                "counter",
                price=None,
                terms_delta={"callback": "manager_within_24h", "appointment": "required"},
                rationale="No prices by phone — book an appointment or we'll call you back.",
            )
        floor = seller_value.dynamic_floor(self.state)
        my_min = seller_value.next_seller_min(self.state, self.round, self.max_rounds)
        buyer_price = inbound.price
        if buyer_price is not None and buyer_price >= my_min:
            return seller_msg(
                "accept",
                price=buyer_price,
                rationale=f"After callback friction, accept ${buyer_price:.0f}.",
            )
        if self.round >= self.max_rounds:
            # Structured ending: callback commitment (not a vague range).
            return seller_msg(
                "reject",
                price=None,
                terms_delta={"callback": "manager_within_24h"},
                rationale="Still need an in-store look; documenting callback commitment.",
            )
        return seller_msg(
            "concede",
            price=round(my_min, 2),
            terms_delta={"range_note": "ballpark_only"},
            rationale=f"Reluctant ballpark ${my_min:.0f} (floor ${floor:.0f}); prefer appointment.",
        )

    def _respond_upseller(self, inbound: NegotiationMessage) -> NegotiationMessage:
        buyer_price = inbound.price
        floor = seller_value.dynamic_floor(self.state)
        bundled = seller_value.bundled_ask(self.state)
        # Concede by stripping add-ons first (protect gown margin), then ease base.
        stripped = seller_value.upsell_ask(self.state, self.round, self.max_rounds)
        my_min = max(floor, stripped)

        if buyer_price is not None and buyer_price >= my_min:
            return seller_msg(
                "accept",
                price=buyer_price,
                terms_delta={"bundle": "stripped_to_essentials"} if buyer_price < bundled else {"bundle": "full"},
                rationale=f"Accept ${buyer_price:.0f} after add-on strip (floor ${floor:.0f}).",
            )
        if self.round >= self.max_rounds:
            if buyer_price is not None and buyer_price >= floor:
                return seller_msg(
                    "accept",
                    price=buyer_price,
                    terms_delta={"bundle": "stripped_to_essentials"},
                    rationale=f"Final round; drop add-ons, accept ${buyer_price:.0f}.",
                )
            return seller_msg(
                "reject",
                price=round(floor, 2),
                rationale=f"Even without add-ons, ${floor:.0f} is the floor.",
            )
        return seller_msg(
            "concede",
            price=round(my_min, 2),
            terms_delta={"bundle": f"round_{self.round}_strip"},
            rationale=f"Upseller concede to ${my_min:.0f} by stripping optional fees.",
        )
