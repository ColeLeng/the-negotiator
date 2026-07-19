"""
FastAPI surface (owner: Suman + Cole for UI wiring) — wires the modules for the Demo UI (§12).
Everything here runs on mocks with no keys, so the UI can integrate immediately.
Trace routes (owner: Jagger) feed the demo's left-screen live agent-behavior panel.

    uvicorn app.main:app --reload
    # then: GET /demo  ·  POST /estimate  ·  POST /search  ·  POST /negotiate
    #       GET /demo/stream  (SSE for the live ticker + transcript)
    #       GET /trace/view   (left-screen live agent-behavior panel)
    #       GET /trace/stream (SSE feed backing that panel)  ·  GET /trace (fallback)
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from negotiator import orchestrator
from negotiator.caller import search
from negotiator.contracts import ProductSpec, RankedOptions
from negotiator.estimator import estimate
from negotiator.tracing import Tracer

app = FastAPI(title="The Negotiator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_DEMO_INPUT = "Ivory Pronovias wedding dress, US 8, ideally under $1800, hard cap $2400, within 30 days."


class EstimateRequest(BaseModel):
    text: str


def _run_demo() -> dict[str, Any]:
    spec = estimate(_DEMO_INPUT)
    ranked = search(spec)
    result = orchestrator.run(ranked, spec)
    return {
        "spec": spec.model_dump(by_alias=True),
        "ranked": ranked.model_dump(),
        "recommendation": (
            result["recommendation"].model_dump(by_alias=True)
            if result["recommendation"] is not None
            else None
        ),
        "sessions": [s.model_dump(by_alias=True) for s in result["sessions"]],
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/estimate", response_model=ProductSpec)
def estimate_endpoint(req: EstimateRequest) -> ProductSpec:
    return estimate(req.text)


@app.post("/search", response_model=RankedOptions)
def search_endpoint(spec: ProductSpec) -> RankedOptions:
    return search(spec)


@app.post("/negotiate")
def negotiate_endpoint(spec: ProductSpec) -> dict:
    ranked = search(spec)
    return orchestrator.run(ranked, spec)


@app.get("/demo")
def demo() -> dict:
    """Full mock pipeline in one call — intake → search → negotiate → rank."""
    return _run_demo()


@app.get("/demo/stream")
async def demo_stream() -> StreamingResponse:
    """SSE: ranked table first, then per-message ticker/transcript events, then recommendation."""

    async def events():
        payload = await asyncio.to_thread(_run_demo)
        yield _sse("ranked", {"spec": payload["spec"], "ranked": payload["ranked"]})

        for session in payload["sessions"]:
            yield _sse(
                "session_start",
                {
                    "session_id": session["session_id"],
                    "option_id": session["option_id"],
                    "status": session["status"],
                    "current_price": session.get("current_price"),
                },
            )
            running_price = None
            for msg in session.get("messages") or []:
                if msg.get("price") is not None:
                    running_price = msg["price"]
                yield _sse(
                    "message",
                    {
                        "session_id": session["session_id"],
                        "option_id": session["option_id"],
                        "message": msg,
                        "current_price": running_price,
                    },
                )
                await asyncio.sleep(0.35)
            yield _sse(
                "session_end",
                {
                    "session_id": session["session_id"],
                    "option_id": session["option_id"],
                    "status": session["status"],
                    "current_price": session.get("current_price"),
                },
            )

        yield _sse("recommendation", {"recommendation": payload["recommendation"]})
        yield _sse("done", {})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


_TRACE_VIEW_PATH = Path(__file__).resolve().parent / "static" / "trace.html"


def _run_demo_traced(tracer: Tracer) -> dict:
    tracer.emit("stage", actor="estimator", label=f'Estimator: parsing "{_DEMO_INPUT}"')
    spec = estimate(_DEMO_INPUT)
    tracer.emit(
        "stage", actor="estimator",
        label=f"ProductSpec {spec.spec_id} ready — target ${spec.negotiation.target_price:,.0f} "
              f"/ reservation ${spec.negotiation.reservation_price:,.0f}",
        price=spec.negotiation.target_price,
        detail={"spec_id": spec.spec_id},
    )

    tracer.emit("stage", actor="caller", label="Caller: fanning out for comparable vendors…")
    ranked = search(spec)
    tracer.emit(
        "stage", actor="caller",
        label=f"Caller: {len(ranked.options)} ranked options found",
        detail={"option_count": len(ranked.options)},
    )

    result = orchestrator.run(ranked, spec, tracer=tracer)
    return {
        "spec": spec.model_dump(by_alias=True),
        "ranked": ranked.model_dump(),
        "recommendation": (
            result["recommendation"].model_dump(by_alias=True)
            if result["recommendation"] is not None
            else None
        ),
        "sessions": [s.model_dump(by_alias=True) for s in result["sessions"]],
    }


@app.get("/trace")
def trace() -> dict:
    """Fallback (non-streaming): run the full demo, return every logged agent event."""
    tracer = Tracer()
    payload = _run_demo_traced(tracer)
    return {"events": [e.to_dict() for e in tracer.events()], **payload}


@app.get("/trace/stream")
async def trace_stream() -> StreamingResponse:
    """SSE feed for the demo's left-screen live agent-behavior panel: one `trace`
    event per logged TraceEvent, emitted as the orchestrator produces them (not
    batched at the end), then `done`."""

    async def events():
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()
        tracer = Tracer()
        tracer.subscribe(lambda evt: loop.call_soon_threadsafe(queue.put_nowait, evt))

        async def run() -> None:
            try:
                await asyncio.to_thread(_run_demo_traced, tracer)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        task = asyncio.create_task(run())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield _sse("trace", event.to_dict())
        finally:
            await task

        yield _sse("done", {})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/trace/view")
def trace_view() -> FileResponse:
    """The left-screen panel itself -- a self-contained page, no build step. Open
    this in one window and the transcript UI (ui/) in another for the dual-screen
    demo recording."""
    return FileResponse(_TRACE_VIEW_PATH)
