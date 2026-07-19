"""Market dataset + spawner (owner: Ella) — CSV → 12 brand Seller Agents vs one buyer."""
import sys
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import run_market  # noqa: E402  (scripts/run_market.py)
from negotiator import market_dataset  # noqa: E402
from negotiator.agents.seller_agent import SellerAgent  # noqa: E402
from negotiator.contracts import Capacity, Inventory, SellerState  # noqa: E402

DATA = str(_ROOT / "data" / "market")


# ── loader ───────────────────────────────────────────────────────────────────
def test_loads_12_brands_four_per_style():
    spec, brands = market_dataset.load_market(DATA)
    assert len(brands) == 12
    counts = Counter(b["state"].style for b in brands)
    assert counts == {"tough_negotiator": 4, "stonewaller_no_prices_by_phone": 4, "hard_sell_upseller": 4}


def test_spec_built_from_structured_fields():
    spec, _ = market_dataset.load_market(DATA)
    assert spec.negotiation.target_price == 1800.0
    assert spec.negotiation.reservation_price == 2400.0
    names = {a.name: a for a in spec.attributes}
    assert names["size"].constraint == "hard"
    assert names["color"].constraint == "soft" and "champagne" in names["color"].substitutions


def test_friendly_style_mapping():
    assert market_dataset.friendly_style("Tough but fair") == "tough_negotiator"
    assert market_dataset.friendly_style("Won't quote by phone") == "stonewaller_no_prices_by_phone"
    assert market_dataset.friendly_style("Upseller") == "hard_sell_upseller"
    assert market_dataset.friendly_style("nonsense") == "tough_negotiator"  # safe default


def test_each_brand_carries_its_own_upsells_and_deals():
    _, brands = market_dataset.load_market(DATA)
    by_vendor = {b["option"].vendor: b for b in brands}
    pron = by_vendor["Pronovias"]
    assert any(u["name"] == "cathedral veil" for u in pron["brand"]["upsell_catalog"])
    assert pron["brand"]["credit_deals"][0]["amount"] == 50.0
    # Distinct catalogs across brands (not a shared default).
    cats = [tuple(sorted(u["name"] for u in b["brand"]["upsell_catalog"])) for b in brands]
    assert len(set(cats)) >= 8


# ── brand injection into the agent ───────────────────────────────────────────
def test_injected_brand_adds_accessories_and_value_score():
    _, brands = market_dataset.load_market(DATA)
    pron = next(b for b in brands if b["option"].vendor == "Pronovias")
    agent = SellerAgent(pron["state"], brand=pron["brand"])
    names = {a.name.lower() for a in agent.state.catalog_addons}
    assert "cathedral veil" in names           # arrived via injected brand dict, no disk file
    assert agent.value_score > 0.0             # SLA/returns drove a hold-price score


# ── per-brand credit deals (honored, margin-safe, gated) ─────────────────────
def _agent_with_deals(deals):
    state = SellerState(vendor="X", cost_floor=1400, list_price=2000, min_margin=440,
                        inventory=Inventory(sku_units=2, stock_age_days=14),
                        capacity=Capacity(lead_time_days=28), style="tough_negotiator")
    return SellerAgent(state, brand={"credit_deals": deals})


def test_pct_deal_computed_from_list_price():
    agent = _agent_with_deals([{"deal_type": "coupon", "pct": 5, "conditions": "photo_review"}])
    face, cond, dtype = agent._select_credit(price_gap=200, current_price=1900)
    assert face == 100.0 and dtype == "coupon"   # 5% of $2000


def test_min_purchase_gates_a_deal():
    deals = [{"deal_type": "coupon", "amount": 60, "conditions": "photo_review", "min_purchase": 2000}]
    agent = _agent_with_deals(deals)
    gated, _, _ = agent._select_credit(price_gap=100, current_price=1500)   # below threshold
    assert gated != 60.0                                                    # gated out → falls back
    allowed, _, _ = agent._select_credit(price_gap=100, current_price=2100)  # clears threshold
    assert allowed == 60.0


# ── full market run ──────────────────────────────────────────────────────────
def test_run_market_yields_12_sessions_valid_endings():
    spec, results = run_market.run_market(DATA)
    assert len(results) == 12
    for _b, s in results:
        assert s.call_ending in {"itemized_quote", "callback_commitment", "declined"}
    trajectories = {tuple((m.sender, m.intent) for m in s.messages) for _b, s in results}
    assert len(trajectories) >= 3               # styles produce distinct trajectories


def test_credit_never_in_price_or_itemized_total():
    _spec, results = run_market.run_market(DATA)
    for _b, s in results:
        if s.itemized_quote:
            non_dep = sum(li.amount for li in s.itemized_quote.line_items if li.code != "deposit")
            assert abs(non_dep - s.itemized_quote.total) < 0.01
            codes = {li.code for li in s.itemized_quote.line_items}
            assert codes.isdisjoint({"credit_offer", "credit_type", "commitment_id"})


def test_brand_configured_deal_amounts_appear_on_the_wire():
    _spec, results = run_market.run_market(DATA)
    seen = {}
    for b, s in results:
        for m in s.messages:
            if m.sender == "seller" and (m.terms_delta or {}).get("credit_offer"):
                seen.setdefault(b["option"].vendor, set()).add(m.terms_delta["credit_offer"])
    assert "98" in seen.get("Stella York", set())        # 5% of $1950
    assert "46" in seen.get("Justin Alexander", set())   # 2% of $2300


def test_results_csv_written(tmp_path):
    _spec, results = run_market.run_market(DATA)
    out = tmp_path / "results.csv"
    run_market.write_csv(results, str(out))
    lines = out.read_text().strip().splitlines()
    assert lines[0].split(",")[:3] == ["vendor", "product", "style"]
    assert len(lines) == 13                              # header + 12 brands
