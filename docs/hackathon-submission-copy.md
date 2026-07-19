# Hackathon submission copy — Citable Negotiator

Paste-ready text for the Hack-Nation final submission form.
Core wedge (Cole): the agent learns your decision matrix, maps it into ZOPA, keeps quote context across shops, haggles the target seller, and returns the best deal with transcript proof — making negotiation nearly free in customized agentic commerce.

**Project name:** Citable Negotiator  
**Live Project URL:** `https://github.com/ColeLeng/the-negotiator`  
**GitHub Repository URL:** `https://github.com/ColeLeng/the-negotiator`

---

## Short Description

An agent that learns your decision-making matrix, maps it into a zone of possible agreement, and haggles sellers with live quote context — then returns the best deal with transcript proof so the next purchase step is obvious. Negotiation for customized products becomes nearly free; the market sets the price.

---

## 1. Problem & Challenge

Customized products don’t have a shelf price. Wedding dresses, movers, made-to-order furniture — you call, you wait, you guess. Quotes for the same job can swing **5.6×**. Most people take the first number (~**67%**). Weddings often get charged more for the same work (~**28%**).

The pain isn’t “finding options.” It’s that buyers can’t hold a coherent decision matrix across five phone calls, can’t translate preferences into a real negotiation zone, and can’t keep competing quotes alive as leverage with the shop they actually want. So the market never clears — sellers set the price, buyers absorb it.

---

## 2. Target Audience

Anyone buying a high-stakes customized product where the price only appears after a conversation — starting with bridal, then movers, furniture, jewelry, B2B packaging. If your preferences are multi-dimensional (style, timeline, budget, must-haves vs nice-to-haves) and the seller still expects you to haggle by phone, you’re the user.

---

## 3. Solution & Core Features

**Citable Negotiator** doesn’t just “call shops.” It negotiates like someone who actually knows what you value.

1. **Decision matrix → ZOPA** — It extracts what you care about (hard constraints, soft tradeoffs, target and walk-away), then translates that into a zone of possible agreement the agent can actually fight inside.
2. **Consult + haggle** — It talks to sellers with that matrix in hand: what you’ll trade, what you won’t, and when to push.
3. **Shared quote context** — Competing quotes stay alive on a shared blackboard. When it reaches your target seller, it uses real leverage from the other shops — same job, same context, better deal.
4. **Best deal + transcript proof** — It returns the recommended seller, the moved price, and citable transcripts so the next step (deposit, appointment, purchase) is grounded in evidence, not vibes.
5. **Honesty line** — It never invents a competing quote. Fake leverage is blocked. The price that moves is a real one.

Pitch: understand you → map the zone → haggle with memory → come back with proof.

---

## 4. Unique Selling Proposition (USP)

Other Track 1 demos will show an agent that talks. Ours shows an agent that **negotiates with your preferences intact**:

- **Decision matrix, not a shopping list** — multi-attribute utility (what matters, how much) drives every concession.
- **ZOPA as the operating system** — target, reservation, and seller floors turn chatter into a winnable deal.
- **Context that survives across calls** — the agent doesn’t forget Shop B’s quote when it’s on the line with Shop A.
- **Citable close** — best deal + transcript proof ready for the purchase step.
- **Money shot** — you watch a real price move under pressure from real competing quotes, not a scripted discount.

That’s the difference between a voice demo and a negotiation system.

---

## 5. Implementation & Technology

- Python + FastAPI orchestration; parallel seller sessions
- Buyer value / multi-attr utility → ZOPA bounds; seller floors + concession policies
- Shared blackboard for live BATNA / competing-quote context across shops
- Honesty guard: outbound competing-quote checks + inbound sanitize
- ElevenLabs voice legs (buyer intake + seller negotiation)
- Next.js live price ticker, transcript, and agent event trace
- End-to-end mock path with no API keys; optional live search when present
- Verticals via config (bridal today → movers / furniture / packaging without a rewrite)

---

## 6. Results & Impact

**Near-term:** a working system where the agent understands a buyer’s decision matrix, maps ZOPA, keeps quote context across shops, moves a real price with the target seller, and returns the deal with transcript proof for the next purchase step.

**Bigger bet:** this is how customized products enter agentic commerce. When negotiation is nearly free — agents consulting and haggling at scale — the market, not the first phone quote, decides the price of any made-to-order good. Opaque “call for a price” categories finally get a clearing price.

---

## What was your most fun moment during the hackathon?

Recording the team intro after an all-nighter — Ella almost said the agent “hags” instead of “haggles,” Cole stopped mid-take to fix it, then roasted his own opening (“I need to stop bullshitting in the beginning”) and we immediately did a cleaner take. Scrappy, sleep-deprived, and somehow the price still moved the morning of submission.

---

## Additional Information (Optional)

Challenge track: Hack-Nation Challenge 01 — The Negotiator (ElevenLabs). Product name: **Citable Negotiator**. Pitch spine: decision matrix → ZOPA → contextual haggle → citable deal → customized agentic commerce. See `docs/final-deliverable-proposal.md`, `docs/technical-architecture.md`, `docs/wedding-dress-research.md`.

---

## Technologies / Tags

- Python
- FastAPI
- Next.js
- ElevenLabs
- TypeScript
- Pydantic

## Additional Tags

- agentic-commerce
- negotiation
- ZOPA
- decision-matrix
- transcript-backed
- customized-products
- voice-agents
- multi-agent
