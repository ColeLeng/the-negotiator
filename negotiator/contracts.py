"""
Frozen data contracts — the integration surface (see docs/technical-architecture.md §4).

These Pydantic models ARE the interface between modules. Freeze them first; everyone
codes to these shapes and stubs their output to match, so downstream owners can integrate
before upstream logic is finished.

    Estimator  ──ProductSpec──▶  Caller  ──RankedOptions──▶  Orchestrator
                                                                  │ spawns
                                            BuyerAgent ⇄ SellerAgent  →  NegotiationSession
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Constraint = Literal["hard", "soft"]
ChannelType = Literal["voice", "ucp", "mock"]
MessageIntent = Literal["open", "counter", "concede", "accept", "reject", "hangup"]
SessionStatus = Literal["in_progress", "agreed", "walked_away", "refused"]
Side = Literal["buyer", "seller"]


# ── 4.1 ProductSpec — Estimator → Caller ────────────────────────────────────
class Attribute(BaseModel):
    """One product attribute, tagged hard (must match) vs soft (tradeable)."""
    name: str
    value: Optional[str] = None
    constraint: Constraint = "soft"
    weight: Optional[float] = None            # relative importance for soft attrs
    substitutions: list[str] = Field(default_factory=list)


class Negotiation(BaseModel):
    target_price: float                       # what we hope to pay
    reservation_price: float                  # hard walk-away max
    currency: str = "USD"
    deadline_days: Optional[int] = None
    must_have_summary: Optional[str] = None


class ProductSpec(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    context: str = Field(default="https://schema.org", alias="@context")
    type: str = Field(default="Product", alias="@type")
    category: Optional[str] = None
    spec_id: str
    attributes: list[Attribute] = Field(default_factory=list)
    negotiation: Negotiation


# ── 4.2 RankedOptions — Caller → Orchestrator/Closer ────────────────────────
class Channel(BaseModel):
    type: ChannelType = "mock"
    endpoint: Optional[str] = None


class Option(BaseModel):
    option_id: str
    vendor: str
    source_url: Optional[str] = None
    listed_price: float
    currency: str = "USD"
    matched_attributes: dict[str, str] = Field(default_factory=dict)
    unmet_soft: list[str] = Field(default_factory=list)   # concession fodder
    match_score: float = 0.0                              # 0..1 utility of the listed offer
    channel: Channel = Field(default_factory=Channel)


class RankedOptions(BaseModel):
    spec_id: str
    options: list[Option] = Field(default_factory=list)
    generated_at: Optional[str] = None


# ── 4.3 NegotiationSession / NegotiationMessage — Closer runtime + transcript ─
class NegotiationMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ts: Optional[str] = None
    # 'from' is a Python keyword → stored as `sender`, serialized as "from".
    sender: Side = Field(alias="from")
    intent: MessageIntent
    price: Optional[float] = None
    terms_delta: dict[str, str] = Field(default_factory=dict)
    text: Optional[str] = None
    rationale: Optional[str] = None


class NegotiationSession(BaseModel):
    session_id: str
    option_id: str
    spec_id: str
    status: SessionStatus = "in_progress"
    current_price: Optional[float] = None       # the moving number the UI watches
    current_terms: dict[str, object] = Field(default_factory=dict)
    batna_utility: Optional[float] = None        # updated live from the blackboard
    messages: list[NegotiationMessage] = Field(default_factory=list)
    outcome: Optional[dict] = None


# ── Seller private state (constructs a SellerAgent) ──────────────────────────
class Inventory(BaseModel):
    sku_units: int = 0
    stock_age_days: int = 0


class Capacity(BaseModel):
    lead_time_days: int = 0
    at_capacity: bool = False


class AddOn(BaseModel):
    name: str
    price: float


class SellerState(BaseModel):
    vendor: str
    cost_floor: float
    list_price: float
    min_margin: float = 0.0
    inventory: Inventory = Field(default_factory=Inventory)
    capacity: Capacity = Field(default_factory=Capacity)
    catalog_addons: list[AddOn] = Field(default_factory=list)


# ── Honesty guard output ─────────────────────────────────────────────────────
class ParsedOffer(BaseModel):
    """Sanitized inbound offer — raw seller text with any injection neutralized."""
    price: Optional[float] = None
    terms: dict[str, str] = Field(default_factory=dict)
    intent: Optional[MessageIntent] = None
    raw_text: Optional[str] = None
    flags: list[str] = Field(default_factory=list)   # e.g. "injection_attempt"


def buyer_msg(intent: MessageIntent, **kw) -> NegotiationMessage:
    return NegotiationMessage(sender="buyer", intent=intent, **kw)


def seller_msg(intent: MessageIntent, **kw) -> NegotiationMessage:
    return NegotiationMessage(sender="seller", intent=intent, **kw)
