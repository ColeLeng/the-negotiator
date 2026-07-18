"""
Estimator (owner: Jagger) — §5. Turn messy human input into a clean ProductSpec with
ZOPA parameters. Does NOT find vendors.

STUB: returns a schema-valid wedding-dress spec, sniffing any prices out of the input so
the demo reflects the user's numbers. TODO(Jagger): LLM extraction to the §4.1 schema,
voice intake (STT), and a clarify loop for missing hard constraints / price bounds.
"""
from __future__ import annotations

import re
from typing import Union

from .contracts import Attribute, Negotiation, ProductSpec


def estimate(input_text: Union[str, bytes]) -> ProductSpec:
    text = input_text.decode() if isinstance(input_text, bytes) else str(input_text)
    prices = [float(p.replace(",", "")) for p in re.findall(r"\$?\s*([0-9][0-9,]{2,}(?:\.\d{1,2})?)", text)]
    target = min(prices) if prices else 1800.0
    reservation = max(prices) if len(prices) >= 2 else round(target * 1.33, 2)

    return ProductSpec(
        spec_id="spec_demo",
        category="WeddingDress",
        attributes=[
            Attribute(name="color", value="ivory", constraint="soft", weight=0.15,
                      substitutions=["champagne", "off-white"]),
            Attribute(name="size", value="US 8", constraint="hard"),
            Attribute(name="brand", value="Pronovias", constraint="soft", weight=0.20,
                      substitutions=["Vera Wang", "comparable designer"]),
        ],
        negotiation=Negotiation(
            target_price=target,
            reservation_price=reservation,
            deadline_days=30,
            must_have_summary="size US 8, delivery within 30 days",
        ),
    )
