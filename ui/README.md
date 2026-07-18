# Demo UI (owner: Cole) — §12

Next.js single page, three panels (see [`../docs/technical-architecture.md`](../docs/technical-architecture.md) §12):

1. **Ranked options table** — from `RankedOptions` (real vendor URLs from the Caller).
2. **Moving-price ticker** — subscribes to each session's `current_price` via SSE (`GET /demo/stream`).
3. **Live transcript** — streamed `NegotiationMessage`s with rationale.

## Run

```bash
# terminal 1 — API (from repo root)
source .venv/bin/activate
uvicorn app.main:app --reload

# terminal 2 — UI
cd ui
npm install
npm run dev
# → http://localhost:3000
```

Optional: `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000` (default).

**Min demoable:** ranked table + live ticker + scrolling transcript for the demo sessions.
