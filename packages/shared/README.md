# @negotiator/shared

Typed contracts every module agrees on — keep in sync with [`schemas/job-spec.schema.json`](../../schemas/job-spec.schema.json).

- **`JobSpec`** — the single contract. Estimator produces it, Caller consumes it verbatim, Closer negotiates against it.
- **`Quote` / `FeeLine` / `CallOutcome`** — what the Caller extracts from each call (itemized, comparable).
- **`NegotiationOutcome`** — the Closer's ranked, evidence-cited recommendation, including `leverageWins`.
- **`VerticalConfig`** — the "config, not code" surface loaded from [`config/verticals/`](../../config/verticals/).

See [`src/index.ts`](src/index.ts).
