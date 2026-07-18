"""
Buyer value / ZOPA model  (owner: Cole) — §7.

The buyer-side utility function, consumed by the Caller (to score listings) and
the Buyer Agent (to evaluate offers). Pure, no I/O, unit-tested — both modules import it.

Signatures stay price-first for backward compatibility with the Buyer Agent. Pass
`offer_attrs` to enable multi-attribute scoring (hard-constraint feasibility + soft
weights / substitution penalties from §7).
"""
from __future__ import annotations

from typing import Mapping, Optional

from .contracts import Attribute, NegotiationSession, ProductSpec

# Soft-attr miss when the offer lands in the allowed substitution set (not preferred).
_SUBSTITUTION_PENALTY = 0.35
# Blend between price utility and soft-attribute utility when attrs are supplied.
_PRICE_WEIGHT = 0.55


def _norm(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _attr_partial(attr: Attribute, offer_value: Optional[str]) -> float:
    """Soft-attribute partial utility u_i ∈ [0, 1] (§7)."""
    if offer_value is None:
        return 0.0
    preferred = _norm(attr.value)
    got = _norm(offer_value)
    if not preferred:
        return 1.0 if got else 0.0
    if got == preferred:
        return 1.0
    if any(_norm(s) == got for s in attr.substitutions):
        return max(0.0, 1.0 - _SUBSTITUTION_PENALTY)
    return 0.0


def _hard_attrs_ok(spec: ProductSpec, offer_attrs: Mapping[str, str]) -> bool:
    for attr in spec.attributes:
        if attr.constraint != "hard":
            continue
        got = offer_attrs.get(attr.name)
        if got is None:
            return False
        allowed = {_norm(attr.value)} | {_norm(s) for s in attr.substitutions}
        allowed.discard("")
        if _norm(got) not in allowed:
            return False
    return True


def _price_utility(offer_price: float, spec: ProductSpec) -> float:
    """1.0 at/below target → 0.0 at reservation (linear)."""
    target = spec.negotiation.target_price
    reservation = spec.negotiation.reservation_price
    if reservation <= target:
        return 1.0 if offer_price <= target else 0.0
    return max(0.0, min(1.0, (reservation - offer_price) / (reservation - target)))


def _soft_attr_utility(spec: ProductSpec, offer_attrs: Mapping[str, str]) -> float:
    soft = [a for a in spec.attributes if a.constraint == "soft"]
    if not soft:
        return 1.0
    total_w = sum((a.weight if a.weight is not None else 1.0) for a in soft)
    if total_w <= 0:
        total_w = float(len(soft))
    score = 0.0
    for attr in soft:
        w = attr.weight if attr.weight is not None else 1.0
        score += (w / total_w) * _attr_partial(attr, offer_attrs.get(attr.name))
    return max(0.0, min(1.0, score))


def is_feasible(
    offer_price: float,
    spec: ProductSpec,
    offer_attrs: Optional[Mapping[str, str]] = None,
) -> bool:
    """Hard walk-away on price; hard attributes must match preferred or substitutions."""
    if offer_price > spec.negotiation.reservation_price:
        return False
    if offer_attrs is None:
        return True
    return _hard_attrs_ok(spec, offer_attrs)


def utility(
    offer_price: float,
    spec: ProductSpec,
    offer_attrs: Optional[Mapping[str, str]] = None,
) -> float:
    """0..1 utility of a feasible offer.

    Price-only when `offer_attrs` is omitted (Buyer Agent negotiation turns).
    With attrs: U ≈ w_price · price_u + (1 − w_price) · Σ ŵ_i · u_i  (§7).
    Infeasible offers (hard-attr miss) score 0.
    """
    if offer_attrs is not None and not _hard_attrs_ok(spec, offer_attrs):
        return 0.0

    price_u = _price_utility(offer_price, spec)
    soft = [a for a in spec.attributes if a.constraint == "soft"]
    if offer_attrs is None or not soft:
        return price_u

    attr_u = _soft_attr_utility(spec, offer_attrs)
    return max(0.0, min(1.0, _PRICE_WEIGHT * price_u + (1.0 - _PRICE_WEIGHT) * attr_u))


def should_accept(
    offer_price: float,
    session: NegotiationSession,
    spec: ProductSpec,
    offer_attrs: Optional[Mapping[str, str]] = None,
) -> bool:
    """Accept only if feasible AND at least as good as the live BATNA (else walk)."""
    batna = session.batna_utility or 0.0
    return is_feasible(offer_price, spec, offer_attrs) and utility(offer_price, spec, offer_attrs) >= batna


def next_concession(
    session: NegotiationSession,
    spec: ProductSpec,
    round_idx: int,
    max_rounds: int,
) -> float:
    """Buyer's max willingness-to-pay this round.

    Boulware: hold near target early, concede toward reservation late (convex curve).
    Returns a price that rises from target_price → reservation_price over the rounds.
    """
    target = spec.negotiation.target_price
    reservation = spec.negotiation.reservation_price
    frac = (round_idx / max(1, max_rounds)) ** 2  # convex: slow then fast
    return target + (reservation - target) * min(1.0, frac)


def unmet_soft_attributes(
    spec: ProductSpec,
    offer_attrs: Mapping[str, str],
) -> list[str]:
    """Soft attributes not at the preferred value — concession fodder for the Buyer Agent."""
    unmet: list[str] = []
    for attr in spec.attributes:
        if attr.constraint != "soft":
            continue
        got = offer_attrs.get(attr.name)
        if got is None or _norm(got) != _norm(attr.value):
            unmet.append(attr.name)
    return unmet
