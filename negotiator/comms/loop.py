"""
Negotiation loop (owner: Suman) — §8.6. One loop alternates turns, routes each message
through the honesty guard (§9) and the SellerChannel (§10), refreshes the buyer's BATNA
from the shared blackboard, and logs every step to the transcript with price + rationale.

Agent-agnostic: identical whether the seller is our mock agent or a real vendor over
voice/UCP — only the channel changes.
"""
from __future__ import annotations

from typing import Optional

from ..guard import guard_outbound
from .blackboard import Blackboard


def run_negotiation(buyer, channel, blackboard: Blackboard, session, max_exchanges: Optional[int] = None):
    """Drive one Buyer ⇄ Seller negotiation to a terminal state; return the NegotiationSession.

    `buyer` is a BuyerAgent (opens the negotiation); `channel` delivers to the seller side.
    """
    if max_exchanges is None:
        max_exchanges = 2 * getattr(buyer, "max_rounds", 6) + 2

    def log(msg) -> None:
        session.messages.append(msg)
        if msg.price is not None:
            session.current_price = msg.price

    outbound = guard_outbound(buyer.open(), blackboard, session.session_id)
    log(outbound)

    for _ in range(max_exchanges):
        # ── seller's turn ──────────────────────────────────────────────
        channel.send(outbound)
        inbound = channel.receive()
        log(inbound)
        if inbound.price is not None:
            blackboard.post(session.session_id, inbound.price)

        if inbound.intent == "accept":
            session.status = "agreed"
            break
        if inbound.intent == "reject":
            session.status = "refused"
            break
        if inbound.intent == "hangup":
            session.status = "walked_away"
            break

        # ── refresh BATNA from live competing offers, then buyer's turn ─
        competing = blackboard.best_excluding(session.session_id)
        if competing is not None:
            session.batna_utility = max(session.batna_utility or 0.0, buyer.evaluate(competing))

        outbound = guard_outbound(buyer.respond(inbound), blackboard, session.session_id)
        log(outbound)

        if outbound.intent == "accept":
            session.status = "agreed"
            break
        if outbound.intent == "hangup":
            session.status = "walked_away"
            break
    else:
        if session.status == "in_progress":
            session.status = "walked_away"

    session.outcome = {"status": session.status, "final_price": session.current_price}
    return session
