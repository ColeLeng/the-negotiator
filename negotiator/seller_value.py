"""
Seller value model  (owner: Ella) — §8.4. The mirror of buyer_value, opposite direction.

The key insight for the "real moving price" criterion: `inventory` and `capacity`
modulate the seller's reservation price (dynamic_floor) in real time. A seller sitting
on aging stock has a lower floor, so it concedes — and the price genuinely moves.
The width of the ZOPA is an emergent product of two private states, not a scripted number.

Pure function — testable in isolation.
"""
from __future__ import annotations

from .contracts import SellerState


def inventory_relief(state: SellerState) -> float:
    """How much aging / piled-up stock lowers the effective floor (up to ~min_margin).

    Old, plentiful stock → the seller will concede below its nominal margin to clear it.
    """
    age_factor = min(1.0, state.inventory.stock_age_days / 180.0)
    stock_factor = min(1.0, state.inventory.sku_units / 20.0)
    return state.min_margin * 0.8 * (0.5 * age_factor + 0.5 * stock_factor)


def dynamic_floor(state: SellerState) -> float:
    """Lowest price the seller will accept right now. Mirror of the buyer's walk-away."""
    return state.cost_floor + state.min_margin - inventory_relief(state)


def surplus(offer_price: float, state: SellerState) -> float:
    """Seller surplus at a given price (mirror of buyer utility)."""
    return offer_price - dynamic_floor(state)


def next_seller_min(state: SellerState, round_idx: int, max_rounds: int) -> float:
    """Seller's minimum acceptable price this round: list_price → dynamic_floor (never below)."""
    floor = dynamic_floor(state)
    start = max(state.list_price, floor)
    frac = (round_idx / max(1, max_rounds)) ** 2
    return max(floor, start - (start - floor) * min(1.0, frac))


def addon_total(state: SellerState) -> float:
    return sum(a.price for a in state.catalog_addons)


def bundled_ask(state: SellerState) -> float:
    """Upseller open: list + catalog add-ons."""
    return round(state.list_price + addon_total(state), 2)


def upsell_ask(state: SellerState, round_idx: int, max_rounds: int) -> float:
    """Concede by stripping add-ons first, then easing the gown price toward dynamic_floor."""
    floor = dynamic_floor(state)
    addons = list(state.catalog_addons)
    # Strip one add-on per early round (most expensive first).
    keep = max(0, len(addons) - round_idx)
    sorted_addons = sorted(addons, key=lambda a: a.price, reverse=True)
    remaining_addon = sum(a.price for a in sorted_addons[:keep])
    # After add-ons are gone, ease base toward floor (same curve as next_seller_min).
    base = next_seller_min(state, max(0, round_idx - len(addons)), max_rounds)
    return max(floor, round(base + remaining_addon, 2))
