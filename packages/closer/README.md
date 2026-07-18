# @negotiator/closer — Module 3

**Negotiation & reporting → a ranked, evidence-cited recommendation.**

With quotes in hand, the Closer **negotiates** and then **reports**.

## Responsibilities
- **Negotiate** — leverage one real bid against another ("I have a binding quote for \$850 — can you beat it?"), push on fees, ask for price-matching or extras.
- **Apply red-flag rules** — any quote 30%+ below the vertical benchmark is surfaced as a **warning to verify**, not auto-ranked #1.
- **Rank** all quotes and pick a recommended deal.
- **Report** in plain language, with full transcripts, recordings, and itemized fee breakdowns cited for every claim.

## The honesty line (enforced)
- Only cite competing quotes that **actually exist** in the quote store with a transcript.
- Never invent inventory, fake a bid, or misrepresent the job.
- Every claim in the report links to a recording/transcript citation.

## Acceptance (from the challenge)
> At least one demonstrated negotiation where the price or terms **change during the call** because of leverage your agent gathered; the final report ranks all quotes and cites transcript evidence.

## Interfaces
- **Input:** `Quote[]` + the original `JobSpec`.
- **Output:** `NegotiationOutcome` (`@negotiator/shared`) — ranked list, recommended deal, `leverageWins` with before/after price and transcript citation.
