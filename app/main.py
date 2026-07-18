"""
FastAPI surface (owner: Suman) — wires the modules for the Demo UI (§12).
Everything here runs on mocks with no keys, so the UI can integrate immediately.

    uvicorn app.main:app --reload
    # then: GET /demo  ·  POST /estimate  ·  POST /search  ·  POST /negotiate
"""
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from negotiator import orchestrator
from negotiator.caller import search
from negotiator.contracts import ProductSpec, RankedOptions
from negotiator.estimator import estimate

app = FastAPI(title="The Negotiator", version="0.1.0")

_DEMO_INPUT = "Ivory Pronovias wedding dress, US 8, ideally under $1800, hard cap $2400, within 30 days."


class EstimateRequest(BaseModel):
    text: str


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
    spec = estimate(_DEMO_INPUT)
    ranked = search(spec)
    return orchestrator.run(ranked, spec)
