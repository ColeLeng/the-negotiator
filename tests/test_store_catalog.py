"""
tests/test_store_catalog.py
===========================
Ella's store inventory (data/market/wedding_stores.csv) must load and make the Caller
search real stock — a non-empty, ranked match instead of a thin/empty catalog.
"""
from __future__ import annotations

from negotiator import store_catalog
from negotiator.caller import search
from negotiator.contracts import Attribute, Negotiation, ProductSpec


def test_loads_twelve_stores_with_parsed_attributes():
    stores = store_catalog.load_store_listings("wedding-dress")
    assert len(stores) == 12
    by_vendor = {s["vendor"]: s for s in stores}
    allure = next(s for v, s in by_vendor.items() if "Allure Bridals" in v)
    assert allure["attributes"]["color"] == "ivory"
    assert allure["attributes"]["size"] == "US 8"
    assert allure["attributes"]["designer"] == "Allure Bridals"
    assert allure["source_url"].startswith("http")
    assert allure["listed_price"] > 0


def test_unknown_vertical_returns_empty():
    assert store_catalog.load_store_listings("space-tourism") == []


def _wedding_spec() -> ProductSpec:
    return ProductSpec(
        spec_id="spec_stores",
        category="Wedding Dress (DTC)",
        attributes=[
            Attribute(name="size", value="US 8", constraint="hard"),
            Attribute(name="color", value="ivory", constraint="soft", weight=0.2,
                      substitutions=["white", "ivory", "champagne"]),
        ],
        negotiation=Negotiation(target_price=1500, reservation_price=2200),
    )


def test_caller_searches_store_inventory_not_empty():
    ranked = search(_wedding_spec())
    assert len(ranked.options) >= 5, "Caller should match against the 12-store inventory"
    # Options should come from Ella's stores (vendor label uses 'Vendor — Product').
    vendors = " ".join(o.vendor for o in ranked.options)
    assert any(name in vendors for name in ("Allure Bridals", "Rebecca Ingram", "Stella York"))
    # Ranked best-first, each a real clickable listing.
    scores = [o.match_score for o in ranked.options]
    assert scores == sorted(scores, reverse=True)
    assert all(o.source_url and o.source_url.startswith("http") for o in ranked.options)
