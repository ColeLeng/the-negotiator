"""
FastAPI surface (owner: Suman + Cole for UI wiring) — wires the modules for the Demo UI (§12).
Everything here runs on mocks with no keys, so the UI can integrate immediately.
Estimator intake routes (owner: Jagger) cover both required intake paths — voice
(ElevenLabs Agents) and document (§5) — converging on the same ProductSpec pipeline.
Trace routes (owner: Jagger) feed the demo's live agent-behavior panel.

    uvicorn app.main:app --reload
    # then: GET /demo  ·  POST /estimate  ·  POST /search  ·  POST /negotiate
    #       GET /demo/stream  (SSE for the live ticker + transcript)
    #       POST /estimate/document  ·  POST /estimate/voice/webhook
    #       GET /estimate/voice/agent-config/{vertical}  ·  POST /estimate/confirm
    #       GET /trace/view   (live agent-behavior panel)
    #       GET /trace/stream (SSE feed backing that panel)  ·  GET /trace (fallback)
"""
from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from negotiator import orchestrator
from negotiator.caller import search
from negotiator.contracts import ProductSpec, RankedOptions
from negotiator.estimator import (
    confirm_spec,
    estimate,
    estimate_from_document,
    missing_requirements,
    to_buyer_intent,
)
from negotiator.inquiry import gather_quotes, run_scenario2, shortlist
from negotiator.seller_market import load_market, spec_from_csv
from negotiator.tracing import Tracer
from negotiator.voice_intake import build_agent_config, handle_tool_call, handle_tool_call_to_intent

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
    vertical: Optional[str] = None


class DocumentEstimateRequest(BaseModel):
    content: str                        # raw text, or base64 when is_base64=True (photos)
    filename: str
    document_type: str = "other"        # "quote" | "bill" | "inventory_list" | "photo" | "other"
    vertical: Optional[str] = None
    is_base64: bool = False


class VoiceWebhookRequest(BaseModel):
    tool_args: dict
    vertical: Optional[str] = None


class ConfirmRequest(BaseModel):
    spec: ProductSpec
    edits: Optional[dict] = None


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
    return estimate(req.text, vertical=req.vertical)


@app.post("/estimate/document", response_model=ProductSpec)
def estimate_document_endpoint(req: DocumentEstimateRequest) -> ProductSpec:
    content = base64.b64decode(req.content) if req.is_base64 else req.content
    return estimate_from_document(content, req.filename, req.document_type, vertical=req.vertical)


@app.post("/estimate/voice/webhook", response_model=ProductSpec)
def estimate_voice_webhook(req: VoiceWebhookRequest) -> ProductSpec:
    """Point the ElevenLabs agent's `submit_intake` server tool at this endpoint."""
    return handle_tool_call(req.tool_args, vertical=req.vertical)


@app.post("/estimate/voice/intent")
def estimate_voice_intent(req: VoiceWebhookRequest) -> dict:
    """Voice tool-call → buyer-intent JSON (the handoff to parallel quote-seeking)."""
    return handle_tool_call_to_intent(req.tool_args, vertical=req.vertical)


@app.post("/estimate/intent")
def estimate_intent_endpoint(spec: ProductSpec) -> dict:
    """A confirmed ProductSpec → the priority + user-intent JSON. Carries a
    `caller_dynamic_variables` block (Stage 1: parallel quote-seeking, no price
    anchoring) and a `negotiation_dynamic_variables` block (Stage 2: negotiation once a
    BATNA exists)."""
    return to_buyer_intent(spec)


@app.get("/estimate/voice/agent-config/{vertical}")
def estimate_voice_agent_config(vertical: str) -> dict:
    try:
        return build_agent_config(vertical)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/estimate/confirm", response_model=ProductSpec)
def estimate_confirm_endpoint(req: ConfirmRequest) -> ProductSpec:
    """The user-confirmation gate — nothing downstream may run on an unconfirmed spec."""
    try:
        return confirm_spec(req.spec, edits=req.edits)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/estimate/missing")
def estimate_missing_endpoint(spec: ProductSpec) -> dict:
    return {"missing": missing_requirements(spec)}


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


# ── Scenario 2 — quote gathering across the 12 seller personas ────────────────
def _scenario2_spec() -> ProductSpec:
    """The buyer's requirements: prefer the market spec fixture, else build from the CSV."""
    fixture = Path(__file__).resolve().parent.parent / "fixtures" / "wedding_market_spec.json"
    if fixture.exists():
        return ProductSpec.model_validate(json.loads(fixture.read_text()))
    return spec_from_csv()


def _scenario2_payload(pool, ranked, spec: ProductSpec) -> dict:
    return {
        "spec": spec.model_dump(by_alias=True),
        "pool": pool.model_dump(),
        "summary": pool.summary(),
        "shortlist": ranked.model_dump(),
    }


@app.post("/inquiry")
def inquiry_endpoint(spec: ProductSpec, keep: int = 5) -> dict:
    """Run the buyer's quote-gathering pass for a given spec → evidence pool + shortlist."""
    result = run_scenario2(spec, keep=keep)
    return _scenario2_payload(result["pool"], result["shortlist"], spec)


@app.get("/inquiry")
def inquiry_demo(keep: int = 5) -> dict:
    """Scenario 2 on the demo market: 12 seller personas → verified pool → top 3–5."""
    spec = _scenario2_spec()
    result = run_scenario2(spec, keep=keep)
    return _scenario2_payload(result["pool"], result["shortlist"], spec)


@app.get("/inquiry/trace")
def inquiry_trace(keep: int = 5) -> dict:
    """Scenario 2 with the full agent-trace event log (inquiry turns, verification, pruning)."""
    spec = _scenario2_spec()
    tracer = Tracer()
    pool = gather_quotes(spec, load_market(), tracer=tracer)
    ranked = shortlist(pool, spec, keep=keep, tracer=tracer)
    return {"events": [e.to_dict() for e in tracer.events()], **_scenario2_payload(pool, ranked, spec)}


@app.get("/inquiry/stream")
async def inquiry_stream(keep: int = 5) -> StreamingResponse:
    """SSE feed of the buyer building its evidence pool live — one `trace` event per
    inquiry turn / verification / pruning decision, then `done`."""

    async def events():
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()
        tracer = Tracer()
        tracer.subscribe(lambda evt: loop.call_soon_threadsafe(queue.put_nowait, evt))

        def run() -> None:
            spec = _scenario2_spec()
            pool = gather_quotes(spec, load_market(), tracer=tracer)
            shortlist(pool, spec, keep=keep, tracer=tracer)

        async def runner() -> None:
            try:
                await asyncio.to_thread(run)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        task = asyncio.create_task(runner())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield _sse("trace", event.to_dict())
                await asyncio.sleep(0.05)
        finally:
            await task
        yield _sse("done", {})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


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
