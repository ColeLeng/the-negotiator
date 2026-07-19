"""
tests/test_wedding_dress_scenario.py
====================================
Verifiable data support for the narrowed wedding-dress scenario
(see docs/wedding-dress-research.md).

Covers:
  - the five wedding-dress channel subtypes exist and are cross-channel ordered
  - the alterations/add-on red flag behaves at the documented threshold
  - the runnable demo fixture conforms to the frozen contracts
  - the fixture's numbers are self-consistent (buyer utility ranking + a real
    ZOPA on the made-to-order leg, so the "price moves" claim holds)
  - the config JSON and market_benchmarks agree on per-channel medians
    (keeps the two data sources reconciled)

Run:
    pytest tests/test_wedding_dress_scenario.py -v
"""
import json
from pathlib import Path

import pytest

from negotiator import buyer_value, seller_value
from negotiator.contracts import ProductSpec, RankedOptions, SellerState
from negotiator.market_benchmarks import (
    get_vertical_config, evaluate_red_flags, get_price_bounds,
)

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "fixtures" / "wedding_dress_scenario.json"
CONFIG = REPO / "config" / "verticals" / "wedding-dress.json"

DRESS_SUBTYPES = [
    "dress_resale",
    "dress_sample_sale",
    "dress_off_the_rack",
    "dress_made_to_order",
    "dress_custom",
]


@pytest.fixture(scope="module")
def scenario():
    return json.loads(FIXTURE.read_text())


@pytest.fixture(scope="module")
def config():
    return json.loads(CONFIG.read_text())


# --- market_benchmarks: the five channel subtypes --------------------------

def test_all_five_dress_subtypes_registered():
    bands = get_vertical_config("wedding").price_bands
    for subtype in DRESS_SUBTYPES:
        assert subtype in bands, f"missing wedding subtype {subtype}"


def test_channel_medians_are_ordered():
    """resale < sample_sale < off_the_rack < made_to_order < custom."""
    bands = get_vertical_config("wedding").price_bands
    medians = [bands[s].market_median for s in DRESS_SUBTYPES]
    assert medians == sorted(medians), f"channel medians not ordered: {medians}"


def test_price_bounds_available_per_channel():
    for subtype in DRESS_SUBTYPES:
        b = get_price_bounds("wedding", subtype)
        assert b.target_price < b.reservation_price < b.walkaway_price
        assert b.currency == "USD"


# --- alterations / add-on red flag -----------------------------------------

def test_alterations_stack_fires_above_threshold():
    band = get_vertical_config("wedding").price_bands["dress_made_to_order"]
    offer = band.market_median * 1.35  # 35% above -> above the 30% threshold
    hits = evaluate_red_flags("wedding", offer_price=offer,
                              market_median=band.market_median)
    names = [h.rule_name for h in hits]
    assert "alterations_and_addon_stack" in names, names


def test_no_flags_at_channel_median():
    band = get_vertical_config("wedding").price_bands["dress_made_to_order"]
    hits = evaluate_red_flags("wedding", offer_price=band.market_median,
                              market_median=band.market_median)
    assert hits == [], f"unexpected flags at median: {hits}"


# --- fixture conforms to the frozen contracts ------------------------------

def test_fixture_spec_and_options_validate(scenario):
    spec = ProductSpec.model_validate(scenario["spec"])
    ro = RankedOptions.model_validate(scenario["ranked_options"])
    assert spec.spec_id == ro.spec_id
    assert len(ro.options) == 3
    sellers = {k: SellerState.model_validate(v)
               for k, v in scenario["sellers"].items()}
    assert set(sellers) == {o.option_id for o in ro.options}


def test_fixture_utility_ranking_is_consistent(scenario):
    """Listed-price utility must rank resale > sample > made-to-order."""
    spec = ProductSpec.model_validate(scenario["spec"])
    ro = RankedOptions.model_validate(scenario["ranked_options"])
    by_id = {o.option_id: o for o in ro.options}
    u = {oid: buyer_value.utility(o.listed_price, spec) for oid, o in by_id.items()}
    assert u["opt_resale"] > u["opt_sample"] > u["opt_mto"]
    # stored match_scores should match the computed utilities
    for oid, o in by_id.items():
        assert abs(o.match_score - u[oid]) < 1e-3, oid


def test_made_to_order_has_a_real_zopa_that_moves(scenario):
    """
    The 'real moving price' claim: the made-to-order seller opens ABOVE the
    buyer's reservation but its hidden floor sits BELOW it, so a ZOPA exists
    and the price can genuinely move down into it.
    """
    spec = ProductSpec.model_validate(scenario["spec"])
    reservation = spec.negotiation.reservation_price
    mto = SellerState.model_validate(scenario["sellers"]["opt_mto"])
    floor = seller_value.dynamic_floor(mto)
    assert mto.list_price > reservation, "opening should be above reservation"
    assert floor < reservation, "hidden floor must be below reservation for a ZOPA"


# --- config JSON <-> market_benchmarks reconciliation ----------------------

def test_config_and_module_medians_agree(config):
    bands = get_vertical_config("wedding").price_bands
    by_channel = config["priceBenchmark"]["byChannel"]
    for subtype in DRESS_SUBTYPES:
        assert subtype in by_channel, f"config missing {subtype}"
        assert by_channel[subtype]["median"] == bands[subtype].market_median, (
            f"{subtype}: config median {by_channel[subtype]['median']} != "
            f"module median {bands[subtype].market_median}"
        )
