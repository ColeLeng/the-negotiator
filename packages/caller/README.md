# @negotiator/caller — Module 2

**Parallel quote gathering → a table of itemized, comparable [Quotes](../../packages/shared/src/index.ts).**

*(Cole's focus area.)*

The Caller phones the market, describes the job **identically every time** (straight from the confirmed `JobSpec`), survives real friction, and extracts an **itemized, comparable quote** from each call.

## Responsibilities
- **Build the call list** programmatically from the vertical config's `callListSource` (Google Places / Yelp) — business numbers, ratings, hours by location.
- **Fan out calls** in parallel (Batch Calling / Twilio / SIP).
- **Handle friction** — interruptions, "someone will call you back", evasive answers, multitasking dispatchers.
- **Capture structured quotes** — every call ends in an `itemized_quote`, a `callback_commitment`, or a documented `declined`. Fees itemized so quotes are comparable.
- Demonstrate against **≥3 distinct counterparty styles** (tough negotiator, stonewaller who won't price by phone, hard-sell upseller — see the vertical config).

## Two research approaches, one output
- **Phone inquiry** (non-transparent data) — the core requirement.
- **AI-search / exposed-API fan-out** — where prices *are* published, gather them as citations into the same quote store, so the buyer gets one apples-to-apples table regardless of source.

## Acceptance (from the challenge)
> Live calls against at least three distinct negotiation styles; every quote captured in structured, comparable form with fees itemized. Batch/parallel where you can; show where the call list would come from in the real world.

## Interfaces
- **Input:** `JobSpec` from the Estimator (used verbatim).
- **Output:** `Quote[]` (`@negotiator/shared`) → handed to the Closer.
