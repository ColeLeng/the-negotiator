"""Scenario 2 dataset + disclosure personas — the 12 seller agents load distinctly."""
from negotiator.agents.inquiry_seller import InquirySellerAgent
from negotiator.seller_market import load_market, spec_from_csv


def test_loads_twelve_sellers_with_provenance():
    sellers = load_market()
    assert len(sellers) == 12
    # Every seller is a real, clickable vendor carrying the buyer's hard attribute.
    for s in sellers:
        assert s.source_url and s.source_url.startswith("http")
        assert s.matched_attributes.get("size") == "US 8"


def test_five_distinct_disclosure_personas_present():
    personas = {s.persona for s in load_market()}
    assert personas == {"transparent", "guarded", "stonewaller", "upseller", "lowball_teaser"}


def test_persona_split_matches_dataset_styles():
    counts: dict[str, int] = {}
    for s in load_market():
        counts[s.persona] = counts.get(s.persona, 0) + 1
    # 4 tough → 2 transparent + 2 guarded; 4 stonewall; 4 upsell → 2 upseller + 2 teaser.
    assert counts["stonewaller"] == 4
    assert counts["transparent"] == 2 and counts["guarded"] == 2
    assert counts["upseller"] == 2 and counts["lowball_teaser"] == 2


def test_spec_from_csv_has_hard_size_constraint():
    spec = spec_from_csv()
    size = next(a for a in spec.attributes if a.name == "size")
    assert size.constraint == "hard" and size.value == "US 8"
    assert spec.negotiation.reservation_price > spec.negotiation.target_price


def _final(seller):
    agent = InquirySellerAgent(seller)
    turns, last = 0, None
    while (d := agent.next_disclosure()) is not None:
        turns += 1
        last = d
    return last, turns


def test_transparent_itemizes_in_one_turn():
    s = next(x for x in load_market() if x.persona == "transparent")
    final, turns = _final(s)
    assert turns == 1
    assert final.intent == "itemized_quote" and final.comparable_total is not None


def test_guarded_only_itemizes_after_being_pressed():
    s = next(x for x in load_market() if x.persona == "guarded")
    agent = InquirySellerAgent(s)
    first = agent.next_disclosure()
    assert first.intent == "quote" and first.comparable_total is None   # base only up front
    second = agent.next_disclosure()
    assert second.intent == "itemized_quote" and second.comparable_total is not None


def test_stonewaller_refuses_first():
    s = next(x for x in load_market() if x.persona == "stonewaller")
    first = InquirySellerAgent(s).next_disclosure()
    assert first.intent == "refuse" and first.headline_price is None


def test_upseller_strips_bundle_to_a_lower_all_in():
    s = next(x for x in load_market() if x.persona == "upseller")
    agent = InquirySellerAgent(s)
    opener = agent.next_disclosure()
    final, _ = _final(s)  # fresh agent walk
    # The headline bundle is strictly higher than the stripped, comparable all-in.
    assert opener.headline_price > s.comparable_total()
    assert final.intent == "revised_quote" and final.comparable_total == s.comparable_total()


def test_lowball_teaser_headline_is_below_the_real_all_in():
    s = next(x for x in load_market() if x.persona == "lowball_teaser")
    final, _ = _final(s)
    assert s.teaser_base is not None and s.teaser_base < final.comparable_total
