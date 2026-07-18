"""
Call-list discovery for the Caller (owner: Cole) — challenge §2.

In the real world the call list comes from Google Places / Yelp (business name,
phone, rating, place_id). When `GOOGLE_PLACES_API_KEY` or `YELP_FUSION_API_KEY`
is set we hit those APIs; otherwise we fall back to a curated Places-shaped
catalog so the demo still shows *where the list would come from*.

Does not negotiate — only returns candidate businesses for RankedOptions.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx

from .contracts import CallListProvenance

_VERTICALS_DIR = Path(__file__).resolve().parent.parent / "config" / "verticals"


@dataclass(frozen=True)
class CallListEntry:
    vendor: str
    phone: Optional[str]
    source_url: Optional[str]
    listed_price: float
    attributes: dict[str, str]
    provenance: CallListProvenance
    rating: Optional[float] = None


# Curated bridal boutiques shaped like Places results — real phones/URLs a human
# can verify. Prices sit in the demo band so ZOPA has room to move.
_CURATED_BRIDAL: list[CallListEntry] = [
    CallListEntry(
        vendor="Kleinfeld Bridal",
        phone="+1-212-452-4500",
        source_url="https://www.kleinfeldbridal.com/collections/wedding-dresses",
        listed_price=2400.0,
        attributes={"color": "ivory", "size": "US 8", "brand": "Vera Wang"},
        provenance=CallListProvenance(
            provider="curated_catalog",
            query="bridal boutique OR wedding dress shop",
            place_id="curated:kleinfeld-nyc",
            note="Stand-in for a Google Places hit (rating≥4, radius 40km). Live key → Places Text.",
        ),
        rating=4.6,
    ),
    CallListEntry(
        vendor="BHLDN / Anthropologie",
        phone="+1-800-309-2500",
        source_url="https://www.bhldn.com/category/wedding-dresses",
        listed_price=2195.0,
        attributes={"color": "ivory", "size": "US 8", "brand": "comparable designer"},
        provenance=CallListProvenance(
            provider="curated_catalog",
            query="bridal boutique OR wedding dress shop",
            place_id="curated:bhldn",
            note="Stand-in for a Yelp Fusion hit. Live key → Yelp Fusion.",
        ),
        rating=4.3,
    ),
    CallListEntry(
        vendor="David's Bridal",
        phone="+1-800-274-3464",
        source_url="https://www.davidsbridal.com/wedding-dresses",
        listed_price=1899.0,
        attributes={"color": "off-white", "size": "US 8", "brand": "comparable designer"},
        provenance=CallListProvenance(
            provider="curated_catalog",
            query="bridal boutique OR wedding dress shop",
            place_id="curated:davids-bridal",
            note="National chain CS line — same shape as a Places phone field.",
        ),
        rating=4.0,
    ),
    CallListEntry(
        vendor="Pronovias (Official)",
        phone="+1-212-897-6393",
        source_url="https://www.pronovias.com/us/wedding-dresses",
        listed_price=2380.0,
        attributes={"color": "ivory", "size": "US 8", "brand": "Pronovias"},
        provenance=CallListProvenance(
            provider="curated_catalog",
            query="Pronovias bridal boutique",
            place_id="curated:pronovias",
            note="Brand boutique — DTC customer-service line path from vertical config.",
        ),
        rating=4.5,
    ),
    CallListEntry(
        vendor="Azazie Bridal",
        phone="+1-855-622-9243",
        source_url="https://www.azazie.com/all/wedding-dresses",
        listed_price=1980.0,
        attributes={"color": "champagne", "size": "US 8", "brand": "comparable designer"},
        provenance=CallListProvenance(
            provider="curated_catalog",
            query="Azazie wedding dress",
            place_id="curated:azazie",
            note="Online DTC with listed CS phone — agent-to-agent mock channel in demo.",
        ),
        rating=4.2,
    ),
]


def _load_vertical(name: Optional[str] = None) -> dict[str, Any]:
    key = (name or os.getenv("VERTICAL") or "wedding-dress").strip().lower()
    # ProductSpec.category is often "WeddingDress" — normalize.
    key = key.replace("_", "-").replace(" ", "-")
    if key.endswith("dress") and "wedding" not in key:
        key = "wedding-dress"
    if "wedding" in key:
        key = "wedding-dress"
    path = _VERTICALS_DIR / f"{key}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _places_query(vertical: dict[str, Any]) -> str:
    cls = vertical.get("callListSource") or {}
    return str(cls.get("query") or "bridal boutique OR wedding dress shop")


def _search_google_places(query: str, api_key: str) -> list[CallListEntry]:
    """Text Search → place details (phone). Prices unknown → 0 (Caller fills from catalog/web)."""
    entries: list[CallListEntry] = []
    with httpx.Client(timeout=12.0) as client:
        resp = client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": query, "key": api_key},
        )
        if resp.status_code != 200:
            return []
        for hit in (resp.json().get("results") or [])[:8]:
            place_id = hit.get("place_id") or ""
            name = hit.get("name") or "Unknown boutique"
            rating = hit.get("rating")
            phone = None
            url = hit.get("website")
            if place_id:
                detail = client.get(
                    "https://maps.googleapis.com/maps/api/place/details/json",
                    params={
                        "place_id": place_id,
                        "fields": "formatted_phone_number,international_phone_number,website",
                        "key": api_key,
                    },
                )
                if detail.status_code == 200:
                    result = detail.json().get("result") or {}
                    phone = (
                        result.get("international_phone_number")
                        or result.get("formatted_phone_number")
                    )
                    url = result.get("website") or url
            entries.append(
                CallListEntry(
                    vendor=name,
                    phone=phone,
                    source_url=url,
                    listed_price=0.0,
                    attributes={},
                    provenance=CallListProvenance(
                        provider="google_places",
                        query=query,
                        place_id=place_id or None,
                        note="Live Google Places Text Search + Details.",
                    ),
                    rating=float(rating) if rating is not None else None,
                )
            )
    return entries


def _search_yelp(query: str, api_key: str, location: str = "New York, NY") -> list[CallListEntry]:
    entries: list[CallListEntry] = []
    with httpx.Client(timeout=12.0) as client:
        resp = client.get(
            "https://api.yelp.com/v3/businesses/search",
            params={"term": query, "location": location, "limit": 8},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        if resp.status_code != 200:
            return []
        for hit in resp.json().get("businesses") or []:
            entries.append(
                CallListEntry(
                    vendor=hit.get("name") or "Yelp business",
                    phone=hit.get("phone") or hit.get("display_phone"),
                    source_url=hit.get("url"),
                    listed_price=0.0,
                    attributes={},
                    provenance=CallListProvenance(
                        provider="yelp",
                        query=query,
                        place_id=hit.get("id"),
                        note="Live Yelp Fusion business search.",
                    ),
                    rating=float(hit["rating"]) if hit.get("rating") is not None else None,
                )
            )
    return entries


def discover_call_list(
    category: Optional[str] = None,
    min_results: int = 3,
) -> tuple[list[CallListEntry], CallListProvenance]:
    """Return (entries, aggregate provenance) for the Caller.

    Prefer live Places, then Yelp; always pad with curated catalog so the demo
    never stalls without keys — and provenance still names the real-world source.
    """
    vertical = _load_vertical(category)
    query = _places_query(vertical)
    live: list[CallListEntry] = []

    places_key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    yelp_key = os.getenv("YELP_FUSION_API_KEY", "").strip()

    if places_key:
        try:
            live = _search_google_places(query, places_key)
        except Exception:
            live = []
        if live:
            prov = CallListProvenance(
                provider="google_places",
                query=query,
                note=f"{len(live)} live Places results (+ curated pad if <{min_results}).",
            )
            if len(live) >= min_results:
                return live, prov
    if yelp_key and len(live) < min_results:
        try:
            yelp = _search_yelp(query, yelp_key)
        except Exception:
            yelp = []
        if yelp:
            live = live + yelp
            prov = CallListProvenance(
                provider="yelp",
                query=query,
                note=f"{len(yelp)} live Yelp results (merged).",
            )
            if len(live) >= min_results:
                return live, prov

    # Curated pad — still advertises Places/Yelp as the production source.
    curated = list(_CURATED_BRIDAL)
    if "wedding" not in (category or vertical.get("vertical") or "wedding").lower() \
            and "dress" not in (category or "").lower():
        curated = curated[:3]  # still return something shape-compatible

    merged = _dedupe(live + curated)
    prov = CallListProvenance(
        provider="curated_catalog",
        query=query,
        note=(
            "Demo catalog shaped like Google Places / Yelp hits (name, phone, place_id, rating). "
            "Set GOOGLE_PLACES_API_KEY or YELP_FUSION_API_KEY for live discovery."
        ),
    )
    return merged, prov


def _dedupe(entries: list[CallListEntry]) -> list[CallListEntry]:
    seen: set[str] = set()
    out: list[CallListEntry] = []
    for e in entries:
        key = (e.phone or e.source_url or e.vendor).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out
