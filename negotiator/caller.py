"""
Caller (owner: Jagger) — §6. Fan out over the web, find real products matching the spec,
return a ranked, negotiable RankedOptions table. Does NOT negotiate.

STUB: synthesizes 3 options across the spec's price band and scores each with the buyer
value function, so the table ranks like the real thing. TODO(Jagger): real fan-out search
(Exa / Tavily / Serper / Brave), extraction of vendor/price/attributes, real URLs + channels.
"""
from __future__ import annotations

from . import buyer_value
from .contracts import Channel, Option, RankedOptions

_VENDORS = ["Bridal Boutique X", "Atelier Y", "Sample-Sale Z"]


def search(spec) -> RankedOptions:
    target = spec.negotiation.target_price
    reservation = spec.negotiation.reservation_price
    listed_prices = [reservation, round((target + reservation) / 2, 2), round(target * 1.05, 2)]

    options: list[Option] = []
    for i, (price, vendor) in enumerate(zip(listed_prices, _VENDORS)):
        options.append(
            Option(
                option_id=f"opt_{i + 1}",
                vendor=vendor,
                source_url=f"https://example.com/listing/{i + 1}",
                listed_price=price,
                matched_attributes={a.name: (a.value or "") for a in spec.attributes},
                match_score=round(buyer_value.utility(price, spec), 3),
                channel=Channel(type="mock"),
            )
        )

    options.sort(key=lambda o: o.match_score, reverse=True)   # best (cheapest here) first
    return RankedOptions(spec_id=spec.spec_id, options=options)
