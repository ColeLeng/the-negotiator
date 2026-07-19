"""
Buyer-intent capture + credit-for-commitment (owner: Ella) — margin lever (nice-to-have).

Two seller-side moves, both expressed entirely through `NegotiationMessage.terms_delta`
(no new intents, no schema change, nothing written to NegotiationSession):

  B1  Capture intent the buyer *volunteers* (why they chose us, flexibility, deadline,
      who they compared against) and, when useful, `ask` for a missing piece before
      conceding. Degrades gracefully: if the buyer never answers, the seller just concedes
      on price as before.

  B2  Offer a small, contingent, NON-REFUNDABLE post-purchase credit (a coupon / store
      credit) in exchange for a post-purchase action (photo review, honest review, sharing
      preference data) — instead of cutting the gown price. The credit lives in
      `terms_delta`, never in `price`, so the comparable landing price stays high. On
      accept, the full commitment is written into the accept message's `terms_delta`; the
      transcript is the bilateral record (the buyer echoing `commitment_id` is an optional
      Suman upgrade).

Honesty (§6/§8): captured intent informs strategy only; a buyer's text is never trusted
as a price claim without the structured `price` field.
"""
from __future__ import annotations

import re

# Intent signals the buyer may volunteer in terms_delta (seller reads, never fabricates).
INTENT_KEYS = (
    "reason_chose",       # why they picked this product for comparison
    "flexibility",        # budget flexibility: low | med | high
    "wedding_date",       # deadline / urgency
    "primary_use",        # what they need it for
    "compared_against",   # the competing option they're weighing
)
# What to ask for first when it hasn't been volunteered (highest strategic value first).
_ASK_PRIORITY = ("reason_chose", "flexibility", "compared_against", "wedding_date")

# What a captured post-purchase action is worth to the merchant (marketing value, $).
ACTION_VALUE = {
    "photo_review": 15.0,
    "honest_positive_review": 10.0,
    "share_preferences": 8.0,
}


class BuyerIntent:
    """Accumulates what the buyer reveals across a negotiation (seller-local state)."""

    def __init__(self) -> None:
        self.signals: dict[str, str] = {}
        self.buyer_prices: list[float] = []
        self.asked: set[str] = set()

    def observe(self, inbound) -> None:
        td = inbound.terms_delta or {}
        for k in INTENT_KEYS:
            if k in td:
                self.signals[k] = td[k]
        if inbound.price is not None:
            self.buyer_prices.append(inbound.price)

    def price_sensitive(self) -> bool:
        """The buyer is actively pushing for a discount (still well below a firm close)."""
        if self.signals.get("flexibility") == "low":
            return True
        return len(self.buyer_prices) >= 2

    def next_ask(self) -> str | None:
        """The most valuable piece of intent not yet volunteered or asked."""
        for k in _ASK_PRIORITY:
            if k not in self.signals and k not in self.asked:
                return k
        return None


def _slug(vendor: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (vendor or "seller").lower()).strip("-")


def commitment_terms(
    vendor: str,
    round_idx: int,
    credit: float,
    list_price: float,
    conditions: str = "photo_review",
) -> dict[str, str]:
    """Build the `terms_delta` describing a contingent credit commitment.

    Deterministic `commitment_id` (no clock/RNG) so runs are reproducible. Credit is
    unlocked only once the purchase is placed and is explicitly non-refundable — it is a
    promotional incentive, not part of the price, so it never returns in a refund.
    """
    return {
        "credit_offer": f"{credit:.0f}",
        "credit_type": "store_credit",
        "credit_pct": f"{round(100 * credit / list_price, 1)}" if list_price else "0",
        "credit_conditions": conditions,
        "credit_unlock": "on_purchase_placed",
        "credit_nonrefundable": "true",
        "commitment_id": f"cmt-{_slug(vendor)}-r{round_idx}",
    }
