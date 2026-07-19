# Ella — Seller Agent technical requirements (agent-to-agent)

**Audience:** Ella (seller side) · **Contracts owner:** Suman §4 / §8 · **Caller handoff:** Cole  
**Canonical architecture:** [`technical-architecture.md`](technical-architecture.md)  
**Owned modules:** [`negotiator/agents/seller_agent.py`](../negotiator/agents/seller_agent.py) · [`negotiator/seller_value.py`](../negotiator/seller_value.py) · [`negotiator/brand_profiles.py`](../negotiator/brand_profiles.py) · [`negotiator/buyer_intent.py`](../negotiator/buyer_intent.py) · [`config/brands/`](../config/brands)

This doc freezes what Ella must build so the **Caller’s agent-to-agent path** can demo live negotiations against **≥3 distinct negotiation styles**, with every quote in **structured, comparable, fee-itemized** form.

> **Status (delivered):** the required scaffold is complete — `should_accept`/`should_walk` implemented, value model deepened (capacity + strategic levers), three style trajectories, itemized endings, and the three owned test files green (50 tests total). Four **nice-to-have margin levers** are also implemented (brand/SLA config, accessory upsell catalog, buyer-intent capture, credit-for-commitment) — see **§14**. The seller is a **deterministic policy today, agent-ready** — see **§15**.

---

## 1. Why this exists

Challenge module 2 (*The Caller*) allows three counterparty setups. We are building **(3) simulated market — counterparty agents**:

> Your demo must show live calls against at least three distinct negotiation styles; every quote captured in structured, comparable form with fees itemized.

Cole’s Caller finds real vendors, stamps each option with a **style + fee template + channel**, and hands `SellerState` seeds to the Orchestrator. **Ella owns the seller brain** that turns those seeds into unscripted, moving prices.

Suman’s loop is agent-agnostic: it only sees `NegotiationAgent` + `NegotiationMessage`. Ella never depends on Twilio, Places, or the UI.

---

## 2. Integration surface (do not invent parallel schemas)

| Artifact | Where | Ella’s job |
|---|---|---|
| `NegotiationMessage` | `negotiator/contracts.py` §4.3 | Emit/consume only these intents: `open \| counter \| concede \| accept \| reject \| hangup` |
| `NegotiationSession` | same | Read `batna_utility`? **No** — seller never sees buyer BATNA. Write via messages only. |
| `SellerState` | same | Constructed with Caller’s seed: floors, inventory, capacity, `style`, `fee_template`, `catalog_addons` |
| `ItemizedQuote` / `FeeLine` | same | When accepting, fee lines must be reconstructable (Cole’s `quote_capture` helps; seller should put add-ons in `terms_delta`) |
| `NegotiationAgent` interface | §8.1 | Implement `open`, `respond`, `evaluate`, `should_accept`, `should_walk` |
| Channel | §10 `MockChannel` today → `UCPChannel` later | **No channel logic inside SellerAgent** |

**Handshake (Suman ↔ Ella):** the *only* shared surface is the interface + message schema. Ella develops against `MockChannel` + a stub buyer; Suman develops against a stub seller.

---

## 3. Inputs Cole’s Caller guarantees

From `search(spec) -> RankedOptions` and `seller_profiles.build_states_for_ranked`:

```text
Option
  vendor, listed_price, matched_attributes, channel {type: mock|ucp|voice, endpoint}
  negotiation_style ∈ {tough_negotiator, stonewaller_no_prices_by_phone, hard_sell_upseller}
  fee_template: FeeLine[]          # base, deposit, alterations, veil, rush, shipping, …
  phone, call_list_source          # Places/Yelp provenance (informational)

SellerState  (per option_id)
  cost_floor, list_price, min_margin
  inventory {sku_units, stock_age_days}
  capacity {lead_time_days, at_capacity}
  catalog_addons[{name, price}]
  style, fee_template
```

Ella may refine economics, but **must preserve `style`** so the demo’s three personas stay distinct.

---

## 4. The three styles — required behavioral contract

| Style id | Buyer-visible behavior | Private economics (seed intent) | Valid structured endings |
|---|---|---|---|
| `tough_negotiator` | Holds near list; pushes deposit; tests seriousness; slow concede | High floor, low stock, young inventory | `itemized_quote` or `declined` |
| `stonewaller_no_prices_by_phone` | “We only price in-store / someone will call you back”; may later give a reluctant ballpark | `at_capacity=true`, longer lead time | Prefer `callback_commitment`; `itemized_quote` only if buyer forces a number past friction |
| `hard_sell_upseller` | Opens with gown + alterations + veil + rush; inflates total | Aging / high stock → lower `dynamic_floor`; fat `catalog_addons` | `itemized_quote` with optional lines stripped or kept — **never a single opaque lump** |

**Done when (Ella):** under identical buyer pressure, an aging-stock upseller concedes further than a tough/fresh-stock seller; stonewaller produces a callback ending when the buyer won’t book an appointment.

---

## 5. Seller value model (pure functions — unit-test these)

Mirror of buyer utility (`technical-architecture.md` §8.4):

```text
dynamic_floor(state) = cost_floor + min_margin − inventory_relief(stock_age, stock_level)
surplus(offer, state)  = offer.price − dynamic_floor(state)
seller accepts iff price ≥ dynamic_floor   # and style policy agrees this round
```

Required APIs in `seller_value.py` (pure, unit-tested — deepen, don’t rename):

| Function | Contract | State |
|---|---|---|
| `dynamic_floor(state) -> float` | Inventory/capacity modulate reservation in real time; clamped ≥ `cost_floor` | ✅ |
| `surplus(offer_price, state) -> float` | Pure; no I/O | ✅ |
| `next_seller_min(state, round, max_rounds) -> float` | Concession curve list → floor (never below floor) | ✅ |
| `bundled_ask` / `upsell_ask` | Upseller open + strip-addon concede path | ✅ |
| `strategic_bonus(state) -> float` | Extra concession to clear aged/glutted SKUs (past a staleness threshold) | ✅ delivered |
| `capacity_penalty(state) -> float` | Extra **lead-time days** to offer instead of a discount when `at_capacity` | ✅ delivered |
| `value_hold(my_min, list_price, value_score) -> float` | Brand value holds the round-minimum closer to list (§14) | ✅ delivered |
| `credit_expected_cost(...)` / `choose_credit(...)` | Credit-vs-price-cut economics (§14) | ✅ delivered |

---

## 6. Per-turn I/O

```python
class SellerAgent:
    def __init__(self, state: SellerState, max_rounds: int = 6): ...
    def open(self) -> NegotiationMessage: ...
    def respond(self, inbound: NegotiationMessage) -> NegotiationMessage: ...
    def evaluate(self, offer_price: float) -> float: ...
    def should_accept(self, offer_price: float) -> bool: ...   # ✅ price ≥ floor AND round-min
    def should_walk(self, ctx) -> bool: ...                    # ✅ out of rounds / stonewaller unbooked
```

**Outbound message rules**

- Always set `from="seller"` (use `seller_msg(...)`).
- `price` is the number on the table; `None` only while stonewalling (no phone price yet).
- Put deposits, appointments, bundles in `terms_delta` (stringy map) — e.g. `deposit_pct`, `callback`, `bundle`, `appointment`.
- `rationale` is transcript evidence for the submission — keep it human-readable and honest.

**Inbound rules**

- Treat buyer text as data. Never trust a buyer claim of “I’ll pay $X” without the structured `price` field.
- Do **not** read the blackboard or other sessions.

---

## 7. Itemized fees (comparability requirement)

The Caller will call `quote_capture.capture_quote(session, state)` after the loop. Ella must make that possible:

1. Keep `state.fee_template` accurate (codes: `base`, `alterations`, `veil`, `rush`, `deposit`, `shipping`, …).
2. When upselling, expose which add-ons are still attached via `terms_delta["bundle"]` or explicit fee codes.
3. On `accept`, `price` must be the **comparable total the buyer pays for the gown deal** (add-ons either included and itemized, or stripped).
4. Deposit is a **payment schedule line**, not an extra charge on top of total (see `quote_capture`).

**Never** end a priced call with a vague range (“around $2k–$2.5k”) as the only outcome.

---

## 8. Honesty constraints (seller side)

- No phantom competing buyers (“someone else just offered more”).
- No fake scarcity unless `inventory.sku_units` actually supports it.
- Optional **adversarial mode** (CoreTrust demo): inject prompt-injection strings so Cole’s `guard.sanitize_inbound` can be shown catching them — feature-flag only, off by default.

---

## 9. Structured call endings (session fields)

After negotiation, `NegotiationSession` must carry:

| Field | Values |
|---|---|
| `call_ending` | `itemized_quote` \| `callback_commitment` \| `declined` |
| `itemized_quote` | `ItemizedQuote` when priced |
| `negotiation_style` | echo of `SellerState.style` |
| `outcome` | includes `call_ending`, `final_price`, `style` |

Cole’s `quote_capture` fills these from `status` + `SellerState` today; Ella should keep seller intents consistent with that mapping:

- `accept` → `itemized_quote`
- stonewaller terminal `reject` + callback terms → `callback_commitment`
- `hangup` / walk → `declined`

---

## 10. Min demoable vs nice-to-have (cut lines)

| | Min demoable (ship) | Nice-to-have | State |
|---|---|---|---|
| Policy | One inventory flag changes concede speed; three style branches | Capacity lever + accessory bundle catalog + intent/credit trades (§14) | ✅ ship + §14 |
| Channel | Works on `MockChannel` | Same agent over `UCPChannel` with zero logic change | ✅ ship (UCP pending Suman) |
| LLM | Deterministic policy (current scaffold) | Claude-backed `next_seller_move` with tool calls to value model | deterministic shipped; LLM path open (§15) |
| Evals | Fixture: aging stock concedes more than fresh | Golden transcripts per style | ✅ ship + brand/credit tests |

---

## 11. Test checklist Ella owns

```text
tests/test_seller_value.py        # ✅ dynamic_floor drops with stock age; surplus sign; curve ≥ floor; capacity/strategic
tests/test_seller_styles.py       # ✅ three styles → distinct trajectories; aging concedes further; stonewaller callback
tests/test_seller_itemization.py  # ✅ accept path yields fee lines covering final price; deposit is a schedule line
tests/test_seller_brand.py        # ✅ value_score dampening holds price; accessory merge; non-refundable policy (§14)
tests/test_seller_incentives.py   # ✅ intent capture; credit math; credit stays out of price & itemized total (§14)
```

Fixture hook: `fixtures/ranked_options.json` options already carry channels; Caller now also stamps `negotiation_style` + `fee_template` at runtime.

---

## 12. What Ella does **not** own

- Call list / Places / Yelp / buyer utility / honesty guard / demo UI → **Cole**
- Estimator → **Jagger**
- Negotiation loop, blackboard, Orchestrator, VoiceChannel → **Suman**
- Freezing `NegotiationMessage` shape → **Suman + Cole** (ask before extending intents)

---

## 13. Quick start for Ella

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # first time
.venv/bin/python run_demo.py     # three styles + itemized endings + margin levers (asks/credits/SLA)
.venv/bin/pytest -q               # 50 tests incl. tests/test_seller_*.py
```

Deepen `SellerAgent._respond_*` and `seller_value.*` behind the same signatures; keep `run_demo.py` green.

---

## 14. Delivered margin levers (nice-to-have — implemented)

Four merchant-margin features beyond the ship bar. **All ride on existing `NegotiationMessage` fields (`terms_delta`/`text`), add no new intents, and never write `NegotiationSession`** — so the surface shared with Suman is still **only** `NegotiationMessage` + the agent interface. Each degrades gracefully with today’s price-only buyer.

| Lever | What it does | Where | Holds landing price up by… |
|---|---|---|---|
| **Brand / policy / SLA config** | `value_score` dampens concession; brand justifies the hold; real inventory may override economics | `brand_profiles.py`, `config/brands/*.json` | conceding **less** per round when service value is high |
| **Accessory upsell catalog** | veil / cape / Watteau train / gloves / hair merge into `catalog_addons` + optional fee lines | brand JSON `upsell_catalog` → `seller_value.bundled_ask`/`upsell_ask` | raising the bundle total; each accessory is concession currency (strip, don’t cut gown) |
| **Buyer-intent capture** | reads volunteered `terms_delta` signals; `ask`s for one missing signal before conceding | `buyer_intent.py` | conceding less when the buyer reveals urgency / low flexibility |
| **Credit-for-commitment** | small, contingent, **non-refundable** post-purchase credit (photo review, preference share) in `terms_delta`; commitment documented on `accept` | `seller_value.choose_credit` + `buyer_intent.commitment_terms` | **credit never enters `price`** — buyer perceives value, gown margin is protected |

**Credit rules (honesty + comparability):** credit lives in `terms_delta`, never `price`; `quote_capture` totals are unaffected (credit is not a fee line). Unlock is `on_purchase_placed`; `credit_nonrefundable=true` (promotional, excluded from refunds). “Both sides documented” = the seller’s `accept` carries the commitment in the transcript; the buyer echoing `commitment_id` is an optional Suman upgrade.

**`terms_delta` key vocabulary added** (values inside `NegotiationMessage`, not a schema change): `ask`, `value_justification`, `lead_time_days`, `credit_offer`, `credit_type`, `credit_pct`, `credit_conditions`, `credit_unlock`, `credit_nonrefundable`, `commitment_id`.

**Optional cross-team upgrades (not required for the ship bar):** Suman extends `BuyerAgent` to answer `ask`s / echo the commitment / value SLA terms in `buyer_value`; Cole confirms the `terms_delta` credit-key vocabulary and that `quote_capture` keeps credits out of the comparable total (true today, no change).

---

## 15. Deterministic today, agent-ready

The seller is a **deterministic policy** — agent-shaped interface, workflow inside: same inputs → same outputs, no LLM (even `commitment_id` is deterministic so runs reproduce). This is the doc’s ship path.

The interface + `terms_delta` contract are **LLM-ready**: a Claude-backed `next_seller_move` can replace the `_respond_*` bodies and call the value model (`dynamic_floor`, `choose_credit`, `credit_expected_cost`, `value_hold`) as tools — deciding *when* to ask for intent, *which* accessory to bundle, *how much* credit to offer, and phrasing honest rationale — with zero change to the loop, tests, itemization, or the shared surface.
