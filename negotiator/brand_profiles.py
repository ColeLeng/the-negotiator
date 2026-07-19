"""
Brand / policy / SLA profiles (owner: Ella) — a margin lever, not in the frozen contract.

A merchant describes its brand, return/refund policy, service SLAs, and a low-price
accessory catalog in `config/brands/<slug>.json`. The SellerAgent loads the profile for
its own vendor and uses it to (1) hold price closer to list via a `value_score` that
dampens concession, (2) justify that hold with honest rationale text, and (3) enrich the
upsell catalog with accessories (veil, cape, train, gloves, hair) that raise the opening
ask and double as concession currency.

Purely seller-side: everything is read *into* the seller's own copy of `SellerState`
(add-ons + fee lines) or into the agent's rationale. Nothing here touches the shared
`NegotiationMessage` schema, the negotiation loop, or `NegotiationSession`.

Mirrors the JSON-config convention of `config/verticals/*.json` (json.loads from disk).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

from .contracts import AddOn, Capacity, FeeLine, Inventory, SellerState

_BRANDS_DIR = Path(__file__).resolve().parent.parent / "config" / "brands"


def _slug(vendor: str) -> str:
    """"David's Bridal" -> "davids-bridal"; "Pronovias (Official)" -> "pronovias-official"."""
    s = vendor.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def load_brand(vendor: str) -> Optional[dict]:
    """Return the brand profile for a vendor, or None if no config file exists."""
    if not vendor:
        return None
    path = _BRANDS_DIR / f"{_slug(vendor)}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def value_score(brand: dict) -> float:
    """0..1 — how much justified value the brand carries (drives concession dampening)."""
    sla = brand.get("service_sla", {}) or {}
    ret = brand.get("returns_refunds", {}) or {}
    specialties = (brand.get("brand", {}) or {}).get("specialties", []) or []

    returns_gen = min(1.0, (ret.get("window_days", 0) or 0) / 30.0)
    support = 1.0 - min(1.0, (sla.get("support_response_hours", 48) or 48) / 48.0)
    craft = 0.7 * min(1.0, len(specialties) / 3.0) + (0.3 if sla.get("lifetime_alterations") else 0.0)

    score = 0.35 * returns_gen + 0.30 * support + 0.35 * craft
    return round(max(0.0, min(1.0, score)), 3)


def justification(brand: dict) -> str:
    """A short, honest reason the seller holds price — built from real SLA/policy facts."""
    sla = brand.get("service_sla", {}) or {}
    ret = brand.get("returns_refunds", {}) or {}
    bits = []
    if sla.get("alteration_weeks"):
        bits.append(f"{sla['alteration_weeks']}-wk in-house tailoring")
    if sla.get("shipping_days"):
        bits.append(f"{sla['shipping_days']}-day shipping")
    if sla.get("lifetime_alterations"):
        bits.append("free lifetime alterations")
    if ret.get("window_days"):
        bits.append(f"{ret['window_days']}-day returns")
    return "value adds: " + ", ".join(bits) if bits else "premium service"


def _acc_code(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def apply_brand(state: SellerState, brand: dict) -> SellerState:
    """Return a copy of `state` enriched with the brand's accessory catalog (and optional
    real-inventory override). Skips accessories whose name/code already exist so totals
    never double-count."""
    addons = list(state.catalog_addons)
    fees = list(state.fee_template)
    have_names = {a.name.lower() for a in addons}
    have_codes = {f.code for f in fees}

    for acc in brand.get("upsell_catalog", []) or []:
        name = acc["name"]
        price = float(acc["price"])
        code = acc.get("code") or _acc_code(name)
        if name.lower() not in have_names:
            addons.append(AddOn(name=name, price=price))
            have_names.add(name.lower())
        if code not in have_codes:
            fees.append(FeeLine(code=code, label=name.title(), amount=price, optional=True))
            have_codes.add(code)

    updates: dict = {"catalog_addons": addons, "fee_template": fees}

    # Optional: connect to an internal inventory system to make dynamic_floor real.
    inv = brand.get("inventory")
    if inv:
        if "cost_floor" in inv:
            updates["cost_floor"] = float(inv["cost_floor"])
        if "sku_units" in inv or "stock_age_days" in inv:
            updates["inventory"] = Inventory(
                sku_units=int(inv.get("sku_units", state.inventory.sku_units)),
                stock_age_days=int(inv.get("stock_age_days", state.inventory.stock_age_days)),
            )
    cap = brand.get("service_sla", {}) or {}
    if cap.get("lead_time_days"):
        updates["capacity"] = Capacity(
            lead_time_days=int(cap["lead_time_days"]),
            at_capacity=state.capacity.at_capacity,
        )

    return state.model_copy(update=updates)
