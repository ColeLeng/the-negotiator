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

from negotiator.estimator import (
    apply_priorities,
    confirm_spec,
    estimate,
    estimate_from_document,
    missing_requirements,
    to_buyer_intent,
)
from negotiator.voice_intake import (
    build_agent_config,
    create_or_update_agent,
    handle_tool_call,
    handle_tool_call_to_intent,
)

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


# -----------------------------------------------------------------------------
# Buyer-intent JSON handoff -- the priority + user-intent document (Section 5 output)
# -----------------------------------------------------------------------------

def test_to_buyer_intent_shape_and_private_reservation():
    demo_text = "Ivory wedding dress, US 8, ideally under $1800, hard cap $2400, within 30 days."
    intent = to_buyer_intent(estimate(demo_text))

    assert intent["intent"] == "buy"
    assert intent["spec_id"].startswith("spec_")
    # size is the hard constraint -> a must-have.
    assert any(m["attribute"] == "size" for m in intent["must_haves"])
    # budget carries the private reservation for the engine...
    assert intent["budget"]["reservation_price"] == 2400.0

    # Stage 1 — the caller / quote-seeking handoff must NOT anchor price.
    caller = intent["caller_dynamic_variables"]
    assert "target_price" not in caller
    assert "reservation_price" not in caller
    assert caller["product_summary"]
    assert caller["deadline_days"] == 30

    # Stage 2 — negotiation handoff may open at target, but never exposes reservation.
    nego = intent["negotiation_dynamic_variables"]
    assert nego["target_price"] == 1800
    assert "reservation_price" not in nego


def test_priorities_rank_soft_attributes_by_weight():
    """A stated priority order re-weights soft attributes, and the intent doc's
    priority_order reflects it (most important first)."""
    tool_args = {
        "attributes": {"silhouette": "A-line", "color": "ivory", "designer": "Pronovias", "size": "US 8"},
        "target_price": 1500,
        "reservation_price": 2200,
        "deadline_days": 120,
        "priorities": ["designer", "silhouette", "color"],
    }
    spec = handle_tool_call(tool_args, vertical="wedding-dress")
    by_name = {a.name: a for a in spec.attributes}
    assert by_name["designer"].weight > by_name["silhouette"].weight > by_name["color"].weight

    intent = to_buyer_intent(spec)
    top3 = [p for p in intent["priority_order"] if p in {"designer", "silhouette", "color"}]
    assert top3 == ["designer", "silhouette", "color"]


def test_apply_priorities_is_a_noop_without_priorities():
    spec = estimate("Ivory wedding dress, US 8, under $1800, cap $2400", vertical="wedding-dress")
    assert apply_priorities(spec, None) is spec
    assert apply_priorities(spec, []) is spec


def test_handle_tool_call_to_intent_returns_json_handoff():
    tool_args = {
        "attributes": {"color": "ivory", "size": "US 8"},
        "target_price": 1500,
        "reservation_price": 2200,
        "deadline_days": 120,
    }
    intent = handle_tool_call_to_intent(tool_args, vertical="wedding-dress")
    # negotiation stage may open at target; caller stage must not anchor price.
    assert intent["negotiation_dynamic_variables"]["target_price"] == 1500
    assert "target_price" not in intent["caller_dynamic_variables"]
    assert intent["budget"]["reservation_price"] == 2200


def test_intent_from_conversation_uses_recorded_transcript(monkeypatch):
    """Post-call path: a recorded ElevenLabs transcript → buyer-intent JSON, without a
    live webhook."""
    import negotiator.voice_intake as vi

    fake_conversation = {
        "transcript": [
            {"role": "agent", "message": "Hi! What dress are you looking for?"},
            {"role": "user", "message": "An ivory wedding dress, size US 8."},
            {"role": "user", "message": "Hoping to stay under $1800, hard cap $2400, within 30 days."},
        ]
    }
    monkeypatch.setattr(vi, "fetch_conversation", lambda cid: fake_conversation)

    intent = vi.intent_from_conversation("conv_test", vertical="wedding-dress")
    assert intent["budget"]["target_price"] == 1800.0
    assert intent["budget"]["reservation_price"] == 2400.0
    assert intent["timeline"]["deadline_days"] == 30
    by_name = {m["attribute"]: m["value"] for m in intent["must_haves"]}
    assert by_name.get("size", "").upper().replace(" ", "") == "US8"
    # caller stage still never anchors price.
    assert "target_price" not in intent["caller_dynamic_variables"]


def test_intent_from_conversation_parses_aliased_submission_json(monkeypatch):
    """A real agent submission with aliased/flat keys (dress_size_us, max_price,
    days_to_delivery, priorities as objects, no attributes wrapper) must still map onto
    the correct intent — deterministically, without needing an LLM."""
    import negotiator.voice_intake as vi

    agent_submission = """Great — I'll start shopping for this.
    {
      "silhouette": "A-line", "color": "Ivory", "dress_size_us": 8,
      "days_to_delivery": 120, "acquisition_channel": "sample_sale_or_preowned",
      "fabric": "Lace", "sleeve": "Long sleeve", "neckline": "Sweetheart",
      "designer": "Pronovias", "customization": null,
      "target_price": 1500, "max_price": 2200,
      "priorities": [
        {"attribute": "designer", "value": "Pronovias"},
        {"attribute": "silhouette", "value": "A-line"},
        {"attribute": "color", "value": "Ivory"}
      ]
    }"""
    convo = {"transcript": [
        {"role": "agent", "message": "Reading it back… does that sound right?"},
        {"role": "user", "message": "Yes, that's exactly right — go ahead."},
        {"role": "agent", "message": agent_submission},
    ]}
    monkeypatch.setattr(vi, "fetch_conversation", lambda cid: convo)

    intent = vi.intent_from_conversation("conv_x", vertical="wedding-dress")
    assert intent["budget"]["target_price"] == 1500.0
    assert intent["budget"]["reservation_price"] == 2200.0     # from max_price alias
    assert intent["timeline"]["deadline_days"] == 120          # from days_to_delivery alias
    by_name = {m["attribute"]: m["value"] for m in intent["must_haves"]}
    assert by_name.get("size", "").upper().replace(" ", "") == "US8"   # from dress_size_us: 8
    # priority objects -> ranked keys; designer first.
    assert intent["priority_order"][0] == "designer"
    # caller stage still never anchors price.
    assert "target_price" not in intent["caller_dynamic_variables"]


def test_intent_from_conversation_prefers_data_collection(monkeypatch):
    """When ElevenLabs' own data_collection_results are present, they win over prose —
    handling spoken numbers ('fifteen hundred' -> 1500) extracted server-side."""
    import negotiator.voice_intake as vi

    convo = {
        "transcript": [
            {"role": "user", "message": "ivory A-line, size US 8, Pronovias"},
        ],
        "analysis": {
            "data_collection_results": {
                "silhouette": {"value": "A-line"},
                "color": {"value": "ivory"},
                "size": {"value": "US 8"},
                "designer": {"value": "Pronovias"},
                "target_price": {"value": 1500},
                "reservation_price": {"value": 2200},
                "deadline_days": {"value": 120},
                "priorities": {"value": "designer, silhouette, color"},
            }
        },
    }
    monkeypatch.setattr(vi, "fetch_conversation", lambda cid: convo)

    intent = vi.intent_from_conversation("conv_dc", vertical="wedding-dress")
    assert intent["budget"]["target_price"] == 1500.0
    assert intent["budget"]["reservation_price"] == 2200.0
    assert intent["timeline"]["deadline_days"] == 120
    assert intent["priority_order"][0] == "designer"   # comma-string priorities parsed
    by_name = {m["attribute"]: m["value"] for m in intent["must_haves"]}
    assert by_name.get("size", "").upper().replace(" ", "") == "US8"


def test_build_data_collection_has_prices_and_priorities():
    from negotiator.voice_intake import build_data_collection
    dc = build_data_collection("wedding-dress")
    assert dc["target_price"]["type"] == "number"
    assert dc["reservation_price"]["type"] == "number"
    assert dc["deadline_days"]["type"] == "integer"
    assert dc["priorities"]["type"] == "string"
    assert "silhouette" in dc  # spec fields included


def test_transcript_to_text_flattens_roles():
    from negotiator.voice_intake import transcript_to_text
    convo = {"transcript": [
        {"role": "user", "message": "ivory dress"},
        {"role": "agent", "message": "got it"},
        {"role": "user", "text": None},
    ]}
    text = transcript_to_text(convo)
    assert "user: ivory dress" in text
    assert "agent: got it" in text


def test_wedding_dress_intake_agent_greets_the_buyer():
    """The intake agent's first line greets the buyer (intakeGreeting), not the
    seller-call disclosure."""
    config = build_agent_config("wedding-dress")
    first = config["conversation_config"]["agent"]["first_message"]
    assert "personal shopping assistant" in first
    assert "calling on behalf" not in first  # that's the seller-call disclosure
