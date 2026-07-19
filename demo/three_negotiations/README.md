# Three negotiations to design (Cole voices all three)

Lives **outside** `negotiator/` on purpose: this is demo-rehearsal scaffolding for one
specific recording session, not a permanent module any other owner's code imports.
Nothing in here changes `negotiator/`, `app/main.py`'s existing routes, or any other
teammate's files beyond two thin new routes that just call into this folder.

The challenge wants **at least three different seller styles**. Cole plays all three
(short, separate calls). Each one proves a different success-criteria bullet, so
together they cover a lot.

| # | Seller style | How Cole plays it | What the agent must do | Proves |
|---|---|---|---|---|
| 1 | **Tough but fair** | Holds firm, pushes a deposit, but will deal | Bring up a real competing quote → price comes down | **Price moves during the call** (the money shot) |
| 2 | **Won't quote by phone** | "We only give prices at an in-store appointment." | Politely push → get a firm callback / price range instead of a vague brush-off | **Every call ends with a real outcome** (a callback commitment) |
| 3 | **Upseller** | Piles on rush fees, veil, alterations to inflate the total | Itemize every fee and strip the non-essentials | **Quotes are itemized and comparable** |

Also worked into call #1:
- Agent **says it's an AI** up front, and again if asked "are you a robot?"
- Agent handles a little **friction** — an interruption or a "we're busy, call back."
- Agent **never invents** a competing quote — it only ever uses one the buyer really has.

That set of three calls covers: 3 styles · price moves · honesty + disclosure · friction ·
structured endings · itemized quotes.

## What's actually live code here vs. scripted

This is a **rehearsal harness**, not a new agent. The goal is to let the real pipeline
run against a stand-in for Cole's voice before the actual call, and to give the
left-screen trace panel something true to render. Being explicit about what's real:

- **Real, unmodified, for all three calls:** `negotiator.agents.buyer_agent.BuyerAgent`,
  `negotiator.comms.blackboard.Blackboard`, `negotiator.comms.loop.run_negotiation`,
  `negotiator.guard.guard_outbound` (the honesty guard actually runs on every buyer
  message), and `negotiator.tracing.Tracer`.
- **Scripted:** the seller's side of the conversation (`scenarios.py`) — in the real
  recording this is Cole's voice; here it's a fixed message sequence per style so the
  harness is deterministic and runnable without a phone call.
- **Scenario 1 (tough-but-fair) is the most "real":** the competing-quote line the
  buyer uses is not hand-written — `runner.py` reads the *actual* live value off
  `Blackboard.best_excluding()` and only asserts it after routing the resulting
  message through the real `guard_outbound()`, so what you see on screen is the real
  honesty guard passing a claim precisely because it's backed by real data.
- **Scenarios 2 and 3 use a scripted price/terms sequence, not scripted BuyerAgent
  logic** — `BuyerAgent` genuinely doesn't know about "extract a callback" or "strip
  this line item" yet (that's Suman's/Ella's TODO for turn-level terms negotiation).
  The seller script for #2 delays a number for two rounds before giving a range; the
  seller script for #3 folds the add-on fees into its opening ask so the *real*
  `BuyerAgent` still negotiates down using its actual Boulware price logic, while the
  itemized fee breakdown shown in the panel is an annotation the scenario computes,
  not a line-by-line negotiation the agent conducted. This is flagged in the UI
  (`scripted` badge) rather than presented as something it isn't.

## Files

| File | What it does |
|---|---|
| `scenarios.py` | The three seller scripts + `ScriptedSellerChannel` (implements the same `SellerChannel` protocol as `MockChannel`/`VoiceChannel`) |
| `runner.py` | Runs one or all three scenarios against the real `BuyerAgent`, tags every `TraceEvent` with its `style`, and computes each scenario's proof-point checklist from the resulting transcript |
| `view.html` | The left-screen panel for this recording: three lanes (one per call), each with its own live transcript feed and a checklist that ticks green as proof points land |

Wired into the existing app via two routes in `app/main.py` (owners: Suman/Cole — only
these two lines were added there, everything else lives in this folder):

```
GET /demo/three-negotiations/stream   # SSE, all three scenarios run in sequence
GET /demo/three-negotiations/view     # the panel itself, no build step
```
