"""
demo/three_negotiations/scenarios.py

The seller's side of each of the three rehearsal calls. In the real recording this is
Cole's voice; here it's a fixed script so the harness is deterministic and runnable
without a phone call. See README.md for exactly what's real vs. scripted per scenario.

`ScriptedSellerChannel` implements the same `SellerChannel` protocol as
`negotiator.comms.channels.MockChannel` / `VoiceChannel`, so `run_negotiation()` drives
it identically to a real seller agent -- it has no idea the other side is scripted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from negotiator.contracts import NegotiationMessage, seller_msg


class ScriptedSellerChannel:
    """Replays a fixed sequence of seller messages, one per `receive()` call --
    exactly the cadence `run_negotiation()` expects from a real `SellerChannel`."""

    def __init__(self, script: list[NegotiationMessage]):
        self._script = list(script)
        self._idx = 0
        self._last_inbound: Optional[NegotiationMessage] = None

    def send(self, msg: NegotiationMessage) -> None:
        self._last_inbound = msg

    def receive(self) -> NegotiationMessage:
        if self._idx < len(self._script):
            msg = self._script[self._idx]
            self._idx += 1
            return msg
        # Script exhausted before the buyer reached a terminal state -- accept
        # whatever was last on the table so the rehearsal always ends cleanly.
        price = self._last_inbound.price if self._last_inbound else None
        return seller_msg("accept", price=price, rationale="Script exhausted; accepting last offer on the table.")


@dataclass
class Scenario:
    style_id: str
    title: str
    how_cole_plays_it: str
    proves: str
    list_price: float
    seller_script: list[NegotiationMessage]
    preamble: list[NegotiationMessage] = field(default_factory=list)  # disclosure/friction, outside the price loop


#: Illustrative per-vendor list prices for the same made-to-order gown, roughly in
#: line with config/verticals/wedding-dress.json's byChannel bands. Deliberately
#: distinct per vendor -- so when call #1 cites "another shop's quote," it's a real
#: discount, not a coincidental match against its own opening price.
TOUGH_BUT_FAIR_LIST = 2200.0
STONEWALLER_LIST = 2350.0
UPSELLER_BASE_LIST = 1950.0


def _tough_but_fair(list_price: float) -> Scenario:
    return Scenario(
        style_id="tough_but_fair",
        title="Tough but fair",
        how_cole_plays_it="Holds firm, pushes a deposit, but will deal.",
        proves="Price moves during the call (the money shot)",
        list_price=list_price,
        preamble=[
            seller_msg("open", text="Hi, thanks for calling -- before we talk numbers, who am I speaking with? "
                                     "Is this an actual person, or am I talking to a robot?"),
            # buyer's disclosure reply is constructed by runner.py (tagged "ai_disclosure")
            seller_msg("open", text="No problem -- one sec, we've got a walk-in at the counter, can you hold?"),
            # buyer's graceful hold is constructed by runner.py (tagged "friction")
        ],
        seller_script=[
            seller_msg("open", price=list_price, rationale="Open at list price."),
            seller_msg("concede", price=round(list_price * 0.94, 2),
                       rationale="Can do a bit better if you're ready to put a deposit down today."),
            # buyer's real competing-quote turn (from the live blackboard) is inserted
            # here by runner.py -- this is the scenario's whole point.
            seller_msg("concede", price=round(list_price * 0.87, 2),
                       rationale="Alright, if you've genuinely got that quote in hand, I can match closer to it."),
            seller_msg("accept", rationale="Let's do it -- I'll get the paperwork started."),
        ],
    )


def _stonewaller(list_price: float) -> Scenario:
    return Scenario(
        style_id="stonewaller",
        title="Won't quote by phone",
        how_cole_plays_it='"We only give prices at an in-store appointment."',
        proves="Every call ends with a real outcome (a callback commitment)",
        list_price=list_price,
        seller_script=[
            seller_msg("open", rationale="We really don't quote pricing over the phone -- "
                                          "you'd need to come in for a fitting appointment."),
            seller_msg("counter", rationale="I hear you, but honestly it varies so much by dress it's not "
                                             "something I can just throw out a number for."),
            # Buyer politely pushes for a range/callback; seller finally gives ground:
            seller_msg("counter", rationale="Okay -- realistically for a made-to-order in your size, "
                                             "you're looking at roughly $1,500-$2,200 depending on customization.",
                       terms_delta={"price_range": "1500-2200"}),
            seller_msg("hangup", rationale="Best I can do today is book you a Tuesday 2pm fitting where "
                                            "we'll firm up the number -- I'll call you Monday to confirm.",
                       terms_delta={"callback": "Tuesday 2pm fitting; confirmation call Monday"}),
        ],
    )


#: One-time add-on fees the upseller folds into its opening ask. The *real* BuyerAgent
#: negotiates the resulting number down with its actual Boulware price logic; this
#: breakdown is what the panel annotates as "itemized", not a line-by-line negotiation
#: the agent conducted -- see README.md.
UPSELLER_ADDONS = {"rush_fee": 150.0, "veil_rental": 120.0, "preservation_kit": 90.0}


def _upseller(list_price: float) -> Scenario:
    inflated = round(list_price + sum(UPSELLER_ADDONS.values()), 2)
    return Scenario(
        style_id="upseller",
        title="Upseller",
        how_cole_plays_it="Piles on rush fees, veil, alterations to inflate the total.",
        proves="Quotes are itemized and comparable",
        list_price=inflated,
        seller_script=[
            seller_msg("open", price=inflated, rationale="That's the gown plus our rush service, veil rental, "
                                                          "and preservation kit -- all bundled in.",
                       terms_delta={k: f"${v:.0f}" for k, v in UPSELLER_ADDONS.items()}),
            seller_msg("concede", price=round(inflated * 0.93, 2),
                       rationale="I can shave a little off the bundle, but the rush fee's non-negotiable."),
            seller_msg("concede", price=round(list_price * 1.04, 2),
                       rationale="Fine -- if you don't need the rush turnaround, that's off the table. "
                                  "Veil and preservation I can still throw in at cost."),
            seller_msg("accept", rationale="Deal -- itemized invoice coming your way."),
        ],
    )


SCENARIOS_ORDER = ["tough_but_fair", "stonewaller", "upseller"]


def build_scenarios() -> dict[str, Scenario]:
    """Return {style_id: Scenario} for all three rehearsal calls."""
    return {
        "tough_but_fair": _tough_but_fair(TOUGH_BUT_FAIR_LIST),
        "stonewaller": _stonewaller(STONEWALLER_LIST),
        "upseller": _upseller(UPSELLER_BASE_LIST),
    }
