# @negotiator/seller-agent — the other end of the line

*(Ella's focus.)*

The **counterparty** — vendor/seller agents that take the Caller's calls and hold the line against the Closer. This is what makes the negotiation real instead of a screenplay; the challenge explicitly allows building counter-agents.

## Responsibilities
- Answer inbound calls describing the customer's job; respond with quotes.
- Implement the **≥3 counterparty styles** from the vertical config:
  - **tough negotiator** — holds price, tests whether the buyer is serious;
  - **stonewaller** — won't give prices by phone (forces a range or a firm callback);
  - **hard-sell upseller** — bundles fees the Closer must itemize and strip.
- Run **agent-to-agent** (simulated market) with the buyer's Caller/Closer, sharing negotiation context so a price can move.
- Explore **UCP (Universal Commerce Protocol)** as the buyer-agent ↔ seller-agent negotiation channel — the reusable, Citable-relevant bet underneath the voice layer.

## The honesty line (both ends)
The seller may be evasive or upsell, but concessions must come from **real** leverage — no scripted price drops. The demo must show a real price change during a call.

## Interfaces
- **Input:** the `JobSpec` as described by the Caller + a `CounterpartyStyle`.
- **Output:** a `Quote`-shaped offer the Caller records; concessions during negotiation with the Closer.

See [`src/index.ts`](src/index.ts).
