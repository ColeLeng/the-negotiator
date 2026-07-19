"""
Event tracing (owner: Jagger) -- logs key agent events and makes them available in
real time for the demo's left-screen panel (live agent-behavior visualization,
distinct from the right-screen conversation transcript).

A `Tracer` is a thin, thread-safe event log with a pub/sub hook: `orchestrator.run()`
and `comms/loop.run_negotiation()` both accept an optional `tracer` kwarg and emit a
`TraceEvent` at every decision point -- session spawned, each buyer/seller turn (with
price + rationale), a guard intervention, a session's outcome, and the final
recommendation. Optional and additive: omitting `tracer` changes nothing, so this
does not touch the existing orchestrator/loop behavior or tests.

    tracer = Tracer()
    tracer.subscribe(lambda evt: print(evt.label))
    orchestrator.run(ranked, spec, tracer=tracer)
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Callable, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


@dataclass
class TraceEvent:
    """One logged agent event. `kind` drives how the left-screen panel styles it."""

    ts: str
    kind: str                          # session_spawned | message | guard_intervention
                                        # | session_end | recommendation
    actor: Optional[str] = None        # buyer | seller | orchestrator
    session_id: Optional[str] = None
    option_id: Optional[str] = None
    vendor: Optional[str] = None
    label: str = ""                    # short human-readable summary for the feed
    price: Optional[float] = None
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class Tracer:
    """In-memory event log + pub/sub. Safe to call `emit` from a worker thread while
    a listener (e.g. an SSE generator) drains events on the event loop thread."""

    def __init__(self) -> None:
        self._events: list[TraceEvent] = []
        self._listeners: list[Callable[[TraceEvent], None]] = []
        self._lock = Lock()

    def emit(
        self,
        kind: str,
        *,
        actor: Optional[str] = None,
        session_id: Optional[str] = None,
        option_id: Optional[str] = None,
        vendor: Optional[str] = None,
        label: str = "",
        price: Optional[float] = None,
        detail: Optional[dict] = None,
    ) -> TraceEvent:
        event = TraceEvent(
            ts=_now_iso(),
            kind=kind,
            actor=actor,
            session_id=session_id,
            option_id=option_id,
            vendor=vendor,
            label=label,
            price=price,
            detail=detail or {},
        )
        with self._lock:
            self._events.append(event)
            listeners = list(self._listeners)
        for listener in listeners:
            listener(event)
        return event

    def subscribe(self, listener: Callable[[TraceEvent], None]) -> None:
        with self._lock:
            self._listeners.append(listener)

    def events(self) -> list[TraceEvent]:
        with self._lock:
            return list(self._events)
