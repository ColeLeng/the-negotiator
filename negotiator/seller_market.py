"""
Seller market — the 12 counterparty agents for Scenario 2 (owner: Cole).

Loads the shared bridal dataset (`data/market/`, real vendors curated by Ella) and
turns each row into a `MarketSeller`: a real vendor stamped with a **disclosure
persona** and the private quote economics that persona reveals during an inquiry.

The 12 sellers span five disclosure personalities so the buyer's quote-gathering pass
meets real-world friction — some itemize honestly, some stonewall ("no prices by
phone"), some pad a bundle, some dangle a fake-low teaser. That variety is what makes
the evidence pool (and the verification that prunes it) worth building.

Product metadata + URLs are real (verifiable); the private cost/fee economics are
synthetic seeds for the demo.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .contracts import Attribute, Negotiation, ProductSpec
from .evidence import DisclosurePersona, FeeLine

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "market"

# CSV seller_style label → the base archetype we split personas out of.
_STYLE_GROUP = {
    "tough but fair": "tough",
    "tough": "tough",
    "won't quote by phone": "stonewall",
    "wont quote by phone": "stonewall",
    "no prices by phone": "stonewall",
    "upseller": "upsell",
    "hard sell upseller": "upsell",
}

# Attributes we carry into matching (mirror the buyer's spec dimensions).
_SPEC_ATTRS = ("color", "size", "silhouette", "fabric", "designer")


@dataclass
class MarketSeller:
    """One vendor the buyer will call, plus the private economics its persona discloses."""

    option_id: str
    vendor: str
    listed_price: float
    currency: str
    source_url: Optional[str]
    matched_attributes: dict[str, str]
    persona: DisclosurePersona

    # Private disclosure economics (what the seller actually knows / will reveal).
    base_price: float = 0.0
    mandatory_fees: list[FeeLine] = field(default_factory=list)
    optional_fees: list[FeeLine] = field(default_factory=list)
    deposit_pct: float = 0.20
    headline_price: Optional[float] = None       # the number the seller LEADS with
    teaser_base: Optional[float] = None          # lowball_teaser only
    ballpark: Optional[tuple[float, float]] = None  # stonewaller who caves to a range
    caves: bool = True                           # stonewaller: eventually offers a number?
    disclosure_quality: float = 1.0

    def comparable_total(self) -> float:
        """Apples-to-apples all-in: base + mandatory fees (deposits/optional excluded)."""
        return round(self.base_price + sum(f.amount for f in self.mandatory_fees), 2)


# ── CSV helpers ──────────────────────────────────────────────────────────────
def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _f(row: dict, key: str, default: float) -> float:
    v = (row.get(key) or "").strip()
    try:
        return float(v.replace(",", "")) if v else default
    except ValueError:
        return default


def _parse_attrs(raw: Optional[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in (raw or "").split(";"):
        if ":" in pair:
            k, v = pair.split(":", 1)
            k = k.strip().lower()
            if k in _SPEC_ATTRS:
                out[k] = v.strip()
    return out


# ── persona assignment ───────────────────────────────────────────────────────
def _persona_for(group: str, idx_in_group: int) -> DisclosurePersona:
    """Split the three dataset archetypes into five distinct disclosure personalities."""
    if group == "tough":
        # Fresh, confident houses: some are fully transparent, some play their cards close.
        return "transparent" if idx_in_group % 2 == 0 else "guarded"
    if group == "stonewall":
        return "stonewaller"
    if group == "upsell":
        # Volume DTC: some pad an honest bundle, some bait with a fake-low sticker.
        return "upseller" if idx_in_group % 2 == 0 else "lowball_teaser"
    return "transparent"


def _fee(code: str, label: str, amount: float, *, optional=False, mandatory=False, schedule_only=False) -> FeeLine:
    return FeeLine(code=code, label=label, amount=round(amount, 2),
                   optional=optional, mandatory=mandatory, schedule_only=schedule_only)


def _apply_economics(seller: MarketSeller) -> None:
    """Seed the private quote a persona will disclose. Deterministic (reproducible demo)."""
    listed = seller.listed_price
    deposit = _fee("deposit", "Deposit to hold order", listed * seller.deposit_pct, schedule_only=True)

    if seller.persona == "transparent":
        seller.base_price = listed
        seller.mandatory_fees = [_fee("shipping", "Shipping / delivery", 75.0, mandatory=True)]
        seller.optional_fees = [
            _fee("alterations", "Alterations package", 300.0, optional=True),
            _fee("veil", "Veil", 120.0, optional=True),
            deposit,
        ]
        seller.headline_price = seller.comparable_total()
        seller.disclosure_quality = 1.0

    elif seller.persona == "guarded":
        seller.base_price = listed
        seller.mandatory_fees = [_fee("shipping", "Shipping / delivery", 45.0, mandatory=True)]
        seller.optional_fees = [
            _fee("alterations", "Alterations package", 250.0, optional=True),
            _fee("veil", "Veil", 100.0, optional=True),
            deposit,
        ]
        seller.headline_price = listed          # leads with base only; fees on request
        seller.disclosure_quality = 0.75

    elif seller.persona == "upseller":
        seller.base_price = listed
        seller.mandatory_fees = [_fee("shipping", "Shipping / delivery", 75.0, mandatory=True)]
        seller.optional_fees = [
            _fee("alterations", "Premium alterations", 350.0, optional=True),
            _fee("veil", "Designer veil", 120.0, optional=True),
            _fee("rush", "Rush / expedited production", 200.0, optional=True),
            deposit,
        ]
        addons = sum(f.amount for f in seller.optional_fees if not f.schedule_only)
        seller.headline_price = round(listed + addons, 2)   # inflated bundle up front
        seller.disclosure_quality = 0.6

    elif seller.persona == "lowball_teaser":
        # Dangle a fake-low base; the real all-in balloons past the sticker with
        # "required" custom fees. base line is genuinely low, mandatory fees hide the truth.
        seller.teaser_base = round(listed * 0.62, 2)
        seller.base_price = seller.teaser_base
        real_all_in = round(listed * 1.12, 2)
        hidden = round(real_all_in - seller.teaser_base, 2)
        seller.mandatory_fees = [
            _fee("custom_sizing", "Required custom sizing", round(hidden * 0.6, 2), mandatory=True),
            _fee("alterations", "Mandatory alterations", round(hidden * 0.4, 2), mandatory=True),
        ]
        seller.optional_fees = [deposit]
        seller.headline_price = seller.teaser_base          # the bait
        seller.disclosure_quality = 0.3

    elif seller.persona == "stonewaller":
        # Won't quote by phone. Half eventually cave to a (wide, useless) ballpark.
        seller.base_price = listed
        seller.mandatory_fees = []
        seller.optional_fees = [deposit]
        seller.headline_price = None
        if seller.caves:
            seller.ballpark = (round(listed * 0.9, 2), round(listed * 1.3, 2))
            seller.disclosure_quality = 0.35
        else:
            seller.disclosure_quality = 0.15


# ── public loaders ───────────────────────────────────────────────────────────
def load_market(data_dir: Optional[Path] = None) -> list[MarketSeller]:
    """Load the 12 seller agents from the shared dataset, stamped with disclosure personas."""
    data_dir = data_dir or _DATA_DIR
    rows = _read_csv(data_dir / "brands.csv")
    sellers: list[MarketSeller] = []
    group_counts: dict[str, int] = {}
    for i, row in enumerate(rows, start=1):
        group = _STYLE_GROUP.get((row.get("seller_style") or "").strip().lower(), "tough")
        idx = group_counts.get(group, 0)
        group_counts[group] = idx + 1
        persona = _persona_for(group, idx)
        listed = _f(row, "listed_price", 2000.0)
        seller = MarketSeller(
            option_id=f"opt_{i}",
            vendor=(row.get("vendor") or f"Vendor {i}").strip(),
            listed_price=listed,
            currency=(row.get("currency") or "USD").strip(),
            source_url=(row.get("source_url") or "").strip() or None,
            matched_attributes=_parse_attrs(row.get("matched_attributes")),
            persona=persona,
            # Stonewallers alternate cave/no-cave so the pool has both refusal shapes.
            caves=(idx % 2 == 0) if group == "stonewall" else True,
        )
        _apply_economics(seller)
        sellers.append(seller)
    return sellers


def spec_from_csv(data_dir: Optional[Path] = None) -> ProductSpec:
    """Build the buyer's ProductSpec from the dataset's buyer.csv (Scenario-1 stand-in)."""
    data_dir = data_dir or _DATA_DIR
    buyer_rows = _read_csv(data_dir / "buyer.csv")
    attr_rows = _read_csv(data_dir / "buyer_attributes.csv")
    b = buyer_rows[0] if buyer_rows else {}
    attrs = [
        Attribute(
            name=(a.get("name") or "").strip(),
            value=((a.get("value") or "").strip() or None),
            constraint=((a.get("constraint") or "soft").strip().lower() or "soft"),  # type: ignore[arg-type]
            weight=_f(a, "weight", None),  # type: ignore[arg-type]
            substitutions=[s.strip() for s in (a.get("substitutions") or "").split(";") if s.strip()],
        )
        for a in attr_rows
        if (a.get("name") or "").strip()
    ]
    return ProductSpec(
        spec_id=(b.get("scenario_id") or "spec_market").strip(),
        category=(b.get("category") or "WeddingDress").strip(),
        attributes=attrs,
        negotiation=Negotiation(
            target_price=_f(b, "target_price", 1800.0),
            reservation_price=_f(b, "reservation_price", 2400.0),
            currency=(b.get("currency") or "USD").strip(),
            deadline_days=int(_f(b, "deadline_days", 30)) or None,
            must_have_summary=(b.get("must_have_summary") or "").strip() or None,
        ),
    )
