"""
Scenario 2 — the buyer's shared evidence pool (owner: Cole).

Scenario 2 ("the second agent process") sits between intake (Scenario 1) and
negotiation (Scenario 3):

    ProductSpec (JSON requirements)  ──▶  Buyer inquiry vs N seller agents
                                          each with a distinct DISCLOSURE persona
                                     ──▶  EvidencePool  (itemized, verified quotes)
                                     ──▶  shortlist → RankedOptions for Scenario 3

This module holds the *data* the buyer accumulates: one `QuoteEvidence` per seller
it talked to, gathered into an `EvidencePool` that computes the cross-vendor
aggregates (median all-in, count verified) the buyer leverages downstream. These
are deliberately NOT in the frozen `contracts.py` — the Caller→Orchestrator hand-off
stays `RankedOptions`; this is the buyer's private working memory on the way there.

Everything is pydantic so the pool serializes cleanly for the demo API / trace panel.
"""
from __future__ import annotations

import statistics
from typing import Literal, Optional

from pydantic import BaseModel, Field

# How the seller behaved when asked for a number. Drives the demo's "12 different
# personalities" story and how much the buyer can trust the quote.
DisclosurePersona = Literal[
    "transparent",      # itemizes the full quote up front
    "guarded",          # base only; itemizes fees only when pressed
    "stonewaller",      # "we don't quote by phone" — appointment / callback / vague ballpark
    "upseller",         # leads with an inflated bundle; real base hides under optional add-ons
    "lowball_teaser",   # dangles a fake-low base; mandatory fees balloon the real all-in
]

# Terminal state of one quote in the pool.
EvidenceStatus = Literal[
    "verified",     # firm, itemized, feasible all-in the buyer trusts
    "flagged",      # firm quote but a red flag fired (kept, ranked lower)
    "no_price",     # seller never disclosed a usable number
    "infeasible",   # violates a hard constraint or exceeds the reservation price
    "red_flag",     # a blocking honesty red flag (e.g. exposed fake-low teaser)
]


class FeeLine(BaseModel):
    """One comparable fee line the buyer extracted from a seller's quote."""

    code: str                       # base | alterations | veil | rush | deposit | shipping | custom_sizing | …
    label: str
    amount: float
    optional: bool = False          # buyer may strip this before comparing
    mandatory: bool = False         # unavoidable → counts toward the comparable all-in
    schedule_only: bool = False     # a payment schedule line (e.g. deposit), NOT an added charge


class ItemizedQuote(BaseModel):
    """Structured, comparable quote — the thing the buyer verifies and ranks on."""

    vendor: str
    currency: str = "USD"
    headline_price: Optional[float] = None       # the number the seller LED with (may be padded/teaser)
    base_price: Optional[float] = None           # the gown/base line
    line_items: list[FeeLine] = Field(default_factory=list)
    comparable_total: Optional[float] = None     # apples-to-apples all-in (mandatory lines only, no schedule)
    ballpark: Optional[list[float]] = None       # [low, high] when only a range was given
    notes: Optional[str] = None

    def recompute_comparable(self) -> "ItemizedQuote":
        """comparable_total = base + mandatory fees; deposits/optional lines excluded."""
        parts = [li.amount for li in self.line_items if li.mandatory and not li.schedule_only]
        base = self.base_price if self.base_price is not None else 0.0
        total = round(base + sum(parts), 2) if (self.base_price is not None or parts) else None
        return self.model_copy(update={"comparable_total": total})


class QuoteEvidence(BaseModel):
    """One seller's entry in the buyer's evidence pool — what was learned + how much to trust it."""

    option_id: str
    vendor: str
    persona: DisclosurePersona
    source_url: Optional[str] = None
    listed_price: Optional[float] = None
    matched_attributes: dict[str, str] = Field(default_factory=dict)

    quote: Optional[ItemizedQuote] = None
    comparable_total: Optional[float] = None
    disclosure_quality: float = 0.0              # 0..1 — how forthcoming/trustworthy the disclosure was
    inquiry_turns: int = 0                        # how many asks it took

    status: EvidenceStatus = "no_price"
    verified: bool = False
    verification_flags: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    utility: float = 0.0                          # buyer utility of the comparable all-in (0..1)
    notes: Optional[str] = None


class EvidencePool(BaseModel):
    """The buyer's shared knowledge/context: every quote gathered, plus cross-vendor aggregates.

    This is the "pool of evidence" Scenario 3 leverages — a verified BATNA landscape
    rather than a single number.
    """

    spec_id: str
    quotes: list[QuoteEvidence] = Field(default_factory=list)

    def add(self, evidence: QuoteEvidence) -> None:
        self.quotes.append(evidence)

    def firm_totals(self) -> list[float]:
        """Every firm (non-ballpark) comparable all-in currently in the pool."""
        return [q.comparable_total for q in self.quotes if q.comparable_total is not None]

    def median_comparable(self) -> Optional[float]:
        totals = self.firm_totals()
        return round(statistics.median(totals), 2) if totals else None

    def verified(self) -> list[QuoteEvidence]:
        return [q for q in self.quotes if q.verified]

    def summary(self) -> dict:
        return {
            "spec_id": self.spec_id,
            "contacted": len(self.quotes),
            "firm_quotes": len(self.firm_totals()),
            "verified": len(self.verified()),
            "median_comparable": self.median_comparable(),
            "by_status": {
                s: sum(1 for q in self.quotes if q.status == s)
                for s in ("verified", "flagged", "no_price", "infeasible", "red_flag")
            },
        }
