"""
Shared negotiation-agent interface (§8.1). Both sides implement it so the loop can
drive either without knowing which it's talking to. Symmetric in structure, asymmetric
in objective: each holds a *private* value model and *private* state.
"""
from __future__ import annotations

from typing import Protocol

from ..contracts import NegotiationMessage


class NegotiationAgent(Protocol):
    def open(self) -> NegotiationMessage:
        """First move."""
        ...

    def respond(self, inbound: NegotiationMessage) -> NegotiationMessage:
        """counter | concede | accept | reject | hangup."""
        ...
