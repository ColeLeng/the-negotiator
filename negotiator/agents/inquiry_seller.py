"""
Inquiry-side Seller Agent (owner: Cole) — Scenario 2.

This is the *quote-gathering* counterpart to the negotiation `SellerAgent`. Scenario 2
is discovery, not haggling: the buyer asks each vendor for a quote, and the vendor's
**disclosure persona** governs how much it reveals and how hard the buyer must push.

Each agent exposes a short, deterministic disclosure script (1–3 turns). The buyer
drives it turn-by-turn and every turn is a traceable event, so the demo shows twelve
visibly different personalities — transparent, guarded, stonewalling, upselling, and
the fake-low teaser — rather than one scripted exchange.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..evidence import FeeLine
from ..seller_market import MarketSeller


@dataclass
class Disclosure:
    """One seller turn during quote gathering."""

    intent: str                                   # itemized_quote | quote | revised_quote | ballpark | refuse | callback
    text: str
    headline_price: Optional[float] = None        # the number the seller is standing behind this turn
    base_price: Optional[float] = None
    line_items: list[FeeLine] = field(default_factory=list)
    comparable_total: Optional[float] = None      # firm all-in, when the seller commits to one
    ballpark: Optional[tuple[float, float]] = None
    terms: dict[str, str] = field(default_factory=dict)
    final: bool = False


class InquirySellerAgent:
    """Wraps a MarketSeller and plays out its persona's disclosure script."""

    def __init__(self, seller: MarketSeller):
        self.seller = seller
        self.persona = seller.persona
        self._script: list[Disclosure] = self._build_script()
        self._step = 0

    @property
    def turns(self) -> int:
        return len(self._script)

    def next_disclosure(self) -> Optional[Disclosure]:
        """Return the next turn, or None once the script is exhausted."""
        if self._step >= len(self._script):
            return None
        d = self._script[self._step]
        self._step += 1
        return d

    # ── persona scripts ──────────────────────────────────────────────────────
    def _build_script(self) -> list[Disclosure]:
        s = self.seller
        mandatory = list(s.mandatory_fees)
        optional = list(s.optional_fees)
        all_in = s.comparable_total()

        if self.persona == "transparent":
            return [
                Disclosure(
                    intent="itemized_quote",
                    text=f"Happy to break it down: the {s.vendor} gown is ${s.base_price:,.0f}, "
                         f"all-in ${all_in:,.0f} with required fees. Extras are optional.",
                    headline_price=all_in,
                    base_price=s.base_price,
                    line_items=mandatory + optional,
                    comparable_total=all_in,
                    final=True,
                )
            ]

        if self.persona == "guarded":
            base_line = [FeeLine(code="base", label="Gown / base price", amount=s.base_price)]
            return [
                Disclosure(
                    intent="quote",
                    text=f"The gown is ${s.base_price:,.0f}. There are a few extras depending on what you need.",
                    headline_price=s.base_price,
                    base_price=s.base_price,
                    line_items=base_line,
                    terms={"deposit_pct": f"{int(s.deposit_pct * 100)}"},
                ),
                Disclosure(
                    intent="itemized_quote",
                    text=f"Fine — itemized it's ${all_in:,.0f} all-in "
                         f"(gown + required shipping); alterations/veil are optional.",
                    headline_price=all_in,
                    base_price=s.base_price,
                    line_items=mandatory + optional,
                    comparable_total=all_in,
                    final=True,
                ),
            ]

        if self.persona == "upseller":
            bundle = s.headline_price or all_in
            bundle_items = [FeeLine(code="base", label="Gown / base price", amount=s.base_price)] + optional
            return [
                Disclosure(
                    intent="quote",
                    text=f"Our complete {s.vendor} package is ${bundle:,.0f} — gown, alterations, "
                         f"designer veil and rush production, everything you need.",
                    headline_price=bundle,
                    base_price=s.base_price,
                    line_items=bundle_items,
                    comparable_total=bundle,
                    terms={"bundle": "gown+alterations+veil+rush"},
                ),
                Disclosure(
                    intent="itemized_quote",
                    text="Here's the itemization — alterations, veil and rush are add-ons.",
                    headline_price=bundle,
                    base_price=s.base_price,
                    line_items=mandatory + optional,
                    comparable_total=bundle,
                    terms={"bundle": "itemized"},
                ),
                Disclosure(
                    intent="revised_quote",
                    text=f"Without the add-ons the gown all-in is ${all_in:,.0f}.",
                    headline_price=all_in,
                    base_price=s.base_price,
                    line_items=mandatory,
                    comparable_total=all_in,
                    terms={"bundle": "stripped_to_essentials"},
                    final=True,
                ),
            ]

        if self.persona == "lowball_teaser":
            teaser = s.teaser_base or s.base_price
            return [
                Disclosure(
                    intent="quote",
                    text=f"We can get you a {s.vendor} gown for as low as ${teaser:,.0f}!",
                    headline_price=teaser,
                    base_price=teaser,
                    line_items=[FeeLine(code="base", label="Gown / base price", amount=teaser)],
                ),
                Disclosure(
                    intent="itemized_quote",
                    text=f"With required custom sizing and mandatory alterations, the total comes to "
                         f"${all_in:,.0f}.",
                    headline_price=all_in,
                    base_price=teaser,
                    line_items=[FeeLine(code="base", label="Gown / base price", amount=teaser)] + mandatory,
                    comparable_total=all_in,
                    final=True,
                ),
            ]

        # stonewaller
        refuse = Disclosure(
            intent="refuse",
            text="We don't give prices over the phone — you'll need an in-store appointment.",
            terms={"appointment": "required"},
        )
        if s.caves and s.ballpark is not None:
            low, high = s.ballpark
            return [
                refuse,
                Disclosure(
                    intent="ballpark",
                    text=f"If you push me… somewhere between ${low:,.0f} and ${high:,.0f}, "
                         f"but I really can't commit without a fitting.",
                    ballpark=[low, high],
                    terms={"range_note": "ballpark_only"},
                    final=True,
                ),
            ]
        return [
            refuse,
            Disclosure(
                intent="callback",
                text="Leave your details and a stylist will call you back after an appointment.",
                terms={"callback": "manager_within_24h"},
                final=True,
            ),
        ]
