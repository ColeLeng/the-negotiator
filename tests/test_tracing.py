"""
tests/test_tracing.py
======================
Event tracing (Jagger) -- logs key agent events for the demo's live left-screen
agent-behavior panel.

Coverage:
  - Tracer.emit stores events and notifies subscribers in order.
  - orchestrator.run(tracer=...) logs session_spawned / message / session_end /
    recommendation events with plausible session/price/vendor linkage.
  - Every negotiation turn logged by comms/loop is also visible through the tracer
    (transcript and trace never diverge -- same underlying messages).
  - Passing no tracer changes nothing (orchestrator.run stays usable exactly as
    before this feature existed).
"""
from __future__ import annotations

from negotiator import orchestrator
from negotiator.comms.blackboard import Blackboard
from negotiator.comms.channels import MockChannel
from negotiator.comms.loop import run_negotiation
from negotiator.agents.buyer_agent import BuyerAgent
from negotiator.agents.seller_agent import SellerAgent
from negotiator.contracts import (
    Channel, Inventory, Negotiation, NegotiationSession, Option, ProductSpec,
    RankedOptions, SellerState,
)
from negotiator.tracing import Tracer, TraceEvent


def _spec(target=1800.0, reservation=2400.0) -> ProductSpec:
    return ProductSpec(spec_id="s", negotiation=Negotiation(target_price=target, reservation_price=reservation))


def _ranked(spec: ProductSpec) -> RankedOptions:
    options = [
        Option(option_id="o1", vendor="Vendor A", listed_price=2200.0, channel=Channel(type="mock")),
        Option(option_id="o2", vendor="Vendor B", listed_price=2100.0, channel=Channel(type="mock")),
    ]
    return RankedOptions(spec_id=spec.spec_id, options=options)


def _seller_states() -> dict:
    return {
        "o1": SellerState(vendor="Vendor A", cost_floor=1200, list_price=2200, min_margin=200,
                           inventory=Inventory(sku_units=10, stock_age_days=120)),
        "o2": SellerState(vendor="Vendor B", cost_floor=1300, list_price=2100, min_margin=150,
                           inventory=Inventory(sku_units=4, stock_age_days=20)),
    }


class TestTracerCore:

    def test_emit_stores_event_and_returns_it(self):
        tracer = Tracer()
        evt = tracer.emit("message", actor="buyer", label="buyer open $1800", price=1800.0)
        assert isinstance(evt, TraceEvent)
        assert tracer.events() == [evt]
        assert evt.kind == "message"
        assert evt.price == 1800.0

    def test_subscribers_notified_in_order(self):
        tracer = Tracer()
        seen = []
        tracer.subscribe(lambda e: seen.append(e.label))
        tracer.emit("message", label="first")
        tracer.emit("message", label="second")
        assert seen == ["first", "second"]

    def test_events_returns_a_copy(self):
        """Callers must not be able to mutate the tracer's internal log."""
        tracer = Tracer()
        tracer.emit("message", label="a")
        events = tracer.events()
        events.append("not a real event")
        assert len(tracer.events()) == 1

    def test_to_dict_is_json_serializable(self):
        import json
        tracer = Tracer()
        evt = tracer.emit("message", actor="seller", session_id="n1", label="seller concede $2000", price=2000.0)
        json.dumps(evt.to_dict())  # must not raise


class TestLoopTracing:

    def test_run_negotiation_logs_every_message_when_tracer_given(self):
        spec = _spec()
        state = SellerState(vendor="V", cost_floor=1200, list_price=2200, min_margin=200,
                             inventory=Inventory(sku_units=10, stock_age_days=120))
        session = NegotiationSession(session_id="n1", option_id="o1", spec_id=spec.spec_id,
                                      batna_utility=0.0, current_price=state.list_price)
        buyer = BuyerAgent(spec, session, max_rounds=6)
        seller = SellerAgent(state, max_rounds=6)
        tracer = Tracer()

        run_negotiation(buyer, MockChannel(seller), Blackboard(), session, tracer=tracer)

        message_events = [e for e in tracer.events() if e.kind in ("message", "guard_intervention")]
        assert len(message_events) == len(session.messages), \
            "every transcript message must have a corresponding trace event"
        assert all(e.session_id == "n1" for e in message_events)

    def test_run_negotiation_without_tracer_is_unaffected(self):
        """Omitting `tracer` must change nothing -- purely additive."""
        spec = _spec()
        state = SellerState(vendor="V", cost_floor=1200, list_price=2200, min_margin=200,
                             inventory=Inventory(sku_units=10, stock_age_days=120))
        session = NegotiationSession(session_id="n1", option_id="o1", spec_id=spec.spec_id,
                                      batna_utility=0.0, current_price=state.list_price)
        buyer = BuyerAgent(spec, session, max_rounds=6)
        seller = SellerAgent(state, max_rounds=6)
        run_negotiation(buyer, MockChannel(seller), Blackboard(), session)  # no crash, no tracer
        assert session.status in ("agreed", "walked_away", "refused")


class TestOrchestratorTracing:

    def test_run_logs_spawn_and_end_per_session(self):
        spec = _spec()
        ranked = _ranked(spec)
        tracer = Tracer()

        orchestrator.run(ranked, spec, seller_states=_seller_states(), top_n=2, tracer=tracer)

        spawned = [e for e in tracer.events() if e.kind == "session_spawned"]
        ended = [e for e in tracer.events() if e.kind == "session_end"]
        assert len(spawned) == 2
        assert len(ended) == 2
        assert {e.vendor for e in spawned} == {"Vendor A", "Vendor B"}
        assert all(e.session_id is not None for e in spawned + ended)

    def test_run_logs_exactly_one_recommendation_event(self):
        spec = _spec()
        ranked = _ranked(spec)
        tracer = Tracer()

        result = orchestrator.run(ranked, spec, seller_states=_seller_states(), top_n=2, tracer=tracer)

        recs = [e for e in tracer.events() if e.kind == "recommendation"]
        assert len(recs) == 1
        if result["recommendation"] is not None:
            assert recs[0].price == result["recommendation"].current_price

    def test_events_interleave_spawn_messages_and_end_in_order(self):
        """The feed must read as a real timeline: spawn, then that session's turns,
        then its end -- not everything batched at the finish."""
        spec = _spec()
        ranked = _ranked(spec)
        tracer = Tracer()

        orchestrator.run(ranked, spec, seller_states=_seller_states(), top_n=2, tracer=tracer)
        kinds = [e.session_id for e in tracer.events() if e.kind in
                 ("session_spawned", "message", "guard_intervention", "session_end")]

        # First session's spawn/messages/end must all appear before the second
        # session's spawn (sequential orchestrator -- see orchestrator.py docstring).
        first_session_id = kinds[0]
        second_spawn_idx = next(i for i, sid in enumerate(kinds) if sid != first_session_id)
        assert all(sid == first_session_id for sid in kinds[:second_spawn_idx])

    def test_run_without_tracer_is_unaffected(self):
        spec = _spec()
        ranked = _ranked(spec)
        result = orchestrator.run(ranked, spec, seller_states=_seller_states(), top_n=2)  # no tracer
        assert "recommendation" in result and "sessions" in result
