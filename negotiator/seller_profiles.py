"""
Seller profile seeds — Caller → Ella handoff for agent-to-agent (owner: Cole).

The Caller assigns each of the top-N options a distinct `NegotiationStyleId` and a
`SellerState` seed (economics + fee_template). Ella owns the SellerAgent policy that
*consumes* these seeds — see docs/ella-seller-a2a-requirements.md.

Cole's responsibility ends at: style tags on RankedOptions + deterministic seeds so
the Orchestrator can spawn ≥3 distinct counterparty styles without waiting on Ella.
"""
from __future__ import annotations

from typing import Optional

from .contracts import (
    AddOn,
    Capacity,
    FeeLine,
    Inventory,
    NegotiationStyleId,
    Option,
    RankedOptions,
    SellerState,
)

# Challenge + vertical config: these three must appear in every demo run.
DEMO_STYLES: tuple[NegotiationStyleId, ...] = (
    "tough_negotiator",
    "stonewaller_no_prices_by_phone",
    "hard_sell_upseller",
)

# Bridal fee lines the Caller insists on capturing for comparability.
_BRIDAL_FEE_CODES: dict[str, tuple[str, bool]] = {
    "base": ("Gown / base price", False),
    "alterations": ("Alterations package", True),
    "veil": ("Veil / accessory bundle", True),
    "rush": ("Rush / expedited production", True),
    "deposit": ("Deposit to hold order", False),
    "shipping": ("Shipping / delivery", True),
}


def default_fee_template(listed_price: float, style: NegotiationStyleId) -> list[FeeLine]:
    """Itemization the Caller expects to extract; amounts are starting offers, not floors."""
    base = listed_price
    lines = [
        FeeLine(code="base", label=_BRIDAL_FEE_CODES["base"][0], amount=round(base, 2)),
        FeeLine(
            code="deposit",
            label=_BRIDAL_FEE_CODES["deposit"][0],
            amount=round(base * 0.20, 2),
            optional=False,
        ),
    ]
    if style == "hard_sell_upseller":
        lines.extend(
            [
                FeeLine(code="alterations", label=_BRIDAL_FEE_CODES["alterations"][0],
                        amount=350.0, optional=True),
                FeeLine(code="veil", label=_BRIDAL_FEE_CODES["veil"][0],
                        amount=120.0, optional=True),
                FeeLine(code="rush", label=_BRIDAL_FEE_CODES["rush"][0],
                        amount=200.0, optional=True),
                FeeLine(code="shipping", label=_BRIDAL_FEE_CODES["shipping"][0],
                        amount=75.0, optional=True),
            ]
        )
    elif style == "tough_negotiator":
        lines.append(
            FeeLine(code="alterations", label=_BRIDAL_FEE_CODES["alterations"][0],
                    amount=250.0, optional=True)
        )
    else:  # stonewaller — sparse until they commit; Caller still tracks the slots
        lines.append(
            FeeLine(code="shipping", label=_BRIDAL_FEE_CODES["shipping"][0],
                    amount=0.0, optional=True)
        )
    return lines


def _economics_for_style(
    listed: float, style: NegotiationStyleId
) -> tuple[float, float, Inventory, Capacity, list[AddOn]]:
    """Private seller economics — inventory/capacity drive dynamic_floor (§8.4)."""
    if style == "tough_negotiator":
        # Fresh, scarce stock → hold near list, concede slowly.
        return (
            round(listed * 0.72, 2),
            round(listed * 0.22, 2),
            Inventory(sku_units=2, stock_age_days=14),
            Capacity(lead_time_days=28, at_capacity=False),
            [AddOn(name="deposit_hold", price=round(listed * 0.20, 2))],
        )
    if style == "stonewaller_no_prices_by_phone":
        # At capacity → prefers callback / appointment over phone discount.
        return (
            round(listed * 0.65, 2),
            round(listed * 0.18, 2),
            Inventory(sku_units=6, stock_age_days=60),
            Capacity(lead_time_days=45, at_capacity=True),
            [],
        )
    # hard_sell_upseller — aging stock + fat add-on catalog; concedes on base, pushes bundles.
    return (
        round(listed * 0.55, 2),
        round(listed * 0.12, 2),
        Inventory(sku_units=18, stock_age_days=240),
        Capacity(lead_time_days=21, at_capacity=False),
        [
            AddOn(name="veil", price=120.0),
            AddOn(name="alterations", price=350.0),
            AddOn(name="rush", price=200.0),
        ],
    )


def seed_seller_state(option: Option, style: Optional[NegotiationStyleId] = None) -> SellerState:
    """Build the SellerState Ella’s agent is constructed with."""
    style = style or option.negotiation_style or "tough_negotiator"
    listed = option.listed_price
    cost_floor, min_margin, inventory, capacity, addons = _economics_for_style(listed, style)
    fees = list(option.fee_template) or default_fee_template(listed, style)
    return SellerState(
        vendor=option.vendor,
        cost_floor=cost_floor,
        list_price=listed,
        min_margin=min_margin,
        inventory=inventory,
        capacity=capacity,
        catalog_addons=addons,
        style=style,
        fee_template=fees,
    )


def assign_styles(options: list[Option]) -> list[Option]:
    """Stamp the top options with the three required styles (cycle if >3)."""
    out: list[Option] = []
    for i, opt in enumerate(options):
        style = DEMO_STYLES[i % len(DEMO_STYLES)]
        fees = list(opt.fee_template) or default_fee_template(opt.listed_price, style)
        # Agent-to-agent demo legs use mock (or ucp when wired); keep voice if already set.
        channel = opt.channel
        if channel.type == "mock" and opt.phone and not channel.endpoint:
            channel = channel.model_copy(update={"endpoint": f"tel:{opt.phone}"})
        out.append(
            opt.model_copy(
                update={
                    "negotiation_style": style,
                    "fee_template": fees,
                    "channel": channel,
                }
            )
        )
    return out


def build_states_for_ranked(
    ranked: RankedOptions,
    top_n: int = 3,
) -> dict[str, SellerState]:
    """option_id → SellerState for the Orchestrator’s parallel sessions."""
    states: dict[str, SellerState] = {}
    for opt in ranked.options[:top_n]:
        style = opt.negotiation_style or DEMO_STYLES[len(states) % len(DEMO_STYLES)]
        states[opt.option_id] = seed_seller_state(opt, style)
    return states
