"""
Itemized quote capture (owner: Cole / Caller) — challenge §2.

Every call must end in a structured, comparable form:
  itemized_quote | callback_commitment | declined

This module turns a completed NegotiationSession (+ its SellerState fee_template)
into an ItemizedQuote the UI / Closer can rank apples-to-apples.
"""
from __future__ import annotations

from .contracts import (
    CallEnding,
    FeeLine,
    ItemizedQuote,
    NegotiationSession,
    SellerState,
)


def capture_quote(session: NegotiationSession, state: SellerState) -> NegotiationSession:
    """Attach call_ending + itemized_quote to a finished session. Idempotent."""
    style = state.style or session.negotiation_style
    session.negotiation_style = style

    if session.status == "agreed" and session.current_price is not None:
        kept_bundle = _accept_kept_bundle(session)
        quote = _itemized_from_deal(session.current_price, state, kept_bundle=kept_bundle)
        session.call_ending = "itemized_quote"
        session.itemized_quote = quote
        session.outcome = {
            **(session.outcome or {}),
            "status": session.status,
            "final_price": session.current_price,
            "call_ending": session.call_ending,
            "itemized_total": quote.total,
            "style": style,
        }
        return session

    if session.status == "refused":
        # Stonewaller path: refused phone price → structured callback, not a vague range.
        session.call_ending = "callback_commitment"
        session.itemized_quote = None
        session.outcome = {
            **(session.outcome or {}),
            "status": session.status,
            "final_price": session.current_price,
            "call_ending": session.call_ending,
            "callback": "in-store appointment / manager callback",
            "style": style,
        }
        return session

    # walked_away / in_progress timeout → documented decline
    session.call_ending = "declined"
    session.itemized_quote = None
    session.outcome = {
        **(session.outcome or {}),
        "status": session.status,
        "final_price": session.current_price,
        "call_ending": session.call_ending,
        "style": style,
    }
    return session


def _accept_kept_bundle(session: NegotiationSession) -> bool:
    """True only if the accepting seller message still carries a full bundle."""
    for msg in reversed(session.messages):
        if msg.intent == "accept" and msg.sender == "seller":
            bundle = (msg.terms_delta or {}).get("bundle", "")
            return bundle == "full"
        if msg.intent == "accept" and msg.sender == "buyer":
            # Buyer accepted a seller ask — inspect the prior seller price message.
            continue
    return False


def _itemized_from_deal(
    final_price: float,
    state: SellerState,
    kept_bundle: bool = False,
) -> ItemizedQuote:
    """Rebuild fee lines so the *base* absorbs negotiation; optional add-ons stay visible."""
    template = list(state.fee_template) or [
        FeeLine(code="base", label="Gown / base price", amount=final_price)
    ]
    base_lines = [li for li in template if li.code == "base"]
    other = [li for li in template if li.code != "base"]

    deposit = [li for li in other if li.code == "deposit"]
    optional = [li for li in other if li.code != "deposit" and li.optional]
    required = [li for li in other if li.code != "deposit" and not li.optional]

    optional_total = sum(li.amount for li in optional)
    lines: list[FeeLine] = []
    if state.style == "hard_sell_upseller" and kept_bundle and optional_total > 0:
        gown = max(0.0, round(final_price - optional_total, 2))
        lines.append(FeeLine(code="base", label="Gown / base price", amount=gown))
        lines.extend(optional)
        lines.extend(required)
    else:
        # Negotiated down / stripped — clean comparable base (+ any non-optional fees).
        lines.append(
            FeeLine(
                code="base",
                label=(base_lines[0].label if base_lines else "Gown / base price"),
                amount=round(final_price, 2),
            )
        )
        lines.extend(required)

    for d in deposit:
        lines.append(d.model_copy(update={"amount": round(final_price * 0.20, 2)}))

    quote = ItemizedQuote(currency="USD", line_items=lines, notes=f"style={state.style}")
    non_deposit = sum(li.amount for li in lines if li.code != "deposit")
    return quote.model_copy(update={"total": round(non_deposit, 2)})


def ending_label(ending: CallEnding | None) -> str:
    return {
        "itemized_quote": "Itemized quote",
        "callback_commitment": "Callback commitment",
        "declined": "Declined",
    }.get(ending or "", "—")
