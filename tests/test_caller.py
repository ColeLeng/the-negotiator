"""Caller — §6 + challenge §2 done-when checks (owner: Cole)."""
from negotiator.caller import search
from negotiator.contracts import Attribute, Negotiation, ProductSpec
from negotiator.seller_profiles import DEMO_STYLES


def _demo_spec() -> ProductSpec:
    return ProductSpec(
        spec_id="spec_demo",
        category="WeddingDress",
        attributes=[
            Attribute(name="color", value="ivory", constraint="soft", weight=0.15,
                      substitutions=["champagne", "off-white"]),
            Attribute(name="size", value="US 8", constraint="hard"),
            Attribute(name="brand", value="Pronovias", constraint="soft", weight=0.2,
                      substitutions=["Vera Wang", "comparable designer"]),
        ],
        negotiation=Negotiation(target_price=1800.0, reservation_price=2400.0, deadline_days=30),
    )


def test_search_returns_at_least_three_ranked_real_options():
    ranked = search(_demo_spec())
    assert len(ranked.options) >= 3
    assert ranked.spec_id == "spec_demo"
    scores = [o.match_score for o in ranked.options]
    assert scores == sorted(scores, reverse=True)
    for opt in ranked.options[:3]:
        assert opt.source_url and opt.source_url.startswith("http")
        assert "example.com" not in opt.source_url
        assert opt.vendor
        assert opt.listed_price > 0


def test_search_filters_hard_constraint_violations():
    ranked = search(_demo_spec())
    for opt in ranked.options:
        assert opt.matched_attributes.get("size") == "US 8"


def test_search_populates_unmet_soft_and_scores_with_attrs():
    ranked = search(_demo_spec())
    assert any(o.unmet_soft for o in ranked.options)
    by_vendor = {o.vendor: o for o in ranked.options}
    assert "Stillwhite (Pre-loved)" in by_vendor or "Pronovias (Official)" in by_vendor
    assert "Azazie Bridal" in by_vendor


def test_search_stamps_three_distinct_negotiation_styles():
    ranked = search(_demo_spec())
    styles = [o.negotiation_style for o in ranked.options[:3]]
    assert len(styles) == 3
    assert set(styles) == set(DEMO_STYLES)
    for opt in ranked.options[:3]:
        assert opt.fee_template, "each option needs a fee_template for itemized quotes"
        assert any(f.code == "base" for f in opt.fee_template)


def test_search_exposes_call_list_provenance():
    ranked = search(_demo_spec())
    assert ranked.call_list_provenance is not None
    assert ranked.call_list_provenance.provider in {
        "google_places", "yelp", "curated_catalog", "web_search"
    }
    # At least one option carries per-vendor provenance or a phone (Places-shaped).
    assert any(o.phone or o.call_list_source for o in ranked.options[:3])
