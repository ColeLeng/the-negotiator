# Challenge Brief — *The Negotiator*

**Hack-Nation 6th Global AI Hackathon · Challenge 01 · powered by ElevenLabs.**
*(Summary of the official brief, for team reference. The vertical is ours to choose; the three modules and the conversation requirement are mandatory.)*

## The pitch

Build a working end-to-end MVP of a voice-agent system that, for a vertical of your choice, **gathers real prices by phone, reports them in comparable form, and negotiates the best deal.** B2C or B2B: moving, medical bills, car buying, contractor bids, freight, equipment rental, wedding vendors — pick the market where you can prove the pain with real numbers.

## Why it matters

Phone-priced markets share three failures:
- **Opaque pricing** — the same job quotes across a 5.6× spread (moving: \$1,158–\$6,506 for one 45-mile move).
- **Unreliable estimates** — sight-unseen phone quotes are 40% more likely to end above the original bill (FMCSA).
- **No way to shop around** — the market is thousands of small operators reachable one phone call at a time; almost nobody has the hours to call 5–8 and compare.

A voice agent is the first technology that meets these markets where they are — no integration required on the other end.

## The three mandatory modules

1. **The Estimator — intake by interview or documents.** A voice interview (ElevenLabs Agents) **and** ≥1 document type (photos, quotes, bills), both producing the **same** structured job spec (e.g. JSON), confirmed by the user and reused verbatim across every call.
2. **The Caller — parallel quote gathering.** Live calls against **≥3 distinct negotiation styles**, every quote captured in structured, comparable form with fees itemized. Counterparties may be real businesses, humans role-playing, or built counter-agents. Build the call list programmatically (Google Places / Yelp).
3. **The Closer — negotiation & reporting.** ≥1 demonstrated negotiation where price/terms **change during the call** because of leverage the agent gathered; apply red-flag rules (30%+ below market = warning). Final report ranks all quotes and cites transcript evidence.

## The conversation requirement (address all four, explicitly)

- **AI disclosure** — who is the agent speaking for; handle *"am I talking to a robot?"*
- **Surviving friction** — interruptions, latency, barge-in, turn-taking.
- **The honesty line** — leverage is fine; inventing inventory / faking a bid / misrepresenting the job is not.
- **Structured call endings** — itemized quote, callback commitment, or documented decline; never a vague range.

## Success criteria

A submission fully meets the challenge when:
1. The loop is closed: intake → calls → negotiation → ranked recommendation with transcript evidence.
2. One structured job spec, built by voice + ≥1 document type, confirmed by the user, reused verbatim.
3. Live calls against ≥3 distinct negotiation styles; every quote itemized and comparable.
4. ≥1 negotiation where price/terms measurably change from leverage the agent gathered.
5. AI disclosure + honesty constraints hold; friction handled gracefully.
6. Every call ends in a structured outcome.
7. The final report ranks all quotes, cites recordings/transcripts, and explains the recommended deal in plain language.

## Strong vs weak submissions

| Strong | Weak |
|---|---|
| A real negotiation — price moves because of leverage the agent gathered. | A screenplay — two agents reading pre-written dialogue (that's TTS, not negotiation). |
| A provable pain with real numbers; comparable quotes, itemized fees. | A cool-sounding vertical with non-comparable prices hidden in a polished dashboard. |
| The closed loop beats a polished fragment. | Over-engineered agent stack, under-engineered conversations. |
| Honest about hard parts (disclosure, refusals, hang-ups). | Lets the agent bluff — invented inventory or a fake bid. |

## Data sources & hints

- **Voice/telephony:** ElevenLabs Agents Platform; Batch Calling / Twilio & SIP; Agent Tools & MCP.
- **Market discovery & pricing:** Google Places / Yelp Fusion / OSM (call list); vertical price benchmarks (FMCSA & moveBuddha for moving, FAIR Health for medical, RepairPal for auto, KBB for car buying, published rate cards for freight/equipment); document parsing via vision/OCR.
- **The other end of the line:** real calls, humans role-playing, or built counter-agents — cover several negotiation types. Record golden calls and build simple evals (does the agent extract every fee? catch the 30%-below-market red flag?).
