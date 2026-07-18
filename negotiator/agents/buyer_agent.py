"""
Buyer Agent (owner: Suman) — §8.2. Represents the user; maximizes buyer utility
(≈ get the discount) while protecting every hard constraint and the deadline.

Private state: ProductSpec, buyer value model (§7), BATNA (from the Caller's ranked
list + live blackboard), remaining rounds. Policy: Boulware concession, trade the
cheapest attribute first, walk the moment U(offer) < BATNA utility.

Honest leverage only: it may reference a competing quote ONLY if that row exists on
the blackboard/RankedOptions — the honesty guard (§9) enforces this on the wire.
"""
from __future__ import annotations

from .. import buyer_value
from ..contracts import NegotiationMessage, NegotiationSession, ProductSpec, buyer_msg


class BuyerAgent:
    def __init__(self, spec: ProductSpec, session: NegotiationSession, max_rounds: int = 6):
        self.spec = spec
        self.session = session          # carries live batna_utility (refreshed from the blackboard)
        self.max_rounds = max_rounds
        self.round = 0

    def evaluate(self, offer_price: float) -> float:
        return buyer_value.utility(offer_price, self.spec)

    def should_accept(self, offer_price: float) -> bool:
        return buyer_value.should_accept(offer_price, self.session, self.spec)

    def open(self) -> NegotiationMessage:
        price = self.spec.negotiation.target_price
        return buyer_msg("open", price=price, rationale="Open at target price.")

    def respond(self, inbound: NegotiationMessage) -> NegotiationMessage:
        self.round += 1
        seller_price = inbound.price
        my_max = buyer_value.next_concession(self.session, self.spec, self.round, self.max_rounds)

        if seller_price is not None and seller_price <= my_max and self.should_accept(seller_price):
            return buyer_msg(
                "accept", price=seller_price,
                rationale=f"Seller ${seller_price:.0f} within walk-away and beats BATNA "
                          f"(utility {self.evaluate(seller_price):.2f} ≥ {self.session.batna_utility or 0:.2f}).",
            )

        if self.round >= self.max_rounds or not buyer_value.is_feasible(my_max, self.spec):
            return buyer_msg(
                "hangup",
                rationale="No ZOPA within the round budget; walking to the BATNA alternative.",
            )

        return buyer_msg(
            "counter", price=round(my_max, 2),
            rationale=f"Counter ${my_max:.0f} (Boulware round {self.round}/{self.max_rounds}).",
        )
