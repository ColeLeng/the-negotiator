"""
tests/test_market_benchmarks.py
================================
Unit tests for negotiator/market_benchmarks.py

Run all tests:
    pytest tests/test_market_benchmarks.py -v

Run just the minimum demoable tests:
    pytest tests/test_market_benchmarks.py -v -m "min_demo"

Coverage:
  - Registry integrity (every vertical has all required fields)
  - Price monotonicity (target < reservation < walkaway)
  - Red-flag detection (wedding tax, sight-unseen lowball, hidden fee stack)
  - BATNA calibration returns sensible numbers
  - Missing vertical / subtype raise clear KeyError messages
  - Attribute weight distributions sum to ~1.0

The demo-critical test at the bottom:
    "a wedding-tagged floral quote 25% above the median MUST fire the
     wedding_tax_markup red flag."
"""

import pytest
from negotiator.market_benchmarks import (
    # data classes
    PriceBenchmark, RedFlagRule, RedFlagHit, NegotiationLever,
    BatnaGuidance, VerticalConfig, PriceBounds,
    # public functions
    list_supported_verticals, get_vertical_config, get_price_bounds,
    evaluate_red_flags, suggest_batna_calibration, default_attribute_weights,
    # registry + constants
    VERTICAL_REGISTRY, LOWBALL_PCT, CATEGORY_TAG_MARKUP, HIDDEN_FEE_STACK,
    MIN_QUOTES_FOR_BATNA, GOOD_QUOTES_FOR_BATNA, STRONG_QUOTES_FOR_BATNA,
)


# -----------------------------------------------------------------------------
# Shared fixtures -- one per vertical, plus a parametrized "all verticals"
# -----------------------------------------------------------------------------

@pytest.fixture
def wedding():
    return get_vertical_config("wedding")


@pytest.fixture
def custom_furniture():
    return get_vertical_config("custom_furniture")


@pytest.fixture
def moving():
    return get_vertical_config("moving_local")


@pytest.fixture
def b2b_packaging():
    return get_vertical_config("b2b_packaging_smb")


# Parametrize helper for tests that must pass on every registered vertical
ALL_VERTICALS = sorted(VERTICAL_REGISTRY.keys())


# -----------------------------------------------------------------------------
# Registry integrity -- cheap safety net; runs on every push
# -----------------------------------------------------------------------------

class TestRegistryIntegrity:

    def test_registry_is_non_empty(self):
        assert len(VERTICAL_REGISTRY) >= 1

    def test_list_supported_verticals_matches_registry(self):
        assert list_supported_verticals() == sorted(VERTICAL_REGISTRY.keys())

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_vertical_has_at_least_one_price_band(self, vertical):
        cfg = get_vertical_config(vertical)
        assert len(cfg.price_bands) >= 1, \
            f"Vertical '{vertical}' has no price bands"

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_vertical_has_at_least_one_red_flag(self, vertical):
        cfg = get_vertical_config(vertical)
        assert len(cfg.red_flags) >= 1, \
            f"Vertical '{vertical}' has no red-flag rules"

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_vertical_has_at_least_one_lever(self, vertical):
        cfg = get_vertical_config(vertical)
        assert len(cfg.levers) >= 1, \
            f"Vertical '{vertical}' has no negotiation levers"

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_vertical_has_batna_guidance(self, vertical):
        cfg = get_vertical_config(vertical)
        assert isinstance(cfg.batna_guidance, BatnaGuidance)


# -----------------------------------------------------------------------------
# Price monotonicity -- target < reservation < walkaway, and inside market band
# -----------------------------------------------------------------------------

class TestPriceMonotonicity:

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_target_less_than_reservation_less_than_walkaway(self, vertical):
        cfg = get_vertical_config(vertical)
        for subtype, band in cfg.price_bands.items():
            assert band.target_price < band.reservation_price, (
                f"{vertical}/{subtype}: target {band.target_price} "
                f">= reservation {band.reservation_price}"
            )
            assert band.reservation_price <= band.walkaway_price, (
                f"{vertical}/{subtype}: reservation {band.reservation_price} "
                f"> walkaway {band.walkaway_price}"
            )

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_market_low_median_high_ordered(self, vertical):
        cfg = get_vertical_config(vertical)
        for subtype, band in cfg.price_bands.items():
            assert band.market_low < band.market_median < band.market_high, (
                f"{vertical}/{subtype}: market band not strictly ordered"
            )

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_all_prices_positive(self, vertical):
        cfg = get_vertical_config(vertical)
        for subtype, band in cfg.price_bands.items():
            for field_name in [
                "market_low", "market_median", "market_high",
                "target_price", "reservation_price", "walkaway_price",
            ]:
                assert getattr(band, field_name) > 0, \
                    f"{vertical}/{subtype}: {field_name} is non-positive"


# -----------------------------------------------------------------------------
# get_price_bounds -- Estimator's main entry point
# -----------------------------------------------------------------------------

class TestGetPriceBounds:

    def test_returns_price_bounds_instance(self, wedding):
        bounds = get_price_bounds("wedding", "photography")
        assert isinstance(bounds, PriceBounds)

    def test_bounds_match_registered_band(self):
        bounds = get_price_bounds("wedding", "photography")
        band = get_vertical_config("wedding").price_bands["photography"]
        assert bounds.target_price == band.target_price
        assert bounds.reservation_price == band.reservation_price
        assert bounds.walkaway_price == band.walkaway_price
        assert bounds.market_median == band.market_median

    def test_currency_propagates(self):
        bounds = get_price_bounds("wedding", "photography")
        assert bounds.currency == "USD"

    def test_unknown_vertical_raises(self):
        with pytest.raises(KeyError, match="Unknown vertical"):
            get_price_bounds("space_tourism", "orbital")

    def test_unknown_subtype_raises_with_available_list(self):
        with pytest.raises(KeyError, match="Available subtypes"):
            get_price_bounds("wedding", "hovercraft")

    def test_buyer_ctx_none_is_accepted(self):
        """Forward-compatibility: None ctx must not crash."""
        bounds = get_price_bounds("wedding", "cake", buyer_ctx=None)
        assert bounds.target_price > 0

    def test_buyer_ctx_empty_dict_is_accepted(self):
        bounds = get_price_bounds("wedding", "cake", buyer_ctx={})
        assert bounds.target_price > 0


# -----------------------------------------------------------------------------
# evaluate_red_flags -- Buyer Agent's sanity check on each incoming offer
# -----------------------------------------------------------------------------

class TestEvaluateRedFlags:

    def test_offer_at_median_fires_no_flags(self):
        """A quote right at market median should be clean."""
        band = get_vertical_config("wedding").price_bands["floral"]
        hits = evaluate_red_flags(
            "wedding", offer_price=band.market_median,
            market_median=band.market_median,
        )
        # At the median, no direction-based rule should fire
        assert hits == [], f"Unexpected flags at median: {hits}"

    def test_gouging_offer_fires_wedding_tax_flag(self):
        """
        Offer 30% above median -- wedding_tax_markup (threshold 25%) fires.
        """
        band = get_vertical_config("wedding").price_bands["floral"]
        gouging = band.market_median * 1.30
        hits = evaluate_red_flags(
            "wedding", offer_price=gouging,
            market_median=band.market_median,
        )
        flag_names = [h.rule_name for h in hits]
        assert "wedding_tax_markup" in flag_names, \
            f"Expected wedding_tax_markup, got {flag_names}"

    def test_lowball_offer_fires_lowball_flag(self):
        """
        Offer 35% below median -- suspiciously_low_lowball (threshold 30%) fires.
        """
        band = get_vertical_config("wedding").price_bands["floral"]
        lowball = band.market_median * 0.65
        hits = evaluate_red_flags(
            "wedding", offer_price=lowball,
            market_median=band.market_median,
        )
        flag_names = [h.rule_name for h in hits]
        assert "suspiciously_low_lowball" in flag_names, \
            f"Expected suspiciously_low_lowball, got {flag_names}"

    def test_moving_sight_unseen_lowball_fires(self):
        """Moving lowball threshold matches FMCSA guidance."""
        band = get_vertical_config("moving_local").price_bands["two_bedroom_45mi"]
        lowball = band.market_median * 0.60
        hits = evaluate_red_flags(
            "moving_local", offer_price=lowball,
            market_median=band.market_median,
        )
        flag_names = [h.rule_name for h in hits]
        assert "sight_unseen_lowball" in flag_names

    def test_custom_furniture_hidden_stack_fires(self):
        """Custom furniture offer 40% above median -- hidden_fee_stack fires."""
        band = get_vertical_config("custom_furniture").price_bands["single_piece"]
        gouging = band.market_median * 1.40
        hits = evaluate_red_flags(
            "custom_furniture", offer_price=gouging,
            market_median=band.market_median,
        )
        flag_names = [h.rule_name for h in hits]
        assert "hidden_fee_stack" in flag_names

    def test_hit_carries_severity_and_message(self):
        band = get_vertical_config("wedding").price_bands["floral"]
        hits = evaluate_red_flags(
            "wedding", offer_price=band.market_median * 1.3,
            market_median=band.market_median,
        )
        for h in hits:
            assert isinstance(h, RedFlagHit)
            assert h.severity in ("info", "warning", "block")
            assert len(h.message) > 20, "Message too short for transcript use"

    def test_market_median_defaults_to_first_band(self):
        """If Buyer Agent forgets to pass market_median, we fall back."""
        hits = evaluate_red_flags(
            "wedding", offer_price=100_000,  # obviously gouging
            market_median=None,
        )
        assert len(hits) >= 1, \
            "Should still detect gouging using fallback median"

    def test_non_positive_median_returns_empty(self):
        """Defensive: bad median should not crash."""
        hits = evaluate_red_flags(
            "wedding", offer_price=1000, market_median=0,
        )
        assert hits == []


# -----------------------------------------------------------------------------
# suggest_batna_calibration
# -----------------------------------------------------------------------------

class TestBatnaCalibration:

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_returns_batna_guidance(self, vertical):
        g = suggest_batna_calibration(vertical)
        assert isinstance(g, BatnaGuidance)

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_min_recommended_strong_are_ordered(self, vertical):
        g = suggest_batna_calibration(vertical)
        assert g.min_quotes <= g.recommended_quotes <= g.strong_quotes

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_min_quotes_at_least_two(self, vertical):
        """One quote is not a BATNA."""
        g = suggest_batna_calibration(vertical)
        assert g.min_quotes >= 2


# -----------------------------------------------------------------------------
# default_attribute_weights
# -----------------------------------------------------------------------------

class TestDefaultAttributeWeights:

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_weights_sum_to_approximately_one(self, vertical):
        weights = default_attribute_weights(vertical)
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-6, \
            f"{vertical}: weights sum to {total}, not 1.0"

    @pytest.mark.parametrize("vertical", ALL_VERTICALS)
    def test_all_weights_positive(self, vertical):
        weights = default_attribute_weights(vertical)
        for name, w in weights.items():
            assert w > 0, f"{vertical}: weight for '{name}' is non-positive"

    def test_returned_dict_is_a_copy(self):
        """Mutating the returned dict must not affect the registry."""
        w1 = default_attribute_weights("wedding")
        w1["date_availability"] = 99.0
        w2 = default_attribute_weights("wedding")
        assert w2["date_availability"] != 99.0, \
            "Registry was mutated by caller"


# -----------------------------------------------------------------------------
# Error surface -- Estimator must get useful KeyError messages
# -----------------------------------------------------------------------------

class TestErrorMessages:

    def test_unknown_vertical_lists_supported(self):
        with pytest.raises(KeyError) as exc_info:
            get_vertical_config("blockchain_wedding")
        # Message should include at least one real vertical name
        msg = str(exc_info.value)
        assert "wedding" in msg or "moving" in msg or "furniture" in msg


# -----------------------------------------------------------------------------
# Demo-critical tests -- the ones that MUST pass for the pitch
# -----------------------------------------------------------------------------

class TestDemoCritical:

    @pytest.mark.min_demo
    def test_wedding_tax_fires_on_25pct_markup(self):
        """
        THE KEY CRITERION for the wedding vertical demo:
        A floral quote 25%+ above the median must fire wedding_tax_markup,
        which is what makes the "wedding tax" story from Consumer Reports
        actionable in the negotiation loop.
        """
        band = get_vertical_config("wedding").price_bands["floral"]
        offer = band.market_median * 1.30  # 30% above median
        hits = evaluate_red_flags(
            "wedding", offer_price=offer,
            market_median=band.market_median,
        )
        assert any(h.rule_name == "wedding_tax_markup" for h in hits), (
            f"wedding_tax_markup should fire at +30% markup. "
            f"Got flags: {[h.rule_name for h in hits]}"
        )

    @pytest.mark.min_demo
    def test_estimator_can_bootstrap_wedding_spec(self):
        """
        Demo path: user says 'wedding photographer'; Estimator calls
        get_price_bounds() and default_attribute_weights() to build a
        valid ProductSpec. This test proves that both calls succeed and
        return non-degenerate values.
        """
        bounds = get_price_bounds("wedding", "photography")
        weights = default_attribute_weights("wedding")

        # Bounds are usable
        assert bounds.target_price > 0
        assert bounds.reservation_price > bounds.target_price
        assert bounds.currency == "USD"

        # Weights are a valid distribution
        assert len(weights) >= 3
        assert abs(sum(weights.values()) - 1.0) < 1e-6

    @pytest.mark.min_demo
    def test_config_swap_end_to_end(self):
        """
        THE most important architectural test:
        Swapping from wedding -> custom_furniture -> moving must NOT change
        the shape of what get_price_bounds() returns. The Estimator can
        loop over verticals without special-casing any of them.
        """
        results = {}
        for v, subtype in [
            ("wedding", "photography"),
            ("custom_furniture", "single_piece"),
            ("moving_local", "two_bedroom_45mi"),
            ("b2b_packaging_smb", "annual_contract"),
        ]:
            bounds = get_price_bounds(v, subtype)
            results[v] = bounds

        # All returned same shape
        for v, b in results.items():
            assert isinstance(b, PriceBounds), f"{v} returned wrong type"
            assert b.target_price < b.reservation_price, f"{v} bounds broken"
            assert b.currency, f"{v} missing currency"
