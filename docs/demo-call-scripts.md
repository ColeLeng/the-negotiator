# Demo Call Scripts (read these to the agents)

All scripts target **one dress that really exists in our 12-store inventory**
(`data/market/wedding_stores.csv`), so the Caller returns strong, non-generic matches.

## The target dress

> **Ivory, size US 8, A-line, lace, sweetheart neckline** — the **Stella York 7560** look
> (also matches Allure Bridals, Rebecca Ingram, Mori Lee, Madi Lane, etc.).

Verified search result for this target (top matches):

| Rank | Store | List price | Seller style |
|---|---|---|---|
| 1 | Stella York — 7560 | $1,950 | Upseller |
| 2 | Allure Bridals — C747 | $1,899 | Upseller |
| 3 | Rebecca Ingram — Lauren | $1,900 | Won't quote by phone |
| 4 | Mori Lee — Meredith | $1,980 | Upseller |
| … | Jenny Yoo, Essense, Madi Lane, Maggie Sottero | $1,950–$2,100 | mixed |

Budget for the demo: **target $1,500 · hard max $2,200 · wedding in ~120 days.**

---

## 1) BUYER script — read to the intake agent

The intake agent (Ella plays the buyer). Answer as it asks; it drives one question at a
time. Keep sentences short. The **correction beat** ("ivory, not champagne") is your hero
moment.

> "Hi! I'm looking for a wedding dress. I'd love an **A-line** gown in **champagne**, size
> **US 8**, and the wedding is in about **four months**."

> "I want a **lace** dress with a **sweetheart neckline**. I love the **Stella York** look,
> but I'm open to comparable designers."

> "My budget is around **fifteen hundred dollars**, and my hard maximum is **twenty-two
> hundred**."

> "I'm open to a **sample sale or preowned** gown to save money."

**Correction (do this on purpose):**
> "Actually — make the color **ivory**, not champagne."

**Priorities:**
> "What matters most is the **A-line silhouette**, then the **lace**, then the **designer
> look**."

**Confirm at the read-back:**
> "Yes, that's exactly right."

That produces the buyer-intent JSON that feeds the Caller (→ the 12 stores) and then the
negotiation.

---

## 2) SELLER scripts — read when the agent calls (Cole plays the seller)

Three separate calls, one per style. Each is a **real store** from the inventory. One
human + our agent per call. The agent phones you; you answer as the store.

### Call A — "Tough but fair" · **Maggie Sottero — Willow** (list $2,100)  ← the money shot

Goal: the price **moves** when the agent brings a real competing quote.

- Open firm: "The Willow is twenty-one hundred. That's our price."
- Push a deposit: "We'd need a deposit to hold it."
- When the agent cites a **real** competing quote (e.g. "Rebecca Ingram has a comparable
  lace gown at nineteen hundred"): give ground once →
  "Okay — I can do **eighteen fifty** if you book this week."
- Don't go below **~$1,750**. Close with a firm number.

### Call B — "Won't quote by phone" · **Rebecca Ingram — Lauren** (list $1,900)

Goal: the agent must extract a **range or a firm callback**, not a brush-off.

- Deflect first: "We really only give pricing at an in-store appointment."
- If the agent presses politely: give a **range** → "Comparable gowns run about
  **seventeen to nineteen hundred**," or offer "I can have a stylist **call you back
  tomorrow with a firm number**."
- End with a concrete outcome (a range or a scheduled callback) — never a vague "it
  depends."

### Call C — "Upseller" · **Stella York — 7560** (list $1,950)  ← the exact target dress

Goal: the agent **itemizes and strips** padded add-ons.

- Lead with a bundle: "The 7560 is nineteen fifty, and with the **veil**, **beading
  upgrade**, and **rush**, you're looking at about **twenty-six hundred** all in."
- When the agent asks you to itemize: break it out — gown $1,950, veil $300, beading $250,
  rush $200.
- Let the agent decline the extras: "Sure, without those it's just the **nineteen fifty**
  gown." Optionally shave to ~$1,850 for cash/prepay.

---

## Why this set works for judging

- **Real leverage / moving price:** Call A drops because of Call B's real quote — honest
  BATNA, not a bluff.
- **Three distinct styles** in three calls (tough / stonewaller / upseller).
- **Structured endings:** a firm quote (A), a callback or range (B), an itemized quote (C).
- **Comparable, itemized quotes** across the same spec — exactly what the final ranked
  report needs.

Say out loud that the sellers are our own store personas (honest about the setup).
