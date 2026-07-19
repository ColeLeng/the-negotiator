# Hackathon submission copy — Citable Negotiator

Paste-ready text for the Hack-Nation final submission form.

**Project name:** Citable Negotiator  
**Live Project URL:** `https://github.com/ColeLeng/the-negotiator`  
**GitHub Repository URL:** `https://github.com/ColeLeng/the-negotiator`

---

## Short Description

Voice agents that call, compare, and haggle on quote-based purchases — confirm what you want once, then get a ranked deal with transcript-backed proof and a price that actually moves.

---

## 1. Problem & Challenge

A huge share of buying still happens on the phone — “call for a price.” For the same job, quotes can swing by as much as **5.6×**, and most people still take the first number they hear (~67%). High-consideration, customized purchases (weddings, movers, made-to-order goods) are opaque, stressful, and easy to overpay for — and almost nobody has time to call five shops, compare fee structures, and negotiate deliberately.

We set out to build an agent that does that work for the buyer: listen once, shop in parallel, haggle honestly, and come back with a clear recommendation plus proof.

---

## 2. Target Audience

- **Primary:** people buying high-emotion, quote-based products where prices aren’t published — starting with custom / sample / resale wedding dresses.
- **Secondary:** anyone shopping opaque phone-quote markets (movers, furniture, jewelry, B2B packaging) who wants leverage without spending hours on hold.
- **Jurors / builders:** teams exploring agent-to-agent commerce, voice agents, and honest multi-party negotiation.

---

## 3. Solution & Core Features

**Citable Negotiator** turns one buyer conversation into multi-shop negotiation:

1. **Estimator (intake)** — voice or document intake confirms a clean product spec (what you want, hard vs soft constraints, target and max price).
2. **Caller** — fans out search across real options and ranks comparable shops (BATNA seeds the next call).
3. **Orchestrator + buyer agents** — runs parallel multi-round negotiations with seller agents; price moves from real ZOPA dynamics, not a script.
4. **Honesty guard** — only cites competing quotes that actually exist; blocks invented leverage and inbound injection.
5. **Recommendation + proof** — ranked outcome with itemized quotes, transcripts, and a live price ticker so you can *see* the deal move.

Pitch line: *You talk once. It shops and haggles. It calls you back with a better deal — and proof.*

---

## 4. Unique Selling Proposition (USP)

- **A price that actually moves** during negotiation — emergent from buyer/seller private floors and concessions, not a canned script.
- **Citable / transcript-backed outcomes** — every recommendation is tied to real call proof, not a vague “best deal.”
- **Honest leverage only** — competing quotes must exist on the shared blackboard; the guard refuses fake BATNAs.
- **Config-swappable verticals** — wedding dress demo today; movers or B2B packaging via config, not a rewrite.
- **Voice-first, contract-first** — ElevenLabs intake + FastAPI/Next.js live demo on stable Pydantic contracts.

---

## 5. Implementation & Technology

- **Backend:** Python 3.12, FastAPI, asyncio parallel negotiation sessions.
- **Contracts:** Pydantic models aligned with schema.org Product / Offer (ProductSpec → RankedOptions → NegotiationSession).
- **Agents:** Estimator, Caller, Buyer/Seller agents with ZOPA / utility models; optional Claude where keys exist, full mock path without keys.
- **Voice:** ElevenLabs agent intake; seller/buyer call legs for the live demo.
- **Search:** curated bridal catalog + optional live web (Exa / Tavily / Serper / Brave).
- **Frontend:** Next.js demo with SSE live price ticker + transcript; agent event trace screen.
- **Safety:** outbound competing-quote honesty + inbound sanitize (`guard.py`).

---

## 6. Results & Impact

- End-to-end demo that shops a bridal scenario and **moves a real negotiating price** on screen.
- Parallel sessions with distinct seller styles (tough, stonewaller, upseller) and structured endings (quote, callback, or decline).
- Jury-facing story backed by market research (quote spreads, wedding premium, “take the first number” behavior).
- Open repo that runs on mocks with no API keys — judges can clone and reproduce.
- Same architecture reusable for other phone-quote markets without rebuilding the core.

---

## What was your most fun moment during the hackathon?

Recording the team intro after an all-nighter — Ella almost said the agent “hags” instead of “haggles,” Cole stopped to course-correct mid-take, then roasted his own opening (“I need to stop bullshitting in the beginning”) and we immediately did a cleaner take. Scrappy, sleep-deprived, and somehow the negotiator demo still worked the morning of submission.

---

## Additional Information (Optional)

Built for **Hack-Nation Challenge 01 — The Negotiator** (ElevenLabs), by a small team shipping Estimator, Caller, Orchestrator, seller personas, market research, and a live trace UI in parallel. Canonical architecture: `docs/technical-architecture.md`. Demo scenario + cited price bands: `docs/wedding-dress-research.md`. Product brand for submission: **Citable Negotiator**.

---

## Technologies / Tags

Add these one at a time:

- Python
- FastAPI
- Next.js
- TypeScript
- Pydantic
- ElevenLabs
- asyncio
- SSE
- Claude / Anthropic (optional)
- schema.org

## Additional Tags

- voice-agents
- agent-to-agent
- negotiation
- ZOPA
- BATNA
- e-commerce
- bridal
- hackathon
- transcript-backed
- multi-agent
