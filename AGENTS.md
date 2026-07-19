# AGENTS.md

## Cursor Cloud specific instructions

"Citable Negotiator" is a single-product Python + Next.js demo. The negotiation engine
runs **on in-process mocks** — no API keys are required for the default path.
Optional search keys (`TAVILY_API_KEY`, `SERPER_API_KEY`, `BRAVE_API_KEY`,
`EXA_API_KEY`) upgrade the Caller to live web results when present.

### Environment
- Python 3.12 venv at `.venv/` (use `.venv/bin/python`, `.venv/bin/pytest`,
  `.venv/bin/uvicorn`). Always run backend commands from `/workspace`.
- UI deps in `ui/node_modules` (`cd ui && npm install`).

### Cole-owned modules
- `negotiator/buyer_value.py` — multi-attr utility; keep price-first call sites working.
- `negotiator/caller.py` — curated real bridal catalog + optional live search.
- `negotiator/guard.py` — outbound competing-quote honesty + inbound sanitize.
- `ui/` — Next.js demo (table + SSE ticker + transcript).

### Run / test (see also README "Getting started")
- Tests: `.venv/bin/pytest -q`
- CLI demo: `.venv/bin/python run_demo.py`
- API: `.venv/bin/uvicorn app.main:app --reload` → `/demo`, `/demo/stream`, `/docs`
- UI: `cd ui && npm run dev` → http://localhost:3000 (expects API on `:8000`)
- UI typecheck: `cd ui && npm run lint` (`tsc --noEmit`)

### Gotchas
- Catalog list prices are intentionally above the demo target (~$1800) so
  buyer/seller concessions have room — otherwise sellers accept the open and the
  "moving price" pitch fails.
- `GET /demo` returns `{ spec, ranked, recommendation, sessions }` (enriched for the UI).
- No Python linter configured; UI lint is TypeScript-only (no ESLint scaffold).
