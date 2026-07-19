# `data/market/` — the 12-seller market dataset

Shared bridal dataset backing **Scenario 2** (the buyer's quote-gathering pass).
Product names, prices and `source_url`s are **real** (verifiable by clicking the
URL); the private cost/fee economics each seller discloses are synthetic demo seeds.

| File | Rows | What it is |
|---|---|---|
| `brands.csv` | 12 | The seller agents — vendor, listed price, attributes, `seller_style`, provenance URL. |
| `buyer.csv` | 1 | The buyer's price band + deadline (a Scenario-1 intake stand-in). |
| `buyer_attributes.csv` | 4 | The buyer's hard/soft attributes (feeds `ProductSpec`). |

## Disclosure personas

`negotiator/seller_market.py` stamps each row with a **disclosure persona** derived
from its `seller_style`, so the 12 sellers behave as distinct personalities during the
buyer's inquiry:

| `seller_style` (dataset) | Personas assigned | Behaviour when asked for a quote |
|---|---|---|
| Tough but fair (×4) | `transparent`, `guarded` | Itemizes up front / gives base only until pressed. |
| Won't quote by phone (×4) | `stonewaller` | Refuses a phone price; some cave to a vague ballpark, some only offer a callback. |
| Upseller (×4) | `upseller`, `lowball_teaser` | Leads with an inflated bundle / dangles a fake-low base that balloons on itemization. |

The buyer verifies every quote against the vendor's own sticker and the market
benchmark median, then prunes stonewallers, exposed teasers and over-budget stickers
down to the top 3–5 verified vendors for Scenario 3.

> Dataset curated by Ella (seller side); consumed by Cole's Scenario-2 inquiry agent.
