# Final Deliverable Design Proposal

**Owner:** Cole (pitch lead) · **For:** the team · **Goal:** clear Hack-Nation submission a tired jury can get in under a minute

Jurors look at **50+ projects in about an hour**. If they have to decode our words, we lose.

---

## Hard rules from the upload site

| Video | Max | Job in one line |
|---|---|---|
| **Demo** | 60 sec | Show how it feels to use |
| **Tech** | 60 sec | Show how it works under the hood |
| **Team** | 60 sec | Show who built it |

Files: MP4 or MOV.  
Numbers: only from Jagger’s market deck or the official challenge brief.

---

## Current scope of work (who builds what)

Latest split — this drives the videos below.

| # | Piece | Owner | What it is (plain) |
|---|---|---|---|
| 1 | **Buyer call** | real person (scripted) | A real person talks to our agent about the dress they want |
| 2 | **Seller call** | real person answering | A real seller picks up a call from our agent and gets negotiated with |
| 3 | **Trace screen** | **Jagger** | A live view of what the agent is doing — shown as a right-side screen |
| 4 | **Negotiator engine** | **Suman** | The part that actually runs the back-and-forth (the orchestrator) |
| 5 | **Estimator (intake)** | **Cole** | Turns the buyer’s call into the clean list of what they want |
| 6 | **Seller data** | **Ella** | Simulated seller info (prices, limits, styles) so the calls have real numbers to work with |

**Two real voice legs now** (buyer↔agent and agent↔seller) — that is a big upgrade from mocks and should be front and center.

**Logistics:** **Cole provides the ElevenLabs credits** for the voice legs. Confirm the credits are loaded and shared before shoot day, so both the buyer intake and the seller call can run on real voice.

### Who plays whom on camera (acting, not building)

| Voice on the call | Played by |
|---|---|
| **Buyer** (the customer) | **Ella** — reads the buyer script to our agent |
| **Seller** (the shops) | **Cole** — voices the three seller styles (using Ella’s seller data) |
| **The agent** | ElevenLabs voice — the automated leg on both calls |

So each real call is **one human + our agent**, never two humans talking. That keeps it honest: the agent really is doing the talking on our side.

---

## The whole pitch in one line

> You talk once. It shops and haggles. It calls you back with a better deal — and proof.

Memorize that. Every video and the written summary should support that line.

---

## Plain language only (no exceptions in jury-facing text)

Use everyday words in the **Demo**, **Team**, **Project Summary**, and Slack.

| Instead of sounding clever | Say |
|---|---|
| Complex agent systems | A phone agent that shops for you |
| Structured product object | The details you confirmed |
| Parallel negotiation sessions | It calls several shops at once |
| Price discovery / concession | The price came down |
| Honest leverage | It only uses real competing quotes — no made-up deals |
| Transcript-backed recommendation | Here’s the best pick, and here’s the proof |
| Config-swappable vertical | Same idea later for furniture, jewelry, etc. |

If a word would need a footnote, don’t use it on camera.

---

## Three videos = three jobs (keep them separate)

| Video | After 60 seconds the juror should think | Put this here | Leave this out |
|---|---|---|---|
| **Demo** | “I’d use this.” | Real-feeling phone talk with the agent | Diagrams, code, jargon |
| **Tech** | “This isn’t a fake script.” | Several shops at once, price moving, no fake quotes | Replaying the whole customer call |
| **Team** | “Solid people.” | Faces + who did what | Feature tour |

**The trace screen (Jagger) = right screen in Tech.** It shows *how the agent works* while it negotiates — perfect for “this is real, not a script.” Keep it out of the Demo hero; the Demo is about the people on the phone. A tiny 3–5 second peek of the trace or “calling the shop…” is the most the Demo should show.

---

## Story we tell (same everywhere)

1. A lot of buying still happens on the phone — “call for a price.”
2. Same job can get wildly different quotes (up to about **5.6×**). Most people take the first number (~**67%**). Weddings often get charged more for the same work (~**28%**).
3. Nobody has time to call five shops. An agent does.
4. We start with **custom wedding dresses** — stressful, hidden prices, easy to overpay.
5. In 60 seconds we prove: natural talk → price that moves → clear answer with proof.

---

## Three negotiations to design (Cole voices all three)

The challenge wants **at least three different seller styles**. Cole plays all three (short, separate calls). Each one proves a different success-criteria bullet, so together they cover a lot.

| # | Seller style | How Cole plays it | What the agent must do | Proves |
|---|---|---|---|---|
| 1 | **Tough but fair** | Holds firm, pushes a deposit, but will deal | Bring up a **real competing quote** → price comes down | **Price moves during the call** (the money shot) |
| 2 | **Won’t quote by phone** | “We only give prices at an in-store appointment.” | Politely push → get a **firm callback / a price range** instead of a vague brush-off | **Every call ends with a real outcome** (a callback commitment) |
| 3 | **Upseller** | Piles on rush fees, veil, alterations to inflate the total | **Itemize** every fee and strip the non-essentials | **Quotes are itemized and comparable** |

Also work into one of the calls (probably #1):

- Agent **says it’s an AI** up front, and again if asked “are you a robot?”
- Agent handles a little **friction** — an interruption or a “we’re busy, call back.”
- Agent **never invents** a competing quote — it only uses one the buyer really has.

That single set of three calls covers: 3 styles · price moves · honesty + disclosure · friction · structured endings · itemized quotes.

---

## Project Summary (150–300 words) — paste candidate

Write this **after** the Demo is final so it matches the video.

> A lot of buying still happens on the phone — “call for a price.” For the same job, quotes can swing by as much as 5.6×, and most people still take the first number they hear. Citable Negotiator is a voice agent that shops those markets for you. You tell it what you want (by voice or from a document). It confirms the details, calls multiple sellers, compares real quotes, and negotiates — then calls you back with a clear recommendation and the proof behind it. We start with custom wedding dresses: high emotion, hidden prices, no time to haggle. In the demo you’ll hear a real back-and-forth with the agent, see a price move during negotiation, and see the final pick with proof from the calls. The same setup can later cover other custom purchases — furniture, jewelry, and more — without rebuilding the core.

---

## Demo video (max 60 sec)

**Goal:** Juror feels the agent *listens*, *gets it*, and *comes back with something solid*.

Now that we have **real voice on both ends**, the Demo should feel like eavesdropping on two real phone calls.

### What to show

```text
1) BUYER (real person) calls the agent        ← Cole’s intake
   → a few natural turns (what you want, size/date, budget)
   → corrects one detail (“ivory, not champagne”)
   → agent repeats the plan back in one short line

2) Agent: “Got it. I’ll call a shop and call you back.”

3) AGENT calls a real SELLER                   ← real seller answers
   → short, real haggle; the price comes down

4) Agent reports BACK to the buyer
   → “Best option: Boutique X at $1,850 — down from $2,200.”
   → one proof line (“Here’s the quote I used.”)
```

Both people can read from a script. **The agent must sound smooth** on both calls — understands, doesn’t repeat itself, and closes with a clear result.

### Rough timing

| Time | What happens |
|---|---|
| 0–5s | Title: “You talk once. It shops. It calls you back.” |
| 5–24s | Buyer ↔ agent (intake, one correction, recap) |
| 24–30s | “Calling the shop…” |
| 30–48s | Agent ↔ real seller — the price comes down |
| 48–56s | Agent reports back: best pick + price drop + proof |
| 56–60s | Name + GitHub |

### Demo quality checklist

- [ ] Agent restates what the buyer needs in plain words  
- [ ] Handles one correction cleanly  
- [ ] Real seller call actually moves the price  
- [ ] Report-back leads with **best pick + price**, then one proof detail  
- [ ] No buzzwords  

**Best case:** real voice on both calls (buyer↔agent and agent↔seller) — we have this now.  
**Fine:** real buyer↔agent + a recorded real seller call edited in.

---

## Tech video (max 60 sec)

**Goal:** Show it’s real work, not actors reading a script.

| Time | What to show |
|---|---|
| 0–8s | “While the agent is on the call — here’s what it’s doing” |
| 8–22s | Three simple boxes: **Listen → Find shops → Negotiate** |
| 22–42s | **Jagger’s trace screen (right side)** running next to the real seller call: watch the agent think, pull up a competing quote, and push the price down |
| 42–52s | “It only uses real competing quotes. Fake ones get blocked.” |
| 52–60s | “Phone for people. Clear details underneath. Other custom markets later.” + GitHub |

The **trace screen is the Tech hero** — the real seller call plays on the left, the agent’s live trace on the right. That is the “right screen showing how agents interact” Jagger is building.

---

## Team video (max 60 sec)

| Time | What |
|---|---|
| 0–8s | “We built Citable Negotiator” |
| 8–50s | Each person: name + one plain job |
| 50–60s | “Shopping agents for markets that still price by phone.” + GitHub |

| Who | Say |
|---|---|
| Cole | Pitch + the first call: turning what you say into a clear plan (intake) |
| Suman | The engine that runs the negotiation |
| Jagger | The live screen that shows how the agent works + why this market |
| Ella | The seller data — realistic shop prices and how they haggle |

---

## GitHub, zip, dataset

- **GitHub:** open with the one-line pitch + a screenshot of the callback result; demo runs without API keys.  
- **Zip:** same commit as the public repo.  
- **Dataset:** put **N/A** unless we have a clearly licensed data file.

---

## How to record a “calling” demo when we’re all on Zoom

**Do not film the Zoom window.** Zoom is only for coordinating. Zoom compresses audio, shows tiles, and looks like a meeting — the opposite of a phone call. Instead, capture each call natively and edit them together.

### The core idea

Each real call is **one person + our ElevenLabs agent**, not two people on Zoom. So the person on that call just talks to the agent from their own computer/phone, and **records their own leg locally**. Cole edits the clips together afterward.

### “But if we record separately, how do the calls connect?”

Two different things — don’t mix them up:

- **The conversations are connected** — through our agent/software, live. The buyer and seller **never talk to each other**; the agent sits in the middle on both calls. That middle is the whole product.
- **“Recording separately”** just means each person captures *their own leg* cleanly, instead of filming a grid of Zoom faces.

**What actually links the two calls = one shared scenario the agent carries:**

```text
Ella (buyer) ── talks to ──▶ AGENT
                              │  writes down the confirmed dress details
                              ▼
                        [ shared scenario ]   ← one frozen file: dress details,
                              │                  buyer’s target + max, seller’s
                              │                  limits/style (Ella’s seller data)
                              ▼
AGENT ── calls with those exact details ──▶ Cole (seller)
                              │  negotiates; price moves
                              ▼
                        report back to buyer  (cites both real transcripts)
```

The buyer’s confirmed details flow **into** the seller call. Cole’s seller behaves according to the **same scenario’s** hidden limits. So even recorded on different laptops, the two calls are the same story — because they share one scenario and the agent passes the state from one to the next.

**Two ways to run it:**

| Way | How | When |
|---|---|---|
| **Live chain (best)** | Do it in one sequence: Ella’s intake finishes → the system calls Cole right away → report. You *can* all be on Zoom to **cue timing** (muted, not recorded) — just record each leg locally. | If the pipeline runs end-to-end |
| **Staged (safe)** | Record the legs at different times, but lock the **same scenario numbers** for all of them, then edit into one story. | If live-chaining is flaky on shoot day |

Either way the numbers line up, because the single frozen scenario is the source of truth. Zoom, if used at all, is just a green room for cueing — never the footage.

### What ElevenLabs does vs. what we build (don’t overclaim)

Be precise so the demo stays honest:

- **ElevenLabs handles one voice conversation at a time** — the listening, talking, and (with Twilio) placing an outbound call, plus running tools mid-call.
- **It does NOT chain the calls by itself.** It doesn’t finish the buyer call, decide to phone sellers, carry the details over, and report back on its own.
- **Our backend (Suman’s negotiator) is the glue:** it saves the buyer’s confirmed details, decides to call the seller, injects those details into the outbound call, collects the result, and produces the report.

So “ElevenLabs takes care of it” is only half true: it does each **voice leg**; **our code connects the legs.**

### How this maps to the real world

- **The real product is asynchronous, not one live chain.** The buyer says what they want once and **hangs up**. The agent calls businesses over the next minutes/hours, then **calls the buyer back**. That “calls you back” model *is* the realistic one — and it’s exactly our pitch.
- **Outbound AI calling to real businesses is a real, existing thing** (Twilio + ElevenLabs). The hard parts in the wild are gatekeepers, phone trees, hang-ups, “are you a robot?”, and the fact that the seller is a **human with no agent** — which is why our seller is a person answering a phone.
- **What would be fake:** implying one ElevenLabs “brain” autonomously roams the market. It doesn’t. Our orchestrator drives it one call at a time (or several at once), passing state between them.

**So don’t build a fragile fully-autonomous live chain for a 60-second video.** Use the async model: real intake call → real outbound call to Cole (with the buyer’s details) → real report-back. Record each leg, keep one scenario, edit into “talk once → it calls → it calls you back.” Simpler *and* more true to life.

### Where the audio actually comes from

ElevenLabs agents **record the call and produce a transcript automatically**. That recording is your cleanest audio — download it and use it as the master track. Everything else (screen, call-UI overlay) is layered on top in editing.

### Two ways to run the calls

| Setup | How it works | Best for |
|---|---|---|
| **Web voice (easiest)** | Person talks to the ElevenLabs agent through a browser mic (web widget / our UI). Screen-record locally. | Fast, reliable, no phone numbers |
| **Real phone (most “call”-like)** | ElevenLabs + Twilio dials a real number; person answers their phone. | If we want an actual ringing-phone moment |

Default to **web voice** unless the phone ring adds real value — it’s far less to go wrong on shoot day.

### Recording checklist (each person, locally)

- [ ] Record with **OBS** (free) — capture **screen + system audio + mic**. QuickTime works for a single mic on Mac.  
- [ ] 1080p, quiet room, headphones on (stops echo).  
- [ ] Start recording **before** the call, stop after — leave handles for editing.  
- [ ] Also **download the ElevenLabs call recording + transcript** as the backup master audio.  
- [ ] Send Cole: your screen recording + the ElevenLabs audio/transcript.

### Making it look like a call (in editing)

- Overlay a simple **incoming-call / call-in-progress screen** (a static graphic + a moving waveform) on top of the real audio.  
- For Tech: put the **real seller call on the left** and **Jagger’s trace screen on the right**, lined up in time.  
- Caption the **price drop** on screen when it happens.

### Who records what

| Clip | Who records it |
|---|---|
| Buyer ↔ agent (intake) | **Ella** (talks to agent, records her screen) |
| Agent ↔ seller ×3 styles | **Cole** (answers as seller, records his screen) |
| Trace screen synced to seller call | **Jagger** (screen-records the trace) |
| Final edit | **Cole** stitches clips + overlays + captions |

**Bottom line:** nobody records “a Zoom call.” Each person records their own real conversation with the agent locally, plus we grab ElevenLabs’ own recording — then Cole assembles it into something that looks and sounds like phone calls.

---

## Recording SOP (step by step, per person)

Follow this in order. Everyone can be on a **muted Zoom to cue timing** — just don’t record the Zoom.

### 0 · Before shoot day (everyone)

- [ ] **Cole:** ElevenLabs credits loaded and shared; both agents (intake + seller-negotiation) working.
- [ ] **Suman:** the pipeline runs end to end at least once (intake → outbound call → report).
- [ ] **Ella:** the one frozen scenario is set — dress details, buyer target price + max, and the three sellers’ hidden limits/styles.
- [ ] **Everyone:** install **OBS**, test screen + system audio + mic capture, use **headphones** (kills echo), quiet room.
- [ ] Agree the **buyer script** and the **three seller scripts** (Cole voices sellers).

### 1 · Shared setup at start of shoot (5 min)

- [ ] Confirm same scenario numbers on everyone’s screen (one source of truth).
- [ ] Everyone starts OBS, does a 10-second test clip, checks the audio meter is moving.
- [ ] Decide take order: Buyer intake → Seller call #1 (price moves) → #2 (callback) → #3 (upsell).

### 2 · Ella — the BUYER (records the intake call)

1. Start OBS (screen + your mic + system audio).  
2. Talk to the intake agent: say what dress you want, size, date, budget.  
3. **Make one correction** on purpose (“ivory, not champagne”) so the agent shows it adapts.  
4. Let the agent **recap** the details; confirm.  
5. Add the **document step**: send/show a dress **photo or screenshot**, let the agent read it into the same details, confirm once. *(This covers a required criterion.)*  
6. Stop OBS. **Download the ElevenLabs recording + transcript** of this call.  
7. Send Cole: the OBS file + the ElevenLabs audio/transcript.

### 3 · Cole — the SELLER (records the three negotiation calls)

Do these as **three separate recordings**.

1. Start OBS. Answer the agent’s outbound call.  
2. **Call #1 — Tough but fair:** hold firm, then give ground when the agent brings a **real competing quote**. Let the **price drop** (this is the money shot). Also here: let the agent **say it’s an AI**, ask “are you a robot?”, and try **one interruption**.  
3. **Call #2 — Won’t quote by phone:** “We only price in-store.” Make the agent get a **firm callback or a range** before you end.  
4. **Call #3 — Upseller:** pile on rush fees / veil / alterations; let the agent **itemize and strip** them.  
5. After each: stop OBS, **download the ElevenLabs recording + transcript**.  
6. Keep all three OBS files + transcripts for editing.

### 4 · Jagger — the TRACE screen

1. Start OBS on the **trace screen** view.  
2. Run it **in sync with Cole’s seller calls** (same scenario) so the trace matches the audio.  
3. Capture at least the moment where the agent **pulls the competing quote and the price moves**.  
4. Stop OBS; send Cole the trace recording (note which seller call it matches).

### 5 · Suman — the engine

1. Make sure each call runs cleanly and the **report/ranking** is produced at the end.  
2. Grab a clean shot (or export) of the **final ranked result** with the price and the proof.  
3. Send Cole the result screen + any log/transcript needed for the report-back.

### 6 · Cole — edit + assemble

1. Collect: Ella’s intake, Cole’s 3 seller calls, Jagger’s trace, Suman’s result screen, all ElevenLabs transcripts.  
2. Use the **ElevenLabs recordings as the master audio**; layer screen + a simple **call-UI overlay**.  
3. Cut the three videos: **Demo** (intake + call #1 price drop + report-back), **Tech** (seller call left + trace right), **Team**.  
4. **Caption the price drop.** Keep everyday language.  
5. QA: play with sound + muted; click the GitHub link logged-out; check each video ≤ 60s.

### What each person hands to Cole

| Person | Deliver |
|---|---|
| Ella | Intake OBS clip + document step + ElevenLabs audio/transcript |
| Cole | 3 seller OBS clips + 3 transcripts |
| Jagger | Trace screen recording (labeled per call) |
| Suman | Final ranked-result screen + report data |

### Common mistakes to avoid

- ❌ Recording the Zoom window. ✅ Record your own screen locally.  
- ❌ Forgetting the ElevenLabs recording. ✅ Download it every call — it’s the clean audio + proof.  
- ❌ Different numbers per call. ✅ One frozen scenario everywhere.  
- ❌ No document step. ✅ Ella does the photo/screenshot — it’s required.  
- ❌ Two humans talking on one call. ✅ Always one human + the agent.  
- ❌ Buzzwords on camera. ✅ Plain words.

---

## Shoot order

0. **Cole loads + shares ElevenLabs credits** so both voice legs work.  
1. Freeze one dress scenario; Ella finalizes seller data for the **three styles**.  
2. Ella records **buyer↔agent** intake locally; Cole records the **three seller calls** locally.  
3. Jagger’s **trace screen** recorded in sync with the seller calls.  
4. Grab the **ElevenLabs recordings + transcripts** for every call (master audio + proof).  
5. Shoot **Demo** (buyer call + one seller call w/ price drop + report-back).  
6. Shoot **Tech** (real seller call left + trace screen right).  
7. Shoot **Team**.  
8. Write **Summary** to match the Demo.  
9. Zip + upload.

---

## Slack message (paste this)

```text
@channel scope + video lock (please read)

Scope + casting:
• Ella = BUYER on camera (reads buyer script to our agent)
• Cole = SELLER on camera — plays THREE styles (uses Ella’s seller data)
• The AGENT = ElevenLabs voice on both calls (each call = 1 human + our agent, never 2 humans)
• Jagger: live TRACE screen = right-side view of how the agent works
• Suman: negotiator engine
• Cole: estimator (intake) + provides ElevenLabs credits (load + share before shoot)
• Ella: simulated seller data (prices, limits, styles)

THREE seller calls to design (Cole voices all):
1) Tough but fair → agent uses a REAL competing quote → price drops (money shot)
2) Won’t quote by phone → agent gets a firm callback / a range (structured ending)
3) Upseller → agent itemizes + strips fees (comparable quote)
Fold into #1: agent says it’s an AI, handles “are you a robot?” + one interruption.

RECORDING (we’re all remote — DON’T film Zoom):
• Each person talks to the agent from their OWN computer and screen-records locally (OBS: screen + system audio + mic).
• Also download ElevenLabs’ own recording + transcript = master audio + proof.
• Cole edits clips together, overlays a simple “call” screen, captions the price drop.

⚠️ GAP to close: challenge requires the job spec built by VOICE **and** at least ONE DOCUMENT (photo/screenshot). We do voice well — need a quick document path too (Cole/intake). ~5s on screen.

Three videos, each MAX 60 seconds (MP4/MOV): Demo, Tech, Team.

DEMO (jury gut-feel)
• Two real calls: buyer↔agent (intake), then agent↔real seller (price comes down), then agent reports back with best pick + proof.
• Everyone can read a script. The agent must sound smooth on both calls.

TECH
• “Listen → Find shops → Negotiate”
• Real seller call on the LEFT, Jagger’s trace screen on the RIGHT. Price moves; we don’t invent competing quotes.

TEAM
• Faces + one plain role each.

Language rule for Demo + Summary + Team: everyday English only.

One line for everything:
“You talk once. It shops and haggles. It calls you back with a better deal — and proof.”

Full plan: docs/final-deliverable-proposal.md

@Cole — estimator + document intake gap + seller acting (3 styles) + ElevenLabs credits + edit/summary
@Suman — negotiator engine (smooth on the seller calls)
@Jagger — trace screen synced to the seller calls + one pain number from the deck
@Ella — buyer acting + simulated seller data (prices/limits/styles)
```

---

## Official success criteria — are we covered?

Straight from the challenge slide. ✅ = our plan covers it; ⚠️ = needs attention.

| # | Criterion | Us | Where |
|---|---|---|---|
| 1 | Closed loop: intake → calls → negotiation → ranked pick with proof | ✅ | Demo end-to-end + report-back |
| 2 | One job spec, built by **voice interview AND ≥1 document type**, confirmed, reused on every call | ⚠️ | We show voice well. **We still need a document path** (e.g. a photo or a screenshot of a dress the buyer likes) that produces the *same* details. Cole (intake) to add. |
| 3 | Live calls vs **≥3 styles**; every quote itemized + comparable | ✅ | The three seller calls |
| 4 | **≥1 price/terms change during a call** from leverage | ✅ | Seller call #1 (tough) |
| 5 | AI disclosure + honesty; handles friction (“are you a robot?”, hang-ups) | ✅ | Built into call #1 |
| 6 | Every call ends in a **structured outcome** (quote / callback / decline) | ✅ | #1 quote · #2 callback · #3 itemized |
| 7 | Final report ranks all quotes, cites transcripts, explains in plain words | ✅ | Report-back card + UI |

**The one real gap is #2’s document path.** It’s required (“voice interview *and* at least one document type”), so we can’t skip it. Cheapest version: buyer sends a photo/screenshot of a dress; the intake reads it into the same details, buyer confirms once. Show it for ~5 seconds in the Demo or Tech.

---

## Direct answers

**Should Demo and Tech be separate?**  
Yes. The site requires it, and it’s clearer for jurors.

**Where does Jagger’s trace screen go?**  
Tech — as the right screen next to the real seller call. In the Demo it’s at most a 3–5 second peek. Demo is about the people on the phone.

**What has to feel real?**  
Two real calls: the buyer being understood, and a real seller getting negotiated down — then a clear result with proof.

**ElevenLabs credits?**  
Cole provides them. Load and share before the shoot so both voice legs run on real voice.

**How do we record a call demo if we’re all on Zoom?**  
Don’t record Zoom. Each real call is one person + our agent. That person talks to the agent from their own computer and records their own screen/audio locally (OBS), and we also download ElevenLabs’ own recording + transcript. Cole edits the clips together and overlays a simple call screen. See the recording section above.

**Who acts?**  
Ella = buyer, Cole = seller (three styles). The agent is the automated voice on both calls.

---

*If someone only watches the Demo, they should still understand the whole product.*
