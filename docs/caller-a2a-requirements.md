# Caller — agent-to-agent technical requirements (Cole)

**Owner:** Cole · **Architecture:** Suman [`technical-architecture.md`](technical-architecture.md) §4.2 / §6  
**Challenge brief:** module 2 — *Parallel Quote Gathering*  
**Seller counterpart:** Ella — [`ella-seller-a2a-requirements.md`](ella-seller-a2a-requirements.md)

---

## Goal

Produce a `RankedOptions` list the Orchestrator can fan out into **≥3 parallel agent-to-agent sessions**, each against a **distinct negotiation style**, and ensure every session ends with a **structured, fee-itemized, comparable quote** (or a documented callback / decline).

Counterparty setup for this path: **built seller agents** (not live Twilio). Voice/human role-play remain valid alternate setups behind the same `channel` field.

---

## Pipeline

```text
ProductSpec
    │
    ▼
call_list.discover_call_list()     # Places → Yelp → curated pad (provenance always set)
    │
    ▼
web fan-out (Tavily/Serper/Brave/Exa) if keys present
    │
    ▼
score + filter (buyer_value.utility / is_feasible)
    │
    ▼
seller_profiles.assign_styles()    # tough / stonewaller / upseller + fee_template
    │
    ▼
RankedOptions  ──►  Orchestrator  ──►  BuyerAgent ⇄ SellerAgent (MockChannel)
                                              │
                                              ▼
                                    quote_capture.capture_quote()
                                              │
                                              ▼
                         itemized_quote | callback_commitment | declined
```

---

## Module map (Cole)

| File | Responsibility |
|---|---|
| `negotiator/call_list.py` | Google Places / Yelp Fusion / curated Places-shaped catalog |
| `negotiator/caller.py` | `search(spec) -> RankedOptions` |
| `negotiator/seller_profiles.py` | Style stamps + `SellerState` seeds for Ella |
| `negotiator/quote_capture.py` | Structured call endings + `ItemizedQuote` |
| `negotiator/buyer_value.py` | Scoring / feasibility (already owned) |
| `negotiator/guard.py` | Honesty on the buyer wire (already owned) |

---

## Contracts added for this path

- `FeeLine`, `ItemizedQuote` — comparable fee breakdown  
- `CallListProvenance` — `provider` ∈ `google_places | yelp | curated_catalog | web_search`  
- `NegotiationStyleId` — the three challenge personas  
- `CallEnding` — `itemized_quote | callback_commitment | declined`  
- `Option.negotiation_style`, `.fee_template`, `.phone`, `.call_list_source`  
- `RankedOptions.call_list_provenance`  
- `SellerState.style`, `.fee_template`  
- `NegotiationSession.call_ending`, `.itemized_quote`, `.negotiation_style`

---

## Done-when checks

1. `search(spec)` returns ≥3 options with real `http` URLs (or live Places phones).  
2. Top-3 options have **three different** `negotiation_style` values.  
3. `call_list_provenance` is present and names Places/Yelp (or the curated stand-in + how to enable live).  
4. After `orchestrator.run`, each session has a `call_ending`; agreed sessions have `itemized_quote.line_items` covering the deal.  
5. Fees are itemized (base + deposit + optional alterations/veil/rush/shipping as applicable) — never a vague range.

---

## Env keys

```bash
GOOGLE_PLACES_API_KEY=    # live call list
YELP_FUSION_API_KEY=      # fallback live call list
TAVILY_API_KEY= / SERPER_API_KEY= / BRAVE_API_KEY= / EXA_API_KEY=   # web fan-out
```

No keys required for the mock demo path.
