"""
tests/test_estimator.py
=======================
Estimator (Section 5, "Intake by Interview or Documents") -- the demo-critical
requirement is that voice, document, and text intake all converge on the identical
ProductSpec shape, confirmed by the user before any vendor call.

Coverage:
  - Text intake for the e-commerce-packaging vertical: hard/soft tagging, price
    bounds, deadline.
  - Document intake (plain text + CSV inventory list) converges on the same spec
    as text intake for equivalent content.
  - Voice intake (ElevenLabs tool-call payload) converges on the same spec as text
    and document intake -- the demo-critical "one spec, three surfaces" test.
  - missing_requirements() / confirm_spec() -- the user-confirmation gate.
  - The market_benchmarks price-bootstrap fallback when no price is stated.
  - Backward compatibility with the existing wedding-dress demo path.
  - ElevenLabs Agent config builder (voice_intake.py) is vertical-driven and
    keyless-safe.
"""
from __future__ import annotations

import pytest

from negotiator.estimator import confirm_spec, estimate, estimate_from_document, missing_requirements
from negotiator.voice_intake import build_agent_config, create_or_update_agent, handle_tool_call

ECOMMERCE = "ecommerce-packaging"


@pytest.fixture(autouse=True)
def no_external_keys(monkeypatch):
    """Force the deterministic keyless fallback paths so tests never hit the network
    or depend on a locally-configured key."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("VERTICAL", raising=False)


def _without_id(spec) -> dict:
    data = spec.model_dump()
    data.pop("spec_id")
    return data


# -----------------------------------------------------------------------------
# Text intake -- e-commerce-packaging vertical
# -----------------------------------------------------------------------------

_ECOMMERCE_TEXT = (
    "We need custom corrugated mailer boxes, dimensions 12x9x3 inches, "
    "minimum_order_quantity: 5000 units, 4-week lead time with some flexibility, "
    "freight included, NET-30 payment terms, one-time order for now. "
    "Target price $30000, hard cap $42000, within 45 days."
)


def test_text_intake_tags_hard_and_soft_attributes():
    spec = estimate(_ECOMMERCE_TEXT, vertical=ECOMMERCE)
    by_name = {a.name: a for a in spec.attributes}

    assert by_name["material_spec"].constraint == "hard"
    assert "corrugated" in by_name["material_spec"].value
    assert by_name["minimum_order_quantity"].constraint == "hard"
    assert "5000" in by_name["minimum_order_quantity"].value
    assert by_name["dimensions"].constraint == "hard"
    assert "12x9x3" in by_name["dimensions"].value

    assert by_name["payment_terms"].constraint == "soft"
    assert by_name["payment_terms"].value == "NET-30"
    assert by_name["delivery_included"].constraint == "soft"
    assert by_name["delivery_included"].value == "freight included"
    assert by_name["annual_commit"].value == "one-time order"


def test_text_intake_sets_price_bounds_and_deadline_from_dollar_amounts():
    spec = estimate(_ECOMMERCE_TEXT, vertical=ECOMMERCE)
    assert spec.negotiation.target_price == 30000.0
    assert spec.negotiation.reservation_price == 42000.0
    assert spec.negotiation.currency == "USD"
    assert spec.negotiation.deadline_days == 45


def test_bare_quantity_is_never_mistaken_for_a_price():
    """5000 (the MOQ) must never leak into target_price/reservation_price."""
    spec = estimate(_ECOMMERCE_TEXT, vertical=ECOMMERCE)
    assert spec.negotiation.target_price != 5000.0
    assert spec.negotiation.reservation_price != 5000.0


def test_fully_specified_ecommerce_spec_has_no_missing_requirements():
    spec = estimate(_ECOMMERCE_TEXT, vertical=ECOMMERCE)
    assert missing_requirements(spec) == []


# -----------------------------------------------------------------------------
# Price bootstrap -- when no $ amount is stated, fall back to market_benchmarks
# -----------------------------------------------------------------------------

def test_missing_price_falls_back_to_market_benchmarks():
    """No dollar figure anywhere in the text -- target/reservation must come from
    market_benchmarks.get_price_bounds('b2b_packaging_smb', 'annual_contract')."""
    text = "material_spec: kraft mailer; minimum_order_quantity: 3000; dimensions: 10x8x2"
    spec = estimate(text, vertical=ECOMMERCE)
    assert spec.negotiation.target_price == 30000.0
    assert spec.negotiation.reservation_price == 42000.0


# -----------------------------------------------------------------------------
# Missing hard constraints -- the clarify-loop / confirmation gate
# -----------------------------------------------------------------------------

def test_missing_hard_constraint_is_flagged():
    text = "minimum_order_quantity: 3000; payment_terms: NET-30; target price $30000; hard cap $42000"
    spec = estimate(text, vertical=ECOMMERCE)
    missing = missing_requirements(spec)
    assert "material_spec" in missing
    assert "dimensions" in missing


def test_confirm_spec_rejects_incomplete_spec():
    text = "minimum_order_quantity: 3000; target price $30000; hard cap $42000"
    spec = estimate(text, vertical=ECOMMERCE)
    with pytest.raises(ValueError, match="material_spec"):
        confirm_spec(spec)


def test_confirm_spec_accepts_once_edits_fill_the_gap():
    text = "minimum_order_quantity: 3000; target price $30000; hard cap $42000"
    spec = estimate(text, vertical=ECOMMERCE)
    confirmed = confirm_spec(spec, edits={"material_spec": "kraft mailer", "dimensions": "10x8x2"})

    assert missing_requirements(confirmed) == []
    assert confirmed.spec_id == spec.spec_id, "confirmation must reuse the same spec_id verbatim"
    by_name = {a.name: a for a in confirmed.attributes}
    assert by_name["material_spec"].value == "kraft mailer"


def test_confirm_spec_does_not_mutate_the_original():
    text = "minimum_order_quantity: 3000; target price $30000; hard cap $42000"
    spec = estimate(text, vertical=ECOMMERCE)
    confirm_spec(spec, edits={"material_spec": "kraft mailer", "dimensions": "10x8x2"})
    assert missing_requirements(spec) != [], "original spec object must be untouched"


# -----------------------------------------------------------------------------
# Document intake -- must converge on the same spec as text intake
# -----------------------------------------------------------------------------

def test_plain_text_document_converges_with_direct_text_intake():
    text_spec = estimate(_ECOMMERCE_TEXT, vertical=ECOMMERCE)
    doc_spec = estimate_from_document(_ECOMMERCE_TEXT, "customer_notes.txt", "quote", vertical=ECOMMERCE)
    assert _without_id(text_spec) == _without_id(doc_spec)


def test_csv_inventory_list_document_extracts_structured_fields():
    csv_content = (
        "material_spec,minimum_order_quantity,dimensions,payment_terms\n"
        "kraft mailer,3000,10x8x2,NET-15\n"
    )
    spec = estimate_from_document(csv_content, "inventory.csv", "inventory_list", vertical=ECOMMERCE)
    by_name = {a.name: a for a in spec.attributes}
    assert by_name["material_spec"].value == "kraft mailer"
    assert by_name["minimum_order_quantity"].value == "3000"
    assert by_name["dimensions"].value == "10x8x2"
    assert by_name["payment_terms"].value == "NET-15"
    # No $ figure anywhere in the CSV -- price bootstrap should kick in.
    assert spec.negotiation.target_price == 30000.0


# -----------------------------------------------------------------------------
# Voice intake -- ElevenLabs tool-call payload converges with text/document intake
# -----------------------------------------------------------------------------

_VOICE_TOOL_ARGS = {
    "attributes": {
        "material_spec": "kraft mailer",
        "minimum_order_quantity": "3000 units",
        "dimensions": "10x8x2",
        "payment_terms": "NET-15",
        "lead_time_reliability": None,
        "delivery_included": None,
        "annual_commit": None,
    },
    "target_price": 30000,
    "reservation_price": 42000,
    "deadline_days": 30,
}


def test_voice_tool_call_produces_a_valid_spec():
    spec = handle_tool_call(_VOICE_TOOL_ARGS, vertical=ECOMMERCE)
    by_name = {a.name: a for a in spec.attributes}
    assert by_name["material_spec"].value == "kraft mailer"
    assert spec.negotiation.target_price == 30000.0
    assert spec.negotiation.reservation_price == 42000.0
    assert spec.negotiation.deadline_days == 30


def test_voice_text_and_document_intake_all_converge_on_one_spec():
    """THE demo-critical test: voice interview, document upload, and typed text all
    produce the identical structured job spec for equivalent content."""
    canonical_text = (
        "material_spec: kraft mailer; minimum_order_quantity: 3000 units; "
        "dimensions: 10x8x2; payment_terms: NET-15; target price $30000; "
        "hard cap $42000; within 30 days"
    )
    text_spec = estimate(canonical_text, vertical=ECOMMERCE)
    doc_spec = estimate_from_document(canonical_text, "quote.txt", "quote", vertical=ECOMMERCE)
    voice_spec = handle_tool_call(_VOICE_TOOL_ARGS, vertical=ECOMMERCE)

    assert _without_id(text_spec) == _without_id(doc_spec) == _without_id(voice_spec)


# -----------------------------------------------------------------------------
# ElevenLabs Agent config -- data-driven per vertical, keyless-safe
# -----------------------------------------------------------------------------

def test_build_agent_config_uses_vertical_disclosure_and_fields():
    config = build_agent_config(ECOMMERCE)
    agent = config["conversation_config"]["agent"]
    assert agent["first_message"].startswith("Hi, this is an AI assistant")
    assert "packaging material and print spec" in agent["prompt"]["prompt"]

    tool = agent["prompt"]["tools"][0]
    assert tool["name"] == "submit_intake"
    assert "material_spec" in tool["parameters"]["properties"]["attributes"]["properties"]


def test_build_agent_config_unknown_vertical_raises():
    with pytest.raises(KeyError, match="Unknown vertical"):
        build_agent_config("space_tourism_packaging")


def test_create_or_update_agent_is_keyless_safe():
    result = create_or_update_agent(ECOMMERCE)
    assert result["mock"] is True
    assert result["config"]["conversation_config"]["agent"]["first_message"]


# -----------------------------------------------------------------------------
# Backward compatibility -- the existing wedding-dress demo path (run_demo.py)
# -----------------------------------------------------------------------------

def test_wedding_dress_demo_text_still_yields_the_same_price_bounds():
    demo_text = "Ivory Pronovias wedding dress, US 8, ideally under $1800, hard cap $2400, within 30 days."
    spec = estimate(demo_text)  # no vertical kwarg -- must default to wedding-dress
    assert spec.negotiation.target_price == 1800.0
    assert spec.negotiation.reservation_price == 2400.0
    assert spec.negotiation.deadline_days == 30

    by_name = {a.name: a for a in spec.attributes}
    assert by_name["color"].value == "ivory"
    assert by_name["size"].value.upper().replace(" ", "") == "US8"
