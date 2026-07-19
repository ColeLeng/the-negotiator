# Final Deliverable Design Proposal

**Owner:** Cole (pitch lead) · **Audience:** team · **Goal:** win Hack-Nation on Technical depth · Communication · Innovation — for a jury scanning **50+ projects in ~1 hour**

This is the submission package design. Platform hard rule from the upload UI:

| Video | Max length | Job |
|---|---|---|
| **Demo** | **60 sec** | User experience / product flow — how it *feels* to use |
| **Tech** | **60 sec** | How we built it — stack, architecture, implementation |
| **Team** | **60 sec** | Who built it and who did what |

**Formats:** MP4 or MOV.  
**Market numbers:** only from Jagger’s deck or the challenge brief — don’t invent new ones.

---

## 1. Jury rule: plain words, one job per video

Jurors are tired. If they need a glossary, we already lost.

| Say this (jury) | Keep in Tech / docs only |
|---|---|
| You tell the agent what you want | Purchase Intent / `ProductSpec` |
| It calls several sellers for you | Caller / Orchestrator / parallel sessions |
| The price actually comes down | ZOPA / dual floors / concession |
| It only uses real competing quotes | blackboard / BATNA / honesty guard |
| You get a clear pick with proof | transcript-backed recommendation |
| Same idea works for other custom stuff later | config-swappable vertical |

**North-star line (memorize):**

> You talk once. It shops and haggles. It calls you back with a better deal — and proof.

---

## 2. Yes — separate Demo and Tech (and keep them separate)

The site already forces three uploads. Use that:

| Video | Audience feeling after 60s | Do **not** put here |
|---|---|---|
| **Demo** | “I get it — I’d use this.” Smooth human ↔ agent conversation. | Architecture diagrams, JSON, jargon |
| **Tech** | “That’s real engineering, not a script.” Why the price moves; honesty; parallel work. | Long market TED talk; full conversation replay |
| **Team** | “Credible people, clear roles.” | Feature tour |

**Where does dual-screen go?**  
Not as the hero of Demo. In **60 seconds**, dual-screen fights the thing that matters most: **smooth, real-feeling talk with the agent**.

- **Demo hero:** the phone loop — you ↔ agent (many turns) → agent works → agent calls you back with a result + proof.  
- **Optional 3–5s flash** in Demo: tiny picture-in-picture of “calling 3 sellers…” while hold music / “give me a minute.”  
- **Tech hero:** the split / cockpit — parallel sellers, price moving, “we don’t invent competing quotes.”

---

## 3. Narrative spine (impact, not jargon)

Same story everywhere. Short sentences.

1. **A lot of buying still happens on the phone** — “call for a price,” not a clean checkout button.
2. **For the same job, quotes can differ by up to ~5.6×.** Most people take the first number (~67%). Weddings often get charged more for the same work (~28% “wedding tax”).
3. **Nobody has time to call five shops and compare.** An agent does.
4. **We start with custom bridal** (hard, emotional, opaque prices) — same engine can later cover other custom buys.
5. **What we prove in 60s:** a natural conversation, a price that moves, a clear answer with proof.

**Avoid on camera:** ZOPA, BATNA, blackboard, ProductSpec, UCP, “agentic commerce,” “protocol,” “DMU,” “rent-seeking,” “fairer for both.”

---

## 4. Project Summary — 150–300 words (plain)

**Write last**, after Demo is cut. Structure:

1. Pain (1 number).  
2. What you do with the product (as a user).  
3. What happens while you wait.  
4. What you get back.  
5. Why bridal first.  
6. What the Demo shows.

**Draft (~180 words):**

> A lot of buying still happens on the phone — “call for a price.” For the same job, quotes can swing by as much as 5.6×, and most people still take the first number they hear. The Negotiator is a voice agent that shops those markets for you. You tell it what you want (by voice or from a document). It confirms the details, calls multiple sellers, compares real quotes, and negotiates — then calls you back with a clear recommendation and the proof behind it. We start with custom wedding dresses: high emotion, hidden prices, no time to haggle. In the demo you’ll hear a real back-and-forth with the agent, see a price move during negotiation, and see the final pick with transcript evidence. The same setup can later cover other custom purchases — furniture, jewelry, and more — without rebuilding the core.

---

## 5. Demo Video (max 60s) — *the conversation is the product*

**Job:** UI/UX + product flow. Jury should feel: *this agent listens, remembers what I care about, and comes back with something solid.*

**Hero format:** one continuous **user journey on a phone / simple screen** — not a dashboard tour, not a dual-screen architecture reel.

### The loop to show (this is the innovation)

```text
YOU call the agent  →  multi-round talk (intent, budget, must-haves)
        ↓
AGENT: “Got it — I’ll shop this. I’ll call you back.”
        ↓
(short bridge: “Calling 3 boutiques…” — optional tiny PIP of work)
        ↓
AGENT calls YOU back  →  plain-language result + proof
        (“Best option: Boutique X at $1,850 — down from $2,200.
          Here’s why, and I can play the quote.”)
```

Human can read a script. **The agent must sound smooth:** understands corrections, repeats back what matters, doesn’t ask the same thing twice, and returns a crisp result with evidence.

### 60-second beat sheet

| Time | On screen / audio | VO (optional — prefer diegetic call audio) |
|---|---|---|
| 0–5s | Title card: “You talk once. It shops. It calls you back.” | One pain line: “Same dress shopping — quotes all over the place.” |
| 5–28s | **Call 1 — you ↔ agent.** 3–5 natural turns: what you want, size/date, budget, one correction (“not champagne — ivory”). Agent confirms in one short recap. | None / light |
| 28–36s | Bridge: agent says it’s going to call sellers. Tiny PIP or caption: “Calling 3 sellers…” | — |
| 36–52s | **Call 2 — agent ↔ you.** Result: best pick, **price that moved** ($2,200 → $1,850), one proof line (“I used a real competing quote — here’s the note”). Show simple result card, not a dense table. | — |
| 52–60s | End card: product name + GitHub | “Honest quotes only. Proof included.” |

### Must land in 60s

1. Multi-round **smooth** intake (understanding + confirm).  
2. Clear handoff (“I’ll call them / I’ll call you back”).  
3. Callback with **solid result** + **proof** (price move or transcript snippet).  
4. Feels like a product someone would actually answer the phone for.

### Cut lines (Demo)

| Tier | What we ship |
|---|---|
| **Gold** | Live (or recorded-live) voice both legs; agent handles a correction mid-call; callback cites a real session price move |
| **Silver** | Rehearsed scripted human + strong agent voice; same scenario; callback card driven by real demo run |
| **Bronze** | Strong callback + result UI; shorter intake; still audible agent |

**Do not** spend Demo time on JSON, architecture, or three full seller transcripts. That’s Tech.

**Recording notes:** 1080p/1440p 16:9; captions for the price drop; silence phone UI chrome; 2–3 takes focusing on *smooth agent*, not perfect human acting.

---

## 6. Tech Video (max 60s) — *why it’s not a screenplay*

**Job:** Technical explanation. Jury that leans in should see depth fast.

### 60-second beat sheet

| Time | Content (plain labels on screen) |
|---|---|
| 0–8s | “Under the hood — while you’re waiting” |
| 8–22s | Simple 3-box diagram: **Listen → Find sellers → Negotiate** (not module codenames) |
| 22–40s | **Split or cockpit:** 2–3 sellers at once; one price ticks down; caption “Price moves because both sides have real limits — not a script” |
| 40–52s | Honesty beat: “Competing quotes must be real — we block fake ones” (flash guard / test or UI warning) |
| 52–60s | “Voice on the phone. Structured details underneath. Same engine, other custom markets later.” + GitHub |

**Optional one-liner (only if it fits):** “We’re also sketching a simple open format so your agent and a shop’s agent can speak the same language later.” — no protocol deep dive.

**Jargon on Tech screen is OK in small captions** if spoken line stays plain.

---

## 7. Team Video (max 60s)

| Time | Content |
|---|---|
| 0–8s | Team name + “We built The Negotiator” |
| 8–50s | Faces: name + one plain role each (≈8–10s each if four people, or faster cuts) |
| 50–60s | “Honest shopping agents for markets that still price by phone.” + GitHub |

| Person | Plain role line |
|---|---|
| Cole | Pitch, shopping/search, fairness checks, demo UI |
| Suman | The engine that runs many seller talks at once |
| Ella | The seller side — how shops push back and concede |
| Jagger | Intake + market story (why bridal / phone pricing) |

---

## 8. GitHub · Zip · Dataset

- **GitHub:** README opens with the north-star line + a callback screenshot; zero-key `run_demo.py`; pin SHA.  
- **Zip:** `git archive` of that SHA.  
- **Dataset:** **N/A** unless a licensed table exists.

---

## 9. What “smooth agent” means (Demo quality bar)

Before you call the Demo done, the intake leg should pass this checklist on video:

- [ ] Agent restates must-haves in plain language once.  
- [ ] Handles **one correction** without restarting the whole interview.  
- [ ] Asks only missing must-haves / budget — not a laundry list.  
- [ ] Ends intake with a clear next step (“I’ll call shops and call you back”).  
- [ ] Callback leads with **recommendation + price**, then one proof detail — not a dump of logs.  
- [ ] Tone: calm, short turns, no buzzwords.

Engineering truth behind that smoothness can stay in Tech/README.

---

## 10. Intent & “open format” — keep it light for jury

Still true, still important — **not** Demo VO.

- What the user said → one confirmed list of needs + budget (reusable across every seller call).  
- Later: a simple open format so **your** agent and a **shop’s** agent can exchange that list and offers without reinventing phone scripts.  
- Merchants keep their costs/limits private; your agent keeps your true max private; only agreed offers and allowed details cross.

**Where it lives:** 1 sentence in Summary *optional*; ~5s in Tech; full writeup for teammates in older § notes / architecture docs — not the 60s Demo.

---

## 11. Mapping challenge “done” → 60s videos

| Challenge need | Demo | Tech |
|---|---|---|
| Closed loop | You → agent → shops → you | Diagram Listen → Find → Negotiate |
| One confirmed job spec | Recap in Call 1 | “Same details sent to every seller” |
| ≥3 seller styles | Bridge “3 sellers” / result compares | Cockpit with labels |
| Price moves from real leverage | Callback number + caption | Ticker + “real limits / real competing quote” |
| Honesty + disclosure | Agent says it’s AI on the call | Guard beat |
| Ranked result + proof | Callback card + “here’s the proof” | Transcript flash |

---

## 12. Cole RACI & shoot order

| Piece | Cole | Others |
|---|---|---|
| Demo (conversation) | Direct, edit, upload QA | Jagger: intake script; Suman: voice smoothness; Ella: callback numbers match a real run |
| Tech | Edit | Suman/Ella: cockpit + honesty beat accuracy |
| Team | Produce | Everyone: face + one line |
| Summary | Write from final Demo | Jagger: number check |

**Order:** freeze one bridal scenario → nail **smooth Call 1 + Call 2** → shoot Demo → shoot Tech (reuse 5s of work footage) → Team → Summary → zip/GitHub → upload.

---

## 13. Emphasize vs cut

**Emphasize:** natural talk · callback with proof · price move · “I’m an AI, calling for a customer” · bridal pain with one number.  
**Cut from Demo:** dual-screen architecture, protocols, module names, long market decks.  
**Cut from Tech:** replaying the whole conversation.

---

## 14. Submission-ready checklist

- [ ] Demo ≤60s: smooth multi-round intake + callback with result/proof + price move  
- [ ] Tech ≤60s: simple 3-step diagram + parallel negotiate + honesty  
- [ ] Team ≤60s: faces + roles  
- [ ] Summary 150–300 words, plain English, claim-locked to Demo  
- [ ] GitHub + zip same SHA; Dataset N/A  

---

## 15. Team Slack copy (ready to paste)

```text
@channel Demo/Tech lock — important (60s max each on the site)

Upload UI: Demo / Tech / Team are THREE separate videos, **max 60 seconds each** (MP4/MOV).

How we’re splitting them (please align):
1) DEMO = the product feeling. Not dual-screen architecture.
   Flow: You call agent (multi-round, smooth) → agent shops → agent calls you BACK with a clear pick + proof (price moved).
   Human can read a script. Agent must sound real: understands corrections, short confirmations, solid callback.
2) TECH = why it’s not a screenplay (60s). Simple “Listen → Find sellers → Negotiate”, parallel sellers, price tick, “we only use real competing quotes.”
3) TEAM = faces + one plain role each.

Jury constraint: they see 50+ projects in ~1 hour. No ZOPA/BATNA/ProductSpec/protocol talk in Demo or Summary. Plain English only.

Doc updated: docs/final-deliverable-proposal.md

Who:
• @Cole — Demo edit + Summary
• @Suman — voice smoothness / engine for Tech cockpit
• @Ella — seller side numbers match callback
• @Jagger — intake script + one pain number (deck-true)
• @Kazi — stay out of Demo VO; utility detail only if Tech needs a caption

Reply if Gold voice callback isn’t ready — we’ll lock Silver tonight.
```

---

## 16. Answer to the open questions (short)

**Separate Demo and Tech?**  
Yes — required, and correct. Demo = “I’d use this.” Tech = “It’s real.”

**Is dual-screen the Demo?**  
No as the main story. Dual-screen/cockpit is **Tech** (and optional 3–5s PIP in Demo). Demo’s innovation is the **smooth two-call user loop** with a proof-backed callback.

**What must feel “real”?**  
Intake that understands intent and values; callback that returns a clear deal with proof — not a jargon dump.

---

*Cole owns the pitch package. If a juror only watches Demo, they should still get the whole product.*
