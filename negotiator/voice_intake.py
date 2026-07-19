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


def build_agent_config(vertical: str) -> dict:
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
    questions = "\n".join(f"- {f['prompt']}" for f in fields)
    system_prompt = (
        f"You are a friendly personal shopping assistant helping a buyer describe a "
        f"{vcfg.get('displayName', vertical)} purchase, before any vendor is contacted. "
        f"Gather the details below, one at a time, in natural conversation — skip "
        f"anything the buyer already answered, and don't read this list aloud:\n"
        f"{questions}\n\n"
        f"Also get: the buyer's target price (what they hope to pay), their hard "
        f"walk-away maximum, and how many days they have.\n"
        f"Then ask which two or three things matter MOST to them (for example: price, "
        f"or a specific look/brand) so we can prioritize while negotiating.\n\n"
        f"Before finishing, briefly read back the key details so the buyer can confirm "
        f"or correct them. When confirmed, call {TOOL_NAME} with what you collected — "
        f"use null for anything the buyer didn't give you, and put the most-important "
        f"soft attributes in `priorities`, most important first (use these exact keys: "
        f"{', '.join(soft_keys) or 'none'}). Never invent a number or a fact the buyer "
        f"didn't state."
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
    return {
        "name": f"Intake — {vcfg.get('displayName', vertical)}",
        "conversation_config": {
            "agent": {
                "first_message": vcfg.get("intakeGreeting") or vcfg.get("disclosure", ""),
                "prompt": {"prompt": system_prompt, "tools": [tool]},
            },
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
    """Post-call path: fetch a recorded ElevenLabs intake call, run its transcript
    through `estimate()`, and return the buyer-intent JSON handoff. Extraction is much
    sharper with ANTHROPIC_API_KEY set (LLM extraction) than with the keyless heuristic."""
    text = transcript_to_text(fetch_conversation(conversation_id))
    return to_buyer_intent(estimate(text, vertical=vertical))


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

    `provision` and `from-call` need ELEVENLABS_API_KEY in the environment (never
    hard-code it). `from-call` is the post-call path — no live webhook/tunnel required.
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
    print(_cli.__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
