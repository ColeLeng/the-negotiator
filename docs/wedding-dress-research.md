# Wedding-Dress Negotiation — Scenario Narrowing + Research & Data Support

**Owner:** Cole · **Status:** ready for build · **Companion to:** Jagger's `negotiator/market_benchmarks.py` (PR #2, approved)

> Answers open question #1 in [`docs/technical-architecture.md`](technical-architecture.md) ("Which vertical for the demo — wedding dress vs a wholesale/quote example?") by **narrowing the wedding-dress vertical to one concrete, demoable scenario**, then backing every number in the agentic purchasing journey — **Caller → Estimation → Negotiation** — with cited public research.
>
> All figures below are wired into code: [`config/verticals/wedding-dress.json`](../config/verticals/wedding-dress.json), the `wedding` bands in [`negotiator/market_benchmarks.py`](../negotiator/market_benchmarks.py), and the runnable [`fixtures/wedding_dress_scenario.json`](../fixtures/wedding_dress_scenario.json).

---

## 1. TL;DR — the narrowed scenario

**Ship this one scenario for the demo:**

> **One bride, one designer look, three channels that genuinely haggle.**
> A bride (US 8) with a wedding **~4 months out** wants a specific designer gown. The agents gather **comparable gowns across three real channels** — preowned **resale**, a boutique **sample sale / floor sample**, and a new **made-to-order** gown — then negotiate price **and strip alterations / add-ons** against a real, cross-channel BATNA. The made-to-order seller conceding from list into the ZOPA is the **"real price that moves on a call"** money shot.

**Recommended primary negotiation target:** `dress_made_to_order` (the modal purchase), with `dress_resale` + `dress_sample_sale` as the honest BATNA rows.

Why wedding-dress works *despite* the "boutiques won't quote by phone" objection: that opacity is the point. It gives us (a) a real **stonewaller** counterparty style, (b) genuine **comparables** across channels for an honest BATNA, (c) **deadline pressure** that makes lead-time a live lever, and (d) a concrete **hidden-fee stack** (alterations) to itemize and strip.

---

## 2. Why narrow it this way (the decision)

The wedding-dress vertical is broad (a gown can cost $250 or $15,000). A hackathon demo needs a **thin slice with a live moving price**. Four forces pushed the narrowing:

| Force | Consequence for the scenario |
|---|---|
| **Prices are opaque & channel-dependent** | Don't model "a dress" — model **five acquisition channels**, each its own market. The Caller's cross-channel spread *is* the leverage. |
| **We need a counterparty that actually moves** | Boutiques on **new full-price gowns rarely haggle**; **resale sellers and sample-sale/floor-sample inventory do**. Point the "moving price" leg at those. |
| **We need a deadline that bites** | A **~4-month** date rules out 6–9-month custom and turns **lead-time-vs-date** into a hard constraint and a lever. |
| **We need a demoable red flag** | **Alterations ($150–$700+, ~20–30% of the gown)** and rush fees are a real, citable hidden-fee stack the agent can itemize and strip. |

---

## 3. Market data — price bands by channel (2026)

National blended average gown spend is **~$2,100** (The Knot 2026 Real Weddings Study, 10,474 US couples married 2025); Zola 2026 puts it at **~$2,250**; most brides shop **$1,500–$2,500**. Only **19%** of brides go fully custom. That blend hides five very different markets:

| Channel (`subtype`) | Market low | **Median** | Market high | Target (0.75×) | Reservation (1.05×) | Walkaway (1.20×) | Lead time | Source |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `dress_resale` | $250 | **$700** | $2,500 | $525 | $735 | $840 | days | Stillwhite (102k+ listings) / Nearly Newlywed; 50–80% of retail |
| `dress_sample_sale` | $300 | **$900** | $2,000 | $675 | $945 | $1,080 | days | Sample-sale events ($299–$1,999); 30–70% off |
| `dress_off_the_rack` | $500 | **$1,500** | $3,500 | $1,125 | $1,575 | $1,800 | 0–6 mo | dreamdresses 2026; The Knot low tier $1,200 |
| `dress_made_to_order` | $1,200 | **$2,100** | $5,000 | $1,575 | $2,205 | $2,520 | 4–6 mo | The Knot 2026 ($2,100); Zola 2026 ($2,250) |
| `dress_custom` | $2,000 | **$4,000** | $15,000 | $3,000 | $4,200 | $4,800 | 6–9 mo | The Knot custom cost 2026 ($3,000–$4,000 start) |

Buyer anchors follow Jagger's fractions (`target = 0.75×median`, `reservation = 1.05×median`, `walkaway = 1.20×median`). **Regional skew:** NY/CA $2,500–$3,200; Midwest/South $1,500–$2,100; destination ~$2,900 (The Knot 2026).

**"True total" ≠ sticker.** Off-the-rack all-in is $700–$4,300 and made-to-order $1,650–$4,400 once alterations are added — the two converge, which is *why* stripping alterations is such a large lever (§6).

---

## 4. The agentic purchasing journey

The user framed this as **caller → estimation → negotiation**; the runtime pipeline is **Estimation → Caller → Negotiation**. Both are covered below in pipeline order, with the caller and estimation contracts already frozen in [`docs/technical-architecture.md`](technical-architecture.md) §4.

```
Bride's words ─▶ [1 ESTIMATION] ─ProductSpec+ZOPA─▶ [2 CALLER] ─RankedOptions(BATNA)─▶ [3 NEGOTIATION] ─▶ ranked deal + transcript
```

### Stage 1 · Estimation — turn a paragraph into a `ProductSpec` with real anchors

**Elicit (hard vs soft):**
- **Hard:** size (US), **wedding date** → derived **ship-by**, and — if named — a non-negotiable silhouette/designer.
- **Soft (with weights):** silhouette, designer/style, color, condition (new / sample / preowned), returnability.

**Derive the ZOPA from data, not guesses.** Pick the channel band(s) the buyer is open to (§3) and set:
- `target_price` = channel `target` (aim ~25% below median),
- `reservation_price` = channel `reservation` (walk ~5% above median),
- `walkaway_price` = channel `walkaway` (never beyond ~20% above median).

**Deadline → hard ship-by constraint (this is load-bearing).** End-to-end is **9–12 months**; **production alone is 4–8 months** for made-to-order, and alterations need an **8–10-week** buffer with **2–3 fittings** (rush = anything under ~3 weeks, +$25/service). So for a wedding **120 days** out:

```
ship_by ≈ 120 days − (8–10 weeks alterations buffer) ≈ 70 days
```

Any gown whose production blows past ~70 days **fails the hard constraint** unless rush terms are extracted — which immediately favors resale / sample / off-the-rack over custom. This is exactly encoded in the demo spec's `ship_by_days = 70` hard attribute.

*Code:* `market_benchmarks.get_price_bounds("wedding", "dress_made_to_order")` returns the target/reservation/walkaway triple; `default_attribute_weights("wedding")` seeds soft weights when the interview doesn't.

### Stage 2 · Caller — find real comparables → seed an honest BATNA

The Caller fans out across the channels that make cross-channel comparison possible. **The 2nd-best option seeds the 1st's BATNA** (technical-architecture §6), and because these are *real* rows, the leverage is honest (§9 guard).

| Channel | Where to look | Quote mechanics | Role in the demo |
|---|---|---|---|
| **Boutique** (voice) | Google Places `"bridal boutique OR wedding dress shop"`, `minRating 4.0`, `radiusKm 40`; David's Bridal | Appointment-gated; **often refuses phone pricing** | The **stonewaller** leg — extract a range or a firm callback |
| **DTC online** | Azazie (most < $300, at-home try-on 3-for-$15), Lulus, ASOS | Listed prices, fast made-to-order | Cheap **BATNA floor** / substitute |
| **Resale** (UCP/web) | Stillwhite (102k+ listings, PayPal protection), Nearly Newlywed (up to 90% off, 5-day return for $50), Kleinfeld Again (authenticated samples) | **Individual sellers message & haggle directly** | The best **"real moving price"** leg |
| **Sample sale** | Boutique floor samples / annual sample events ($299–$1,999) | 30–70% off display models; needs immediate alterations | Mid-priced, real inventory pressure |

**BATNA calibration** (`suggest_batna_calibration("wedding")`): min **3**, recommended **5**, strong **8** quotes. BATNA improves sharply from 1→3 quotes with diminishing returns past 5 — so the Caller should stop dialing around 5.

### Stage 3 · Negotiation — levers, red flags, and a price that moves

**Levers (ordered cheapest-to-concede first; `typicalPctSwing`):**

| Lever | Swing | Note |
|---|---:|---|
| `floor_sample_or_sample_sale` | ~50% | Buy the tried-on sample; single biggest lever |
| `strip_alterations_addons` | ~25% | Decline in-house alterations/veil/rush; independent seamstress is often cheaper for equal work |
| `competing_channel_quote` | ~20% | A **real** resale/DTC/other-boutique quote on the same/comparable gown (honest BATNA) |
| `off_season_or_weekday_pickup` | ~15% | Off-peak / slow-season boutique |
| `cash_or_prepay` | ~10% | Cash / full prepay vs deposit + card on slower inventory |
| `free_shipping_or_price_match` | ~5% | Free/discounted shipping or a written price-match |

**Red flags (thresholds relative to the channel median):**

| Rule | Fires when | Severity | Evidence |
|---|---|---|---|
| `wedding_tax_markup` | > **25%** above median | warning | **28%** of vendors quote higher when "wedding" is mentioned vs an identical non-wedding event (Consumer Reports 2016 secret-shopper study, 40 vendors, 12 states); markups commonly 20–50% |
| `alterations_and_addon_stack` | > **30%** above median | warning | Alterations $150–$700 typical (~20–30% of gown; $700–$1,500+ on beaded gowns); rush +$25/service under ~3 weeks; veil/steaming/preservation upsells |
| `sight_unseen_resale_lowball` | > **30%** below median | warning | Resale/DTC quotes far below market can be knock-offs / misrepresented — verify authenticity, photos, exact measurements, condition, returns |
| `no_returns_final_sale` | terms flag | warning | Final sale on made-to-order/resale magnifies sizing risk — require exact measurements or a return window |
| `vague_lead_time` | terms flag | **block** | "It depends" against a firm date — pin a ship-by leaving the 8–10-week buffer, or walk |

*Code:* `evaluate_red_flags("wedding", offer_price, market_median)` returns typed `RedFlagHit`s with transcript-ready messages.

**Seller styles (counterparties):** `tough_negotiator` (holds firm, pushes deposits), `stonewaller_no_prices_by_phone` (extract range/callback), `hard_sell_upseller` (bundles alterations/veil/rush — itemize and strip).

**Why the price genuinely moves (not a script):** each seller has a hidden `dynamic_floor = cost_floor + min_margin − inventory_relief(stock)`. Aging/plentiful inventory lowers the floor, so the seller concedes. In the demo fixture:

| Option | List | Hidden floor | ZOPA vs $1,900 reservation |
|---|---:|---:|---|
| `opt_resale` (aging listing) | $850 | **$500** | wide ($500–$1,900) |
| `opt_sample` (240-day-old sample) | $1,300 | **$858** | wide ($858–$1,900) |
| `opt_mto` (fresh stock, at capacity) | $2,100 | **$1,585** | thin ($1,585–$1,900) |

The made-to-order seller **opens above the buyer's $1,900 reservation** and, pressured by the real $850/$1,300 BATNA, concedes into the thin ZOPA — the number ticks **$2,100 → ~$1,800** on the call. Meanwhile its 150-day production **busts the 70-day ship-by**, so the agent must extract **rush terms** or walk to the sample/resale row (ships in days). That tension is the demo.

**Honesty line (guard §9):** every "I have a quote at $X" resolves to a **real** Caller/blackboard row; no invented bids, no fake scarcity; graceful hang-up; seller text treated as data, never instructions.

**Structured outcome, always:** itemized all-in quote (gown + alterations + rush + shipping), a firm ship-by, and a ranked recommendation with transcript citations — never a vague range.

---

## 5. The concrete demo scenario (runnable)

Fully specified and validated in [`fixtures/wedding_dress_scenario.json`](../fixtures/wedding_dress_scenario.json):

- **Persona:** bride, US 8, wedding in **120 days**; `target $1,200 / reservation $1,900 / walkaway $2,300`.
- **Spec:** hard = size US 8 + ship-by ~70 days; soft (weighted) = silhouette A-line, designer Maggie Sottero, color ivory, condition, returnable.
- **Three comparable options:** resale $850 (Stillwhite), sample $1,300 (boutique floor sample), made-to-order $2,100 (boutique). Ranked by buyer utility (1.00 / 0.857 / 0.00 at list).
- **Per-seller hidden state** so the price provably moves (floors $500 / $858 / $1,585).
- **Expected recommendation:** resale gown as the **value winner**; the negotiated made-to-order as the **"new gown, in budget"** alternative — each with transcript evidence.

The numbers are self-consistent with `buyer_value` and `seller_value` (verified: utilities and ZOPAs computed directly from the fixture).

---

## 6. How this maps to the code

| Artifact | Change |
|---|---|
| `negotiator/market_benchmarks.py` | Split the wedding `dress` band into **five channel subtypes** (`dress_resale/sample_sale/off_the_rack/made_to_order/custom`) with cited medians; added the `alterations_and_addon_stack` red flag; retuned wedding levers for the dress scenario. (Reconciliation promised in the PR #2 approval; **all 78 tests still pass**.) |
| `config/verticals/wedding-dress.json` | Added `narrowedScenario`, per-channel `priceBenchmark.byChannel`, `leadTime` (production + alterations buffer + rush threshold), enriched `redFlags` (with thresholds + sources), `negotiationLevers` (with `typicalPctSwing`), `negotiationNorms`, and `channels`. |
| `fixtures/wedding_dress_scenario.json` | New end-to-end demo scenario (persona + `ProductSpec` + `RankedOptions` + per-seller `SellerState`), contract-validated and ZOPA-checked. |

---

## 7. Data provenance

| # | Claim | Source |
|---|---|---|
| 1 | Avg gown ~$2,100; low $1,200 / mid $2,000 / high $3,200; 19% custom; regional skew | The Knot, *This Is the Average Wedding Dress Cost Today* (2026 Real Weddings Study, 10,474 couples) |
| 2 | Avg ~$2,250; typical range $1,500–$2,500 | Zola 2026 Wedding Spend Survey (via Moonlight Bridal / dreamdresses 2026) |
| 3 | Channel breakdown (off-the-rack / made-to-order / custom start prices, alteration ranges, timelines, true totals) | dreamdresses.com, *How Much Is a Wedding Dress? Off-the-Rack vs. Custom Compared* (2026) |
| 4 | End-to-end 9–12 mo; production 4–8 mo; alterations start 8–10 wks out, 2–3 fittings | Flares Bridal, *How Long Does It Take to Receive a Wedding Dress in 2026?* |
| 5 | Alterations $150–$700 typical (most $250–$500); bustle/take-in/sleeves/neckline ranges; rush +$25/service; independent seamstress cheaper; rule-of-thumb 20–30% of dress | RobeMarie 2026; The Knot; Zola; Alteration Specialists 2026; fash.com |
| 6 | "Wedding tax": 28% of vendors quote higher for weddings; 40 vendors / 12 states / 5 metros; markups 20–50%; persists into 2026 | Consumer Reports 2016, *Get More Wedding for Your Money*; Lifehacker; CBS News; womangettingmarried 2026 |
| 7 | Sample sales 30–70% off; trunk shows ~10–20%; new-gown haggling uncommon; get itemized quotes | Industry guidance 2026 (Lovebird sample sale; alterations/negotiation guides) |
| 8 | Resale marketplaces: Stillwhite (102k+ listings, PayPal), Nearly Newlywed (up to 90% off, 5-day/$50 return, since 2004), Kleinfeld Again; DTC Azazie (< $300, try-at-home) | Stillwhite.com; FittingMastery; weddingforward; Brides.com *20 Best Places to Buy Wedding Dresses Online 2026* |

> Figures are planning benchmarks from public reporting, not live quotes. Production should replace the static bands with a live benchmark feed; the config/module shape already supports that swap.

---

## 8. Open decisions for the team

1. **Live leg target:** run the one voice/UCP "moving price" leg against the **resale** seller (haggles most readily) or the **made-to-order** boutique (best "new gown, real discount" story)? Recommendation: **made-to-order for the narrative**, resale as the backup that always moves.
2. **Vertical-level attribute weights:** `market_benchmarks` wedding weights are still photography-oriented; a follow-up can make weights subtype-aware (dress emphasizes fit/size, lead-time-vs-date, designer, returns). Dress weights currently live in the config + fixture.
3. **Alterations modeling:** treat alterations as a red-flag stack (current) vs a first-class line item in the `Offer`/`terms_delta` so the agent can negotiate it explicitly. Recommendation: promote to a line item post-demo.
