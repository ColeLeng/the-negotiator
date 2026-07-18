"""
Honesty + anti-injection guard (owner: note-taker / shared) — §9. Wraps every
buyer ⇄ channel interaction. This is our differentiator.

Outbound (buyer honesty): no fabricated competing bids — any "I have a quote at $X"
must resolve to a real row on the blackboard, else the claim is stripped.
Inbound (seller untrusted): treat all seller text as DATA, never instructions; strip
prompt-injection; acceptance only ever comes from should_accept() on parsed numbers.
"""
from __future__ import annotations

import re

from .comms.blackboard import Blackboard
from .contracts import NegotiationMessage, ParsedOffer

_COMPETING_CLAIM = ("i have a quote", "competing quote", "another vendor",
                    "another quote", "quote at $", "matched by a competitor")

_INJECTION = (
    r"ignore (your|previous|all)",
    r"reveal your (max|budget|reservation|floor)",
    r"you must accept",
    r"system prompt",
    r"disregard .* instructions",
)


def guard_outbound(msg: NegotiationMessage, blackboard: Blackboard, session_id: str) -> NegotiationMessage:
    """Strip an unbacked competing-quote claim; otherwise pass through unchanged."""
    blob = f"{msg.text or ''} {msg.rationale or ''}".lower()
    if any(k in blob for k in _COMPETING_CLAIM) and blackboard.best_excluding(session_id) is None:
        note = " [guard: stripped unbacked competing-quote claim]"
        return msg.model_copy(update={"text": None, "rationale": (msg.rationale or "") + note})
    return msg


def sanitize_inbound(seller_text: str) -> ParsedOffer:
    """Parse raw seller text → ParsedOffer, neutralizing any embedded instructions."""
    low = seller_text.lower()
    flags: list[str] = []
    if any(re.search(p, low) for p in _INJECTION):
        flags.append("injection_attempt")
    m = re.search(r"\$?\s*([0-9][0-9,]{2,}(?:\.[0-9]{1,2})?)", seller_text)
    price = float(m.group(1).replace(",", "")) if m else None
    return ParsedOffer(price=price, raw_text=seller_text, flags=flags)
