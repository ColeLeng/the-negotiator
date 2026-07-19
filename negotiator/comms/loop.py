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
from ..tracing import Tracer
from .blackboard import Blackboard


def run_negotiation(
    buyer,
    channel,
    blackboard: Blackboard,
    session,
    max_exchanges: Optional[int] = None,
    tracer: Optional[Tracer] = None,
    trace_detail: Optional[dict] = None,
):
    """Drive one Buyer ⇄ Seller negotiation to a terminal state; return the NegotiationSession.

    `buyer` is a BuyerAgent (opens the negotiation); `channel` delivers to the seller side.
    `tracer`, if given, logs every turn for the demo's live agent-behavior panel.
    `trace_detail`, if given, is merged into every emitted event's `detail` (e.g. a
    caller running several named scenarios can tag `{"style": "..."}` so a consumer
    can route each event to the right lane without this loop knowing about lanes).
    """
    if max_exchanges is None:
        max_exchanges = 2 * getattr(buyer, "max_rounds", 6) + 2
    extra_detail = trace_detail or {}

    def log(msg) -> None:
        session.messages.append(msg)
        if msg.price is not None:
            session.current_price = msg.price
        if tracer is not None:
            guarded = "[guard:" in (msg.rationale or "")
            price_str = f" ${msg.price:,.0f}" if msg.price is not None else ""
            tracer.emit(
                "guard_intervention" if guarded else "message",
                actor=msg.sender,
                session_id=session.session_id,
                option_id=session.option_id,
                label=f"{msg.sender} {msg.intent}{price_str}",
                price=msg.price,
                detail={
                    "intent": msg.intent, "text": msg.text, "rationale": msg.rationale,
                    "terms_delta": msg.terms_delta, **extra_detail,
                },
            )

    outbound = guard_outbound(buyer.open(), blackboard, session.session_id)
    log(outbound)

    for _ in range(max_exchanges):
        # ── seller's turn ──────────────────────────────────────────────
        channel.send(outbound)
        inbound = channel.receive()
        log(inbound)
        if inbound.price is not None:
            blackboard.post(session.session_id, inbound.price)
            if tracer is not None:
                tracer.emit(
                    "blackboard_update",
                    actor="blackboard",
                    session_id=session.session_id,
                    option_id=session.option_id,
                    label=f"Blackboard: posted ${inbound.price:,.0f} for {session.session_id}",
                    price=inbound.price,
                    detail=dict(extra_detail),
                )

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
