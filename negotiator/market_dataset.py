"""
Market dataset loader (owner: Ella) — CSV-driven multi-brand test harness.

Reads a normalized set of CSVs (buyer, buyer_attributes, brands, upsells, deals) and
builds the objects the negotiation core consumes:
  · one `ProductSpec` (the buyer), built directly from structured fields
  · per brand: an `Option`, a `SellerState`, and a brand dict (SLA + upsell_catalog +
    credit_deals) to inject into `SellerAgent(state, brand=...)`

Zero dependencies — stdlib `csv` only. Mirrors the `Path(...).read_text()` config idiom
used by `caller.py` / `brand_profiles.py`. Product metadata is real; prices are synthetic.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from . import seller_profiles
from .contracts import (
    Attribute,
    Capacity,
    Inventory,
    Negotiation,
    Option,
    ProductSpec,
    RankedOptions,
    SellerState,
)

# Friendly CSV labels → canonical NegotiationStyleId (the styles already exist).
_STYLE_MAP = {
    "tough but fair": "tough_negotiator",
    "tough": "tough_negotiator",
    "tough_negotiator": "tough_negotiator",
    "won't quote by phone": "stonewaller_no_prices_by_phone",
    "wont quote by phone": "stonewaller_no_prices_by_phone",
    "no prices by phone": "stonewaller_no_prices_by_phone",
    "stonewaller": "stonewaller_no_prices_by_phone",
    "stonewaller_no_prices_by_phone": "stonewaller_no_prices_by_phone",
    "upseller": "hard_sell_upseller",
    "hard sell upseller": "hard_sell_upseller",
    "hard_sell_upseller": "hard_sell_upseller",
}


def friendly_style(label: Optional[str]) -> str:
    return _STYLE_MAP.get((label or "").strip().lower(), "tough_negotiator")


# ── tiny CSV parsing helpers ─────────────────────────────────────────────────
def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _s(row: dict, key: str, default: str = "") -> str:
    return (row.get(key) or "").strip() or default


def _f(row: dict, key: str, default):
    v = (row.get(key) or "").strip()
    if v == "":
        return default
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return default


def _i(row: dict, key: str, default: int) -> int:
    v = _f(row, key, None)
    return int(round(v)) if v is not None else default


def _b(row: dict, key: str, default: bool) -> bool:
    v = (row.get(key) or "").strip().lower()
    if v == "":
        return default
    return v in ("true", "1", "yes", "y")


def _list(v: Optional[str], sep: str = ";") -> list[str]:
    return [x.strip() for x in (v or "").split(sep) if x.strip()]


def _kv(v: Optional[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in _list(v):
        if ":" in pair:
            k, val = pair.split(":", 1)
            out[k.strip()] = val.strip()
    return out


# ── builders ─────────────────────────────────────────────────────────────────
def build_spec(buyer_row: dict, attr_rows: list[dict]) -> ProductSpec:
    attrs = [
        Attribute(
            name=_s(a, "name"),
            value=_s(a, "value") or None,
            constraint=(_s(a, "constraint", "soft").lower() or "soft"),
            weight=_f(a, "weight", None),
            substitutions=_list(a.get("substitutions")),
        )
        for a in attr_rows
        if _s(a, "name")
    ]
    return ProductSpec(
        spec_id=_s(buyer_row, "scenario_id", "spec_market"),
        category=_s(buyer_row, "category", "WeddingDress"),
        attributes=attrs,
        negotiation=Negotiation(
            target_price=_f(buyer_row, "target_price", 1800.0),
            reservation_price=_f(buyer_row, "reservation_price", 2400.0),
            currency=_s(buyer_row, "currency", "USD"),
            deadline_days=_i(buyer_row, "deadline_days", 30) or None,
            must_have_summary=_s(buyer_row, "must_have_summary") or None,
        ),
    )


def to_option(brand_row: dict, idx: int) -> Option:
    style = friendly_style(brand_row.get("seller_style"))
    listed = _f(brand_row, "listed_price", 2000.0)
    return Option(
        option_id=f"opt_{idx}",
        vendor=_s(brand_row, "vendor"),
        source_url=_s(brand_row, "source_url") or None,
        listed_price=listed,
        currency=_s(brand_row, "currency", "USD"),
        matched_attributes=_kv(brand_row.get("matched_attributes")),
        negotiation_style=style,
        fee_template=seller_profiles.default_fee_template(listed, style),
    )


def to_seller_state(brand_row: dict) -> SellerState:
    """Economics from the CSV (synthetic); per-style fallbacks for any blank numeric field.
    Upsell accessories arrive via the brand dict (apply_brand), not here."""
    style = friendly_style(brand_row.get("seller_style"))
    listed = _f(brand_row, "listed_price", 2000.0)
    return SellerState(
        vendor=_s(brand_row, "vendor"),
        cost_floor=_f(brand_row, "cost_floor", round(listed * 0.65, 2)),
        list_price=listed,
        min_margin=_f(brand_row, "min_margin", round(listed * 0.18, 2)),
        inventory=Inventory(
            sku_units=_i(brand_row, "sku_units", 6),
            stock_age_days=_i(brand_row, "stock_age_days", 60),
        ),
        capacity=Capacity(
            lead_time_days=_i(brand_row, "lead_time_days", 30),
            at_capacity=_b(brand_row, "at_capacity", style == "stonewaller_no_prices_by_phone"),
        ),
        catalog_addons=[],
        style=style,
        fee_template=seller_profiles.default_fee_template(listed, style),
    )


def to_brand_dict(brand_row: dict, upsell_rows: list[dict], deal_rows: list[dict]) -> dict:
    upsell_catalog = []
    for u in upsell_rows:
        name = _s(u, "accessory_name")
        if not name:
            continue
        entry = {"name": name, "price": _f(u, "price", 0.0)}
        if _s(u, "code"):
            entry["code"] = _s(u, "code")
        upsell_catalog.append(entry)

    credit_deals = []
    for d in deal_rows:
        credit_deals.append({
            "deal_type": _s(d, "deal_type", "store_credit"),
            "amount": _f(d, "amount", None),
            "pct": _f(d, "pct", None),
            "conditions": _s(d, "conditions", "photo_review"),
            "unlock": _s(d, "unlock", "on_purchase_placed"),
            "nonrefundable": _b(d, "nonrefundable", True),
            "min_purchase": _f(d, "min_purchase", None),
        })

    return {
        "vendor": _s(brand_row, "vendor"),
        "brand": {
            "positioning": _s(brand_row, "positioning"),
            "specialties": _list(brand_row.get("specialties")),
            "heritage": _s(brand_row, "heritage"),
        },
        "returns_refunds": {
            "window_days": _i(brand_row, "returns_window_days", 0),
            "restocking_fee_pct": _f(brand_row, "restocking_fee_pct", 0.0),
            "notes": _s(brand_row, "returns_notes"),
        },
        "service_sla": {
            "support_response_hours": _i(brand_row, "support_response_hours", 24),
            "alteration_weeks": _i(brand_row, "alteration_weeks", 0),
            "shipping_days": _i(brand_row, "shipping_days", 0),
            "lead_time_days": _i(brand_row, "lead_time_days", 0),
            "lifetime_alterations": _b(brand_row, "lifetime_alterations", False),
        },
        "upsell_catalog": upsell_catalog,
        "credit_deals": credit_deals,
    }


def load_market(data_dir) -> tuple[ProductSpec, list[dict]]:
    """Return (buyer ProductSpec, [ {row, idx, option, state, brand} per brand ])."""
    d = Path(data_dir)
    buyer_rows = _read_csv(d / "buyer.csv")
    attr_rows = _read_csv(d / "buyer_attributes.csv")
    brand_rows = _read_csv(d / "brands.csv")
    upsell_rows = _read_csv(d / "upsells.csv")
    deal_rows = _read_csv(d / "deals.csv")

    buyer_row = buyer_rows[0] if buyer_rows else {}
    scen = _s(buyer_row, "scenario_id")
    spec = build_spec(buyer_row, [a for a in attr_rows if not scen or _s(a, "scenario_id") == scen])

    brands = []
    for i, br in enumerate(brand_rows):
        vendor = _s(br, "vendor")
        if not vendor:
            continue
        ups = [u for u in upsell_rows if _s(u, "vendor") == vendor]
        dls = [dl for dl in deal_rows if _s(dl, "vendor") == vendor]
        brands.append({
            "row": br,
            "idx": i,
            "option": to_option(br, i),
            "state": to_seller_state(br),
            "brand": to_brand_dict(br, ups, dls),
        })
    return spec, brands


def build_ranked(spec: ProductSpec, brands: list[dict]) -> RankedOptions:
    return RankedOptions(spec_id=spec.spec_id, options=[b["option"] for b in brands])
