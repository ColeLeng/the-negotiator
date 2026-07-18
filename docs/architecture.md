# Architecture

The architecture now lives in two places:

- **[../README.md](../README.md)** — the conceptual map: the three buyer-side beats (Estimator → Caller → Buyer Agent + Orchestrator) plus the seller side.
- **[technical-architecture.md](technical-architecture.md)** — the **canonical, build-ready spec** (authored by Suman): frozen data contracts, per-owner module I/O, buyer & seller value/ZOPA models, orchestrator + shared blackboard, channels (mock/voice/UCP), honesty guard, and the hour-by-hour parallel build plan.
- **[caller-a2a-requirements.md](caller-a2a-requirements.md)** — Cole: Caller agent-to-agent path (call list, styles, itemized quotes).
- **[ella-seller-a2a-requirements.md](ella-seller-a2a-requirements.md)** — Ella: seller-agent behavioral + value-model contract for the three styles.

Start with the README, then build against the technical spec and the frozen contracts in [`../negotiator/contracts.py`](../negotiator/contracts.py).
