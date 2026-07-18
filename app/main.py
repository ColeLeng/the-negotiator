"""
FastAPI surface (owner: Suman + Cole for UI wiring) — wires the modules for the Demo UI (§12).
Everything here runs on mocks with no keys, so the UI can integrate immediately.

    uvicorn app.main:app --reload
    # then: GET /demo  ·  POST /estimate  ·  POST /search  ·  POST /negotiate
    #       GET /demo/stream  (SSE for the live ticker + transcript)
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from negotiator import orchestrator
from negotiator.caller import search
from negotiator.contracts import ProductSpec, RankedOptions
from negotiator.estimator import estimate

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
