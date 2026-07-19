"""
Store catalog (owner: Cole) — makes the Caller search a real inventory instead of a
thin hardcoded list.

Loads the vendor inventory Ella prepared (`data/market/wedding_stores.csv` — 12 real
bridal stores with product, price, and attributes) into plain listing dicts the Caller
scores against the buyer's spec. Keeps only the *public* product fields (vendor, product,
price, attributes, lead time, URL); the seller's private economics live on the seller
side, not here.

    from negotiator import store_catalog
    listings = store_catalog.load_store_listings("wedding-dress")   # -> 12 dicts

CLI preview:
    python -m negotiator.store_catalog wedding-dress
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "market"

# vertical -> inventory file (add a row here to make a new vertical searchable).
_STORE_FILES = {
    "wedding-dress": "wedding_stores.csv",
}


def _store_path(vertical: str) -> Optional[Path]:
    name = _STORE_FILES.get((vertical or "").strip().lower())
    if not name:
        return None
    path = _DATA_DIR / name
    return path if path.exists() else None


def _parse_attributes(raw: str) -> dict[str, str]:
    """'color:ivory;size:US 8;designer:Pronovias' -> {'color':'ivory', ...}."""
    attrs: dict[str, str] = {}
    for pair in (raw or "").split(";"):
        if ":" in pair:
            key, _, value = pair.partition(":")
            key, value = key.strip(), value.strip()
            if key and value:
                attrs[key] = value
    return attrs


def load_store_listings(vertical: str = "wedding-dress") -> list[dict]:
    """Return the vertical's stores as listing dicts:
    {vendor, product_name, source_url, listed_price, currency, attributes,
     channel_type, channel_endpoint, seller_style, lead_time_days}.
    Empty list if the vertical has no inventory file (Caller then falls back)."""
    path = _store_path(vertical)
    if path is None:
        return []

    listings: list[dict] = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            try:
                price = float(row["listed_price"])
            except (KeyError, TypeError, ValueError):
                continue
            product = (row.get("product_name") or "").strip()
            vendor = (row.get("vendor") or "").strip()
            label = f"{vendor} — {product}" if product else vendor
            listings.append({
                "vendor": label,
                "product_name": product,
                "source_url": (row.get("source_url") or "").strip() or None,
                "listed_price": price,
                "currency": (row.get("currency") or "USD").strip(),
                "attributes": _parse_attributes(row.get("matched_attributes", "")),
                # These are phone/appointment sellers the Caller quotes over voice.
                "channel_type": "voice",
                "channel_endpoint": None,
                "seller_style": (row.get("seller_style") or "").strip(),
                "lead_time_days": _int_or_none(row.get("lead_time_days")),
            })
    return listings


def _int_or_none(v) -> Optional[int]:
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def _cli(argv: Optional[list] = None) -> int:
    import sys

    argv = argv if argv is not None else sys.argv[1:]
    vertical = argv[0] if argv else "wedding-dress"
    listings = load_store_listings(vertical)
    print(f"{len(listings)} stores in '{vertical}':")
    for x in listings:
        attrs = ", ".join(f"{k}={v}" for k, v in x["attributes"].items())
        print(f"  ${x['listed_price']:>6.0f}  {x['vendor']:<34}  [{x['seller_style']}]  {attrs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
