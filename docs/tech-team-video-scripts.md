# Tech + Team Video Scripts (read these to camera / teleprompter)

Companion to [`demo-call-scripts.md`](demo-call-scripts.md) (the on-call buyer + seller
lines). This file is the **narration** for the other two required videos. Every spoken
line is written **word-for-word** so you can drop it straight into a teleprompter and
read it — no improvising on camera.

**The rules we're honoring** (from [`final-deliverable-proposal.md`](final-deliverable-proposal.md)):

- Three videos, each **≤ 60 seconds**, MP4/MOV.
- **Demo** = how it feels · **Tech** = how it works · **Team** = who built it.
- Plain, everyday English. If a word needs a footnote, cut it.
- Numbers only from Jagger's market deck / the challenge brief: **5.6×** price spread,
  ~**67%** take the first number, weddings ~**28%** more for the same work.
- Every number on screen matches the one frozen scenario in
  [`demo-call-scripts.md`](demo-call-scripts.md): **Maggie Sottero — Willow $2,100 → $1,850**,
  dropped by a **real** competing quote (**Rebecca Ingram — Lauren, ~$1,900**).

How to read the tables: **SAY** = read this out loud, exactly. **SHOW** = what's on
screen while you say it. The full spoken track is repeated at the bottom of each section
as a clean teleprompter block (no stage directions).

---

# Tech video (≤ 60 sec) — "how it works"

**Narrator:** one clear voice (Cole). **Job of the video:** prove this is real work, not
two actors reading a screenplay. **Hero shot:** Jagger's live trace screen
(`/trace/view`) on the **right**, the real seller call playing on the **left**, price
moving in time with the audio.

### What you need on screen before you record

- **Left:** the real **Call A** recording (Maggie Sottero — Willow, "tough but fair").
- **Right:** the trace screen at `GET /trace/view` running the **same** scenario, so its
  events line up with the call audio (session spawned → buyer/seller turns with price →
  guard note → outcome).
- A big **caption** ready to pop when the price moves: **$2,100 → $1,850**.

### Script

| Time | SAY (word-for-word) | SHOW |
|---|---|---|
| 0–8s | "You just heard the agent on a real call. Here's what it's doing underneath while it talks." | Title card: **"How it works."** Then split screen appears: seller call left, trace screen right. |
| 8–22s | "It does three simple things. It listens and writes down exactly what you want. It finds real shops that actually have it. Then it calls them and negotiates." | Three boxes light up one at a time: **Listen → Find shops → Negotiate.** |
| 22–42s | "Watch the right side while the seller call plays. The agent pulls up a real competing quote — about nineteen hundred at another shop — and uses it. The seller's price comes down from twenty-one hundred to eighteen-fifty. Live, on the call." | Left: the Willow call audio at the concession beat. Right: trace feed scrolls the buyer turn citing the competing quote, then the seller's lower number. **Caption pops: $2,100 → $1,850.** |
| 42–52s | "And it can only use a quote that's actually real. If the agent ever tried to invent a competing offer, our honesty guard blocks it before it's ever said." | Right screen shows a **guard** line marking a stripped/blocked claim. |
| 52–60s | "A phone agent for people, with clear details underneath — wedding dresses today, other custom markets next. Code's on GitHub." | Closing card: one-line pitch + **GitHub URL.** |

### Teleprompter block (Tech — read straight through)

> You just heard the agent on a real call. Here's what it's doing underneath while it talks.
>
> It does three simple things. It listens and writes down exactly what you want. It finds real shops that actually have it. Then it calls them and negotiates.
>
> Watch the right side while the seller call plays. The agent pulls up a real competing quote — about nineteen hundred at another shop — and uses it. The seller's price comes down from twenty-one hundred to eighteen-fifty. Live, on the call.
>
> And it can only use a quote that's actually real. If the agent ever tried to invent a competing offer, our honesty guard blocks it before it's ever said.
>
> A phone agent for people, with clear details underneath — wedding dresses today, other custom markets next. Code's on GitHub.

### Tech quality checklist

- [ ] Trace screen (right) is time-synced to the real seller call (left).
- [ ] The price move on screen is **$2,100 → $1,850** and matches the call audio.
- [ ] The competing quote shown is the **real** one (~$1,900), not invented.
- [ ] The guard/"blocked fake quote" moment is visible for at least ~2 seconds.
- [ ] No jargon on camera; GitHub link shown at the end.

---

# Team video (≤ 60 sec) — "who built it"

**Job of the video:** the juror thinks "solid people." Faces + one plain job each — no
feature tour. Each person reads **their own line to camera**; keep it first-person and
short. Film each person separately, cut them together.

### Script

| Time | Who | SAY (word-for-word) | SHOW |
|---|---|---|---|
| 0–8s | Narrator (Cole) | "We built The Negotiator — a phone agent that shops and haggles for you." | Team title card / group shot. |
| 8–18s | **Cole** | "I'm Cole. I turn what you say on the phone into a clear plan the agent can shop with — and I put the pitch together." | Cole to camera; name lower-third. |
| 18–28s | **Suman** | "I'm Suman. I built the engine that runs the back-and-forth — the part that actually talks the price down." | Suman to camera; name lower-third. |
| 28–40s | **Jagger** | "I'm Jagger. I built the live screen that shows what the agent is thinking, and I dug up why this market overcharges people." | Jagger to camera; name lower-third. |
| 40–50s | **Ella** | "I'm Ella. I built the shops the agent calls — real-world prices, their limits, and the different ways they haggle." | Ella to camera; name lower-third. |
| 50–60s | Narrator (Cole) | "Shopping agents for markets that still price by phone. Code's on GitHub." | Closing card: one-line pitch + **GitHub URL.** |

### Teleprompter block (Team — one line per person)

> **(Cole, open):** We built The Negotiator — a phone agent that shops and haggles for you.
>
> **(Cole):** I'm Cole. I turn what you say on the phone into a clear plan the agent can shop with — and I put the pitch together.
>
> **(Suman):** I'm Suman. I built the engine that runs the back-and-forth — the part that actually talks the price down.
>
> **(Jagger):** I'm Jagger. I built the live screen that shows what the agent is thinking, and I dug up why this market overcharges people.
>
> **(Ella):** I'm Ella. I built the shops the agent calls — real-world prices, their limits, and the different ways they haggle.
>
> **(Cole, close):** Shopping agents for markets that still price by phone. Code's on GitHub.

### Team quality checklist

- [ ] Every person shows their face and says their **name** + **one plain job**.
- [ ] Names as lower-thirds so jurors can match voice to face.
- [ ] No feature tour, no diagrams — this video is about the people.
- [ ] Same one-line pitch + GitHub as the other two videos.

---

## Recording notes (both videos)

- Read at a calm pace — the whole spoken block for each video is written to land under
  **60 seconds** with room to breathe. If you're rushing to fit, cut a sentence, don't
  speed up.
- Keep the **one line** everywhere: *"You talk once. It shops and haggles. It calls you
  back with a better deal — and proof."*
- Follow the capture + edit steps in [`final-deliverable-proposal.md`](final-deliverable-proposal.md)
  ("How to record" + "Recording SOP"): screen-record locally with OBS, grab the
  ElevenLabs recording as master audio, Cole assembles.
