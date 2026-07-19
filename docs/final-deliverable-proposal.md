# Final Deliverable Design Proposal

**Owner:** Cole (pitch lead) · **Audience:** team · **Goal:** maximize Hack-Nation score on Technical depth · Communication · Innovation & creativity

This is the submission package design — not another architecture doc. Every artifact below is mapped to a judging axis and a cut line so we ship a coherent story, not seven disconnected uploads.

**Market grounding:** Jagger’s *Case for Voice Buying Agents* deck (July 2026) — use those numbers in VO; do not invent new ones.

---

## 1. North-star pitch (one sentence)

> An agent that interviews you once, finds real bridal options, then **haggles in parallel** until a live price moves — with honest leverage only, and a ranked recommendation backed by transcripts.

Everything we submit must make that sentence feel **inevitable**, not aspirational.

### Narrative spine (clear + impactful)

Tell one story in this order. Same words in Summary, Demo cold-open, and Tech closer.

1. **Most commerce still prices by conversation.** Retail e-com looks solved; the larger pool still “calls for pricing.” Jagger: ~\$28T B2B layer where price discovery is phone/email/rep — only ~26% of US B2B wholesale actually clears on websites.
2. **Custom / high-consideration is where the pain is sharpest.** Same job, same day → quotes swing **2.8–5.6×** (moving \$1,158–\$6,506 is the documented headline). Wedding “tax”: ~28% markup when the word *wedding* is said. **67% of buyers accept the first quote.**
3. **Agents collapse the cost of shopping the phone market.** A human won’t run 5–8 comparable calls; an agent will — in parallel — and keep every fee itemized.
4. **We beachhead on customized DTC bridal** (demo-fit ★★★★★ in Jagger’s prioritization): high emotion, opaque quotes, structured vendor types, config-swappable into furniture / jewelry / later B2B.
5. **Immediate value = savings + matched custom trades. Strategic value = structured intent + price data** that can eventually reverse the flow (merchants respond to verified demand). Our hackathon slice: prove the closed loop and a price that *moves*.

**Phrase bank (reuse everywhere):** *call-for-pricing* · *closed loop* · *moving price* · *honest leverage* · *one confirmed intent* · *transcript-backed*.

**Avoid:** “rent-seeking,” “fairer prices for both every time,” stack-name tours, overclaiming live Twilio if we didn’t ship it.

---

## 2. How judges score — what we optimize for

| Axis | What wins | Our proof |
|---|---|---|
| **Technical depth** | Real systems work, not a scripted TTS dialogue | ZOPA + dual value models · shared blackboard BATNA · honesty guard · contract-first A2A loop · ≥3 seller styles · price that *emerges* |
| **Communication** | Docs + videos a non-author can follow in &lt;10 min | Project summary · **dual-pane Demo** · Tech · Team · README that runs with zero keys |
| **Innovation & creativity** | Original framing + creative mechanism | Customization / price-discovery beachhead · **split-screen human call + parallel agent cockpit** · portable **Purchase Intent** + open negotiation protocol sketch |

**Implication:** Demo must *feel* like a new interface for commerce (Jagger’s closer), not a dashboard walkthrough. Tech must show the contracts that make that interface portable.

---

## 3. Submission package — design per item

Upload target: **projects.hack-nation.ai**. Cole owns sequencing, scripts, cuts, and final upload QA. Module owners supply footage/clips and review accuracy.

### 3.1 Project Summary — Text (150–300 words)

**Purpose:** High-level pitch for the jury (often read *before* videos).

**Structure:**

1. **Hook** — call-for-pricing + one hard number (5.6× or wedding tax / first-quote stat).
2. **Why bridal** — customized, high-emotion, opaque; beachhead into broader custom + B2B.
3. **What it does** — Estimator → Caller → parallel negotiations → ranked recommendation.
4. **Proof** — dual floors / ZOPA, blackboard BATNA, honesty guard; price moves.
5. **Why it matters beyond the demo** — one machine-readable intent reused across sellers; path to an open negotiation layer.
6. **Close** — what the Demo shows on screen.

**Hard rules:** ≤300 words · only Jagger/brief-backed metrics · name ElevenLabs only where we actually use it · claim-lock to footage.

**Draft skeleton (~240 words):**

> Most of commerce still prices by conversation — “call for pricing” is the default outside neat retail carts. For identical work, quotes swing as much as 5.6×; in wedding categories, saying the word *wedding* can add ~28%, and most buyers still accept the first number they hear. The Negotiator is a voice buying agent for that layer. We beachhead on customized bridal: one confirmed purchase intent (voice or document) becomes a structured `ProductSpec`, a Caller ranks real comparable options, and Buyer Agents negotiate in parallel against distinct seller styles — trading soft attributes against price inside a live ZOPA. Sessions share a blackboard so leverage is always a real competing offer, enforced by an honesty guard. The demo shows a human confirming intent, then a dual view: the voice negotiation on one side and the agent cockpit — parallel sellers, moving prices, transcript evidence — on the other. Immediate value is a better-matched custom deal. Strategic value is turning opaque phone markets into a machine-readable discovery layer merchants and personal agents can both speak. Config swaps the vertical; the negotiation engine stays the same.

---

### 3.2 Demo Video — *dual-pane: human call + agent cockpit*

**Purpose:** Innovation + Communication vehicle. Prove the closed loop **and** that this is a new interface — not a screenplay, not a static table.

**Length target:** **120–150 seconds** (hard cap 165s). Slightly longer than a pure UI reel because the split-screen needs breathing room.

#### The innovative format (recommended)

**Split screen for the middle of the video** — front experience + backend synchronous showcase:

| Pane | What the jury sees | What it proves |
|---|---|---|
| **A · Human / voice** | Real person (or clearly framed buyer) speaking; agent voice answers (ElevenLabs / voice channel). Confirm intent → later hear one live negotiation turn (disclosure, counter, concession). | Conversation requirement; “this is actually a call” |
| **B · Agent cockpit** | Our Next.js UI: ≥3 seller sessions in parallel, price tickers, blackboard BATNA flash, scrolling transcripts with intents (`open` / `counter` / `concede`). | Parallel discovery; moving price; not one scripted dialogue |

**Cold open (full frame)** → **intake (A primary)** → **fan-out (B primary)** → **money shot (A+B locked)** → **recommendation (full frame)**.

```text
[0–12s]  FULL: pain number (5.6× or “67% accept first quote”) + brand line
[12–35s] PANE A lead: human ↔ Estimator voice; confirm ProductSpec / Purchase Intent on screen
[35–50s] PANE B lead: Caller fills ranked options (≥3 vendors, style labels)
[50–110s] SPLIT LOCKED: one voice negotiation audible in A while B shows 2–3 parallel sessions;
          caption the price move on the active session (“$2,200 → $1,850”)
[110–140s] FULL: ranked recommendation + transcript citation + “honest leverage only”
[140–150s] Tag: GitHub + one-line thesis (“voice is the interface; intent is the payload”)
```

#### Must show on camera (non-negotiable)

1. Closed loop: intent confirm → options → negotiate → recommend.
2. **Audible agent voice** for ≥1 negotiation beat (disclosure or counter) — not only TTS over a fake script with no UI truth.
3. **≥1 visible price move** on Pane B with a preceding offer/counter in the transcript.
4. ≥2 parallel sessions visible (third can be “stonewaller / walked”).
5. Final recommendation with a transcript citation.

#### Production reality / cut lines

| Tier | What we shoot | When to use |
|---|---|---|
| **Gold** | Live (or recorded-live) human ↔ voice agent on Pane A; real SSE cockpit on Pane B, same run | If voice channel is stable for one take |
| **Silver** | Record Pane A (voice) and Pane B (UI) in one rehearsed scenario with **shared timestamps / same `spec_id`**; edit split — disclose “one run, two views” | Default if live dual-capture is flaky |
| **Bronze** | Strong UI/SSE dual-session cockpit + short voice intake-only clip; say out loud sellers are agent counterparties | Last resort — still better than silent fallback |

**Honesty on camera is a feature:** “Seller side is agent counterparties with hidden floors — so you can see a real ZOPA, not a screenplay.”

**Recording setup (Cole):**

- 1440p or 1080p, 16:9; both panes large enough to read prices.
- Burn-in captions for price deltas and for “Purchase Intent confirmed.”
- Pre-warm API + UI; freeze scenario seed; 2–3 takes; pick clearest price move.
- Soft bed under VO only outside the call audio; never duck the negotiation so low jurors miss the concession.

**RACI tweak:** Suman supplies voice-channel readiness; Ella confirms seller styles readable in UI; Jagger supplies intake script + market cold-open numbers; Cole directs/edits.

---

### 3.3 Tech Video — *explain how we built it*

**Purpose:** Maximize **Technical depth**. Different story from Demo — no market TED talk (Demo already used Jagger’s numbers).

**Length target:** **2–3 minutes** (cap 3:30).

| Beat | Time | Content |
|---|---|---|
| Architecture | 0–35s | Estimator · Caller · Orchestrator + Seller side |
| Intent → contracts | 35–75s | `ProductSpec` as portable Purchase Intent; hard/soft attrs; ZOPA bounds |
| Negotiation science | 75–130s | Buyer utility + seller `dynamic_floor` · why price *emerges* |
| Coordination + ethics | 130–170s | Blackboard BATNA · honesty guard · AI disclosure |
| Protocol punch | 170–200s | Channel-agnostic messages (voice / mock / UCP) → sketch of open **Negotiation Intent Protocol** (§12) |
| Evidence | 200–210s | `tests/`, `run_demo.py` |

**Do not:** re-demo the full dual-pane. Cross-cut 5–10s of the money-shot only as evidence.

---

### 3.4 Team Video — *who we are*

**Purpose:** Trust + Communication. Short human context; not a second tech talk.

**Length target:** **45–75 seconds**.

| Person | One-liner to say |
|---|---|
| Cole | Pitch + Caller / buyer value / honesty guard / demo UI (dual-pane) |
| Suman | Orchestrator, negotiation loop, channels, blackboard |
| Ella | Seller agents + concession / inventory floors |
| Jagger | Estimator + market case (call-for-pricing → custom beachhead) |

**Script shape:** “We’re [team]. Most commerce still prices by phone — we built The Negotiator so a personal agent can confirm your intent once and haggle in parallel, honestly. Here’s who owned what.” End on names + GitHub.

**Cut if behind:** Cole solo with name cards — still upload *something*.

---

### 3.5 GitHub Repository — Public link

**Purpose:** Technical depth that skeptics can verify in 5 minutes.

1. One-sentence pitch + dual-pane / ticker screenshot or GIF.
2. Problem → bridal beachhead → architecture (README).
3. **Zero-key path:** `run_demo.py`, pytest, UI.
4. Challenge criteria → code map.
5. Team & roles; link this proposal + technical architecture.
6. Optional: short “Purchase Intent / protocol” pointer (§12) so Innovation jurors see the foresight.

**Hygiene:** README “done” matches reality · no secrets · green tests · public · pin SHA.

---

### 3.6 Zipped Code — `.zip` backup

Same SHA as public repo:

```bash
git archive --format=zip --output=the-negotiator-$(git rev-parse --short HEAD).zip HEAD
```

---

### 3.7 Dataset — Link or **N/A**

Default **N/A**. Fixtures/catalog are not a research dataset. If Jagger publishes a small licensed benchmark table, link it; otherwise do not zip scraped pages.

---

## 4. Narrative architecture across the three videos

```text
Team   → why us / roles                         (trust)
Demo   → dual-pane: voice + parallel cockpit    (belief + innovation)
Tech   → contracts, ZOPA, guard, open protocol  (depth)
Summary→ glue for skimmers                      (recall)
```

---

## 5. Mapping challenge success criteria → where jurors see them

| Challenge “done” criterion | Primary artifact | Backup |
|---|---|---|
| Closed loop intake → calls → negotiate → rank | **Demo dual-pane** | `run_demo.py` |
| One structured spec, voice + ≥1 document path | Demo intent confirm + Tech | Estimator fixtures |
| ≥3 negotiation styles; comparable quotes | Pane B labels + table | Seller configs |
| ≥1 price/terms change from real leverage | **Split money shot** | Session transcript |
| Disclosure + honesty + friction | Audible disclosure in Pane A + Tech guard | `guard.py` |
| Structured call endings | Demo close | Contracts |
| Ranked report with transcript citations | Demo final frame | `/demo` JSON |

**Anti-patterns checklist:**

- [ ] Price move preceded by offer/counter on Pane B (not a jump cut).
- [ ] No invented competing bid.
- [ ] Same `spec_id` / scenario across both panes.
- [ ] We say out loud what is live voice vs agent counterparty.

---

## 6. Cole’s ownership — RACI for the package

| Deliverable | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Project Summary | Cole | Cole | Jagger (numbers), All | — |
| Demo Video (dual-pane) | Cole (direct/edit) | Cole | Suman (voice/loop), Ella (sellers), Jagger (intake + cold open) | — |
| Tech Video | Cole (edit) | Cole | Suman, Ella, Jagger | — |
| Team Video | Cole (produce) | Cole | All | — |
| GitHub polish | Cole | Cole | Module owners | — |
| Zip / Dataset field | Cole | Cole | Jagger if data link | — |

**Cole’s cut list:**

1. Protect **split money-shot reliability** over new features after freeze.
2. Freeze one bridal scenario + three seller styles (list prices above ~\$1800 target).
3. Claim-lock Summary to the final Demo cut.
4. Upload dry-run early (formats/limits).

---

## 7. Recommended freeze & shoot order

1. Scenario freeze (`ProductSpec` + three sellers).
2. Cockpit reliability pass (SSE / parallel sessions / clear ticker).
3. Voice intake + one negotiation beat recorded (Gold/Silver).
4. Edit dual-pane Demo (2 cuts).
5. Tech Video (contracts + protocol punch).
6. Team Video.
7. Project Summary from final Demo claims.
8. GitHub polish + zip at that SHA; Dataset N/A.
9. Upload QA.

---

## 8. What to emphasize vs de-emphasize

### Emphasize

- Call-for-pricing → machine-readable discovery (Jagger).
- Dual-pane Demo (human voice + parallel agent cockpit).
- Emergent moving price; honest BATNA; transcript-backed pick.
- Purchase Intent as the reusable payload; open protocol as the “what’s next.”
- Config-swappable vertical (bridal now → custom / B2B later).

### De-emphasize

- Provider alphabet soup; Redis/scale/auth.
- Shipping a full standards body RFC in 20 hours (sketch + working contracts is enough).
- Overclaiming ElevenLabs surface area we didn’t ship.
- Dashboard chrome without a price move.

---

## 9. Definition of “submission-ready”

1. Demo shows **dual-pane** (or Silver equivalent) with audible voice beat + captioned price move.
2. Tech explains ZOPA + blackboard + guard + intent/protocol punch without contradicting Demo.
3. Team video ≥45s.
4. Summary 150–300 words, claim-locked, Jagger-safe metrics only.
5. Public GitHub at known SHA runs mock demo without keys.
6. Zip matches that SHA.
7. Dataset N/A or licensed link.

---

## 10. Open decisions for Cole to close

1. **Demo tier:** Gold vs Silver dual-pane (default Silver if live sync is risky).
2. **Who is on camera** for Pane A (Cole / teammate / willing friend).
3. **Cold-open number:** 5.6× spread vs 67% first-quote vs wedding tax 28% — pick **one** primary.
4. **Document intake on camera** vs “same schema” mention in Tech only.
5. How loud to push **open protocol** in Demo tagline vs keep it for Tech (recommend: one tagline in Demo, full sketch in Tech).

---

## 11. Team Slack copy (ready to paste)

```text
@channel pitch package update — narrative + Demo format lock

Doc: docs/final-deliverable-proposal.md (read the Demo + Intent/Protocol sections)

NARRATIVE (use these words; drop older “rent-seeking” language entirely)
• Most commerce still *calls for pricing* — Jagger’s deck: huge phone-priced layer; custom/high-consideration is the sharp pain (5.6× spreads, wedding tax ~28%, 67% take first quote).
• We beachhead bridal/custom because demo-fit + personalization surplus; architecture stays config-swappable toward broader custom / B2B.
• Dual win wording: buyers get comparison + real BATNA; merchants get completed, better-matched custom trades + (later) structured demand — not “everyone gets a better price every time.”

DEMO FORMAT (innovation bet)
• Dual-pane: Pane A = real person + agent voice (intent confirm + one negotiation beat). Pane B = agent cockpit (parallel sellers, moving price, transcripts) in sync.
• Gold = one live run both panes; Silver = same scenario/timestamps edited split. Bronze = cockpit + intake-only voice.
• Money shot stays: visible price move with a preceding counter on Pane B.

INTENT / PROTOCOL (Tech punch + “what’s next”)
• We’re treating the Estimator output as a portable Purchase Intent (DMU → machine-readable constraints, prefs, ZOPA).
• Hackathon ships working contracts; we *advocate* an open Negotiation Intent Protocol so personal agents and merchants can exchange intent/offers without every vertical reinventing phone scripts — details in §12 of the doc.

Who does what for Demo:
• @Cole — directs dual-pane + Summary VO
• @Suman — voice channel / loop readiness for Pane A↔B sync
• @Ella — seller styles obvious on Pane B
• @Jagger — cold-open metric + intake script (deck-true numbers only)
• @Kazi — utility/ZOPA one-liner if needed in Tech

Reply in-thread if your module can’t support Gold — we’ll lock Silver vs Bronze tonight.
```

---

## 12. Purchase Intent, DMU → machine-readable intent, and an open protocol

This is the **Innovation foresight** piece: Demo proves the loop; Tech + Summary point at the standard that makes the loop a platform.

### 12.1 What “DMU as intent” means here

In classic B2B, the **Decision Making Unit** is the set of roles that shape a buy (user, buyer, influencer, approver). In customized consumer (bridal), the same idea collapses into one person but **many constraints**: taste, fit, timeline, budget authority, deal-breakers, tradeables.

**Estimator’s job** is to interview that DMU and emit a portable object — not a chat log:

| DMU / human concept | Machine field (today → next) |
|---|---|
| What I need (musts) | `attributes[]` with `constraint: hard` |
| What I’d trade | `attributes[]` with `constraint: soft` + `weight` + `substitutions` |
| Budget authority | `negotiation.target_price` / `reservation_price` |
| Time pressure | `deadline_days` / wedding date |
| Who may act for me | disclosure + `acting_for` / consent scope (protocol addition) |
| What merchants may see | **Intent grant** — redacted vs full intent (privacy) |

Today that object is `ProductSpec` in [`negotiator/contracts.py`](../negotiator/contracts.py). For the pitch, name it **Purchase Intent** (payload) carried over voice or document intake, **reused verbatim** across every seller — that is how opaque markets become comparable.

### 12.2 Why an open protocol (not only our app)

Phone opacity persists because every boutique has a different script and no shared schema. Apps that keep intent trapped in one vendor’s CRM recreate the silo.

**Advocate (hackathon posture):** ship working contracts + channel abstraction now; propose a thin open **Negotiation Intent Protocol (NIP)** so:

- **Personal agents** can publish *consented* intent (or query merchants) without giving every seller the raw diary.
- **Merchant agents** can expose capability + quote/negotiate endpoints without inventing a bespoke API per vertical.
- **Marketplaces / reverse-auction later** (Jagger’s terminal state) become possible because demand is structured.

We do **not** need to ratify a standards body this weekend. We need a crisp, demable sketch that maps 1:1 to code we already have.

### 12.3 What is needed (minimum viable protocol)

Four message families — align names to existing contracts where possible:

```text
1) IntentAnnouncement   ← ProductSpec + consent/scope + vertical id
2) Offer / Quote        ← Option-like: itemized price, matched attrs, validity, channel
3) Negotiate            ← NegotiationMessage intents: open|counter|concede|accept|reject|hangup
4) SettlementReceipt    ← structured outcome + transcript hash / citation ids
```

**Plus three non-optional rules** (this is our differentiator):

1. **Provenance for leverage** — any “I have a better quote” claim must reference an `offer_id` the peer can resolve (our blackboard/guard).
2. **Channel neutrality** — same Negotiate messages over voice (TTS/STT), mock, or structured transport (UCP-class / HTTP+JSON). Voice is a *carrier*; intent is the *payload*.
3. **Consent & redaction** — merchants receive the projection they need (hard constraints + soft prefs they’re allowed to see), not the buyer’s full reservation price by default unless the user opts in.

### 12.4 What merchants vs personal agents capture

| Side | Captures | Exposes to the other side |
|---|---|---|
| **Personal agent** | Full intent, true reservation, BATNA, transcripts, outcome prefs | Redacted IntentAnnouncement; counters; accept/reject |
| **Merchant agent** | Inventory, `dynamic_floor`, capacity, upsell catalog, style policy | Offers; negotiate moves; itemized quotes; decline reasons |
| **Shared / market** | Anonymized cleared prices + attribute mixes (flywheel) | Benchmarks / red-flag priors (optional network service) |

Opaque world → outer world: **intent is the API**. Voice remains how you talk to humans who have no API; NIP is how agents talk once both sides are machine-reachable.

### 12.5 How we show this without boiling the ocean

| Layer | Hackathon ship | Pitch claim |
|---|---|---|
| `ProductSpec` / sessions / guard | **Working in repo** | “Purchase Intent + honest Negotiate already run” |
| `SellerChannel` (mock / voice / UCP stub) | Mock (+ voice if Gold) | “Carrier-agnostic” |
| NIP doc sketch (this §) | **In proposal + 20s Tech beat** | “We’re open to standardizing this” |
| Public schema file (`docs/nip-0.1.md` or JSON Schema) | Nice-to-have if time | Link from README |
| Real multi-vendor adoption | Out of scope | Roadmap only |

### 12.6 One-line for Demo tag / Tech closer

> Voice is how opaque markets answer the phone. **Purchase Intent is how personalization becomes portable — and an open negotiate protocol is how merchants and personal agents meet without recreating the phone tree.**

---

*Cole owns the pitch package. Everyone else owns truth in their module. The winning submission is a single story told five ways (summary + 3 videos + repo), not five stories fighting for attention.*
