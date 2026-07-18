"""
Orchestrator + shared blackboard (owner: Suman) — §11. Consumes RankedOptions, spawns
one Buyer ⇄ Seller session per top-N option, collects results, picks the best closed
deal, and emits the final recommendation.

Skeleton runs sessions sequentially (deterministic, easy to test). The blackboard already
threads real BATNA leverage across them; TODO(Suman): asyncio.gather for true parallelism
(§13 cut line — parallel sessions are a nice-to-have).
"""
from __future__ import annotations

from typing import Optional

from . import buyer_value
from .agents.buyer_agent import BuyerAgent
from .agents.seller_agent import SellerAgent
from .comms.blackboard import Blackboard
from .comms.channels import MockChannel
from .comms.loop import run_negotiation
from .contracts import NegotiationSession, Option, ProductSpec, RankedOptions, SellerState


def _synthetic_seller_state(option: Option) -> SellerState:
    """Placeholder seller economics derived from a listed price, until real vendor data
    is wired. TODO(Ella): source cost_floor / inventory / capacity for real vendors."""
    listed = option.listed_price
    return SellerState(
        vendor=option.vendor,
        cost_floor=round(listed * 0.60, 2),
        list_price=listed,
        min_margin=round(listed * 0.12, 2),
    )


def run(
    ranked: RankedOptions,
    spec: ProductSpec,
    seller_states: Optional[dict[str, SellerState]] = None,
    top_n: int = 3,
    max_rounds: int = 6,
) -> dict:
    seller_states = seller_states or {}
    blackboard = Blackboard()
    options = ranked.options[:top_n]
    sessions: list[NegotiationSession] = []

    for i, opt in enumerate(options):
        # BATNA = utility of the next-best listed option (a real fallback the buyer holds).
        if i + 1 < len(options):
            nxt = options[i + 1]
            batna = buyer_value.utility(nxt.listed_price, spec, offer_attrs=nxt.matched_attributes)
        else:
            batna = 0.0
        session = NegotiationSession(
            session_id=f"neg_{opt.option_id}",
            option_id=opt.option_id,
            spec_id=spec.spec_id,
            batna_utility=batna,
            current_price=opt.listed_price,
        )
        state = seller_states.get(opt.option_id) or _synthetic_seller_state(opt)
        buyer = BuyerAgent(spec, session, max_rounds=max_rounds)
        seller = SellerAgent(state, max_rounds=max_rounds)
        run_negotiation(buyer, MockChannel(seller), blackboard, session)
        sessions.append(session)

    closed = [s for s in sessions if s.status == "agreed" and s.current_price is not None]
    best = min(closed, key=lambda s: s.current_price) if closed else None
    return {"recommendation": best, "sessions": sessions}
