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
from .estimator import estimate, load_vertical_config

_ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
TOOL_NAME = "submit_intake"


def build_agent_config(vertical: str) -> dict:
    """
    The ElevenLabs Conversational AI agent config for this vertical: the vertical's
    disclosure as the first message (AI-disclosure requirement), a system prompt built
    from its specFields prompts, and a `submit_intake` tool the agent calls once it has
    enough to build a job spec.
    """
    vcfg = load_vertical_config(vertical)
    fields = vcfg.get("specFields", [])
    questions = "\n".join(f"- {f['prompt']}" for f in fields)
    system_prompt = (
        f"You are an intake specialist gathering a {vcfg.get('displayName', vertical)} "
        f"job spec on behalf of a buyer, before any vendor calls are made. Ask the "
        f"following, one at a time, in natural conversation -- skip any the buyer has "
        f"already answered:\n{questions}\n\n"
        f"Also get the buyer's target price (what they hope to pay), their hard "
        f"walk-away maximum, and how many days they have. When you have enough to "
        f"build a job spec, call {TOOL_NAME} with what you collected -- use null for "
        f"anything the buyer didn't give you. Never invent a number or a fact the "
        f"buyer didn't state."
    )
    tool = {
        "name": TOOL_NAME,
        "description": "Submit the structured job spec gathered so far.",
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
            },
            "required": ["attributes"],
        },
    }
    return {
        "name": f"Intake -- {vcfg.get('displayName', vertical)}",
        "conversation_config": {
            "agent": {
                "first_message": vcfg.get("disclosure", ""),
                "prompt": {"prompt": system_prompt, "tools": [tool]},
            },
        },
    }


def create_or_update_agent(vertical: str, agent_id: Optional[str] = None) -> dict:
    """
    Push the agent config to ElevenLabs. Without ELEVENLABS_API_KEY, returns the built
    config with a `mock` marker instead of calling the network, so the team can flip on
    the real key later without touching this function.
    """
    config = build_agent_config(vertical)
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return {"mock": True, "agent_id": agent_id or "mock-agent-id", "config": config}

    headers = {"xi-api-key": api_key}
    if agent_id:
        resp = httpx.patch(f"{_ELEVENLABS_BASE_URL}/convai/agents/{agent_id}", json=config, headers=headers, timeout=30)
    else:
        resp = httpx.post(f"{_ELEVENLABS_BASE_URL}/convai/agents/create", json=config, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def handle_tool_call(tool_args: dict, vertical: Optional[str] = None) -> ProductSpec:
    """
    Called by the `/estimate/voice/webhook` endpoint when the ElevenLabs agent invokes
    `submit_intake` at the end of the call. Flattens the collected slots into the same
    plain-text shape the text/document path parses, then calls `estimate()` -- the
    identical function the text and document paths call -- so voice intake can never
    diverge from them.
    """
    return estimate(_flatten_tool_args(tool_args), vertical=vertical)


def _flatten_tool_args(tool_args: dict) -> str:
    parts = [f"{k}: {v}" for k, v in (tool_args.get("attributes") or {}).items() if v]
    if tool_args.get("target_price"):
        parts.append(f"target price ${tool_args['target_price']}")
    if tool_args.get("reservation_price"):
        parts.append(f"hard cap ${tool_args['reservation_price']}")
    if tool_args.get("deadline_days"):
        parts.append(f"within {tool_args['deadline_days']} days")
    return "; ".join(parts)
