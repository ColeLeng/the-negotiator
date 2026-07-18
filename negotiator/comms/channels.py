"""
Transport channels (owner: Suman) — §10. Negotiation logic is transport-independent:
the loop emits/consumes `NegotiationMessage`s; the channel is how they reach the seller.

  · MockChannel   — in-process seller agent. Fastest; build/test + parallel legs.
  · VoiceChannel  — Vapi / Retell / Bland / Twilio: TTS out, STT in. The ONE live leg
                    that gives the demo its "real moving price on a call" moment.
  · UCPChannel    — structured agent-to-agent over UCP. Thin adapter; drop in the wire
                    format here — everything upstream is unchanged.
"""
from __future__ import annotations

from typing import Optional, Protocol

from ..agents.seller_agent import SellerAgent
from ..contracts import NegotiationMessage


class SellerChannel(Protocol):
    def send(self, msg: NegotiationMessage) -> None: ...
    def receive(self) -> NegotiationMessage: ...


class MockChannel:
    """In-process seller. `send` hands the buyer's message to the seller; `receive`
    returns the seller's reply (its opening move on the very first receive)."""

    def __init__(self, seller: SellerAgent) -> None:
        self.seller = seller
        self._last_inbound: Optional[NegotiationMessage] = None

    def send(self, msg: NegotiationMessage) -> None:
        self._last_inbound = msg

    def receive(self) -> NegotiationMessage:
        if self._last_inbound is None:
            return self.seller.open()
        return self.seller.respond(self._last_inbound)


class VoiceChannel:  # stub (Suman) — §8/§10, the live leg
    def send(self, msg: NegotiationMessage) -> None:
        raise NotImplementedError("Wire Vapi/Retell/Bland/Twilio: render msg via TTS.")

    def receive(self) -> NegotiationMessage:
        raise NotImplementedError("STT the seller's speech → sanitize (§9) → NegotiationMessage.")


class UCPChannel:  # stub (Suman) — §10, confirm UCP wire format first
    def send(self, msg: NegotiationMessage) -> None:
        raise NotImplementedError("Map NegotiationMessage → UCP wire format.")

    def receive(self) -> NegotiationMessage:
        raise NotImplementedError("Map UCP inbound → NegotiationMessage.")
