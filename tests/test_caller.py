"""Caller — §6 done-when checks (owner: Cole)."""
from negotiator.caller import search
from negotiator.contracts import Attribute, Negotiation, ProductSpec


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
    # Ranked descending by match_score.
    scores = [o.match_score for o in ranked.options]
    assert scores == sorted(scores, reverse=True)
    # Real, clickable URLs (not the old example.com stub).
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
    # At least one option should differ on a soft attr (e.g. brand not matched).
    assert any(o.unmet_soft for o in ranked.options)
    # Options are drawn from Ella's real store inventory.
    assert any("Allure Bridals" in o.vendor or "Rebecca Ingram" in o.vendor for o in ranked.options)
    # With soft matches ~equal across the ivory/US-8 stock, the cheapest listing ranks first.
    assert ranked.options[0].listed_price == min(o.listed_price for o in ranked.options)
