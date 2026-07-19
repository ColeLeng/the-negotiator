"""
Voice intake (owner: Jagger) -- the other required intake path (Section 5, "Intake by
Interview or Documents"), built on ElevenLabs Agents. Builds a per-vertical agent
config data-driven from config/verticals/*.json (the same source the document/text
path reads), and converts the agent's end-of-call tool submission into the exact same
ProductSpec pipeline as text and document intake -- see `handle_tool_call()`.

Creating/updating the live agent needs ELEVENLABS_API_KEY; without one this module
still builds and returns a valid agent config (useful for tests, a dry run, or pasting
into the ElevenLabs dashboard by hand) -- the same "runs on mocks with no keys"
posture as the rest of the repo. Verify the agent-config shape against ElevenLabs'
current Conversational AI API docs before pointing a real agent at it.
"""
from __future__ import annotations

import os
from typing import Optional

import httpx

from .contracts import ProductSpec
from .estimator import apply_priorities, estimate, load_vertical_config, to_buyer_intent

_ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
TOOL_NAME = "submit_intake"


def build_agent_config(vertical: str, with_tool: bool = True) -> dict:
    """
    The ElevenLabs Conversational AI agent config for the buyer-facing INTAKE agent:
    a buyer-facing greeting as the first message (`intakeGreeting`, falling back to the
    vertical's disclosure), a system prompt built from its specFields prompts, and a
    `submit_intake` tool the agent calls once it has enough to build a job spec.

    This is the estimator's voice surface — the buyer describes what they want once; the
    tool payload funnels through the same `estimate()` pipeline as text/document intake,
    and `to_buyer_intent()` turns the result into the priority + user-intent JSON handed
    off to the negotiation agent for parallel quote-seeking.
    """
    vcfg = load_vertical_config(vertical)
    fields = vcfg.get("specFields", [])
    soft_keys = [
        f["key"] for f in fields
        if f.get("type") != "date" and f.get("constraint", "hard" if f.get("required", True) else "soft") == "soft"
    ]
    # Exclude date-type fields: we only need a rough timeline (handled by the dedicated
    # timeline line + data collection), so the agent must NOT treat an exact wedding date
    # as a required must-have (that caused an exact-date question loop).
    hard_keys = [
        f["key"] for f in fields
        if f.get("type") != "date"
        and f.get("constraint", "hard" if f.get("required", True) else "soft") == "hard"
    ]
    questions = "\n".join(
        f"- {f['key']}: {f['prompt']}" for f in fields if f.get("type") != "date"
    )
    system_prompt = (
        f"You are a warm, efficient personal shopping assistant helping a buyer describe "
        f"a {vcfg.get('displayName', vertical)} purchase before any vendor is contacted. "
        f"Your job is to collect a short, structured brief — quickly and without "
        f"repeating yourself.\n\n"
        f"WHAT TO COLLECT (don't read this list aloud):\n{questions}\n"
        f"- budget: the target price (what they hope to pay) AND their hard maximum\n"
        f"- timeline: roughly how far away they need it (a timeframe is fine)\n"
        f"- priorities: which 2–3 things matter MOST (e.g. the designer look, the "
        f"silhouette, the price)\n\n"
        f"CONVERSATION RULES (important):\n"
        f"1. Ask ONE question per turn, in natural language.\n"
        f"2. NEVER ask about something the buyer already told you, even approximately. "
        f"Track what you have and only ask for what's still missing. Do not repeat a "
        f"question you've already asked.\n"
        f"3. TIMELINE: a rough timeframe like 'about four months' or 'this fall' is "
        f"ENOUGH — accept it, silently convert it to a rough number of days, and move "
        f"on. You may ask for an exact date AT MOST ONCE; if the buyer only gives a "
        f"timeframe or doesn't have an exact date, that is fine — NEVER ask for the "
        f"wedding date again.\n"
        f"4. Must-haves come first: {', '.join(hard_keys) or 'the essentials'} and the "
        f"budget. Everything else (fabric, sleeve, neckline, customization, etc.) is "
        f"OPTIONAL: ask each optional detail AT MOST ONCE. If the buyer doesn't answer "
        f"it, is vague, deflects, or says things like 'no preference' / 'good enough' / "
        f"\"that's all\", treat it as 'none' and MOVE ON — do NOT ask it again. Never let "
        f"one field stall the conversation.\n"
        f"5. If the buyer corrects something (e.g. changes the color), acknowledge the "
        f"change once and update it — don't re-ask the earlier question.\n"
        f"6. If the buyer is briefly silent, wait patiently; prompt gently at most once, "
        f"then keep going. Never nag.\n"
        f"7. Don't get stuck collecting details. As soon as you have the must-haves, "
        f"budget, and priorities, proceed to the read-back even if some fields are blank "
        f"or approximate.\n"
        f"8. When ready, read the brief back ONCE, concisely, and ask the buyer to "
        f"confirm or correct.\n"
        f"9. After they confirm, say one short closing line (e.g. \"Great — I'll start "
        f"shopping for this.\"). Do NOT say the words 'JSON', field names, code, or "
        f"numbers-as-data aloud. Never invent a value the buyer didn't state.\n"
    )
    if with_tool:
        system_prompt += (
            f"\nWhen (and only when) the buyer has confirmed, call the {TOOL_NAME} tool "
            f"with what you collected: put the item details under `attributes` (use these "
            f"exact keys: {', '.join(f['key'] for f in fields)}), set `target_price` and "
            f"`reservation_price` (the hard maximum) and `deadline_days`, and list the "
            f"most-important soft attributes in `priorities` (most important first, using "
            f"the keys: {', '.join(soft_keys) or 'none'}). Use null for anything not stated."
        )
    tool = {
        "name": TOOL_NAME,
        "description": "Submit the structured, buyer-confirmed job spec gathered so far.",
        "parameters": {
            "type": "object",
            "properties": {
                "attributes": {
                    "type": "object",
                    "properties": {f["key"]: {"type": ["string", "null"]} for f in fields},
                },
                "target_price": {"type": ["number", "null"]},
                "reservation_price": {"type": ["number", "null"]},
                "deadline_days": {"type": ["integer", "null"]},
                "priorities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Soft attributes the buyer cares about most, most important first.",
                },
            },
            "required": ["attributes"],
        },
    }
    agent_cfg = {
        "first_message": vcfg.get("intakeGreeting") or vcfg.get("disclosure", ""),
        "prompt": {"prompt": system_prompt, "tools": [tool] if with_tool else []},
    }
    return {
        "name": f"Intake — {vcfg.get('displayName', vertical)}",
        "conversation_config": {
            # Patient turn-taking so the agent doesn't nag on brief silences.
            "turn": {"turn_timeout": 15, "mode": "turn"},
            "agent": agent_cfg,
        },
    }


def _intake_body_schema(vertical: str) -> dict:
    """The object JSON schema for the submit_intake payload — reused as the inline tool
    `parameters` (dashboard/reference) and as the webhook tool's `request_body_schema`."""
    fields = load_vertical_config(vertical).get("specFields", [])
    return {
        "type": "object",
        "properties": {
            "attributes": {
                "type": "object",
                "properties": {f["key"]: {"type": ["string", "null"]} for f in fields},
            },
            "target_price": {"type": ["number", "null"]},
            "reservation_price": {"type": ["number", "null"]},
            "deadline_days": {"type": ["integer", "null"]},
            "priorities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Soft attributes the buyer cares about most, most important first.",
            },
        },
        "required": ["attributes"],
    }


def _eleven_request_body_schema(vertical: str) -> dict:
    """The submit_intake body in ElevenLabs' own property format (single `type` per
    property, every property carries a `description`) — required by POST /convai/tools,
    which does not accept raw JSON-Schema union/nullable types."""
    fields = load_vertical_config(vertical).get("specFields", [])
    attr_props = {
        f["key"]: {"type": "string", "description": f.get("prompt", f["key"])}
        for f in fields
    }
    return {
        "type": "object",
        "description": "The structured, buyer-confirmed job spec.",
        "required": ["attributes"],
        "properties": {
            "attributes": {
                "type": "object",
                "description": "One key per spec field; omit anything the buyer didn't state.",
                "properties": attr_props,
            },
            "target_price": {"type": "number", "description": "What the buyer hopes to pay (USD)."},
            "reservation_price": {"type": "number", "description": "Hard walk-away maximum (USD)."},
            "deadline_days": {"type": "integer", "description": "Days until the buyer needs it."},
            "priorities": {
                "type": "array",
                "description": "Soft attributes the buyer cares about most, most important first.",
                "items": {"type": "string", "description": "A spec field key."},
            },
        },
    }


def build_submit_intake_tool(vertical: str, webhook_url: str) -> dict:
    """The modern (non-deprecated) ElevenLabs webhook-tool config for `submit_intake`,
    created via POST /v1/convai/tools and then referenced by the agent's `tool_ids`.
    Point `webhook_url` at this app's POST /estimate/voice/intent (a public URL — e.g. a
    tunnel/deploy — since ElevenLabs calls it from their side)."""
    return {
        "type": "webhook",
        "name": TOOL_NAME,
        "description": "Submit the structured, buyer-confirmed job spec gathered so far.",
        "response_timeout_secs": 20,
        "api_schema": {
            "url": webhook_url,
            "method": "POST",
            "request_body_schema": _eleven_request_body_schema(vertical),
        },
    }


def create_or_update_agent(vertical: str, agent_id: Optional[str] = None) -> dict:
    """
    Provision the buyer-facing intake agent on ElevenLabs (modern tool_ids flow): create
    the `submit_intake` webhook tool, then create/patch the agent referencing it plus the
    built-in `end_call` tool. Without ELEVENLABS_API_KEY, returns the built config with a
    `mock` marker (no network), so the team can flip on the real key without code changes.

    Set INTAKE_WEBHOOK_URL to this app's public POST /estimate/voice/intent before the
    agent can actually deliver the buyer-intent JSON (ElevenLabs calls it server-side).
    """
    config = build_agent_config(vertical)
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return {"mock": True, "agent_id": agent_id or "mock-agent-id", "config": config}

    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    webhook_url = os.getenv("INTAKE_WEBHOOK_URL", "https://REPLACE_WITH_PUBLIC_URL/estimate/voice/intent")

    tool_resp = httpx.post(
        f"{_ELEVENLABS_BASE_URL}/convai/tools",
        json={"tool_config": build_submit_intake_tool(vertical, webhook_url)},
        headers=headers, timeout=30,
    )
    tool_resp.raise_for_status()
    tool_id = tool_resp.json().get("id") or tool_resp.json().get("tool_id")

    agent = config["conversation_config"]["agent"]
    payload = {
        "name": config["name"],
        "conversation_config": {
            "agent": {
                "first_message": agent["first_message"],
                "prompt": {
                    "prompt": agent["prompt"]["prompt"],
                    "tool_ids": [tool_id],
                },
            },
        },
    }
    if agent_id:
        resp = httpx.patch(f"{_ELEVENLABS_BASE_URL}/convai/agents/{agent_id}", json=payload, headers=headers, timeout=30)
    else:
        resp = httpx.post(f"{_ELEVENLABS_BASE_URL}/convai/agents/create", json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return {"tool_id": tool_id, **resp.json()}


def handle_tool_call(tool_args: dict, vertical: Optional[str] = None) -> ProductSpec:
    """
    Called by the `/estimate/voice/webhook` endpoint when the ElevenLabs agent invokes
    `submit_intake` at the end of the call. Flattens the collected slots into the same
    plain-text shape the text/document path parses, then calls `estimate()` -- the
    identical function the text and document paths call -- so voice intake can never
    diverge from them. Any stated `priorities` (which have no place in the flattened
    text) are then applied on top, so the buyer's ranking survives the voice path.
    """
    spec = estimate(_flatten_tool_args(tool_args), vertical=vertical)
    return apply_priorities(spec, tool_args.get("priorities"), vertical=vertical)


def handle_tool_call_to_intent(tool_args: dict, vertical: Optional[str] = None) -> dict:
    """Voice tool-call → the buyer-intent JSON handoff. Includes a
    `caller_dynamic_variables` block (Stage 1 — hand to the caller for parallel
    quote-seeking, no price anchoring) and a `negotiation_dynamic_variables` block
    (Stage 2 — for negotiation once a BATNA exists)."""
    return to_buyer_intent(handle_tool_call(tool_args, vertical=vertical))


def fetch_conversation(conversation_id: str) -> dict:
    """GET a completed ElevenLabs conversation (transcript + analysis). Needs
    ELEVENLABS_API_KEY. This is the post-call path: no live webhook/tunnel required —
    just process the call ElevenLabs already recorded."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("fetch_conversation needs ELEVENLABS_API_KEY.")
    resp = httpx.get(
        f"{_ELEVENLABS_BASE_URL}/convai/conversations/{conversation_id}",
        headers={"xi-api-key": api_key}, timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def transcript_to_text(conversation: dict) -> str:
    """Flatten an ElevenLabs conversation transcript to plain text (role: message per
    line), ready for the same `estimate()` pipeline the text/document paths use."""
    lines = []
    for turn in conversation.get("transcript", []):
        msg = turn.get("message") or turn.get("text")
        if msg:
            lines.append(f"{turn.get('role', 'user')}: {msg}")
    return "\n".join(lines)


def intent_from_conversation(conversation_id: str, vertical: Optional[str] = None) -> dict:
    """Post-call path: fetch a recorded ElevenLabs intake call and return the buyer-intent
    JSON handoff. Extraction priority (most to least reliable):
      1. ElevenLabs' own `data_collection_results` (configured via build_data_collection;
         LLM-extracted server-side — no tunnel, no local key, handles spoken numbers).
      2. A structured submission JSON embedded in the transcript (schema-tolerant).
      3. Running the transcript text through `estimate()` (sharper with ANTHROPIC_API_KEY).
    """
    conversation = fetch_conversation(conversation_id)

    dc = _data_collection_values(conversation)
    if dc:
        tool_args = _normalize_submission(dc, vertical=vertical)
        return to_buyer_intent(handle_tool_call(tool_args, vertical=vertical))

    text = transcript_to_text(conversation)
    submission = _extract_submission_json(text)
    if submission is not None:
        tool_args = _normalize_submission(submission, vertical=vertical)
        return to_buyer_intent(handle_tool_call(tool_args, vertical=vertical))

    return to_buyer_intent(estimate(text, vertical=vertical))


def _data_collection_values(conversation: dict) -> dict:
    """Flatten ElevenLabs `analysis.data_collection_results` into {field: value}, keeping
    only fields the extractor actually filled. Empty/missing → {} so we fall through."""
    results = ((conversation.get("analysis") or {}).get("data_collection_results")) or {}
    flat: dict = {}
    for key, entry in results.items():
        value = entry.get("value") if isinstance(entry, dict) else entry
        if value not in (None, "", []):
            flat[key] = value
    return flat


def build_data_collection(vertical: str) -> dict:
    """The `platform_settings.data_collection` map: tells ElevenLabs which structured
    fields to extract from each intake call server-side. Results land in
    `analysis.data_collection_results` and are read by `intent_from_conversation` — no
    webhook/tunnel and no local LLM key needed, and spoken numbers ('fifteen hundred',
    'four months') are handled by ElevenLabs' analysis LLM."""
    fields = load_vertical_config(vertical).get("specFields", [])
    soft_keys = [
        f["key"] for f in fields
        if f.get("type") != "date" and f.get("constraint", "hard" if f.get("required", True) else "soft") == "soft"
    ]
    dc = {
        f["key"]: {"type": "string", "description": f.get("prompt", f["key"])}
        for f in fields if f.get("type") != "date"
    }
    dc["target_price"] = {"type": "number", "description": "The buyer's target price in USD (what they hope to pay). Digits only, e.g. 1500."}
    dc["reservation_price"] = {"type": "number", "description": "The buyer's hard maximum / walk-away price in USD. Digits only, e.g. 2200."}
    dc["deadline_days"] = {"type": "integer", "description": "Number of days until the buyer needs the item. Convert weeks/months to days (1 month = 30 days), e.g. 'four months' -> 120."}
    dc["priorities"] = {
        "type": "string",
        "description": (
            "The soft attributes the buyer cares about MOST, most important first, as a "
            f"comma-separated list using ONLY these keys: {', '.join(soft_keys)}. "
            "E.g. 'designer, silhouette, color'."
        ),
    }
    return dc


def configure_data_collection(agent_id: str, vertical: str) -> dict:
    """PATCH an existing agent so ElevenLabs extracts our structured fields from every
    call. Needs ELEVENLABS_API_KEY."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("configure_data_collection needs ELEVENLABS_API_KEY.")
    resp = httpx.patch(
        f"{_ELEVENLABS_BASE_URL}/convai/agents/{agent_id}",
        json={"platform_settings": {"data_collection": build_data_collection(vertical)}},
        headers={"xi-api-key": api_key, "Content-Type": "application/json"}, timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# Aliases the agent LLM commonly invents for our canonical keys.
_SUBMISSION_ALIASES = {
    "max_price": "reservation_price",
    "maximum_price": "reservation_price",
    "hard_max": "reservation_price",
    "hard_maximum": "reservation_price",
    "walkaway_price": "reservation_price",
    "days_to_delivery": "deadline_days",
    "delivery_days": "deadline_days",
    "lead_time_days": "deadline_days",
    "dress_size_us": "size",
    "size_us": "size",
    "us_size": "size",
}


def _extract_submission_json(text: str) -> Optional[dict]:
    """Find the last JSON object in the transcript (the agent's end-of-call submission).
    Returns None if there isn't a parseable one."""
    import json

    depth, start, candidates = 0, None, []
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                candidates.append(text[start : i + 1])
    for blob in reversed(candidates):
        try:
            obj = json.loads(blob)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


def _normalize_submission(obj: dict, vertical: Optional[str] = None) -> dict:
    """Map a loose/aliased agent submission onto our submit_intake tool_args shape:
    {attributes:{<spec keys>}, target_price, reservation_price, deadline_days, priorities:[keys]}.
    Tolerates flat layouts, aliased keys, {attribute,value} priority objects, and numeric
    size values."""
    vertical = vertical or os.getenv("VERTICAL", "wedding-dress")
    spec_keys = [f["key"] for f in load_vertical_config(vertical).get("specFields", [])]

    canon: dict = {}
    for key, val in obj.items():
        canon[_SUBMISSION_ALIASES.get(key, key)] = val

    nested = canon.get("attributes") if isinstance(canon.get("attributes"), dict) else {}
    attributes: dict = {}
    for k in spec_keys:
        v = nested.get(k, canon.get(k))
        if v is None or v == "":
            continue
        if k == "size" and not isinstance(v, str):
            v = f"US {v}"
        elif k == "size" and str(v).strip().isdigit():
            v = f"US {str(v).strip()}"
        attributes[k] = str(v)

    priorities = canon.get("priorities")
    if isinstance(priorities, str):
        priorities = [p.strip() for p in priorities.split(",") if p.strip()]
    elif isinstance(priorities, list):
        priorities = [
            (p.get("attribute") if isinstance(p, dict) else p)
            for p in priorities
        ]
        priorities = [p for p in priorities if p]

    def _num(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    return {
        "attributes": attributes,
        "target_price": _num(canon.get("target_price")),
        "reservation_price": _num(canon.get("reservation_price")),
        "deadline_days": (int(canon["deadline_days"]) if str(canon.get("deadline_days") or "").strip().isdigit() else None),
        "priorities": priorities,
    }


def _flatten_tool_args(tool_args: dict) -> str:
    parts = [f"{k}: {v}" for k, v in (tool_args.get("attributes") or {}).items() if v]
    if tool_args.get("target_price"):
        parts.append(f"target price ${tool_args['target_price']}")
    if tool_args.get("reservation_price"):
        parts.append(f"hard cap ${tool_args['reservation_price']}")
    if tool_args.get("deadline_days"):
        parts.append(f"within {tool_args['deadline_days']} days")
    return "; ".join(parts)


def _cli(argv: Optional[list] = None) -> int:
    """Small operator CLI:

        python -m negotiator.voice_intake config    <vertical>           # print agent config JSON
        python -m negotiator.voice_intake provision  <vertical> [id]     # create/update the live agent
        python -m negotiator.voice_intake intent     <vertical> "text"   # buyer-intent JSON from text
        python -m negotiator.voice_intake from-call  <vertical> <conv_id># buyer-intent JSON from a recorded call
        python -m negotiator.voice_intake data-collection <vertical> <agent_id>  # turn on ElevenLabs field extraction

    `provision`, `from-call`, and `data-collection` need ELEVENLABS_API_KEY in the
    environment (never hard-code it). `from-call` is the post-call path — no live
    webhook/tunnel required.
    """
    import json
    import sys

    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(_cli.__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "config" and rest:
        print(json.dumps(build_agent_config(rest[0]), indent=2, ensure_ascii=False))
        return 0
    if cmd == "provision" and rest:
        vertical, agent_id = rest[0], (rest[1] if len(rest) > 1 else None)
        print(json.dumps(create_or_update_agent(vertical, agent_id=agent_id), indent=2, ensure_ascii=False))
        return 0
    if cmd == "intent" and len(rest) >= 2:
        intent = to_buyer_intent(estimate(rest[1], vertical=rest[0]))
        print(json.dumps(intent, indent=2, ensure_ascii=False))
        return 0
    if cmd == "from-call" and len(rest) >= 2:
        print(json.dumps(intent_from_conversation(rest[1], vertical=rest[0]), indent=2, ensure_ascii=False))
        return 0
    if cmd == "data-collection" and len(rest) >= 2:
        # data-collection <vertical> <agent_id> — turn on ElevenLabs field extraction
        print(json.dumps(configure_data_collection(rest[1], rest[0]).get("agent_id"), indent=2))
        return 0
    print(_cli.__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
