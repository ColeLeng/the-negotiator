"""
Scenario 2 — the buyer's quote-gathering agent process (owner: Cole).

    ProductSpec (JSON requirements)
        │  gather_quotes()  ── buyer inquiry agent ⇄ 12 seller agents (disclosure personas)
        ▼
    EvidencePool  ── itemized, verified quotes + cross-vendor aggregates (shared context)
        │  shortlist()  ── prune stonewallers / teasers / over-budget, keep the top 3–5
        ▼
    RankedOptions  ── the frozen Caller→Orchestrator contract, ready for Scenario 3

The buyer never negotiates here. It *collects and verifies*: cross-checking every
quote against the vendor's own sticker and the market benchmark median so a fake-low
teaser or a hidden fee-stack is caught before it pollutes the negotiation BATNA. Every
inquiry, disclosure, verification and pruning decision is emitted to the optional
tracer so the demo can show the buyer building its pool of evidence live.
"""
from __future__ import annotations

from typing import Optional

from . import buyer_value, market_benchmarks
from .agents.inquiry_seller import Disclosure, InquirySellerAgent
from .contracts import Channel, Option, ProductSpec, RankedOptions
from .evidence import EvidencePool, ItemizedQuote, QuoteEvidence
from .seller_market import MarketSeller, load_market
from .tracing import Tracer

# Wedding vertical key in market_benchmarks (its registry key, not the spec category).
_BENCHMARK_VERTICAL = "wedding"
# A headline this far below the firm all-in is a bait-and-switch teaser.
_TEASER_RATIO = 0.75


def _quote_from_disclosures(
    seller: MarketSeller, headline: Optional[float], final: Disclosure
) -> ItemizedQuote:
    """Fold the buyer's final understanding of a seller into a structured quote."""
    return ItemizedQuote(
        vendor=seller.vendor,
        currency=seller.currency,
        headline_price=headline,
        base_price=final.base_price,
        line_items=list(final.line_items),
        comparable_total=final.comparable_total,
        ballpark=list(final.ballpark) if final.ballpark else None,
        notes=final.text,
    )


def _opening_ask(spec: ProductSpec) -> str:
    want = spec.negotiation.must_have_summary or "the gown"
    return (
        f"Hi — I'm an assistant comparing quotes for {want}, budget up to "
        f"${spec.negotiation.reservation_price:,.0f}. Can you give me an itemized quote?"
    )


def _followup_ask(prev_intent: Optional[str]) -> str:
    """The buyer's next-turn utterance, chosen from how the seller just answered."""
    if prev_intent == "quote":
        return "Thanks — can you itemize every fee (alterations, veil, rush, shipping, deposit) so I can compare like-for-like?"
    if prev_intent == "itemized_quote":
        return "Which of those are optional? Please strip them and give me the gown all-in."
    if prev_intent == "refuse":
        return "I understand you prefer in-store — can you give me even a rough ballpark so I can compare?"
    return "Can you give me your best comparable, itemized number?"


def _emit_disclosure(tracer: Tracer, seller: MarketSeller, d: Disclosure) -> None:
    price_str = f" ${d.headline_price:,.0f}" if d.headline_price is not None else ""
    tracer.emit(
        "disclosure",
        actor="seller",
        option_id=seller.option_id,
        vendor=seller.vendor,
        label=f"{seller.vendor} ({seller.persona}) {d.intent}{price_str}",
        price=d.headline_price,
        detail={"intent": d.intent, "text": d.text, "terms": d.terms, "persona": seller.persona},
    )


class _CallState:
    """Live state of one buyer ⇄ seller call while it's in flight."""

    __slots__ = ("seller", "agent", "headline", "final", "turns", "prev_intent", "done")

    def __init__(self, seller: MarketSeller):
        self.seller = seller
        self.agent = InquirySellerAgent(seller)
        self.headline: Optional[float] = None
        self.final: Optional[Disclosure] = None
        self.turns = 0
        self.prev_intent: Optional[str] = None
        self.done = False


def _advance(st: _CallState, tracer: Optional[Tracer]) -> None:
    """Play one buyer-ask → seller-reply exchange for a single call."""
    agent = st.agent
    # A follow-up buyer question precedes every turn after the opener (only if the
    # seller still has something to say — no dangling questions).
    if st.turns >= 1 and agent.has_next() and tracer is not None:
        ask = _followup_ask(st.prev_intent)
        tracer.emit(
            "buyer_ask", actor="buyer", option_id=st.seller.option_id, vendor=st.seller.vendor,
            label=f"Buyer → {st.seller.vendor}: {ask}", detail={"text": ask},
        )
    d = agent.next_disclosure()
    if d is None:
        st.done = True
        _emit_call_end(tracer, st)
        return
    st.turns += 1
    if st.headline is None:
        st.headline = d.headline_price
    st.final = d
    st.prev_intent = d.intent
    if tracer is not None:
        _emit_disclosure(tracer, st.seller, d)
    if not agent.has_next():
        st.done = True
        _emit_call_end(tracer, st)


def _emit_call_end(tracer: Optional[Tracer], st: "_CallState") -> None:
    if tracer is None:
        return
    tracer.emit(
        "call_end", actor="seller", option_id=st.seller.option_id, vendor=st.seller.vendor,
        label=f"Call ended: {st.seller.vendor} after {st.turns} turn(s)",
        detail={"turns": st.turns, "final_intent": st.prev_intent, "persona": st.seller.persona},
    )


def _verify(pool: EvidencePool, spec: ProductSpec, tracer: Optional[Tracer]) -> None:
    """Second pass: verify each quote against the vendor sticker + the live pool median.

    Runs after every inquiry so red-flag detection uses the median all-in actually
    observed across the market (market_benchmarks recommends the live median)."""
    median = pool.median_comparable()
    reservation = spec.negotiation.reservation_price

    for ev in pool.quotes:
        quote = ev.quote
        comparable = ev.comparable_total
        flags: list[str] = []
        reds: list[str] = []

        # No usable number → cannot be leveraged as a BATNA row.
        if comparable is None:
            ev.status = "no_price"
            ev.verified = False
            if quote and quote.ballpark:
                flags.append("ballpark_only")
                ev.notes = f"Reluctant ballpark ${quote.ballpark[0]:,.0f}–${quote.ballpark[1]:,.0f}; not firm."
            else:
                flags.append("no_price_disclosed")
                ev.notes = "Would not quote by phone; callback only."
            ev.verification_flags = flags
            _trace_verify(tracer, ev)
            continue

        ev.utility = round(buyer_value.utility(comparable, spec, offer_attrs=ev.matched_attributes), 3)

        # Benchmark red flags off the live median (catches fake-low + gouging).
        for kind, price in (("headline", quote.headline_price), ("all_in", comparable)):
            if price is None:
                continue
            for hit in market_benchmarks.evaluate_red_flags(_BENCHMARK_VERTICAL, price, median):
                reds.append(f"{hit.rule_name}:{kind}")

        # Bait-and-switch: a headline far under the real all-in.
        if quote.headline_price is not None and quote.headline_price < _TEASER_RATIO * comparable:
            flags.append("teaser_headline_below_all_in")
            reds.append("bait_and_switch")

        # Hidden fee-stack: add-ons piled on the base quote (>30% of base → flag, per
        # market_benchmarks). The buyer strips them, but records that it had to.
        if quote.headline_price is not None and quote.base_price and quote.base_price > 0:
            pad = (quote.headline_price - quote.base_price) / quote.base_price
            if pad > market_benchmarks.HIDDEN_FEE_STACK:
                flags.append("hidden_fee_stack")

        feasible = buyer_value.is_feasible(comparable, spec, ev.matched_attributes)

        if reds:
            ev.status = "red_flag"
            ev.verified = False
            ev.notes = ev.notes or "Quote exposed by verification; excluded from the shortlist."
        elif not feasible or comparable > reservation:
            ev.status = "infeasible"
            ev.verified = False
            ev.notes = (
                f"All-in ${comparable:,.0f} exceeds reservation ${reservation:,.0f}."
                if comparable > reservation
                else "Fails a hard requirement."
            )
        elif flags:
            ev.status = "flagged"
            ev.verified = True
            ev.notes = "Firm & feasible after stripping padding."
        else:
            ev.status = "verified"
            ev.verified = True
            ev.notes = "Firm, itemized, feasible all-in."

        ev.verification_flags = flags
        ev.red_flags = reds
        _trace_verify(tracer, ev)


def _trace_verify(tracer: Optional[Tracer], ev: QuoteEvidence) -> None:
    if tracer is None:
        return
    tracer.emit(
        "verification",
        actor="buyer",
        option_id=ev.option_id,
        vendor=ev.vendor,
        label=f"Verify {ev.vendor}: {ev.status}"
        + (f" @ ${ev.comparable_total:,.0f}" if ev.comparable_total is not None else ""),
        price=ev.comparable_total,
        detail={
            "status": ev.status,
            "verified": ev.verified,
            "flags": ev.verification_flags,
            "red_flags": ev.red_flags,
            "notes": ev.notes,
        },
    )


# Where the call list comes from in the real world (challenge §02). The demo runs
# on a curated set of real vendors; in production this is a Places/Yelp business search.
CALL_LIST_SOURCE = "Curated real vendors — in production: Google Places / Yelp business search"


def gather_quotes(
    spec: ProductSpec,
    sellers: Optional[list[MarketSeller]] = None,
    tracer: Optional[Tracer] = None,
    interleave: bool = False,
) -> EvidencePool:
    """Run the buyer's inquiry pass across every seller and return the verified pool.

    With `interleave=True` the calls are driven round-robin (one exchange per call per
    round) so the trace reads as **parallel sessions** — several calls in flight at once,
    finishing at different turn depths — rather than one call fully before the next.
    """
    sellers = sellers if sellers is not None else load_market()
    pool = EvidencePool(spec_id=spec.spec_id)
    opening = _opening_ask(spec)

    calls = [_CallState(s) for s in sellers]
    if tracer is not None:
        tracer.emit(
            "call_list",
            actor="buyer",
            label=f"Call list: {len(calls)} vendors · {CALL_LIST_SOURCE}",
            detail={"source": CALL_LIST_SOURCE, "count": len(calls)},
        )
        for st in calls:
            tracer.emit(
                "inquiry_start", actor="buyer", option_id=st.seller.option_id, vendor=st.seller.vendor,
                label=f"Buyer → {st.seller.vendor}: {opening}",
                detail={"persona": st.seller.persona, "text": opening, "source_url": st.seller.source_url},
            )

    if interleave:
        while any(not st.done for st in calls):
            for st in calls:
                if not st.done:
                    _advance(st, tracer)
    else:
        for st in calls:
            while not st.done:
                _advance(st, tracer)

    for st in calls:
        quote = _quote_from_disclosures(st.seller, st.headline, st.final)
        ev = QuoteEvidence(
            option_id=st.seller.option_id,
            vendor=st.seller.vendor,
            persona=st.seller.persona,
            source_url=st.seller.source_url,
            listed_price=st.seller.listed_price,
            matched_attributes=dict(st.seller.matched_attributes),
            quote=quote,
            comparable_total=quote.comparable_total,
            disclosure_quality=st.seller.disclosure_quality,
            inquiry_turns=st.turns,
        )
        pool.add(ev)
        if tracer is not None:
            tracer.emit(
                "evidence",
                actor="buyer",
                option_id=ev.option_id,
                vendor=ev.vendor,
                label=f"Pool += {ev.vendor}"
                + (f" (all-in ${ev.comparable_total:,.0f})" if ev.comparable_total else " (no firm price)"),
                price=ev.comparable_total,
                detail={
                    "persona": ev.persona,
                    "turns": st.turns,
                    "source_url": ev.source_url,
                    "listed_price": ev.listed_price,
                    "headline": quote.headline_price,
                    "base": quote.base_price,
                    "comparable_total": quote.comparable_total,
                    "ballpark": quote.ballpark,
                    "line_items": [li.model_dump() for li in quote.line_items],
                },
            )

    _verify(pool, spec, tracer)
    if tracer is not None:
        tracer.emit(
            "pool_summary",
            actor="buyer",
            label=f"Evidence pool: {len(pool.verified())}/{len(pool.quotes)} verified · "
            f"median all-in ${pool.median_comparable() or 0:,.0f}",
            detail={**pool.summary(), "call_list_source": CALL_LIST_SOURCE},
        )
    return pool


def shortlist(
    pool: EvidencePool,
    spec: ProductSpec,
    keep: int = 5,
    min_keep: int = 3,
    tracer: Optional[Tracer] = None,
) -> RankedOptions:
    """Prune the obviously-bad quotes; return the top verified vendors for Scenario 3.

    Verified quotes are ranked by buyer utility (then disclosure quality). Everything
    else — stonewallers with no firm price, exposed teasers, over-budget stickers — is
    dropped, with the reason traced. `min_keep` backfills feasible-but-flagged rows if
    too few clean quotes survive, so the negotiation always has a BATNA landscape.
    """
    verified = pool.verified()
    verified.sort(key=lambda q: (q.utility, q.disclosure_quality, -(q.comparable_total or 0)), reverse=True)
    kept = verified[:keep]

    if len(kept) < min_keep:
        backfill = sorted(
            (q for q in pool.quotes if not q.verified and q.status == "flagged" and q.comparable_total),
            key=lambda q: q.utility,
            reverse=True,
        )
        kept += backfill[: min_keep - len(kept)]

    kept_ids = {q.option_id for q in kept}
    if tracer is not None:
        for q in pool.quotes:
            if q.option_id in kept_ids:
                continue
            tracer.emit(
                "prune",
                actor="buyer",
                option_id=q.option_id,
                vendor=q.vendor,
                label=f"Drop {q.vendor}: {q.status}",
                detail={"status": q.status, "reason": q.notes, "flags": q.red_flags or q.verification_flags},
            )

    options: list[Option] = []
    for i, q in enumerate(kept, start=1):
        options.append(
            Option(
                option_id=q.option_id,
                vendor=q.vendor,
                source_url=q.source_url,
                listed_price=q.comparable_total or q.listed_price or 0.0,
                currency=spec.negotiation.currency,
                matched_attributes=dict(q.matched_attributes),
                unmet_soft=buyer_value.unmet_soft_attributes(spec, q.matched_attributes),
                match_score=q.utility,
                channel=Channel(type="mock"),
            )
        )

    if tracer is not None:
        tracer.emit(
            "shortlist",
            actor="buyer",
            label="Shortlist for negotiation: "
            + ", ".join(f"{o.vendor} (${o.listed_price:,.0f})" for o in options),
            detail={"kept": [o.option_id for o in options], "contacted": len(pool.quotes)},
        )

    return RankedOptions(spec_id=spec.spec_id, options=options)


def run_scenario2(
    spec: ProductSpec,
    sellers: Optional[list[MarketSeller]] = None,
    keep: int = 5,
    tracer: Optional[Tracer] = None,
) -> dict:
    """Full Scenario 2: gather → verify → shortlist. Returns the pool + RankedOptions."""
    pool = gather_quotes(spec, sellers, tracer=tracer)
    ranked = shortlist(pool, spec, keep=keep, tracer=tracer)
    return {"pool": pool, "shortlist": ranked}
