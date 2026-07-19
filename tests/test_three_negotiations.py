"""
tests/test_three_negotiations.py
=================================
demo/three_negotiations/ -- the "three seller styles" rehearsal harness (Cole voices
all three). See demo/three_negotiations/README.md for what's real vs. scripted.

Coverage:
  - All three scenarios run to a structured outcome, tagged with the right style.
  - Scenario 1 (tough-but-fair): price genuinely moves, the honesty guard actually
    ran and passed a real (blackboard-backed) competing-quote claim, and the AI
    disclosure + friction preamble is present in the transcript.
  - Scenario 2 (stonewaller): ends in a callback/range commitment, not a bare price.
  - Scenario 3 (upseller): the add-on fees show up as terms_delta, itemized.
  - Every TraceEvent from run_all() is tagged with its scenario's style, so the
    3-lane panel can always route events to the right lane.
"""
from __future__ import annotations

from negotiator.tracing import Tracer
from demo.three_negotiations.runner import run_all
from demo.three_negotiations.scenarios import SCENARIOS_ORDER, UPSELLER_ADDONS, build_scenarios


def test_build_scenarios_covers_all_three_styles():
    scenarios = build_scenarios()
    assert set(scenarios.keys()) == set(SCENARIOS_ORDER) == {"tough_but_fair", "stonewaller", "upseller"}


def test_run_all_returns_a_result_per_style():
    results = run_all()
    assert set(results.keys()) == {"tough_but_fair", "stonewaller", "upseller"}
    for style, r in results.items():
        assert r["session"].status in ("agreed", "walked_away", "refused")
        assert isinstance(r["checklist"], dict)


class TestToughButFair:

    def test_price_genuinely_moves(self):
        r = run_all()["tough_but_fair"]
        prices = [m.price for m in r["session"].messages if m.price is not None]
        assert len(set(prices)) >= 3
        assert r["checklist"]["price_moves"] is True

    def test_ai_discloses_and_friction_is_handled(self):
        r = run_all()["tough_but_fair"]
        assert r["checklist"]["ai_disclosure"] is True
        assert r["checklist"]["friction_handled"] is True
        disclosure_lines = [m for m in r["session"].messages if m.sender == "buyer" and "AI" in (m.text or "")]
        assert disclosure_lines, "the transcript must contain the buyer's actual disclosure line"

    def test_honesty_guard_actually_ran_and_passed_a_real_claim(self):
        """The competing-quote claim must be backed by a real blackboard price --
        this is what proves the guard isn't just decorative."""
        tracer = Tracer()
        run_all(tracer=tracer)
        honesty_events = [e for e in tracer.events()
                           if e.kind == "honesty_check" and e.detail.get("style") == "tough_but_fair"]
        assert len(honesty_events) == 1
        assert "comparable quote at $" in honesty_events[0].detail["text"]

    def test_ends_in_a_structured_agreement(self):
        r = run_all()["tough_but_fair"]
        assert r["session"].status == "agreed"
        assert r["session"].outcome["status"] == "agreed"


class TestStonewaller:

    def test_does_not_end_in_a_bare_accept(self):
        """The point of this style is a callback/range, not a negotiated price."""
        r = run_all()["stonewaller"]
        assert r["session"].status != "agreed"
        assert r["checklist"]["callback_or_range_extracted"] is True

    def test_transcript_carries_a_range_or_callback_commitment(self):
        r = run_all()["stonewaller"]
        terms = [m.terms_delta for m in r["session"].messages]
        assert any("price_range" in t or "callback" in t for t in terms)

    def test_still_a_structured_ending_not_a_vague_hang_up(self):
        r = run_all()["stonewaller"]
        assert r["checklist"]["structured_ending"] is True
        assert r["session"].outcome is not None


class TestUpseller:

    def test_addon_fees_are_itemized_in_terms_delta(self):
        r = run_all()["upseller"]
        assert r["checklist"]["fees_itemized"] is True
        sellers_opening_ask = next(m for m in r["session"].messages if m.sender == "seller")
        assert set(sellers_opening_ask.terms_delta) & set(UPSELLER_ADDONS)

    def test_price_still_moves_down_from_the_inflated_ask(self):
        r = run_all()["upseller"]
        seller_prices = [m.price for m in r["session"].messages if m.sender == "seller" and m.price is not None]
        assert seller_prices[0] > seller_prices[-1], "the inflated opening ask must come down"


class TestTracingIntegration:

    def test_every_event_is_tagged_with_its_style(self):
        tracer = Tracer()
        run_all(tracer=tracer)
        untagged = [e for e in tracer.events() if e.kind not in ("call_start",) and "style" not in e.detail]
        assert untagged == [], f"events missing a style tag: {[e.kind for e in untagged]}"

    def test_call_start_and_call_end_bracket_each_scenario(self):
        tracer = Tracer()
        run_all(tracer=tracer)
        starts = [e.detail["style"] for e in tracer.events() if e.kind == "call_start"]
        ends = [e.detail["style"] for e in tracer.events() if e.kind == "call_end"]
        assert starts == SCENARIOS_ORDER
        assert ends == SCENARIOS_ORDER

    def test_call_end_carries_the_final_status_and_checklist(self):
        tracer = Tracer()
        run_all(tracer=tracer)
        for e in tracer.events():
            if e.kind == "call_end":
                assert e.detail["status"] in ("agreed", "walked_away", "refused")
                assert isinstance(e.detail["checklist"], dict)

    def test_no_tracer_is_a_no_op(self):
        """run_all() must work without a tracer -- e.g. a plain fallback endpoint."""
        results = run_all(tracer=None)
        assert len(results) == 3
