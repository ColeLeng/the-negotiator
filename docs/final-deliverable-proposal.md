# Final Deliverable Design Proposal

**Owner:** Cole (pitch lead) · **Audience:** team · **Goal:** maximize Hack-Nation score on Technical depth · Communication · Innovation & creativity

This is the submission package design — not another architecture doc. Every artifact below is mapped to a judging axis and a cut line so we ship a coherent story, not seven disconnected uploads.

---

## 1. North-star pitch (one sentence)

> An agent that interviews you once, finds real bridal options, then **haggles in parallel** until a live price moves — with honest leverage only, and a ranked recommendation backed by transcripts.

Everything we submit must make that sentence feel **inevitable**, not aspirational.

---

## 2. How judges score — what we optimize for

| Axis | What wins | Our proof |
|---|---|---|
| **Technical depth** | Real systems work, not a scripted TTS dialogue | ZOPA + dual value models · shared blackboard BATNA · honesty guard · contract-first A2A loop · ≥3 seller styles · price that *emerges* |
| **Communication** | Docs + videos that a non-author can follow in &lt;10 min | Project summary · Demo / Tech / Team videos · README “done” checklist · transcript-cited recommendation in UI |
| **Innovation & creativity** | Original framing + creative mechanism | Opaque-market wedge (bridal / config-swappable) · **honest** multi-agent leverage (blackboard, not bluffing) · attribute↔price tradeoffs, not price-only bots |

**Implication:** Do not spend pitch time on stack trivia. Spend it on (1) the pain with a number, (2) the closed loop, (3) the moving price + why it isn’t a screenplay, (4) the honesty line.

---

## 3. Submission package — design per item

Upload target: **projects.hack-nation.ai**. Cole owns sequencing, scripts, cuts, and final upload QA. Module owners supply footage/clips and review accuracy.

### 3.1 Project Summary — Text (150–300 words)

**Purpose:** High-level pitch for the jury (often read *before* videos).

**Design:** Write it last, after Demo + Tech are locked, so claims match footage. Structure:

1. **Hook (1–2 sentences)** — opaque quote markets; bridal as the wedge; movers/config-swappable as the general case.
2. **What it does (3 beats)** — Estimator → Caller → parallel Closer/Orchestrator → ranked recommendation.
3. **Proof of depth (2–3 sentences)** — dual reservation prices, ZOPA, blackboard BATNA, honesty guard; price moves from dynamics.
4. **Conversation ethics (1 sentence)** — AI disclosure, no invented bids, structured endings.
5. **Ask / outcome (1 sentence)** — demo shows a live concession and a transcript-backed pick.

**Hard rules:** ≤300 words · no unverified metrics · name the vertical · name ElevenLabs only where we actually use it (intake / voice leg) — don’t overclaim.

**Draft skeleton (replace numbers only with demo-true facts):**

> Phone-priced markets hide real prices behind opaque quotes. For made-to-order bridal, buyers have high emotion, low leverage, and no time to call five boutiques. The Negotiator turns one confirmed product spec into parallel negotiations: an Estimator builds a structured `ProductSpec` (voice or document), a Caller ranks real comparable options, and Buyer Agents haggle against Seller Agents with hidden floors and distinct styles — trading soft attributes against price inside a real ZOPA. Parallel sessions share a blackboard so leverage is always a *real* competing offer, enforced by an honesty guard. The demo shows a price that moves during the call, then ranks closed deals with transcript evidence. Config swaps the vertical; the negotiation engine stays the same.

---

### 3.2 Demo Video — *show the product working*

**Purpose:** Prove the closed loop and the money shot. This is the Communication + Innovation vehicle; Technical depth is *felt*, not lectured.

**Length target:** **90–120 seconds** (hard cap 150s). Jury attention drops after ~2 min.

| Beat | Time | On screen | Voiceover |
|---|---|---|---|
| 0 · Cold open | 0–10s | Pain number or “list $2,400 → …” tease | Opaque markets / why bridal |
| 1 · Intake | 10–25s | Estimator confirms `ProductSpec` (voice clip *or* confirmed form) | “One spec, reused verbatim” |
| 2 · Fan-out | 25–40s | Ranked options table (≥3 vendors, styles implied) | Real options + BATNA seed |
| 3 · Money shot | 40–85s | UI ticker + transcript; **price ticks down** mid-negotiation | “Not a script — two private floors meet” |
| 4 · Close | 85–110s | Ranked recommendation + cite a transcript line | Structured outcome + pick |
| 5 · Tag | 110–120s | Logo + GitHub URL | One-line thesis |

**Must show on camera (non-negotiable):**

1. Closed loop: intake → options → negotiate → recommend.
2. **≥1 visible price move** with a preceding buyer/seller turn (so it can’t read as a fake counter).
3. ≥2 parallel sessions *or* clear “vs tough / stonewaller / upseller” labeling.
4. Final recommendation with a transcript citation visible.

**Cut if behind:** Live Twilio/Vapi leg. Prefer **mock/SSE UI** that is rock-solid over a flaky live call. Voice can live in Tech Video as a secondary clip.

**Recording setup (Cole):**

- 1440p or 1080p, 16:9, clean browser profile, zoom UI so ticker is readable.
- Cursor highlight on; no desktop clutter.
- Pre-warm API (`uvicorn` + `npm run dev`); rehearse one clean run; record 2 takes; pick the clearer price move.
- Burn in tiny captions for the price delta (“$2,200 → $1,850”).

---

### 3.3 Tech Video — *explain how we built it*

**Purpose:** Maximize **Technical depth**. Different story from Demo — no market TED talk.

**Length target:** **2–3 minutes** (cap 3:30).

| Beat | Time | Content |
|---|---|---|
| Architecture | 0–40s | Mermaid / 3-module diagram: Estimator · Caller · Orchestrator + Seller side |
| Contracts | 40–70s | `ProductSpec` → `RankedOptions` → `NegotiationSession` (show real JSON briefly) |
| Negotiation science | 70–130s | Buyer utility + seller `dynamic_floor` · ZOPA · why price *emerges* |
| Coordination + ethics | 130–170s | Blackboard BATNA · honesty guard (real row required) · AI disclosure |
| Evidence | 170–200s | Point at `tests/`, `run_demo.py`, evals / golden transcript if present |

**Do not:** re-demo the full UI run. Cross-cut 5–10s of the money-shot only as evidence.

**Owner clips:** Suman (orchestrator/loop) · Ella (seller policy) · Jagger (estimator) · Cole (caller, value, guard, UI). Cole edits the A-roll.

---

### 3.4 Team Video — *who we are*

**Purpose:** Trust + Communication. Short human context; not a second tech talk.

**Length target:** **45–75 seconds**.

**Format:** Talking heads (grid or quick cuts) — name, role, one concrete ownership line.

| Person | One-liner to say |
|---|---|
| Cole | Pitch + Caller / buyer value / honesty guard / demo UI |
| Suman | Orchestrator, negotiation loop, channels, blackboard |
| Ella | Seller agents + concession / inventory floors |
| Jagger | Estimator + market framing / intake |

**Script shape:** “We’re [team]. We built The Negotiator for ElevenLabs’ challenge because opaque markets punish people who can’t spend hours on the phone. Here’s who owned what — and why we care that the agent stays honest.” End on names + GitHub.

**Cut if behind:** Single spokesperson (Cole) with name cards for others — still upload *something*; empty Team video is a free Communication miss.

---

### 3.5 GitHub Repository — Public link

**Purpose:** Technical depth that skeptics can verify in 5 minutes.

**Landing experience (README is the lobby):**

1. One-sentence pitch + money-shot GIF or screenshot of the ticker.
2. Problem → vertical → architecture diagram (already in README).
3. **Getting started that works with zero API keys** (`run_demo.py`, pytest, UI).
4. Explicit map: challenge criteria → where they live in code.
5. Team & roles table.
6. Link to `docs/technical-architecture.md` and this proposal (optional for jurors).

**Hygiene before freeze:**

- [ ] `README` “What done looks like” checked against reality.
- [ ] `.env.example` only — no secrets.
- [ ] `pytest -q` green on a clean clone story.
- [ ] Public repo; license present.
- [ ] Pin the commit SHA in the Project Summary or submission notes.

---

### 3.6 Zipped Code — `.zip` backup

**Purpose:** Local backup for organizers if GitHub blips.

**Design:** Export from the **same SHA** as the public repo.

```bash
# from repo root, clean tree
git archive --format=zip --output=the-negotiator-$(git rev-parse --short HEAD).zip HEAD
```

**Exclude:** `.venv/`, `ui/node_modules/`, `.env`, large media, `__pycache__/`. Prefer `git archive` so excludes follow gitignore.

---

### 3.7 Dataset — Link or **N/A**

**Purpose:** Raw/processed data if used or generated.

**Recommendation:** Prefer **N/A** unless we ship a clearly licensed artifact.

| If we… | Submit |
|---|---|
| Only use curated in-repo bridal fixtures / catalog | **N/A** + one README sentence: “demo catalog is fixtures under `fixtures/` / caller catalog; list prices are synthetic for ZOPA room” |
| Publish a small anonymized quote table we generated | Public gist or `data/` folder + license note + link |
| Hit live web search at demo time | Still **N/A** for “dataset”; mention sources in Tech Video / README, not as a downloadable dataset |

**Do not** zip scraped vendor pages without licenses — that creates risk for zero scoring upside.

---

## 4. Narrative architecture across the three videos

Treat Demo / Tech / Team as **one trilogy**, not three restarts.

```text
Team   → why us / roles          (trust)
Demo   → what it does / money shot (belief)
Tech   → why it’s real engineering (depth)
Summary→ glue for skimmers        (recall)
```

**Shared motifs (reuse, don’t reinvent):**

- Visual: dark UI, ticker as hero number, teal accent only for price deltas (match existing demo feel).
- Phrase bank (say the same words every time): *closed loop* · *moving price* · *honest leverage* · *ZOPA* · *transcript-backed*.
- Avoid: “multi-agent framework,” model name drops, dashboard tours.

---

## 5. Mapping challenge success criteria → where jurors see them

| Challenge “done” criterion | Primary artifact | Backup |
|---|---|---|
| Closed loop intake → calls → negotiate → rank | **Demo Video** + UI | `run_demo.py` in GitHub |
| One `ProductSpec`, voice + ≥1 document path | Demo (confirm step) + Tech | Estimator fixtures |
| ≥3 negotiation styles; itemized/comparable quotes | Demo table + seller labels | Seller agent configs / Tech |
| ≥1 price/terms change from real leverage | **Demo money shot** | Session transcript in UI |
| Disclosure + honesty + friction | Tech (guard) + short Demo beat | `guard.py` + tests |
| Structured call endings | Demo close + transcript | Contracts |
| Ranked report with transcript citations | Demo final frame | `/demo` JSON |

**Strong vs weak (from brief) — our anti-patterns checklist:**

- [ ] Price move is preceded by an offer/counter on screen (not a jump cut to a lower number).
- [ ] No invented competing bid in any recorded turn.
- [ ] Fees/attributes comparable across rows (same spec).
- [ ] We say out loud: counterparties are seller agents (and voice bridge if any) — honesty about the setup is a *feature*.

---

## 6. Cole’s ownership — RACI for the package

| Deliverable | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Project Summary | Cole | Cole | All | — |
| Demo Video | Cole (edit + record UI) | Cole | Suman (loop), Ella (seller beat) | Jagger |
| Tech Video | Cole (edit) | Cole | Suman, Ella, Jagger (accuracy) | — |
| Team Video | Cole (produce) | Cole | All (appear / lines) | — |
| GitHub polish | Cole (README/demo path) | Cole | Module owners | — |
| Zip | Cole | Cole | — | — |
| Dataset field | Cole | Cole | Jagger (if any data claim) | — |

**Cole’s personal cut list (protect the pitch):**

1. Protect the **money-shot reliability** over new features after freeze.
2. Freeze demo scenario + seed (same dress, same three sellers) so takes are reproducible.
3. Write Summary from the final Demo cut, not from the architecture doc.
4. Upload dry-run on the site early (formats/limits) before the deadline scramble.

---

## 7. Recommended freeze & shoot order

Work backward from upload. Exact clock times are team-local; order is fixed.

1. **Scenario freeze** — one bridal `ProductSpec`, three sellers (tough / stonewaller / upseller), known list prices above target (~$1800) so concessions have room.
2. **Demo reliability pass** — `pytest -q` + one clean UI SSE run; capture golden screenshots/GIF.
3. **Record Demo Video** (2 takes).
4. **Record Tech Video** (architecture walk + code pointers).
5. **Record Team Video** (can be parallel / phone camera).
6. **Write Project Summary** to match Demo claims.
7. **GitHub polish** at the demo SHA; tag `hacknation-submit` if useful.
8. **Zip from that SHA**; Dataset = N/A (unless a real `data/` drop exists).
9. **Upload QA** — play all three videos muted and with sound; click GitHub link from a logged-out browser.

---

## 8. What to emphasize vs de-emphasize (value maximization)

### Emphasize (high score density)

- Emergent moving price from dual private value models.
- Honest BATNA via blackboard (innovation *and* ethics).
- Contract-first parallel build that actually integrates.
- Config-swappable vertical (bridal demo, broader thesis).
- Transcript-cited recommendation (Communication + challenge fit).

### De-emphasize (low score density / risk)

- Live web search keys / provider alphabet soup.
- UCP adapter unless it demos cleanly in &lt;15s.
- Production concerns (Redis, scale, auth).
- Overclaiming ElevenLabs surface area we didn’t ship.
- Polished dashboard chrome without a price move.

---

## 9. Definition of “submission-ready”

We upload when:

1. Demo Video shows a **clear, captioned price move** inside a closed loop.
2. Tech Video explains ZOPA + blackboard + guard without contradicting Demo.
3. Team Video exists (≥45s) with roles.
4. Summary is 150–300 words and claim-locked to footage.
5. Public GitHub at known SHA runs mock demo without keys.
6. Zip matches that SHA.
7. Dataset is **N/A** or a licensed link — never a vague “see repo.”

---

## 10. Open decisions for Cole to close (short list)

1. **Voice in Demo vs Tech only** — default: Demo = UI/SSE reliability; Tech = optional ElevenLabs intake clip.
2. **Spokesperson** — Cole on Demo/Tech VO; full team on Team video.
3. **Vertical wording** — “customized DTC bridal” primary; “movers via config” as one clause, not a second demo.
4. **Whether to show document intake** — if flaky, say “voice + document paths share one schema” in Tech and show the confirmed spec once in Demo.

---

*Cole owns the pitch package. Everyone else owns truth in their module. The winning submission is a single story told five ways (summary + 3 videos + repo), not five stories fighting for attention.*
