"""Scenario 2 — gather → verify → shortlist, with tracing and Scenario-3 hand-off."""
import json
from pathlib import Path

from negotiator import orchestrator
from negotiator.contracts import ProductSpec, RankedOptions
from negotiator.inquiry import gather_quotes, run_scenario2, shortlist
from negotiator.seller_market import load_market
from negotiator.tracing import Tracer

_SPEC = ProductSpec.model_validate(
    json.loads((Path(__file__).resolve().parent.parent / "fixtures" / "wedding_market_spec.json").read_text())
)


def _pool():
    return gather_quotes(_SPEC, load_market())


def test_pool_contacts_all_twelve_and_verifies_a_leverageable_subset():
    pool = _pool()
    assert len(pool.quotes) == 12
    # A defensible BATNA needs several firm quotes (market_benchmarks.MIN_QUOTES_FOR_BATNA=3).
    assert len(pool.verified()) >= 3
    assert pool.median_comparable() is not None


def test_stonewallers_never_yield_a_firm_price():
    pool = _pool()
    stone = [q for q in pool.quotes if q.persona == "stonewaller"]
    assert stone and all(q.status == "no_price" and not q.verified for q in stone)


def test_verification_catches_the_fake_low_teaser():
    pool = _pool()
    teasers = [q for q in pool.quotes if q.persona == "lowball_teaser"]
    assert teasers
    for q in teasers:
        assert q.status == "red_flag" and not q.verified
        assert "bait_and_switch" in q.red_flags
        assert any(r.startswith("suspiciously_low_lowball") for r in q.red_flags)


def test_over_reservation_sticker_is_pruned_as_infeasible():
    pool = _pool()
    over = [q for q in pool.quotes if q.comparable_total and q.comparable_total > _SPEC.negotiation.reservation_price]
    assert over and all(q.status == "infeasible" and not q.verified for q in over)


def test_upseller_survives_but_is_flagged_for_padding():
    pool = _pool()
    up = [q for q in pool.quotes if q.persona == "upseller"]
    assert up
    for q in up:
        assert q.verified and q.status == "flagged"
        assert "hidden_fee_stack" in q.verification_flags


def test_shortlist_keeps_three_to_five_verified_options():
    pool = _pool()
    ranked = shortlist(pool, _SPEC, keep=5)
    assert isinstance(ranked, RankedOptions)
    assert 3 <= len(ranked.options) <= 5
    kept = {o.option_id for o in ranked.options}
    verified_ids = {q.option_id for q in pool.verified()}
    assert kept <= verified_ids                      # nothing unverified sneaks in
    # Ranked best-first by buyer utility.
    scores = [o.match_score for o in ranked.options]
    assert scores == sorted(scores, reverse=True)


def test_pruned_set_excludes_stonewallers_teasers_and_over_budget():
    pool = _pool()
    ranked = shortlist(pool, _SPEC, keep=5)
    kept = {o.option_id for o in ranked.options}
    for q in pool.quotes:
        if q.status in ("no_price", "red_flag", "infeasible"):
            assert q.option_id not in kept


def test_tracing_emits_the_full_inquiry_lifecycle():
    tracer = Tracer()
    pool = gather_quotes(_SPEC, load_market(), tracer=tracer)
    shortlist(pool, _SPEC, keep=5, tracer=tracer)
    kinds = {e.kind for e in tracer.events()}
    assert {"inquiry_start", "disclosure", "verification", "evidence", "prune", "shortlist"} <= kinds
    # Each of the 12 sellers gets at least one disclosure turn traced.
    disclosures = [e for e in tracer.events() if e.kind == "disclosure"]
    assert len({e.vendor for e in disclosures}) == 12


def test_shortlist_feeds_scenario_three():
    result = run_scenario2(_SPEC, keep=5)
    ranked = result["shortlist"]
    out = orchestrator.run(ranked, _SPEC, top_n=3)
    assert len(out["sessions"]) == min(3, len(ranked.options))
    assert all(s.status in ("agreed", "walked_away", "refused") for s in out["sessions"])


def test_pipeline_is_deterministic():
    a = shortlist(_pool(), _SPEC, keep=5)
    b = shortlist(_pool(), _SPEC, keep=5)
    assert [o.option_id for o in a.options] == [o.option_id for o in b.options]
