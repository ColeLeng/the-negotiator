# Hackathon submission copy — Citable Negotiator

Paste-ready text for the Hack-Nation final submission form.
Tone follows `docs/final-deliverable-proposal.md`: plain language, one sharp wedge, no architecture dump in jury-facing fields.

**Project name:** Citable Negotiator  
**Live Project URL:** `https://github.com/ColeLeng/the-negotiator`  
**GitHub Repository URL:** `https://github.com/ColeLeng/the-negotiator`

**One line (memorize):** You talk once. It shops and haggles. It calls you back with a better deal — and proof.

---

## Short Description

You talk once. It shops and haggles. It calls you back with a better deal — and proof. A phone agent for “call for a price” markets that moves a real number on the call, only uses real competing quotes, and returns the pick with the transcripts behind it.

---

## 1. Problem & Challenge

A lot of buying still happens on the phone — “call for a price.” For the same job, quotes can swing by as much as **5.6×**. Most people still take the first number (~**67%**). Weddings often get charged more for the same work (~**28%**).

The only defense is calling five shops, comparing messy fee structures, and negotiating — and almost nobody does that. Other demos in this track will show an agent that *talks*. The hard problem is an agent that **actually moves a price**, never invents leverage, and can show **why** the deal is the deal.

---

## 2. Target Audience

Brides (and anyone else) stuck in opaque, phone-quote markets: custom dresses, movers, furniture, jewelry — high stakes, hidden prices, no time to haggle. If you’ve ever taken the first quote because calling five more shops felt impossible, you’re the user.

---

## 3. Solution & Core Features

**Citable Negotiator** is a phone agent that shops those markets for you — then proves it.

1. You tell it what you want (voice or a document). It confirms the details in plain words.
2. It calls several shops at once — including a real seller on the line, not just chat.
3. On the call, the **price comes down** because of a real competing quote, not a scripted discount.
4. It only uses quotes the buyer actually has. Made-up deals get blocked.
5. It calls you back with the best pick, the new price, and the **proof** (transcripts / cited quotes).

What you’ll see in 60 seconds: natural talk → a number that moves → a clear answer with proof.

---

## 4. Unique Selling Proposition (USP)

Most Track 1 projects will demo an agent that negotiates. Ours has to survive three jury tests:

1. **Is the price fake?** — You watch it move live during the call (the money shot).
2. **Is the leverage fake?** — It only cites real competing quotes. Fake ones are refused.
3. **Can I trust the answer?** — The recommendation comes with proof from the calls — that’s why it’s *Citable*.

Also: two real voice legs (buyer↔agent and agent↔seller), three seller styles (tough / won’t-quote / upseller), and a live trace so you can see the agent think — not actors reading a script.

---

## 5. Implementation & Technology

Built so the demo is reproducible, not a one-off video:

- Python + FastAPI orchestration; parallel shop sessions
- Voice on both legs via ElevenLabs (buyer intake + seller negotiation)
- Honesty guard on outbound competing quotes + inbound sanitize
- Shared blackboard so leverage is only real BATNAs
- Next.js live price ticker + transcript; agent event trace screen
- Runs end-to-end on mocks with no API keys; optional live search when keys exist
- Same core later for furniture, jewelry, movers — config swap, not a rewrite

---

## 6. Results & Impact

- A demo where a **real negotiating price moves** on screen / on the call
- Structured endings every time: itemized quote, callback commitment, or documented decline — never a vague range
- Three seller styles covered in one scenario set (deal / callback / itemize the upsell)
- Open repo judges can clone and run without keys
- Jury story anchored in market numbers (5.6× spread, ~67% take the first quote, ~28% wedding premium) — not vibes

---

## What was your most fun moment during the hackathon?

Recording the team intro after an all-nighter — Ella almost said the agent “hags” instead of “haggles,” Cole stopped mid-take to fix it, then roasted his own opening (“I need to stop bullshitting in the beginning”) and we immediately did a cleaner take. Scrappy, sleep-deprived, and somehow the price still moved the morning of submission.

---

## Additional Information (Optional)

Challenge track: Hack-Nation Challenge 01 — The Negotiator (ElevenLabs). Product name for submission: **Citable Negotiator**. Pitch doc we wrote against: `docs/final-deliverable-proposal.md`. Architecture: `docs/technical-architecture.md`. Bridal scenario + cited price bands: `docs/wedding-dress-research.md`.

---

## Technologies / Tags

- Python
- FastAPI
- Next.js
- ElevenLabs
- TypeScript
- Pydantic

## Additional Tags

- voice-agents
- negotiation
- honest-leverage
- transcript-backed
- price-discovery
- bridal
- e-commerce
- multi-agent
