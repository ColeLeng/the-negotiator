"""
Shared blackboard (owner: Suman) — §11. Holds each session's current best offer so
parallel Buyer Agents coordinate through loose coupling (never sharing internal
reservation values). As one seller's price improves, the buyer negotiating elsewhere
gains **honest, real** leverage.

In-memory for the hackathon; swap for Redis pub/sub only if time (§13 cut line).
"""
from __future__ import annotations

from threading import Lock
from typing import Optional


class Blackboard:
    def __init__(self) -> None:
        self._offers: dict[str, float] = {}
        self._lock = Lock()

    def post(self, session_id: str, price: float) -> None:
        with self._lock:
            self._offers[session_id] = price

    def best_excluding(self, session_id: str) -> Optional[float]:
        """Best (lowest, for a buyer) live price among the OTHER sessions — the real BATNA."""
        with self._lock:
            others = [p for sid, p in self._offers.items() if sid != session_id]
            return min(others) if others else None
