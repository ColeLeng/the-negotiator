# Ella — Seller Agent technical requirements (agent-to-agent)

**Audience:** Ella (seller side) · **Contracts owner:** Suman §4 / §8 · **Caller handoff:** Cole  
**Canonical architecture:** [`technical-architecture.md`](technical-architecture.md)  
**Runnable scaffold:** [`negotiator/agents/seller_agent.py`](../negotiator/agents/seller_agent.py) · [`negotiator/seller_value.py`](../negotiator/seller_value.py)

This doc freezes what Ella must build so the **Caller’s agent-to-agent path** can demo live negotiations against **≥3 distinct negotiation styles**, with every quote in **structured, comparable, fee-itemized** form.

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

Required APIs (already stubbed in `seller_value.py` — deepen, don’t rename):

| Function | Contract |
|---|---|
| `dynamic_floor(state) -> float` | Inventory/capacity modulate reservation in real time |
| `surplus(offer_price, state) -> float` | Pure; no I/O |
| `next_seller_min(state, round, max_rounds) -> float` | Concession curve list → floor (never below floor) |
| `bundled_ask` / `upsell_ask` | Upseller open + strip-addon concede path |

**Nice-to-have:** capacity penalty (longer lead time instead of discount when `at_capacity`); strategic bonus for clearing aged SKUs.

---

## 6. Per-turn I/O

```python
class SellerAgent:
    def __init__(self, state: SellerState, max_rounds: int = 6): ...
    def open(self) -> NegotiationMessage: ...
    def respond(self, inbound: NegotiationMessage) -> NegotiationMessage: ...
    def evaluate(self, offer_price: float) -> float: ...
    def should_accept(self, offer_price: float) -> bool: ...   # TODO deepen
    def should_walk(self, ctx) -> bool: ...                    # TODO deepen
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

| | Min demoable (ship) | Nice-to-have |
|---|---|---|
| Policy | One inventory flag changes concede speed; three style branches | Full capacity + bundle planner + multi-attr trades |
| Channel | Works on `MockChannel` | Same agent over `UCPChannel` with zero logic change |
| LLM | Deterministic policy (current scaffold) | Claude-backed `next_seller_move` with tool calls to value model |
| Evals | Fixture: aging stock concedes more than fresh | Golden transcripts per style |

---

## 11. Test checklist Ella owns

```text
tests/test_seller_value.py     # dynamic_floor drops with stock age; surplus sign
tests/test_seller_styles.py    # three styles → three distinct message trajectories
tests/test_seller_itemization.py  # accept path yields fee lines covering final price
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
source .venv/bin/activate
python run_demo.py          # watch three styles + itemized endings
pytest -q tests/test_caller.py tests/test_negotiation.py
```

Deepen `SellerAgent._respond_*` and `seller_value.*` behind the same signatures; keep `run_demo.py` green.
