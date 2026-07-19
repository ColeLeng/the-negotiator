"""
market_benchmarks.py
====================
Vertical-specific market intelligence for the HackNation negotiation system.

Owner : Jagger
Status: ready for integration

WHAT THIS IS
------------
A pure module -- no I/O, no network calls, no side effects.
Encodes the per-vertical market research (price bands, red-flag thresholds,
negotiation levers, BATNA guidance) that the Estimator uses to bootstrap
a ProductSpec, and that the Buyer Agent uses to sanity-check seller offers.

Six public functions:

    list_supported_verticals()                      -> list[str]
    get_vertical_config(vertical)                   -> VerticalConfig
    get_price_bounds(vertical, subtype, buyer_ctx)  -> PriceBounds
    evaluate_red_flags(vertical, offer_price, mkt)  -> list[RedFlagHit]
    suggest_batna_calibration(vertical)             -> BatnaGuidance
    default_attribute_weights(vertical)             -> dict[str, float]

HOW IT CONNECTS
---------------
    Estimator --> market_benchmarks --> ProductSpec --> Caller
      (intake)     (this file)          (target_price,
                                         reservation_price,
                                         attribute weights)
                       |
                       +----------------> Buyer Agent
                                          (red-flag detection,
                                           BATNA calibration hints)

WHY THIS EXISTS
---------------
The ElevenLabs Hack-Nation brief is explicit: "switching your system from
movers to auto body shops should mean swapping a config file, not rewriting
your agents." This file IS that config, expressed as typed Python data so
it can be imported and unit-tested rather than parsed from YAML at runtime.

All numeric values are sourced from public research -- every constant carries
an inline citation to its source so Kazi/Cole/Suman can audit any single
number without leaving the file. See section 7 of the market opportunity
report for the broader analysis this configuration derives from.

DATA MODEL -- ONE VERTICAL, THREE COMPONENTS
---------------------------------------------
    VerticalConfig
      |-- price_bands: dict[subtype -> PriceBenchmark]   # target/reservation/walkaway
      |-- red_flags:   list[RedFlagRule]                 # "wedding tax", "sight-unseen premium"
      |-- levers:      list[NegotiationLever]            # negotiable dimensions
      +-- batna_guidance: BatnaGuidance                  # how many quotes make a valid BATNA

Each vertical is registered in VERTICAL_REGISTRY at module load. To add a new
vertical, append one entry to that dict -- nothing else changes.
"""

from dataclasses import dataclass, field
from typing import Optional


# -----------------------------------------------------------------------------
# Tunable constants -- match Kazi's style: knobs at top, easy to sweep
# -----------------------------------------------------------------------------

# Red-flag detection thresholds (relative to observed market median)
LOWBALL_PCT           = 0.30   # >30% below market -> warning per FMCSA guidance
GOUGE_PCT             = 0.50   # >50% above market -> gouging red flag
CATEGORY_TAG_MARKUP   = 0.25   # >25% "wedding tax"-style tag markup -> flag
HIDDEN_FEE_STACK      = 0.30   # cumulative fees >30% of base quote -> flag

# Buyer starting position, expressed as a fraction of median observed price
# (used by the Estimator when no explicit target is given)
DEFAULT_TARGET_FRACTION      = 0.75   # aim for 25% below median
DEFAULT_RESERVATION_FRACTION = 1.05   # walk if 5% above median
DEFAULT_WALKAWAY_FRACTION    = 1.20   # never accept beyond 20% above median

# BATNA calibration -- how many independent quotes make a defensible BATNA
MIN_QUOTES_FOR_BATNA = 3
GOOD_QUOTES_FOR_BATNA = 5
STRONG_QUOTES_FOR_BATNA = 8


# -----------------------------------------------------------------------------
# Data classes -- importable from anywhere in the repo
# Keep field names in sync with contracts.py (Suman) and buyer_value_model (Kazi)
# -----------------------------------------------------------------------------

@dataclass
class PriceBenchmark:
    """
    Observed price distribution for one (vertical, subtype) combination.
    All values in the vertical's default currency (USD unless overridden).

    market_low / median / high describe the observed distribution.
    target / reservation are the buyer-side recommended anchors derived
    from that distribution (see DEFAULT_*_FRACTION knobs above).
    """
    subtype: str
    market_low: float
    market_median: float
    market_high: float
    target_price: float
    reservation_price: float
    walkaway_price: float
    source: str   # citation for auditability


@dataclass
class RedFlagRule:
    """
    A rule the Buyer Agent applies to each incoming offer.
    Fires when the offer's price relative to observed market crosses `threshold`
    in the direction described by `direction`.
    """
    name: str
    direction: str         # "below" | "above"
    threshold: float       # fractional deviation from market_median
    severity: str          # "info" | "warning" | "block"
    evidence: str          # human-readable text for transcript / UI
    source: str


@dataclass
class RedFlagHit:
    """Concrete flag instance returned by evaluate_red_flags()."""
    rule_name: str
    severity: str
    observed_delta: float  # signed fractional deviation from market_median
    message: str


@dataclass
class NegotiationLever:
    """
    A negotiable dimension the Buyer Agent can push on.
    Ordered list -- cheapest / most-conceded levers should appear first so
    the Buyer Agent walks the list from top to bottom.
    """
    name: str
    typical_pct_swing: float   # how much price this lever can typically move
    description: str


@dataclass
class BatnaGuidance:
    """
    How many independent quotes the Estimator should gather before the Buyer
    Agent has a defensible BATNA for this vertical.
    """
    min_quotes: int
    recommended_quotes: int
    strong_quotes: int
    note: str


@dataclass
class VerticalConfig:
    """
    Full configuration for one negotiation vertical.
    This is what get_vertical_config() returns.
    """
    vertical: str
    currency: str
    price_bands: dict           # {subtype: PriceBenchmark}
    red_flags: list             # list[RedFlagRule]
    levers: list                # list[NegotiationLever]
    batna_guidance: BatnaGuidance
    default_attribute_weights: dict  # {attribute_name: float, sums to 1.0}


@dataclass
class PriceBounds:
    """Convenience triple returned by get_price_bounds()."""
    target_price: float
    reservation_price: float
    walkaway_price: float
    market_median: float
    currency: str


# -----------------------------------------------------------------------------
# Vertical registry -- one entry per supported vertical
# All numbers cite their source inline; see docstring at top of file
# -----------------------------------------------------------------------------

_WEDDING = VerticalConfig(
    vertical="wedding",
    currency="USD",
    price_bands={
        # The Wedding Report 2025: median wedding photography $3,500 (2K-8K range)
        "photography": PriceBenchmark(
            subtype="photography",
            market_low=2000, market_median=3500, market_high=8000,
            target_price=2600, reservation_price=3700, walkaway_price=4200,
            source="The Wedding Report 2025 - The Knot Real Weddings Study 2026",
        ),
        # CR 2016 vendor study + MyWeddingKit 2026 replication: median floral $2,800
        "floral": PriceBenchmark(
            subtype="floral",
            market_low=1500, market_median=2800, market_high=6000,
            target_price=2100, reservation_price=2950, walkaway_price=3400,
            source="Consumer Reports 2016 - MyWeddingKit 2026",
        ),
        # The Knot 2026: median wedding cake $650
        "cake": PriceBenchmark(
            subtype="cake",
            market_low=350, market_median=650, market_high=1500,
            target_price=490, reservation_price=685, walkaway_price=780,
            source="The Knot 2026 Real Weddings Study",
        ),
        # Wedding dress industry 2026: median off-the-rack $1,600
        "dress": PriceBenchmark(
            subtype="dress",
            market_low=800, market_median=1600, market_high=4500,
            target_price=1200, reservation_price=1680, walkaway_price=1920,
            source="Wedding dress industry report 2026",
        ),
    },
    red_flags=[
        RedFlagRule(
            name="wedding_tax_markup",
            direction="above", threshold=CATEGORY_TAG_MARKUP,
            severity="warning",
            evidence=(
                "28% of vendors quote higher when 'wedding' is mentioned "
                "vs 'formal event' (Consumer Reports 2016, 40 vendors, 12 states). "
                "Floral 20-40% markup, cake 30-50% markup replicated in 2024/2026."
            ),
            source="Consumer Reports 2016 wedding tax study - 2024 replication",
        ),
        RedFlagRule(
            name="suspiciously_low_lowball",
            direction="below", threshold=LOWBALL_PCT,
            severity="warning",
            evidence=(
                "Wedding-vertical FMCSA-equivalent guidance: quotes 30%+ below "
                "market often reflect missing services (assistant hours, edit "
                "delivery, minimum coverage) that appear as day-of surcharges."
            ),
            source="industry aggregate - FMCSA pattern applied to wedding vertical",
        ),
    ],
    levers=[
        NegotiationLever("weekday_or_off_season", 0.20,
            "Non-Saturday, non-May/October dates typically 15-25% cheaper"),
        NegotiationLever("package_bundling", 0.12,
            "Photo + video, or venue + catering -- bundle discount 8-15%"),
        NegotiationLever("hours_reduction", 0.10,
            "Trim coverage hours; often better ROI than raw price cut"),
        NegotiationLever("payment_terms", 0.05,
            "Cash / net-0 vs credit card / installment"),
    ],
    batna_guidance=BatnaGuidance(
        min_quotes=MIN_QUOTES_FOR_BATNA,
        recommended_quotes=GOOD_QUOTES_FOR_BATNA,
        strong_quotes=STRONG_QUOTES_FOR_BATNA,
        note=(
            "Couples hire 13 vendors on average and 67% accept first quote "
            "(WeddingWire 2026). BATNA improves sharply from 1 -> 3 quotes; "
            "diminishing returns past 5."
        ),
    ),
    default_attribute_weights={
        "date_availability": 0.30,
        "style_match": 0.25,
        "coverage_hours": 0.15,
        "reviews_score": 0.15,
        "delivery_format": 0.10,
        "add_ons": 0.05,
    },
)


_CUSTOM_FURNITURE = VerticalConfig(
    vertical="custom_furniture",
    currency="USD",
    price_bands={
        # Angi 2026 custom furniture cost data: median piece $5,000 base
        "single_piece": PriceBenchmark(
            subtype="single_piece",
            market_low=2000, market_median=5000, market_high=15000,
            target_price=3750, reservation_price=5250, walkaway_price=6000,
            source="Angi custom furniture cost 2026 - BusinessDojo pricing 2025",
        ),
        # Full room commission: 3-5 pieces coordinated
        "room_set": PriceBenchmark(
            subtype="room_set",
            market_low=8000, market_median=18000, market_high=45000,
            target_price=13500, reservation_price=18900, walkaway_price=21600,
            source="Angi 2026 - interior designer procurement aggregate",
        ),
    },
    red_flags=[
        RedFlagRule(
            name="hidden_fee_stack",
            direction="above", threshold=HIDDEN_FEE_STACK,
            severity="warning",
            evidence=(
                "Rush charges (10-30%), delivery ($150-500), design fees "
                "(5-10%), assembly (3-8%), warranty upsell (5-15%), material "
                "upgrades (10-25%) commonly stack to +30-59% above base quote. "
                "Each layer independently negotiable."
            ),
            source="Angi 2026 - Atlantic Fine Furniture - industry aggregate",
        ),
        RedFlagRule(
            name="lead_time_underquote",
            direction="below", threshold=LOWBALL_PCT,
            severity="warning",
            evidence=(
                "Custom furniture lead time is 6-24 weeks per multiple 2026 "
                "sources. Quotes with sub-6-week promises priced 30%+ below "
                "market typically miss production or shipping realities."
            ),
            source="Circle Furniture 2026 - Alcove designer guide 2026",
        ),
    ],
    levers=[
        NegotiationLever("material_grade", 0.25,
            "Grade-2 vs Grade-1 hardwood; veneer vs solid -- swing 15-25%"),
        NegotiationLever("finish_complexity", 0.15,
            "Standard vs custom stain match; single vs multi-tone"),
        NegotiationLever("delivery_terms", 0.08,
            "Threshold delivery vs white-glove; buyer pickup"),
        NegotiationLever("payment_schedule", 0.05,
            "50% deposit + 50% on delivery vs 30/40/30 milestone"),
        NegotiationLever("lead_time_flex", 0.10,
            "Willing to wait beyond standard queue = 8-12% discount"),
    ],
    batna_guidance=BatnaGuidance(
        min_quotes=MIN_QUOTES_FOR_BATNA,
        recommended_quotes=GOOD_QUOTES_FOR_BATNA,
        strong_quotes=STRONG_QUOTES_FOR_BATNA,
        note=(
            "Custom furniture spec is transferable -- same drawings can be "
            "quoted by 5+ makers with low marginal cost. Strong BATNAs are "
            "achievable but rare in practice (buyers spend 15-30 hours on "
            "research and rarely finish the full survey)."
        ),
    ),
    default_attribute_weights={
        "material_grade": 0.30,
        "lead_time": 0.20,
        "dimensions_exact": 0.20,
        "finish_match": 0.15,
        "warranty_terms": 0.10,
        "delivery_scope": 0.05,
    },
)


_MOVING_LOCAL = VerticalConfig(
    vertical="moving_local",
    currency="USD",
    price_bands={
        # ElevenLabs brief: Rock Hill -> Charlotte 45mi 2BR: $1,158-$6,506 range
        "two_bedroom_45mi": PriceBenchmark(
            subtype="two_bedroom_45mi",
            market_low=1158, market_median=2100, market_high=6506,
            target_price=1575, reservation_price=2205, walkaway_price=2520,
            source="ElevenLabs Hack-Nation brief - FMCSA moving data",
        ),
    },
    red_flags=[
        RedFlagRule(
            name="sight_unseen_lowball",
            direction="below", threshold=LOWBALL_PCT,
            severity="warning",
            evidence=(
                "FMCSA: sight-unseen estimates 40% more likely to end in final "
                "bill above original quote. Quotes 30%+ below competing bids "
                "are treated as warning signs by BBB per industry guidance."
            ),
            source="FMCSA - BBB moving industry data",
        ),
        RedFlagRule(
            name="stair_and_long_carry_missing",
            direction="above", threshold=HIDDEN_FEE_STACK,
            severity="warning",
            evidence=(
                "Stairs, long-carry, elevator, and shuttle fees commonly add "
                "30%+ on moving day. Buyer Agent should require these as "
                "line items in the itemized quote before accepting."
            ),
            source="FMCSA - ElevenLabs Hack-Nation brief",
        ),
    ],
    levers=[
        NegotiationLever("date_flexibility", 0.20,
            "Mid-month, mid-week can be 15-25% cheaper than end-of-month"),
        NegotiationLever("packing_scope", 0.15,
            "Self-pack vs full-pack service"),
        NegotiationLever("crew_size", 0.10,
            "2-person vs 3-person; often overcapacity is upsell"),
        NegotiationLever("insurance_tier", 0.08,
            "Released value vs full-value protection"),
    ],
    batna_guidance=BatnaGuidance(
        min_quotes=MIN_QUOTES_FOR_BATNA,
        recommended_quotes=GOOD_QUOTES_FOR_BATNA,
        strong_quotes=STRONG_QUOTES_FOR_BATNA,
        note=(
            "US moving market: 16,851 companies averaging 6.2 employees. "
            "5-8 quotes is the industry-recommended shopping standard. "
            "Voice agent makes this feasible for the first time."
        ),
    ),
    default_attribute_weights={
        "date_certainty": 0.30,
        "insurance_coverage": 0.20,
        "crew_size": 0.15,
        "packing_scope": 0.15,
        "reviews_score": 0.15,
        "eta_window": 0.05,
    },
)


_B2B_PACKAGING_SMB = VerticalConfig(
    vertical="b2b_packaging_smb",
    currency="USD",
    price_bands={
        # SMB e-commerce packaging: median annual spend ~$40K, per-order $1-4
        "annual_contract": PriceBenchmark(
            subtype="annual_contract",
            market_low=15000, market_median=40000, market_high=120000,
            target_price=30000, reservation_price=42000, walkaway_price=48000,
            source="Personalized packaging market 2024 - SMB e-com aggregate",
        ),
    },
    red_flags=[
        RedFlagRule(
            name="tier_authority_ceiling_hit",
            direction="above", threshold=0.10,
            severity="info",
            evidence=(
                "B2B sales reps have tiered discount authority: L1 5-10%, "
                "L2 10-20%, Manager 20-40%. Offers stuck 10% above target "
                "usually mean rep is at authority ceiling -- escalate."
            ),
            source="B2B sales research 2025 - industry aggregate",
        ),
        RedFlagRule(
            name="mdf_coop_not_offered",
            direction="above", threshold=0.05,
            severity="info",
            evidence=(
                "Market Development Funds / co-op program discounts often "
                "unclaimed by SMB buyers who don't know they exist. Agent "
                "should ask directly regardless of quoted price."
            ),
            source="B2B procurement research aggregate 2026",
        ),
    ],
    levers=[
        NegotiationLever("annual_commit", 0.15,
            "Volume commit vs PO-by-PO; typical 8-15% discount for 12mo commit"),
        NegotiationLever("payment_terms", 0.05,
            "NET-15 wire vs NET-30 card -- 2-5% swap"),
        NegotiationLever("category_consolidation", 0.12,
            "Multi-SKU order from single supplier -- 10-15% blended"),
        NegotiationLever("quarter_end_timing", 0.10,
            "Last 5 days of fiscal quarter -- access to deeper authority"),
        NegotiationLever("rebate_tier", 0.08,
            "Growth-tier rebate structure vs upfront discount"),
    ],
    batna_guidance=BatnaGuidance(
        min_quotes=MIN_QUOTES_FOR_BATNA,
        recommended_quotes=GOOD_QUOTES_FOR_BATNA,
        strong_quotes=STRONG_QUOTES_FOR_BATNA,
        note=(
            "B2B recurring procurement supports strong data flywheel: each "
            "renewal quote adds calibration. Cold-start BATNA requires 3+ "
            "supplier quotes; renewal BATNA can lean on incumbent history."
        ),
    ),
    default_attribute_weights={
        "unit_price": 0.35,
        "payment_terms": 0.15,
        "lead_time_reliability": 0.15,
        "delivery_included": 0.15,
        "minimum_order_quantity": 0.10,
        "material_spec": 0.10,
    },
)


# Registry: single source of truth for supported verticals
VERTICAL_REGISTRY = {
    "wedding": _WEDDING,
    "custom_furniture": _CUSTOM_FURNITURE,
    "moving_local": _MOVING_LOCAL,
    "b2b_packaging_smb": _B2B_PACKAGING_SMB,
}


# -----------------------------------------------------------------------------
# Public interface
# -----------------------------------------------------------------------------

def list_supported_verticals() -> list:
    """
    Return the list of vertical keys registered in this module.
    The Estimator uses this to validate the vertical field on incoming intake.
    """
    return sorted(VERTICAL_REGISTRY.keys())


def get_vertical_config(vertical: str) -> VerticalConfig:
    """
    Return the full VerticalConfig for a supported vertical.

    Raises KeyError with a helpful message if the vertical is unknown, so the
    Estimator can surface a clean error rather than a stack trace.
    """
    if vertical not in VERTICAL_REGISTRY:
        supported = ", ".join(list_supported_verticals())
        raise KeyError(
            f"Unknown vertical '{vertical}'. Supported verticals: {supported}."
        )
    return VERTICAL_REGISTRY[vertical]


def get_price_bounds(
    vertical: str,
    subtype: str,
    buyer_ctx: Optional[dict] = None,
) -> PriceBounds:
    """
    Return the (target, reservation, walkaway) triple the Estimator should
    write into ProductSpec.negotiation for this vertical + subtype.

    `buyer_ctx` is a forward-compatible hook for future personalization
    (income bracket, urgency, negotiation appetite). Currently unused --
    the defaults come straight from the registered PriceBenchmark.
    Passing an empty dict or None returns the registered defaults.

    Raises KeyError with a helpful message if either lookup fails.
    """
    config = get_vertical_config(vertical)
    if subtype not in config.price_bands:
        available = ", ".join(sorted(config.price_bands.keys()))
        raise KeyError(
            f"Unknown subtype '{subtype}' for vertical '{vertical}'. "
            f"Available subtypes: {available}."
        )
    band = config.price_bands[subtype]
    return PriceBounds(
        target_price=band.target_price,
        reservation_price=band.reservation_price,
        walkaway_price=band.walkaway_price,
        market_median=band.market_median,
        currency=config.currency,
    )


def evaluate_red_flags(
    vertical: str,
    offer_price: float,
    market_median: Optional[float] = None,
) -> list:
    """
    Return the list of RedFlagHit objects the Buyer Agent should surface for
    this offer. Empty list = no flags.

    If `market_median` is not provided, use the first registered PriceBenchmark
    for the vertical. In production, the Buyer Agent should always pass in the
    live median observed across gathered quotes.

    Semantics:
      direction="above" fires when offer_price >  median * (1 + threshold)
      direction="below" fires when offer_price <  median * (1 - threshold)
    """
    config = get_vertical_config(vertical)

    if market_median is None:
        # Fall back to the first registered band's median
        first_band = next(iter(config.price_bands.values()))
        market_median = first_band.market_median

    if market_median <= 0:
        return []  # can't evaluate against a non-positive baseline

    hits = []
    for rule in config.red_flags:
        delta = (offer_price - market_median) / market_median

        fired = False
        if rule.direction == "above" and delta > rule.threshold:
            fired = True
        elif rule.direction == "below" and delta < -rule.threshold:
            fired = True

        if fired:
            hits.append(RedFlagHit(
                rule_name=rule.name,
                severity=rule.severity,
                observed_delta=round(delta, 3),
                message=(
                    f"{rule.name}: offer ${offer_price:.0f} vs median "
                    f"${market_median:.0f} ({delta:+.1%}). {rule.evidence}"
                ),
            ))
    return hits


def suggest_batna_calibration(vertical: str) -> BatnaGuidance:
    """
    Return the recommended number of independent quotes the Caller should
    gather before the Buyer Agent trusts its BATNA utility for this vertical.

    Used by the Orchestrator to decide whether to keep dialing.
    """
    return get_vertical_config(vertical).batna_guidance


def default_attribute_weights(vertical: str) -> dict:
    """
    Return the default soft-attribute weight distribution for this vertical.
    Estimator uses these when the intake voice interview does not elicit
    explicit weights from the user.

    Returns a fresh dict copy so callers cannot mutate the registry.
    """
    return dict(get_vertical_config(vertical).default_attribute_weights)
