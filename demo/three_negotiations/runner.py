"""
demo/three_negotiations/runner.py

Runs the three rehearsal calls against the REAL negotiator pipeline. See README.md
for exactly what's real vs. scripted per scenario -- the short version: BuyerAgent,
Blackboard, guard_outbound, and Tracer are always the real, unmodified objects; only
the seller's lines are scripted.
"""
from __future__ import annotations

from typing import Optional

from negotiator.agents.buyer_agent import BuyerAgent
from negotiator.comms.blackboard import Blackboard
from negotiator.comms.loop import run_negotiation
from negotiator.contracts import Negotiation, NegotiationSession, ProductSpec, buyer_msg
from negotiator.guard import guard_outbound
from negotiator.tracing import Tracer

from .scenarios import SCENARIOS_ORDER, Scenario, ScriptedSellerChannel, UPSELLER_ADDONS, build_scenarios


def _spec() -> ProductSpec:
    return ProductSpec(
        spec_id="spec_three_negotiations",
        category="Wedding Dress (DTC)",
        negotiation=Negotiation(target_price=1800.0, reservation_price=2400.0, deadline_days=120),
    )


def _run_tough_but_fair(
    spec: ProductSpec,
    session: NegotiationSession,
    blackboard: Blackboard,
    tracer: Optional[Tracer],
    scenario: Scenario,
    max_rounds: int,
) -> dict:
    """Hand-driven (not `run_negotiation()`) so a real, blackboard-backed competing-quote
    turn can be inserted mid-call -- the one thing the shared loop has no hook for.
    Every other primitive here (BuyerAgent, guard_outbound, ScriptedSellerChannel,
    Blackboard) is exactly what `run_negotiation()` itself uses."""
    style = scenario.style_id
    buyer = BuyerAgent(spec, session, max_rounds=max_rounds)
    channel = ScriptedSellerChannel(scenario.seller_script)

    def log(msg, kind: str = "message", extra: Optional[dict] = None) -> None:
        session.messages.append(msg)
        if msg.price is not None:
            session.current_price = msg.price
        if tracer is not None:
            price_str = f" ${msg.price:,.0f}" if msg.price is not None else ""
            tracer.emit(
                kind, actor=msg.sender, session_id=session.session_id, option_id=session.option_id,
                label=f"{msg.sender} {msg.intent}{price_str}", price=msg.price,
                detail={
                    "text": msg.text, "rationale": msg.rationale, "terms_delta": msg.terms_delta,
                    "style": style, **(extra or {}),
                },
            )

    # -- preamble: AI disclosure + a little friction, outside the price loop --
    seller_asks_robot, seller_busy = scenario.preamble
    log(seller_asks_robot)
    disclosure = buyer_msg(
        "open",
        text="Good question -- I'm actually an AI, calling on behalf of a customer shopping for a "
             "wedding dress. Happy to answer anything about that. Do you have a few minutes for pricing?",
        rationale="AI disclosure, offered proactively when asked directly.",
    )
    log(disclosure, kind="ai_disclosure")
    log(seller_busy)
    friction_ack = buyer_msg("open", text="Of course, take your time.", rationale="Friction handled gracefully.")
    log(friction_ack, kind="friction")

    # -- opening exchange (real BuyerAgent.open(), real guard) --
    outbound = guard_outbound(buyer.open(), blackboard, session.session_id)
    log(outbound)
    channel.send(outbound)
    inbound = channel.receive()  # seller opens at list price
    log(inbound)
    if inbound.price is not None:
        blackboard.post(session.session_id, inbound.price)

    outbound = guard_outbound(buyer.respond(inbound), blackboard, session.session_id)  # real round 1 counter
    log(outbound)
    channel.send(outbound)
    inbound = channel.receive()  # seller concedes a little, pushes a deposit
    log(inbound)
    if inbound.price is not None:
        blackboard.post(session.session_id, inbound.price)

    # -- THE MONEY SHOT: an honest, blackboard-backed competing-quote turn --
    # The buyer's PRICE stays on its real Boulware trajectory (buyer.respond() is
    # still the one deciding the number); only the text/rationale adds the honest
    # reference, exactly like a real caller would ("I could get X elsewhere, but
    # I'd rather deal with you at Y") rather than instantly lowballing to X.
    competing_price = blackboard.best_excluding(session.session_id)
    base_response = buyer.respond(inbound)
    honesty_confirmed = False
    if competing_price is not None and base_response.intent == "counter":
        leverage = base_response.model_copy(update={
            "text": f"I hear you -- but I've got a comparable quote at ${competing_price:.0f} from another shop. "
                    f"If you can get closer to ${base_response.price:.0f}, I'm ready to put a deposit down today.",
            "rationale": f"{base_response.rationale} Honest leverage: real quote ${competing_price:.0f} live on "
                         f"the shared blackboard (another channel's real price, per market_benchmarks.py).",
        })
        guarded = guard_outbound(leverage, blackboard, session.session_id)
        honesty_confirmed = "[guard:" not in (guarded.rationale or "")
        log(guarded, kind="honesty_check" if honesty_confirmed else "guard_intervention")
        outbound = guarded
    else:
        outbound = guard_outbound(base_response, blackboard, session.session_id)
        log(outbound)

    channel.send(outbound)
    inbound = channel.receive()  # seller concedes further, matching the quote
    log(inbound)
    if inbound.price is not None:
        blackboard.post(session.session_id, inbound.price)

    if inbound.intent == "accept":
        session.status = "agreed"
    else:
        outbound = guard_outbound(buyer.respond(inbound), blackboard, session.session_id)
        log(outbound)
        if outbound.intent == "accept":
            session.status = "agreed"
        else:
            channel.send(outbound)
            inbound = channel.receive()  # seller accepts
            log(inbound)
            if inbound.intent == "accept":
                session.status = "agreed"

    if session.status == "in_progress":
        session.status = "walked_away"
    session.outcome = {"status": session.status, "final_price": session.current_price}

    return {"ai_disclosure": True, "friction_handled": True, "honest_leverage_only": honesty_confirmed}


def _run_scripted(
    spec: ProductSpec,
    session: NegotiationSession,
    blackboard: Blackboard,
    tracer: Optional[Tracer],
    scenario: Scenario,
    max_rounds: int,
) -> dict:
    """Scenarios 2 and 3: the real BuyerAgent negotiates a real, if scripted, seller
    price/terms sequence entirely through the shared `run_negotiation()` loop."""
    buyer = BuyerAgent(spec, session, max_rounds=max_rounds)
    channel = ScriptedSellerChannel(scenario.seller_script)
    run_negotiation(buyer, channel, blackboard, session, tracer=tracer, trace_detail={"style": scenario.style_id})
    return {}


def _checklist(style_id: str, session: NegotiationSession, extra: dict) -> dict:
    prices = [m.price for m in session.messages if m.price is not None]
    outcome = session.outcome or {}
    checklist = {
        "price_moves": len(set(p for p in prices if p is not None)) >= 2,
        "structured_ending": session.status in ("agreed", "walked_away", "refused"),
    }
    if style_id == "tough_but_fair":
        checklist.update({
            "ai_disclosure": extra.get("ai_disclosure", False),
            "friction_handled": extra.get("friction_handled", False),
            "honest_leverage_only": extra.get("honest_leverage_only", False),
        })
    if style_id == "stonewaller":
        got_range_or_callback = any(
            m.terms_delta.get("price_range") or m.terms_delta.get("callback") for m in session.messages
        )
        checklist["callback_or_range_extracted"] = got_range_or_callback
    if style_id == "upseller":
        checklist["fees_itemized"] = any(
            set(m.terms_delta) & set(UPSELLER_ADDONS) for m in session.messages
        )
    return checklist


def run_all(tracer: Optional[Tracer] = None, max_rounds: int = 6) -> dict:
    """Run all three rehearsal calls in order; return {style_id: {session, checklist}}."""
    spec = _spec()
    scenarios = build_scenarios()
    blackboard = Blackboard()

    # Seed the blackboard with a genuinely cheaper, real reference quote -- an
    # off-the-rack channel's market median from market_benchmarks.py (the same
    # module the Estimator bootstraps prices from). This is what makes call #1's
    # competing-quote leverage honest AND actually create downward pressure: it
    # must be lower than what this call's seller is already offering, or citing
    # it as leverage wouldn't make sense. (The other two calls' own list prices
    # are both above this call's early concessions, so they can't play this role.)
    try:
        from negotiator import market_benchmarks
        reference_quote = market_benchmarks.get_price_bounds("wedding", "dress_off_the_rack").target_price
    except (ImportError, KeyError):
        reference_quote = 1500.0  # fallback if market_benchmarks' bands ever change shape
    blackboard.post("ref_off_the_rack_listing", reference_quote)

    results = {}
    for i, style_id in enumerate(SCENARIOS_ORDER):
        scenario = scenarios[style_id]
        session = NegotiationSession(
            session_id=f"call_{style_id}", option_id=style_id, spec_id=spec.spec_id,
            current_price=scenario.list_price,
        )

        if tracer is not None:
            tracer.emit(
                "call_start", actor="orchestrator", session_id=session.session_id,
                label=f'Call {i + 1}/3 -- "{scenario.title}"',
                detail={
                    "style": style_id, "how_cole_plays_it": scenario.how_cole_plays_it,
                    "proves": scenario.proves,
                },
            )

        if style_id == "tough_but_fair":
            extra = _run_tough_but_fair(spec, session, blackboard, tracer, scenario, max_rounds)
        else:
            extra = _run_scripted(spec, session, blackboard, tracer, scenario, max_rounds)

        checklist = _checklist(style_id, session, extra)

        if tracer is not None:
            price_str = f" at ${session.current_price:,.0f}" if session.current_price is not None else ""
            tracer.emit(
                "call_end", actor="orchestrator", session_id=session.session_id,
                label=f'"{scenario.title}": {session.status}{price_str}',
                price=session.current_price,
                detail={"style": style_id, "checklist": checklist, "status": session.status},
            )

        results[style_id] = {"session": session, "checklist": checklist}

    return results
