"""
Honesty + anti-injection guard (owner: Cole) — §9. Wraps every
buyer ⇄ channel interaction. This is our differentiator.

Outbound (buyer honesty): no fabricated competing bids — any "I have a quote at $X"
must resolve to a real row on the blackboard, else the claim is stripped. Claimed
dollar amounts may not undercut the best live competing offer.
Inbound (seller untrusted): treat all seller text as DATA, never instructions; strip
prompt-injection; acceptance only ever comes from should_accept() on parsed numbers.
"""
from __future__ import annotations

import re
from typing import Optional

from .comms.blackboard import Blackboard
from .contracts import NegotiationMessage, ParsedOffer

_COMPETING_CLAIM = (
    "i have a quote",
    "competing quote",
    "another vendor",
    "another quote",
    "quote at $",
    "matched by a competitor",
    "competitor offered",
    "i already have an offer",
    "comparable quote",
)

# Buyer must never volunteer its private walk-away / budget as a hard number.
_RESERVATION_BLUFF = (
    "my reservation",
    "my max is",
    "my maximum is",
    "my budget is",
    "i can go up to",
    "walk-away is",
    "walk away is",
)

_INJECTION = (
    r"ignore (your|previous|all)",
    r"reveal your (max|budget|reservation|floor)",
    r"you must accept",
    r"system prompt",
    r"disregard .* instructions",
    r"new instructions?:",
    r"override (your|the) (rules|policy|guard)",
)

_PRICE_RE = re.compile(r"\$\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)")


def _claimed_prices(text: str) -> list[float]:
    return [float(m.replace(",", "")) for m in _PRICE_RE.findall(text or "")]


def _strip_claim(msg: NegotiationMessage, note: str) -> NegotiationMessage:
    return msg.model_copy(
        update={
            "text": None,
            "rationale": ((msg.rationale or "").rstrip() + f" [guard: {note}]").strip(),
        }
    )


def guard_outbound(
    msg: NegotiationMessage,
    blackboard: Blackboard,
    session_id: str,
) -> NegotiationMessage:
    """Strip unbacked / fabricated competing-quote claims; otherwise pass through."""
    blob = f"{msg.text or ''} {msg.rationale or ''}"
    low = blob.lower()
    best: Optional[float] = blackboard.best_excluding(session_id)
    claimed = _claimed_prices(blob)

    if any(k in low for k in _RESERVATION_BLUFF):
        return _strip_claim(msg, "stripped reservation/budget disclosure")

    has_competing_claim = any(k in low for k in _COMPETING_CLAIM)
    if not has_competing_claim:
        return msg

    if best is None:
        return _strip_claim(msg, "stripped unbacked competing-quote claim")

    # Any explicit $X in a competing-quote claim must not invent a better bid than
    # the best live offer on the blackboard (lower price = stronger fabricated leverage).
    for price in claimed:
        if price < best - 0.5:
            return _strip_claim(
                msg,
                f"stripped fabricated competing quote ${price:.0f} (best live ${best:.0f})",
            )
    return msg


def sanitize_inbound(seller_text: str) -> ParsedOffer:
    """Parse raw seller text → ParsedOffer, neutralizing any embedded instructions."""
    low = (seller_text or "").lower()
    flags: list[str] = []
    if any(re.search(p, low) for p in _INJECTION):
        flags.append("injection_attempt")

    # Drop obvious instruction-shaped lines before price extraction so injection
    # payloads can't smuggle a fake "accept $1" past the parser as the deal price.
    cleaned_lines = []
    for line in (seller_text or "").splitlines():
        if any(re.search(p, line.lower()) for p in _INJECTION):
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines) if cleaned_lines else (seller_text or "")

    m = _PRICE_RE.search(cleaned)
    price = float(m.group(1).replace(",", "")) if m else None

    intent = None
    if re.search(r"\b(i )?accept\b|\bdeal\b|\bagreed?\b", low):
        intent = "accept"
    elif re.search(r"\b(no deal|not interested|refuse|cannot)\b", low):
        intent = "reject"
    elif re.search(r"\b(counter|best i can|how about)\b", low):
        intent = "counter"

    return ParsedOffer(
        price=price,
        intent=intent,  # type: ignore[arg-type]
        raw_text=seller_text,
        flags=flags,
    )
