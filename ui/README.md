# Demo UI (owner: note-taker) — §12

Next.js single page, three panels (see [`../docs/technical-architecture.md`](../docs/technical-architecture.md) §12):

1. **Ranked options table** — from `RankedOptions`.
2. **Moving-price ticker** — subscribes to each session's `current_price`; the number ticking down is the money shot.
3. **Live transcript** — streamed `NegotiationMessage`s with rationale.

**Backend** (FastAPI, [`../app/main.py`](../app/main.py)): `GET /demo`, `POST /estimate|search|negotiate`, `GET /health`. Run it with `uvicorn app.main:app --reload`.

**Min demoable:** static table + one live ticker + scrolling transcript for a single session.

TODO(note-taker): scaffold Next.js here (`npx create-next-app@latest .`) and wire SSE/websocket to the backend for the live ticker + transcript.
