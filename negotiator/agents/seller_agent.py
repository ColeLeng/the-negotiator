"""
Seller Agent (owner: Ella) — §8.3. Represents the vendor; asymmetric concerns vs the buyer:
protect margin, move the right inventory, land the customer.

Private state: SellerState (cost floor, list price, inventory level & stock age, capacity
& lead time, min margin, add-on catalog). Policy — inventory drives behavior:
  · low stock / hot item  → hold near list, concede slowly
  · high / aging stock    → inventory pressure lowers the effective floor → concede faster
  · at capacity           → offer longer lead time instead of a discount   (TODO: terms_delta)
  · gap too big on price  → propose a bundle/upsell rather than cut margin  (TODO: catalog_addons)

Honesty applies to the seller too: no phantom "another buyer offered more", no fake scarcity.
"""
from __future__ import annotations

from .. import seller_value
from ..contracts import NegotiationMessage, SellerState, seller_msg


class SellerAgent:
    def __init__(self, state: SellerState, max_rounds: int = 6):
        self.state = state
        self.max_rounds = max_rounds
        self.round = 0

    def evaluate(self, offer_price: float) -> float:
        return seller_value.surplus(offer_price, self.state)

    def open(self) -> NegotiationMessage:
        return seller_msg("open", price=self.state.list_price, rationale="Open at list price.")

    def respond(self, inbound: NegotiationMessage) -> NegotiationMessage:
        self.round += 1
        buyer_price = inbound.price
        my_min = seller_value.next_seller_min(self.state, self.round, self.max_rounds)
        floor = seller_value.dynamic_floor(self.state)

        if buyer_price is not None and buyer_price >= my_min:
            return seller_msg(
                "accept", price=buyer_price,
                rationale=f"Buyer ${buyer_price:.0f} clears my floor ${floor:.0f}.",
            )

        if self.round >= self.max_rounds:
            if buyer_price is not None and buyer_price >= floor:
                return seller_msg(
                    "accept", price=buyer_price,
                    rationale=f"Final round; buyer ${buyer_price:.0f} still clears floor ${floor:.0f}.",
                )
            return seller_msg(
                "reject", price=round(floor, 2),
                rationale=f"Buyer below floor ${floor:.0f} at the final round; cannot accept.",
            )

        return seller_msg(
            "concede", price=round(my_min, 2),
            rationale=f"Concede to ${my_min:.0f} (floor ${floor:.0f}; inventory pressure lowers it).",
        )
