# Market dataset — one buyer vs many brand Seller Agents

CSV-driven test data for the market harness. Author in Excel (one sheet per file below),
then **Save As CSV (UTF-8)** per sheet into this folder. Loaded by
[`negotiator/market_dataset.py`](../../negotiator/market_dataset.py) with the stdlib `csv`
module — **no dependencies**.

Run it:

```bash
.venv/bin/python scripts/run_market.py --data data/market --out market_results.csv
.venv/bin/python scripts/run_buyer_example.py --brand "Jenny Yoo"
```

## ⚠️ Prices are synthetic; product metadata is real

The **gown metadata** (designer, silhouette, fabric, neckline, sleeve, colors, sizing,
customization) is taken from each designer's **real product detail page** (see `source_url`).
The **prices and economics** (`listed_price`, `cost_floor`, `min_margin`, inventory, capacity)
are **synthetic**, chosen only so the negotiation has room to move: list prices sit above the
buyer's $1800 target but at/under the $2400 reservation (per `AGENTS.md`). Do not treat prices
as real quotes.

## Files & columns

Multi-value cells use `;` for lists and `:` for key/value. Booleans are `true`/`false`.
Join key across sheets is **`vendor`** (must match exactly). Blank cells fall back to defaults.

### `buyer.csv` (one row = the buyer scenario)
`scenario_id, category, target_price, reservation_price, currency, deadline_days, must_have_summary`

### `buyer_attributes.csv` (many rows, joined by `scenario_id`)
`scenario_id, name, value, constraint(hard|soft), weight, substitutions(;-list)`

### `brands.csv` (one row per brand = one Seller Agent)
`vendor, product_name, listed_price, currency, seller_style, category, matched_attributes(k:v;…),`
`cost_floor, min_margin, sku_units, stock_age_days, lead_time_days, at_capacity,`
`positioning, specialties(;-list), heritage,`
`support_response_hours, alteration_weeks, shipping_days, lifetime_alterations,`
`returns_window_days, restocking_fee_pct, returns_notes, source_url`

`seller_style` is a **friendly label** mapped to the engine's canonical styles:

| CSV `seller_style` | Canonical style | Behavior |
|---|---|---|
| `Tough but fair` | `tough_negotiator` | Holds firm, pushes deposit, concedes as the buyer leverages competing quotes |
| `Won't quote by phone` | `stonewaller_no_prices_by_phone` | Stalls → firm callback / reluctant range, never a vague brush-off |
| `Upseller` | `hard_sell_upseller` | Piles on veil/rush/alterations; itemizes every fee, strips nonessentials |

### `upsells.csv` (many rows per brand)
`vendor, accessory_name, price, code(optional)` → the brand's upsell catalog (bundled by the
upseller, stripped as concession currency). `code` auto-slugs from the name if blank.

### `deals.csv` (many rows per brand — credit-only, margin-safe)
`vendor, deal_type(store_credit|coupon), amount($) OR pct(%of list), conditions(photo_review|honest_positive_review|share_preferences), unlock(default on_purchase_placed), nonrefundable(default true), min_purchase(optional)`

Deals are **contingent, non-refundable credits that ride in `terms_delta` — never in `price`**,
so the landing price stays high. A brand's own deals are preferred over the default tiers;
`min_purchase` gates a deal until the agreed price clears that threshold.

## This dataset

12 real gowns, **4 per seller style**. Economics are varied so the ZOPA is emergent (aged-stock
upsellers concede further than fresh-stock tough brands; stonewallers run at capacity). See
`brands.csv` for `source_url` per gown.

## Notes / caveats

- Sessions run **sequentially** (the engine's current behavior), and each session's BATNA is
  seeded from the *next* brand's listed price, upgraded live from competing offers on the shared
  blackboard. So brands negotiated early see fewer competing offers than later ones — the final
  **recommendation still picks the globally lowest agreed price**.
- A hard buyer attribute a brand doesn't match (e.g. size) makes the buyer walk — keep
  `matched_attributes` honest to the gown.

## Blank template
Header-only copies live in [`template/`](template/) — fill them to build a new market.
