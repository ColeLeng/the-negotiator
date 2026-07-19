"""
Estimator (owner: Jagger) -- Section 5. Turn messy human input into a clean ProductSpec
with ZOPA parameters. Does NOT find vendors.

Three intake surfaces converge on one pipeline, so the spec they produce can never
diverge:

    text / voice-transcript  --\\
    document (quote/bill/CSV) ---> estimate() -> _slots_to_spec() -> ProductSpec
    voice tool-call (flattened)-/

`estimate_from_document()` (document_intake.py) and `voice_intake.handle_tool_call()`
both funnel into `estimate()` itself -- not a parallel extractor -- so "both paths
produce the same structured job spec" is true by construction, not by convention.

Extraction prefers an LLM (Claude, via ANTHROPIC_API_KEY) against the vertical's
specFields schema (config/verticals/*.json); with no key, or if the LLM call fails,
falls back to a deterministic heuristic extractor so the demo never breaks. Missing
hard constraints or price bounds are surfaced by `missing_requirements()`, and
`confirm_spec()` is the gate: nothing reaches the Caller until the user has confirmed
(and optionally corrected) the spec.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

from .contracts import Attribute, Negotiation, ProductSpec

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config" / "verticals"
_DEFAULT_VERTICAL = "wedding-dress"

# Bridges to negotiator/market_benchmarks.py: when no price is stated in the intake
# text, the Estimator bootstraps target/reservation from vertical market research
# instead of a bare hardcoded guess (see market_benchmarks.py's "HOW IT CONNECTS").
# wedding-dress's default subtype matches config/verticals/wedding-dress.json's
# narrowedScenario.recommendedDemoTarget; if the buyer states an acquisition_channel
# (resale/sample_sale/off_the_rack/made_to_order/custom) we bootstrap from that
# channel's band instead -- see `_market_benchmark_bounds()`.
_MARKET_BENCHMARK_MAP = {
    "wedding-dress": ("wedding", "dress_made_to_order"),
    "moving": ("moving_local", "two_bedroom_45mi"),
    "ecommerce-packaging": ("b2b_packaging_smb", "annual_contract"),
}

_KEYWORD_FIELDS = {
    "material_spec": [
        "corrugated", "kraft", "mailer", "rigid box", "poly mailer",
        "4-color", "4 color", "matte", "gloss", "custom print", "cardboard",
    ],
}

_FIELD_PATTERNS = {
    "minimum_order_quantity": re.compile(
        r"\bMOQ\b[^\d]{0,10}([\d,]+)|minimum[_\s]order(?:[_\s]quantity)?[^\d]{0,10}([\d,]+)",
        re.IGNORECASE,
    ),
    "dimensions": re.compile(r"\d+\s*[x×]\s*\d+\s*[x×]\s*\d+\s*(?:in|inch(?:es)?|cm)?", re.IGNORECASE),
    "payment_terms": re.compile(r"\bNET[-\s]?\d+\b|\bdeposit\b(?:\s*\+\s*balance)?|\bnet\s+terms\b", re.IGNORECASE),
    "lead_time_reliability": re.compile(r"\d+\s*(?:[-–]|to)?\s*\d*\s*(?:day|week|month)s?", re.IGNORECASE),
    "delivery_included": re.compile(
        r"delivery included|freight included|free shipping|FOB\s*\w*|own logistics|own trucking",
        re.IGNORECASE,
    ),
    "annual_commit": re.compile(
        r"annual commit(?:ment)?|one[-\s]?time order|ongoing (?:order|commitment)",
        re.IGNORECASE,
    ),
    "size": re.compile(r"\bUS\s*\d+\b|\bsize\s*\d+\b", re.IGNORECASE),
}


@lru_cache(maxsize=None)
def load_vertical_config(vertical: str) -> dict:
    """Read config/verticals/<vertical>.json -- the single source of truth for intake
    questions, shared by the voice-agent prompt builder, the document parser, and the
    heuristic/LLM extractors below."""
    path = _CONFIG_DIR / f"{vertical}.json"
    if not path.exists():
        available = sorted(p.stem for p in _CONFIG_DIR.glob("*.json"))
        raise KeyError(f"Unknown vertical '{vertical}'. Supported verticals: {', '.join(available)}.")
    return json.loads(path.read_text())


def estimate(input_text: Union[str, bytes], vertical: Optional[str] = None) -> ProductSpec:
    """
    IN: a free-text requirements paragraph, a voice transcript, or flattened voice
    tool-call args (audio to transcribe should be STT'd by the caller first).
    OUT: exactly one schema-valid ProductSpec.
    """
    text = input_text.decode() if isinstance(input_text, bytes) else str(input_text)
    vertical = vertical or os.getenv("VERTICAL", _DEFAULT_VERTICAL)
    vcfg = load_vertical_config(vertical)

    data = None
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            data = _extract_with_llm(text, vcfg)
        except Exception:
            data = None  # never let a flaky/missing-dependency LLM call break intake
    if data is None:
        data = _extract_heuristic(text, vcfg, vertical)

    return _slots_to_spec(data, vcfg, vertical)


def estimate_from_document(
    content: Union[str, bytes],
    filename: str,
    document_type: str = "other",
    vertical: Optional[str] = None,
) -> ProductSpec:
    """
    Document intake path -- photos, existing quotes, bills, inventory lists.
    Parses the document to text, then calls `estimate()` itself, so document and
    text/voice intake can never produce divergent spec shapes.
    """
    from .document_intake import parse_document

    text = parse_document(content, filename, document_type)
    return estimate(text, vertical=vertical)


def to_buyer_intent(spec: ProductSpec, *, confirmed: Optional[bool] = None) -> dict:
    """
    The buyer-intent handoff document (Section 5 output).

    ProductSpec is the machine contract the Caller consumes (`search(spec)`); this is the
    readable *priority + user-intent JSON* that documents what the buyer wants, how much
    each thing matters, and — critically — carries TWO stage-specific handoff blocks,
    because the pipeline is `Estimator → Caller (quote-seeking) → negotiation`:

      • `caller_dynamic_variables` — for the CALLER / parallel quote-seeking. It states
        what to ask about and which substitutions count as comparable, and deliberately
        DOES NOT include target/reservation: revealing a budget while gathering quotes
        anchors the seller and poisons the BATNA the caller exists to collect. Ask for the
        seller's honest price + availability first.

      • `negotiation_dynamic_variables` — for the LATER negotiation stage, once real
        quotes (a BATNA) exist. It may open at `target_price`, but never exposes
        `reservation_price` (the private walk-away max — engine only, in `budget`).
    """
    hard = [a for a in spec.attributes if a.constraint == "hard"]
    soft = [a for a in spec.attributes if a.constraint == "soft"]

    ranked = sorted(soft, key=lambda a: (a.weight or 0.0), reverse=True)
    preferences = [
        {
            "attribute": a.name,
            "value": a.value,
            "importance": round(a.weight, 3) if a.weight is not None else None,
            "flexible": bool(a.substitutions),
            "substitutions": a.substitutions,
        }
        for a in ranked
    ]

    n = spec.negotiation
    return {
        "intent": "buy",
        "spec_id": spec.spec_id,
        "category": spec.category,
        "confirmed": confirmed if confirmed is not None else (missing_requirements(spec) == []),
        "must_haves": [{"attribute": a.name, "value": a.value} for a in hard if a.value],
        "open_questions": [a.name for a in hard if not a.value],
        "preferences": preferences,
        "priority_order": [p["attribute"] for p in preferences if p["value"]],
        "budget": {
            "target_price": n.target_price,
            "reservation_price": n.reservation_price,   # PRIVATE — engine only, never spoken
            "currency": n.currency,
        },
        "timeline": {"deadline_days": n.deadline_days},
        "summary": n.must_have_summary,
        # Stage 1 — hand this to the caller / quote-seeking agent. No price anchoring.
        "caller_dynamic_variables": {
            "product_summary": _product_summary(spec),
            "must_have_summary": n.must_have_summary or "",
            "acceptable_substitutions": _substitutions_summary(spec),
            "deadline_days": n.deadline_days,
            "instruction": (
                "Ask each seller for their best price and availability on this or a "
                "comparable item. Do NOT state any budget, target, or maximum — we are "
                "gathering honest quotes to compare."
            ),
        },
        # Stage 2 — hand this to the negotiation agent AFTER quotes/BATNA exist.
        "negotiation_dynamic_variables": {
            "product_summary": _product_summary(spec),
            "must_have_summary": n.must_have_summary or "",
            "target_price": int(n.target_price) if n.target_price else None,
            "deadline_days": n.deadline_days,
        },
    }


def _substitutions_summary(spec: ProductSpec) -> str:
    """Readable 'what counts as comparable' string for the quote-seeking caller, e.g.
    'silhouette: A-line/ball-gown/mermaid; color: white/ivory/champagne'. Only soft
    attributes with substitutions — the room the caller has to find comparable options."""
    parts = [
        f"{a.name}: {'/'.join(a.substitutions)}"
        for a in spec.attributes
        if a.constraint == "soft" and a.substitutions
    ]
    return "; ".join(parts)


def _product_summary(spec: ProductSpec) -> str:
    """A short human phrase of what the buyer wants, for the negotiation agent's
    `product_summary` dynamic variable (e.g. 'A-line, ivory, US 8, Pronovias (Wedding
    Dress (DTC))')."""
    desc = ", ".join(a.value for a in spec.attributes if a.value)
    category = spec.category or "item"
    return f"{desc} ({category})" if desc else category


def missing_requirements(spec: ProductSpec) -> list:
    """Hard constraints with no extracted value, plus missing/zero price bounds --
    the two things that are load-bearing for negotiation (per docs Section 5)."""
    missing = [a.name for a in spec.attributes if a.constraint == "hard" and not a.value]
    if not spec.negotiation.target_price or spec.negotiation.target_price <= 0:
        missing.append("target_price")
    if not spec.negotiation.reservation_price or spec.negotiation.reservation_price <= 0:
        missing.append("reservation_price")
    return missing


def confirm_spec(spec: ProductSpec, edits: Optional[dict] = None) -> ProductSpec:
    """
    The confirmation gate: applies any user edits (a correction, or an answer to a
    missing-requirement prompt), then refuses to confirm an incomplete spec. The
    returned spec is what every subsequent vendor call must reuse verbatim -- nothing
    re-estimates after this point.
    """
    if edits:
        spec = _apply_edits(spec, edits)
    missing = missing_requirements(spec)
    if missing:
        raise ValueError(f"Cannot confirm spec {spec.spec_id}: missing {', '.join(missing)}.")
    return spec


def _apply_edits(spec: ProductSpec, edits: dict) -> ProductSpec:
    data = spec.model_dump(by_alias=True)
    price_keys = ("target_price", "reservation_price", "deadline_days", "currency", "must_have_summary")
    for attr in data["attributes"]:
        if attr["name"] in edits:
            attr["value"] = edits[attr["name"]]
    for key in price_keys:
        if key in edits:
            data["negotiation"][key] = edits[key]
    return ProductSpec.model_validate(data)


def _field_constraint(field: dict) -> str:
    """Some vertical configs tag a field with an explicit `constraint` (hard/soft);
    others rely on the `required` convention (default True -> hard). Explicit wins."""
    if "constraint" in field:
        return field["constraint"]
    return "hard" if field.get("required", True) else "soft"


def _slots_to_spec(data: dict, vcfg: dict, vertical: str) -> ProductSpec:
    """The single convergence point every intake surface funnels through."""
    raw_attrs = data.get("attributes") or {}
    weights = _priority_weights(data.get("priorities"), vcfg)
    attrs = []
    for field in vcfg.get("specFields", []):
        if field.get("type") == "date":
            # A date is a lead-time constraint (checked as an inequality against a
            # vendor's lead time), not a literal-match attribute -- ProductSpec.attributes
            # is for equality/substitution matching (contracts.py's Attribute docstring).
            # It belongs on Negotiation.deadline_days, not here.
            continue
        key = field["key"]
        constraint = _field_constraint(field)
        attrs.append(Attribute(
            name=key,
            value=raw_attrs.get(key),
            constraint=constraint,
            weight=None if constraint == "hard" else weights.get(key, 0.15),
            substitutions=field.get("values", []) if field.get("type") == "enum" else [],
        ))

    fallback_target, fallback_reservation = _market_benchmark_bounds(vertical, raw_attrs) or (1800.0, 2400.0)
    target = float(data["target_price"]) if data.get("target_price") else fallback_target
    reservation = float(data["reservation_price"]) if data.get("reservation_price") else fallback_reservation
    deadline = data.get("deadline_days")

    hard_parts = [f"{a.name}={a.value}" for a in attrs if a.constraint == "hard" and a.value]
    summary = ", ".join(hard_parts) if hard_parts else None
    if deadline:
        summary = f"{summary}; within {deadline} days" if summary else f"within {deadline} days"

    return ProductSpec(
        spec_id=f"spec_{uuid.uuid4().hex[:8]}",
        category=vcfg.get("displayName", vertical),
        attributes=attrs,
        negotiation=Negotiation(
            target_price=target,
            reservation_price=reservation,
            currency=vcfg.get("priceBenchmark", {}).get("currency", "USD"),
            deadline_days=deadline,
            must_have_summary=summary,
        ),
    )


def _priority_weights(priorities, vcfg: dict) -> dict:
    """Turn a buyer's stated priorities into normalized soft-attribute weights.

    Accepts either a ranked list of field keys (most important first) or a
    {field_key: importance} mapping. Returns {} when nothing was stated, so intake with
    no priorities keeps the flat default weight and all three intake surfaces stay
    identical. Only soft fields are weighted (hard constraints are must-match, not traded).
    """
    if not priorities:
        return {}
    soft_keys = {
        f["key"] for f in vcfg.get("specFields", [])
        if f.get("type") != "date" and _field_constraint(f) == "soft"
    }

    scores: dict = {}
    if isinstance(priorities, dict):
        for key, imp in priorities.items():
            if key in soft_keys:
                try:
                    scores[key] = float(imp)
                except (TypeError, ValueError):
                    continue
    elif isinstance(priorities, (list, tuple)):
        ranked = [k for k in priorities if k in soft_keys]
        n = len(ranked)
        for i, key in enumerate(ranked):
            scores[key] = float(n - i)   # first = highest rank

    total = sum(v for v in scores.values() if v > 0)
    if total <= 0:
        return {}
    return {key: round(val / total, 3) for key, val in scores.items() if val > 0}


def apply_priorities(spec: ProductSpec, priorities, vertical: Optional[str] = None) -> ProductSpec:
    """Re-weight a spec's soft attributes from a buyer's stated priorities, returning a
    new spec (original untouched). Used by the voice path, whose structured tool-call
    carries priorities the flattened-text convergence step can't. No-op if priorities is
    empty or names no soft fields."""
    vertical = vertical or os.getenv("VERTICAL", _DEFAULT_VERTICAL)
    weights = _priority_weights(priorities, load_vertical_config(vertical))
    if not weights:
        return spec
    data = spec.model_dump(by_alias=True)
    for attr in data["attributes"]:
        if attr.get("constraint") == "soft" and attr["name"] in weights:
            attr["weight"] = weights[attr["name"]]
    return ProductSpec.model_validate(data)


def _extract_heuristic(text: str, vcfg: dict, vertical: str) -> dict:
    """Deterministic, keyless fallback -- regex/keyword slot-filling against the
    vertical's specFields, plus the market_benchmarks price bootstrap when the text
    states no explicit number."""
    raw_attrs = {f["key"]: _find_field_value(f, text) for f in vcfg.get("specFields", [])}
    target, reservation = _price_bounds(text, vertical, raw_attrs)
    return {
        "attributes": raw_attrs,
        "target_price": target,
        "reservation_price": reservation,
        "deadline_days": _sniff_deadline_days(text),
    }


def _extract_with_llm(text: str, vcfg: dict) -> dict:
    import anthropic

    fields = vcfg.get("specFields", [])
    tool = {
        "name": "submit_intake",
        "description": "Submit the structured job spec extracted from the buyer's requirements.",
        "input_schema": {
            "type": "object",
            "properties": {
                "attributes": {
                    "type": "object",
                    "description": "One key per spec field; null for anything not mentioned.",
                    "properties": {f["key"]: {"type": ["string", "null"]} for f in fields},
                },
                "target_price": {"type": ["number", "null"], "description": "What the buyer hopes to pay."},
                "reservation_price": {"type": ["number", "null"], "description": "Hard walk-away max."},
                "deadline_days": {"type": ["integer", "null"]},
                "priorities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "The soft attributes the buyer cares about MOST, in order (most "
                        "important first) — e.g. ['designer', 'silhouette', 'color']. "
                        "Use the exact field keys. Omit if the buyer didn't say."
                    ),
                },
            },
            "required": ["attributes"],
        },
    }
    prompt_fields = "\n".join(f"- {f['key']}: {f.get('prompt', '')}" for f in fields)
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=1024,
        tools=[tool],
        tool_choice={"type": "tool", "name": "submit_intake"},
        messages=[{
            "role": "user",
            "content": (
                f"Vertical: {vcfg.get('displayName')}\n"
                f"Extract these fields from the buyer's requirements below. Use null for "
                f"anything not actually stated -- never guess or invent a value.\n\n"
                f"Fields:\n{prompt_fields}\n\nBuyer requirements:\n{text}"
            ),
        }],
    )
    tool_use = next(b for b in message.content if b.type == "tool_use")
    return tool_use.input


def _find_field_value(field: dict, text: str) -> Optional[str]:
    key = field["key"]
    if field.get("type") == "enum":
        for value in field.get("values", []):
            # Word-bounded so a short value can't match inside a longer word
            # (e.g. "custom" must not match inside "customization").
            if re.search(rf"\b{re.escape(value)}\b", text, re.IGNORECASE):
                return value
        return None

    label = key.replace("_", "[ _-]?")
    exact = re.search(rf"\b{label}\b\s*(?:is|:|=|-)\s*([^\n,;]+)", text, re.IGNORECASE)
    if exact:
        return exact.group(1).strip().rstrip(".")

    if key in _KEYWORD_FIELDS:
        hits = [kw for kw in _KEYWORD_FIELDS[key] if re.search(re.escape(kw), text, re.IGNORECASE)]
        if hits:
            return ", ".join(hits)

    pattern = _FIELD_PATTERNS.get(key)
    if pattern:
        m = pattern.search(text)
        if m:
            groups = [g for g in m.groups() if g]
            return (groups[0] if groups else m.group(0)).strip()
    return None


def _sniff_prices(text: str) -> list:
    """Only counts numbers with an explicit '$' -- a bare number like '5000 units'
    (e.g. an MOQ) must never be mistaken for a price."""
    return [float(p.replace(",", "")) for p in re.findall(r"\$\s*([0-9][0-9,]{2,}(?:\.\d{1,2})?)", text)]


def _sniff_deadline_days(text: str) -> Optional[int]:
    m = re.search(r"\b(\d+)\s*day", text, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _price_bounds(text: str, vertical: str, raw_attrs: Optional[dict] = None) -> tuple:
    prices = _sniff_prices(text)
    benchmark = _market_benchmark_bounds(vertical, raw_attrs)
    if len(prices) >= 2:
        return min(prices), max(prices)
    if len(prices) == 1:
        target = prices[0]
        spread = (benchmark[1] / benchmark[0]) if benchmark else 1.33
        return target, round(target * spread, 2)
    return benchmark or (1800.0, 2400.0)


def _market_benchmark_bounds(vertical: str, raw_attrs: Optional[dict] = None) -> Optional[tuple]:
    mapping = _MARKET_BENCHMARK_MAP.get(vertical)
    if not mapping:
        return None
    mb_vertical, subtype = mapping

    # wedding-dress: if the buyer named a channel (resale/sample_sale/off_the_rack/
    # made_to_order/custom), bootstrap from THAT channel's band instead of the
    # default -- see config/verticals/wedding-dress.json's per-channel price bands.
    if vertical == "wedding-dress" and raw_attrs:
        channel = raw_attrs.get("acquisition_channel")
        if channel:
            subtype = f"dress_{channel.strip().lower().replace('-', '_').replace(' ', '_')}"

    try:
        from . import market_benchmarks
        bounds = market_benchmarks.get_price_bounds(mb_vertical, subtype)
        return bounds.target_price, bounds.reservation_price
    except (ImportError, KeyError):
        return None
