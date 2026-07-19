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

**Dual screen:** fine in **Tech**. In **Demo**, only a tiny 3–5 second “Calling 3 shops…” flash if needed. Demo’s job is the **human conversation**, not the control room.

---

## Story we tell (same everywhere)

1. A lot of buying still happens on the phone — “call for a price.”
2. Same job can get wildly different quotes (up to about **5.6×**). Most people take the first number (~**67%**). Weddings often get charged more for the same work (~**28%**).
3. Nobody has time to call five shops. An agent does.
4. We start with **custom wedding dresses** — stressful, hidden prices, easy to overpay.
5. In 60 seconds we prove: natural talk → price that moves → clear answer with proof.

---

## Project Summary (150–300 words) — paste candidate

Write this **after** the Demo is final so it matches the video.

> A lot of buying still happens on the phone — “call for a price.” For the same job, quotes can swing by as much as 5.6×, and most people still take the first number they hear. The Negotiator is a voice agent that shops those markets for you. You tell it what you want (by voice or from a document). It confirms the details, calls multiple sellers, compares real quotes, and negotiates — then calls you back with a clear recommendation and the proof behind it. We start with custom wedding dresses: high emotion, hidden prices, no time to haggle. In the demo you’ll hear a real back-and-forth with the agent, see a price move during negotiation, and see the final pick with proof from the calls. The same setup can later cover other custom purchases — furniture, jewelry, and more — without rebuilding the core.

---

## Demo video (max 60 sec)

**Goal:** Juror feels the agent *listens*, *gets it*, and *comes back with something solid*.

### What to show

```text
1) YOU call the agent
   → a few natural turns (what you want, size/date, budget)
   → you correct one detail (“ivory, not champagne”)
   → agent repeats back the plan in one short sentence

2) Agent: “Got it. I’ll call some shops and call you back.”

3) Short bridge: “Calling 3 boutiques…”

4) Agent calls YOU back
   → “Best option: Boutique X at $1,850 — down from $2,200.”
   → one proof line (“Here’s the competing quote I used.”)
```

You can read a script. **The agent must sound smooth** — short answers, handles the correction, doesn’t restart from zero, ends with a clear result.

### Rough timing

| Time | What happens |
|---|---|
| 0–5s | Title: “You talk once. It shops. It calls you back.” |
| 5–28s | Call 1 — you and the agent |
| 28–36s | “Calling 3 shops…” |
| 36–52s | Call 2 — agent calls you back with pick + price drop + proof |
| 52–60s | Name + GitHub |

### Demo quality checklist

- [ ] Agent restates what you need in plain words  
- [ ] Handles one correction cleanly  
- [ ] Says it will call shops and call you back  
- [ ] Callback leads with **best pick + price**, then one proof detail  
- [ ] No buzzwords  

**Best case:** real voice both calls.  
**Fine:** rehearsed human + strong agent voice, numbers from a real demo run.

---

## Tech video (max 60 sec)

**Goal:** Show it’s real work, not actors reading a script.

| Time | What to show |
|---|---|
| 0–8s | “While you’re waiting — here’s what the agent does” |
| 8–22s | Three simple boxes: **Listen → Find shops → Negotiate** |
| 22–40s | Screen with 2–3 shops at once; one price ticks down. Caption: “Price moves for real — both sides have limits. Not a script.” |
| 40–52s | “It only uses real competing quotes. Fake ones get blocked.” |
| 52–60s | “Phone for people. Clear details underneath. Other custom markets later.” + GitHub |

That’s where a split view belongs — not in the Demo.

---

## Team video (max 60 sec)

| Time | What |
|---|---|
| 0–8s | “We built The Negotiator” |
| 8–50s | Each person: name + one plain job |
| 50–60s | “Shopping agents for markets that still price by phone.” + GitHub |

| Who | Say |
|---|---|
| Cole | Pitch, finding shops, fairness checks, demo screen |
| Suman | Engine that talks to many shops at once |
| Ella | How shops push back and give discounts |
| Jagger | First call with the customer + why this market |

---

## GitHub, zip, dataset

- **GitHub:** open with the one-line pitch + a screenshot of the callback result; demo runs without API keys.  
- **Zip:** same commit as the public repo.  
- **Dataset:** put **N/A** unless we have a clearly licensed data file.

---

## Shoot order

1. Freeze one dress scenario and three shops.  
2. Nail smooth Call 1 + Call 2.  
3. Shoot **Demo**.  
4. Shoot **Tech** (reuse a few seconds of “calling shops”).  
5. Shoot **Team**.  
6. Write **Summary** to match the Demo.  
7. Zip + upload.

---

## Slack message (paste this)

```text
@channel quick lock on final videos (please read)

The site wants THREE videos, each max 60 seconds: Demo, Tech, Team.

DEMO (the important one for jury gut-feel)
• Not a dual-screen architecture video.
• Show: you call the agent → natural back-and-forth → agent shops → agent CALLS YOU BACK with best pick, price that came down, and proof.
• Human can read a script. Agent must sound smooth (handles a correction, short confirm, clear result).

TECH
• “Listen → Find shops → Negotiate”
• Several shops at once, price ticks down, we don’t invent competing quotes.
• Split screen belongs HERE.

TEAM
• Faces + one plain role each.

Language rule for Demo + Summary + Team: everyday English only. If a juror would need a dictionary, cut the word.

One line for everything:
“You talk once. It shops and haggles. It calls you back with a better deal — and proof.”

Full plan: docs/final-deliverable-proposal.md

@Cole — Demo + summary
@Suman — voice smoothness + tech “many shops” screen
@Ella — shop-side numbers match the callback
@Jagger — first-call script + one pain number from the deck
```

---

## Direct answers

**Should Demo and Tech be separate?**  
Yes. The site requires it, and it’s clearer for jurors.

**Is dual-screen the Demo?**  
No. Dual-screen is Tech. Demo is the two phone calls (you → agent, then agent → you).

**What has to feel real?**  
The agent understanding you, then calling back with a clear deal and proof — not a jargon lecture.

---

*If someone only watches the Demo, they should still understand the whole product.*
