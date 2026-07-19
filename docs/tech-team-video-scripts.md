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
| 52–60s | "A phone agent for people, with clear details underneath — wedding dresses today, other custom markets next. That's The Citable Negotiator. Code's on GitHub." | Closing card: one-line pitch + **GitHub URL.** |

### Teleprompter block (Tech — read straight through)

> You just heard the agent on a real call. Here's what it's doing underneath while it talks.
>
> It does three simple things. It listens and writes down exactly what you want. It finds real shops that actually have it. Then it calls them and negotiates.
>
> Watch the right side while the seller call plays. The agent pulls up a real competing quote — about nineteen hundred at another shop — and uses it. The seller's price comes down from twenty-one hundred to eighteen-fifty. Live, on the call.
>
> And it can only use a quote that's actually real. If the agent ever tried to invent a competing offer, our honesty guard blocks it before it's ever said.
>
> A phone agent for people, with clear details underneath — wedding dresses today, other custom markets next. That's The Citable Negotiator. Code's on GitHub.

### Tech quality checklist

- [ ] Trace screen (right) is time-synced to the real seller call (left).
- [ ] The price move on screen is **$2,100 → $1,850** and matches the call audio.
- [ ] The competing quote shown is the **real** one (~$1,900), not invented.
- [ ] The guard/"blocked fake quote" moment is visible for at least ~2 seconds.
- [ ] No jargon on camera; GitHub link shown at the end.

---

# Team video (≤ 60 sec) — "who built it *and why it matters*"

**Job of the video:** the juror thinks "solid people — and I get why this matters." This
is the **only** video where the humans talk to the camera, so it carries **the vision and
the impact**, not just names. Keep the *feel* in the Demo and the *proof it's real* (trace
+ honesty guard) in the Tech; here we say, in order: **why we built it → who built it →
where it goes.** Don't re-tour features.

**So — team only, or vision/impact too?** Both, in the Team video, because there's
nowhere else the founders speak. Split it like this:

| Put in Team | Leave in its own video |
|---|---|
| The one-line vision + **one** pain number (the "why") | The full customer call / price move (**Demo**) |
| Faces + name + one plain job each (the "who") | The trace screen + honesty guard (**Tech**) |
| Where it goes next — the business (the "so what") | A feature walkthrough (belongs nowhere — cut it) |

Film each person separately, cut them together. Cole carries the voiceover open/close.

### Script

| Time | Who | SAY (word-for-word) | SHOW |
|---|---|---|---|
| 0–8s | Cole (VO) | "A lot of buying still happens on the phone — 'call for a price' — and most people take the first number they hear." | Title card: **The Citable Negotiator.** B-roll: a phone, "call for a price." |
| 8–16s | Cole (VO) | "For the same job, quotes can swing five-point-six times. Nobody has time to call five shops. So we built an agent that does." | One bold stat fills the screen: **5.6× for the same job.** |
| 16–24s | **Cole** | "I'm Cole — I turn your phone call into a clear plan to shop with, and I lead the pitch." | Cole to camera; name lower-third. |
| 24–32s | **Suman** | "I'm Suman — I built the engine that actually talks the price down." | Suman to camera; name lower-third. |
| 32–40s | **Jagger** | "I'm Jagger — I built the live view of the agent thinking, and the research on why this market overcharges." | Jagger to camera; name lower-third. |
| 40–48s | **Ella** | "I'm Ella — I built the shops it calls: real prices, real limits, real haggling." | Ella to camera; name lower-third. |
| 48–60s | Cole (VO) | "You talk once. It shops, haggles, and calls you back with a better deal — and proof. Wedding dresses today, more custom markets next. That's The Citable Negotiator." | Closing card: one-line pitch + **GitHub URL.** |

### Teleprompter block (Team — read straight through)

> **(Cole, VO):** A lot of buying still happens on the phone — "call for a price" — and most people take the first number they hear.
>
> **(Cole, VO):** For the same job, quotes can swing five-point-six times. Nobody has time to call five shops. So we built an agent that does.
>
> **(Cole):** I'm Cole — I turn your phone call into a clear plan to shop with, and I lead the pitch.
>
> **(Suman):** I'm Suman — I built the engine that actually talks the price down.
>
> **(Jagger):** I'm Jagger — I built the live view of the agent thinking, and the research on why this market overcharges.
>
> **(Ella):** I'm Ella — I built the shops it calls: real prices, real limits, real haggling.
>
> **(Cole, close):** You talk once. It shops, haggles, and calls you back with a better deal — and proof. Wedding dresses today, more custom markets next. That's The Citable Negotiator.

### Team quality checklist

- [ ] Opens on the **vision + one pain number** (5.6×) — the "why," not a feature.
- [ ] Every person shows their face and says their **name** + **one plain job**.
- [ ] Names as lower-thirds so jurors can match voice to face.
- [ ] Closes on **where it goes next** (the business), and names **The Citable Negotiator**.
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
