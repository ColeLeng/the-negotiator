"""
Seller value model  (owner: Ella) — §8.4. The mirror of buyer_value, opposite direction.

The key insight for the "real moving price" criterion: `inventory` and `capacity`
modulate the seller's reservation price (dynamic_floor) in real time. A seller sitting
on aging stock has a lower floor, so it concedes — and the price genuinely moves.
The width of the ZOPA is an emergent product of two private states, not a scripted number.

Pure function — testable in isolation.
"""
from __future__ import annotations

from typing import Optional

from .contracts import SellerState


def inventory_relief(state: SellerState) -> float:
    """How much aging / piled-up stock lowers the effective floor (up to ~min_margin).

    Old, plentiful stock → the seller will concede below its nominal margin to clear it.
    """
    age_factor = min(1.0, state.inventory.stock_age_days / 180.0)
    stock_factor = min(1.0, state.inventory.sku_units / 20.0)
    return state.min_margin * 0.8 * (0.5 * age_factor + 0.5 * stock_factor)


def strategic_bonus(state: SellerState) -> float:
    """Extra willingness to concede purely to clear aged / piled-up stock (§8.4 bonus).

    Distinct from `inventory_relief`: relief reflects that the item is *worth* less to
    hold; this bonus is a strategic push to move a specific SKU that has sat too long.
    Small (≤ ~8% of margin), only kicks in past a staleness threshold.
    """
    if state.inventory.stock_age_days < 120:
        return 0.0
    age_over = min(1.0, (state.inventory.stock_age_days - 120) / 240.0)
    glut = min(1.0, state.inventory.sku_units / 20.0)
    return state.min_margin * 0.08 * (0.6 * age_over + 0.4 * glut)


def capacity_penalty(state: SellerState) -> float:
    """When at capacity, the seller would rather quote a longer lead time than discount.

    Returns the number of *extra* lead-time days to surface in `terms_delta` instead of
    dropping price. Zero when not at capacity. This is a margin lever: trade time, not money.
    """
    if not state.capacity.at_capacity:
        return 0.0
    # The more backed up, the more lead time offered in lieu of price movement.
    return round(min(30.0, 7.0 + 0.5 * state.capacity.lead_time_days), 1)


def dynamic_floor(state: SellerState) -> float:
    """Lowest price the seller will accept right now. Mirror of the buyer's walk-away.

    Aged/glutted stock lowers the floor via both `inventory_relief` and `strategic_bonus`,
    so an upseller sitting on old inventory concedes measurably further (Done-when #1).
    Never drops below `cost_floor` — the seller never sells at a loss.
    """
    floor = state.cost_floor + state.min_margin - inventory_relief(state) - strategic_bonus(state)
    return max(state.cost_floor, round(floor, 2))


def surplus(offer_price: float, state: SellerState) -> float:
    """Seller surplus at a given price (mirror of buyer utility)."""
    return offer_price - dynamic_floor(state)


def next_seller_min(state: SellerState, round_idx: int, max_rounds: int) -> float:
    """Seller's minimum acceptable price this round: list_price → dynamic_floor (never below)."""
    floor = dynamic_floor(state)
    start = max(state.list_price, floor)
    frac = (round_idx / max(1, max_rounds)) ** 2
    return max(floor, start - (start - floor) * min(1.0, frac))


def credit_expected_cost(
    face: float,
    redemption_prob: float = 0.6,
    cogs_ratio: float = 0.5,
    action_value: float = 0.0,
) -> float:
    """Expected margin cost of a post-purchase credit.

    A $X store credit rarely costs $X of margin: not everyone redeems (`redemption_prob`)
    and what they buy carries margin (`cogs_ratio` < 1 of the face is real cost). The
    `action_value` the seller gets in return (a photo review / preference data has real
    marketing worth) is netted off. Can go negative — i.e. the credit pays for itself.
    """
    return round(face * redemption_prob * cogs_ratio - action_value, 2)


def choose_credit(list_price: float, price_gap: float, action_value: float = 0.0) -> Optional[float]:
    """Pick the smallest standard credit ($10, $20, or 5% of list) whose *expected cost*
    is cheaper than cutting price by `price_gap`. Returns None if a price cut is cheaper.

    This is the core margin move: swap a dollar-for-dollar price concession for a
    contingent, non-refundable credit that costs the seller far less in expectation and
    buys a review / preference data on top.
    """
    if price_gap <= 0:
        return None
    tiers = sorted({10.0, 20.0, round(list_price * 0.05, 2)})
    for face in tiers:
        if face <= 0:
            continue
        if credit_expected_cost(face, action_value=action_value) < price_gap:
            return face
    return None


def value_hold(my_min: float, list_price: float, value_score: float) -> float:
    """Brand value → hold the round-minimum closer to list (concede less).

    A merchant with strong service/returns/craftsmanship (high `value_score`, 0..1) has a
    justified reason to give up less ground each round, so the landing price lands higher.
    Only ever raises `my_min` toward list; never lowers it, never exceeds list.
    """
    vs = max(0.0, min(1.0, value_score))
    gap = max(0.0, list_price - my_min)          # only pull up when below list
    return my_min + gap * 0.5 * vs


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
