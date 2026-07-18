# Architecture

The Negotiator is three buyer-side agents chained by a single shared contract — the **Structured Job Spec** — negotiating against a **seller-side counterparty agent** on the other end of the line. Build the spec once, confirm it with the user, and reuse it *verbatim* on every call so every quote is for the exact same job. The buyer and seller agents ideally negotiate **agent-to-agent over UCP (Universal Commerce Protocol)**; voice (ElevenLabs) is the required layer on top, not the point.

```
  Buyer
    │  voice interview  +  documents (photos, quotes, bills)
    ▼
┌─────────────────┐
│  1 · ESTIMATOR  │  intake → structured job spec (confirmed by user)
└─────────────────┘
    │  JobSpec (schemas/job-spec.schema.json)
    ▼
┌─────────────────┐   call list: Google Places / Yelp           ┌───────────────────────────┐
│  2 · CALLER     │   parallel calls: Batch / Twilio / SIP  ──▶  │  SELLER-SIDE AGENT        │
└─────────────────┘   ≥3 counterparty styles                     │  (the other end of the    │
    │  Quote[]  (itemized, comparable, fee-broken-down)          │   line)                   │
    ▼                                                            │  tough · stonewaller ·    │
┌─────────────────┐                                              │  upseller                 │
│  3 · CLOSER     │  ◀── agent-to-agent negotiation · UCP ────▶  │                           │
└─────────────────┘  negotiate (leverage bids, push fees)        └───────────────────────────┘
    │  NegotiationOutcome + ranked report + transcript citations
    ▼
  Recommended deal (plain language)
```

## The contract: Structured Job Spec

- Defined in [`../schemas/job-spec.schema.json`](../schemas/job-spec.schema.json); typed in [`../packages/shared`](../packages/shared).
- A **common envelope** (buyer, budget/ZOPA, timeline, negotiation levers, red-flags) + a **vertical-specific `spec`** whose fields are declared by the vertical config.
- Two producers (voice, documents) → **one identical schema**. The user confirms it before any call.
- One consumer contract: the Caller reads it to describe the job identically every time; the Closer reads it to know the walk-away and levers.

## The other end of the line — the seller-side agent

The counterparty is a first-class part of the system, not a script. Seller/vendor agents answer the Caller's calls and hold the line against the Closer, each configured to a **counterparty style** from the vertical config:
- **tough negotiator** — holds price, tests whether the buyer is serious;
- **stonewaller** — won't give prices by phone (extract a range or a firm callback);
- **hard-sell upseller** — bundles fees the Closer must itemize and strip.

Running the buyer agents **against** these seller agents — sharing negotiation context so a price can actually move — is what separates a real negotiation from a text-to-speech screenplay. The endgame bet: buyer-agent ↔ seller-agent negotiation over **UCP (Universal Commerce Protocol)**. Voice (ElevenLabs) is the required top layer; the negotiation/decision logic underneath is the reusable, Citable-relevant asset. See [`../packages/seller-agent`](../packages/seller-agent).

## Vertical config, not code

`config/verticals/<vertical>.json` carries everything that differs between markets:

| Field | Purpose |
|---|---|
| `specFields` | The shape of the vertical-specific `spec` (what the Estimator collects). |
| `priceBenchmark` | Ground truth for red-flag detection (median / p25 / p75). |
| `redFlags` | Rules like *"30%+ below market → warn."* |
| `negotiationLevers` | What the Closer is allowed to push (competing quote, bundle, cash, off-season…). |
| `callListSource` | How the Caller builds its list (provider + query + filters). |
| `counterpartyStyles` | The negotiation styles to simulate/expect. |
| `disclosure` | The AI-disclosure line the agent opens with. |

Swapping `wedding-dress.json` for `moving.json` re-points the whole system at a new market — **no agent code changes.**

## The conversation requirement

Voice is the mechanism of trust on both ends of the call. The prototype addresses four points explicitly, and the demo plays real call audio for each:

1. **Who is the agent speaking for?** Opens with the vertical's `disclosure` line — an AI calling on behalf of a customer. When asked *"am I talking to a robot?"* it confirms honestly and keeps the conversation on track. It never pretends to be human.
2. **Surviving friction.** Busy dispatchers interrupt, answer vaguely, and multitask. We tune latency, barge-in, and turn-taking so the call sounds like a serious buyer, not a bot. Vague answers get a follow-up; "we'll call you back" becomes a logged callback commitment.
3. **The honesty line.** Leverage is allowed — *"I have a binding quote for \$850"* — **only when the quote is real**. The agent is constrained (prompt + tool-level checks) to never invent inventory, fake a competing bid, or misrepresent the job. If it has no real leverage, it doesn't manufacture any.
4. **How every call ends.** Every call terminates in a **structured outcome**: an itemized quote, a callback commitment, or a documented decline. No vague "around two thousand" ever enters the comparison.

## Honesty constraints (enforced, not aspirational)

- The Closer may only cite a competing quote that exists in the quote store with a transcript.
- No `spec` field is ever fabricated; missing info is asked for or left null, never invented.
- Red-flag rule: a quote 30%+ below the vertical benchmark is surfaced as a **risk to verify**, not auto-ranked #1.
- Every claim in the final report links to a recording/transcript citation.

## Data flow summary

| Stage | Input | Output | Key services |
|---|---|---|---|
| Estimator | voice + documents | `JobSpec` (confirmed) | ElevenLabs Agents, vision/OCR |
| Caller | `JobSpec` + vertical config | `Quote[]` | Google Places/Yelp, Batch/Twilio/SIP, Agent Tools/MCP |
| Closer | `Quote[]` + `JobSpec` | `NegotiationOutcome` + ranked report | ElevenLabs Agents, benchmark lookup |
| Seller-side agent | `JobSpec` as described on the call + counterparty style | quote + concessions (agent-to-agent) | ElevenLabs Agents, UCP (target) |
