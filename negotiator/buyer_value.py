"""
Buyer value / ZOPA model  (owner: Cole + Kazi) — §7.

The buyer-side utility function, consumed by the Estimator (to score listings) and
the Buyer Agent (to evaluate offers). Pure, no I/O, unit-tested — both modules import it.

This skeleton is price-only. The nice-to-have is full multi-attribute weights +
substitution penalties (see §7); keep the signatures stable and extend the bodies.
"""
from __future__ import annotations

from .contracts import NegotiationSession, ProductSpec


def is_feasible(offer_price: float, spec: ProductSpec) -> bool:
    """Any offer above the reservation price is infeasible (hard walk-away)."""
    return offer_price <= spec.negotiation.reservation_price


def utility(offer_price: float, spec: ProductSpec) -> float:
    """0..1 utility of a feasible offer. 1.0 at/below target, 0.0 at reservation.

    TODO(Cole/Kazi): add soft-attribute partial utility Σ w_i·u_i(value_i) once
    the Caller returns matched/unmet attributes per offer.
    """
    target = spec.negotiation.target_price
    reservation = spec.negotiation.reservation_price
    if reservation <= target:
        return 1.0 if offer_price <= target else 0.0
    return max(0.0, min(1.0, (reservation - offer_price) / (reservation - target)))


def should_accept(offer_price: float, session: NegotiationSession, spec: ProductSpec) -> bool:
    """Accept only if feasible AND at least as good as the live BATNA (else walk)."""
    batna = session.batna_utility or 0.0
    return is_feasible(offer_price, spec) and utility(offer_price, spec) >= batna


def next_concession(session: NegotiationSession, spec: ProductSpec, round_idx: int, max_rounds: int) -> float:
    """Buyer's max willingness-to-pay this round.

    Boulware: hold near target early, concede toward reservation late (convex curve).
    Returns a price that rises from target_price → reservation_price over the rounds.
    """
    target = spec.negotiation.target_price
    reservation = spec.negotiation.reservation_price
    frac = (round_idx / max(1, max_rounds)) ** 2   # convex: slow then fast
    return target + (reservation - target) * min(1.0, frac)
