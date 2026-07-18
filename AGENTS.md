# AGENTS.md

## Cursor Cloud specific instructions

"The Negotiator" is a single-product Python project (agent-to-agent price
negotiation). It runs **entirely on in-process mocks** — no external services,
databases, or API keys are required to run, test, or demo it. The keys in
`.env.example` (Anthropic, Exa/Tavily, Vapi/Twilio, Redis, etc.) are for
future/optional real-module wiring and are not needed for any current flow.

### Environment
- Python 3.12 with a virtualenv at `.venv/` (created by the update script). Use
  `.venv/bin/python`, `.venv/bin/pytest`, `.venv/bin/uvicorn` (or activate it).
- `pyproject.toml` sets `pythonpath = ["."]`, so tests and imports resolve from
  the repo root — always run commands from `/workspace`.

### Run / test / build (all from `/workspace`; see README "Getting started")
- Tests: `.venv/bin/pytest -q`
- CLI mock pipeline: `.venv/bin/python run_demo.py` (offline; prints a moving price)
- API server (dev): `.venv/bin/uvicorn app.main:app --reload`
  - Endpoints: `GET /health`, `GET /demo` (full pipeline in one call),
    `POST /estimate`, `POST /search`, `POST /negotiate`, plus Swagger UI at `/docs`.

### Notes
- There is no linter configured and no build step (pure Python package).
- The `ui/` directory is a Next.js spec only — it is **not scaffolded** (no
  `package.json`), so there are no JS deps to install yet.
- No git hooks (pre-commit/pre-push) are configured.
