"""
Seller Agent (owner: Ella) — §8.3. Represents the vendor; asymmetric concerns vs the buyer:
protect margin, move the right inventory, land the customer.

Private state: SellerState (cost floor, list price, inventory, capacity, style, fee_template).
Cole's Caller stamps `style` + `fee_template`; Ella owns the full policy. This file is a
*runnable scaffold* so the agent-to-agent demo shows ≥3 distinct negotiation styles
without blocking on Ella — deepen behind the same NegotiationMessage interface.

Styles (challenge-required):
  · tough_negotiator              — hold near list, push deposit, concede slowly
  · stonewaller_no_prices_by_phone — refuse phone pricing early → callback / late range
  · hard_sell_upseller            — open with bundled fees; concede by stripping add-ons

Honesty: no phantom "another buyer offered more", no fake scarcity.
"""
from __future__ import annotations

from .. import brand_profiles, buyer_intent, seller_value
from ..contracts import NegotiationMessage, SellerState, seller_msg


class SellerAgent:
    def __init__(self, state: SellerState, max_rounds: int = 6, brand: dict | None = None):
        # Brand/policy/SLA profile: use an injected dict (CSV-driven harness) if given,
        # else load this vendor's config from disk. Folded into our own copy of the state:
        # adds accessory upsells + a value_score that holds price + per-brand credit_deals.
        self.brand = brand if brand is not None else brand_profiles.load_brand(state.vendor)
        if self.brand:
            state = brand_profiles.apply_brand(state, self.brand)
            self.value_score = brand_profiles.value_score(self.brand)
        else:
            self.value_score = 0.0
        self.state = state
        self.max_rounds = max_rounds
        self.round = 0
        self.style = state.style or "tough_negotiator"
        self.intent = buyer_intent.BuyerIntent()   # captures what the buyer volunteers

    def evaluate(self, offer_price: float) -> float:
        return seller_value.surplus(offer_price, self.state)

    # ── decision helpers (§6 interface — shared with Suman) ──────────────────

    def _round_min(self) -> float:
        """Lowest price this style will take *this round*. Collapses to floor on the
        final round; above floor earlier (style-specific hold)."""
        floor = seller_value.dynamic_floor(self.state)
        if self.round >= self.max_rounds:
            return floor
        my_min = seller_value.next_seller_min(self.state, self.round, self.max_rounds)
        if self.style == "tough_negotiator":
            # Tough holds a wider gap to floor early (stretch the concession curve).
            my_min = max(my_min, floor + (self.state.list_price - floor) * 0.25 * (1 - self.round / self.max_rounds))
        elif self.style == "hard_sell_upseller":
            # Upseller's round minimum is driven by the add-on-strip path.
            my_min = max(floor, seller_value.upsell_ask(self.state, self.round, self.max_rounds))
        # Brand value justifies conceding less → hold the round-minimum closer to list.
        if self.value_score:
            my_min = seller_value.value_hold(my_min, self.state.list_price, self.value_score)
        return max(floor, my_min)

    def should_accept(self, offer_price: float) -> bool:
        """Accept iff the offer clears the dynamic floor AND this round's style hold."""
        if offer_price is None:
            return False
        return offer_price >= seller_value.dynamic_floor(self.state) and offer_price >= self._round_min()

    def should_walk(self, ctx=None) -> bool:
        """Terminate rather than deal: out of rounds with no floor-clearing offer, or a
        stonewaller the buyer never booked. `ctx` may be the inbound message (or None)."""
        floor = seller_value.dynamic_floor(self.state)
        price = getattr(ctx, "price", None) if ctx is not None else None
        if self.style == "stonewaller_no_prices_by_phone" and self.round >= self.max_rounds:
            return not self.should_accept(price)
        if self.round >= self.max_rounds:
            return price is None or price < floor
        return False

    def open(self) -> NegotiationMessage:
        if self.style == "hard_sell_upseller":
            bundled = seller_value.bundled_ask(self.state)
            return seller_msg(
                "open",
                price=bundled,
                terms_delta={"bundle": "gown+alterations+veil+rush"},
                rationale=(
                    f"Open at bundled ask ${bundled:.0f} (list ${self.state.list_price:.0f} "
                    f"+ add-ons) — upseller style."
                ),
            )
        if self.style == "stonewaller_no_prices_by_phone":
            return seller_msg(
                "open",
                price=None,
                terms_delta={"appointment": "required"},
                rationale="We only quote after an in-store appointment — stonewaller open.",
            )
        rationale = "Open at list; deposit required to hold — tough negotiator."
        terms = {"deposit_pct": "20"}
        if self.brand:
            rationale += f" ({brand_profiles.justification(self.brand)})"
            terms["value_justification"] = brand_profiles.justification(self.brand)
        return seller_msg(
            "open",
            price=self.state.list_price,
            terms_delta=terms,
            rationale=rationale,
        )

    def respond(self, inbound: NegotiationMessage) -> NegotiationMessage:
        self.round += 1
        self.intent.observe(inbound)   # B1: capture volunteered buyer intent
        if self.style == "stonewaller_no_prices_by_phone":
            return self._respond_stonewaller(inbound)
        if self.style == "hard_sell_upseller":
            return self._respond_upseller(inbound)
        return self._respond_tough(inbound)

    # ── intent + credit enrichment (B1/B2 — terms_delta only, price untouched) ──

    def _enrich_concede(self, terms: dict, buyer_price, my_min: float) -> dict:
        """Ask for one missing intent signal, and — when the buyer is below what we'll
        take and is price-sensitive — sweeten with a contingent credit instead of cutting
        price further. Mutates only `terms_delta`; the conceded `price` is unchanged."""
        ask = self.intent.next_ask()
        if ask:
            terms["ask"] = ask
            self.intent.asked.add(ask)
        if buyer_price is not None and buyer_price < my_min and self.intent.price_sensitive():
            gap = my_min - buyer_price
            face, conditions, deal_type = self._select_credit(gap, buyer_price)
            if face:
                terms.update(buyer_intent.commitment_terms(
                    self.state.vendor, self.round, face, self.state.list_price, conditions, deal_type
                ))
        return terms

    def _commitment_on_accept(self, terms: dict) -> dict:
        """Document a small review-for-credit commitment in the accept message's terms_delta
        (the transcript is the bilateral record; buyer echo is an optional Suman upgrade)."""
        current = terms.get("_price")  # not set; use list*0.05 gap to force a small standard deal
        face, conditions, deal_type = self._select_credit(self.state.list_price * 0.05, current)
        face = face or 10.0
        terms.update(buyer_intent.commitment_terms(
            self.state.vendor, self.round, face, self.state.list_price, conditions, deal_type
        ))
        return terms

    def _select_credit(self, price_gap: float, current_price):
        """Pick a credit deal — prefer the brand's configured `credit_deals` (respecting
        `min_purchase`, cheapest applicable that beats the price gap), else fall back to the
        default $10/$20/5% tiers. Returns (face, conditions, deal_type). Credit only — never price."""
        deals = (self.brand or {}).get("credit_deals") or []
        cands = []
        for d in deals:
            face = d.get("amount") or (round(self.state.list_price * float(d["pct"]) / 100, 2) if d.get("pct") else 0.0)
            if not face:
                continue
            mp = d.get("min_purchase")
            if mp and current_price is not None and current_price < float(mp):
                continue
            cands.append((float(face), d.get("conditions", "photo_review"), d.get("deal_type", "store_credit")))
        if cands:
            cands.sort(key=lambda c: c[0])   # smallest face first (protect margin)
            for face, cond, dtype in cands:
                av = buyer_intent.ACTION_VALUE.get(cond, 0.0)
                if price_gap <= 0 or seller_value.credit_expected_cost(face, action_value=av) < price_gap:
                    return face, cond, dtype
            return cands[0]                  # smallest applicable, even if not strictly cheaper
        conditions = "photo_review"
        face = seller_value.choose_credit(
            self.state.list_price, price_gap if price_gap > 0 else self.state.list_price * 0.05,
            action_value=buyer_intent.ACTION_VALUE[conditions],
        )
        return face, conditions, "store_credit"

    # ── style policies (scaffold — Ella deepens) ─────────────────────────────

    def _respond_tough(self, inbound: NegotiationMessage) -> NegotiationMessage:
        buyer_price = inbound.price
        floor = seller_value.dynamic_floor(self.state)
        my_min = self._round_min()

        if self.should_accept(buyer_price):
            return seller_msg(
                "accept",
                price=buyer_price,
                terms_delta=self._commitment_on_accept({"deposit_pct": "20"}),
                rationale=f"Buyer ${buyer_price:.0f} clears tough floor ${floor:.0f}; deposit still required.",
            )
        if self.should_walk(inbound):
            return seller_msg(
                "reject",
                price=round(floor, 2),
                rationale=f"Below floor ${floor:.0f}; no deal without a serious deposit.",
            )
        return seller_msg(
            "concede",
            price=round(my_min, 2),
            terms_delta=self._enrich_concede({"deposit_pct": "20"}, buyer_price, my_min),
            rationale=f"Tough concede to ${my_min:.0f} (floor ${floor:.0f}).",
        )

    def _respond_stonewaller(self, inbound: NegotiationMessage) -> NegotiationMessage:
        # At capacity → trade a longer lead time, not a phone discount (§8.4 capacity lever).
        extra_lead = seller_value.capacity_penalty(self.state)
        appt_terms = {"callback": "manager_within_24h", "appointment": "required"}
        if extra_lead:
            appt_terms["lead_time_days"] = f"{self.state.capacity.lead_time_days + extra_lead:.0f}"

        # Early rounds: refuse phone pricing (non-terminal counter) → callback path.
        # Using reject would end the loop; counter+empty price models "someone will call you back".
        if self.round <= 2:
            return seller_msg(
                "counter",
                price=None,
                terms_delta=appt_terms,
                rationale="No prices by phone — book an appointment or we'll call you back.",
            )
        floor = seller_value.dynamic_floor(self.state)
        my_min = self._round_min()
        buyer_price = inbound.price
        if self.should_accept(buyer_price):
            return seller_msg(
                "accept",
                price=buyer_price,
                terms_delta=self._commitment_on_accept({}),
                rationale=f"After callback friction, accept ${buyer_price:.0f}.",
            )
        if self.should_walk(inbound):
            # Structured ending: callback commitment (not a vague range).
            return seller_msg(
                "reject",
                price=None,
                terms_delta={"callback": "manager_within_24h"},
                rationale="Still need an in-store look; documenting callback commitment.",
            )
        return seller_msg(
            "concede",
            price=round(my_min, 2),
            terms_delta=self._enrich_concede({"range_note": "ballpark_only"}, buyer_price, my_min),
            rationale=f"Reluctant ballpark ${my_min:.0f} (floor ${floor:.0f}); prefer appointment.",
        )

    def _respond_upseller(self, inbound: NegotiationMessage) -> NegotiationMessage:
        buyer_price = inbound.price
        floor = seller_value.dynamic_floor(self.state)
        bundled = seller_value.bundled_ask(self.state)
        my_min = self._round_min()

        if self.should_accept(buyer_price):
            bundle = {"bundle": "stripped_to_essentials"} if buyer_price < bundled else {"bundle": "full"}
            return seller_msg(
                "accept",
                price=buyer_price,
                terms_delta=self._commitment_on_accept(bundle),
                rationale=f"Accept ${buyer_price:.0f} after add-on strip (floor ${floor:.0f}).",
            )
        if self.should_walk(inbound):
            return seller_msg(
                "reject",
                price=round(floor, 2),
                rationale=f"Even without add-ons, ${floor:.0f} is the floor.",
            )
        return seller_msg(
            "concede",
            price=round(my_min, 2),
            terms_delta=self._enrich_concede({"bundle": f"round_{self.round}_strip"}, buyer_price, my_min),
            rationale=f"Upseller concede to ${my_min:.0f} by stripping optional fees.",
        )
