"""Seller value model (owner: Ella) — §5/§11.

dynamic_floor drops with stock age; surplus sign is correct; the concession curve
never dips below the floor; capacity/strategic levers behave.
"""
from negotiator import seller_value
from negotiator.contracts import AddOn, Capacity, Inventory, SellerState


def _state(**kw) -> SellerState:
    base = dict(vendor="V", cost_floor=1200.0, list_price=2200.0, min_margin=300.0)
    base.update(kw)
    return SellerState(**base)


def test_dynamic_floor_drops_with_stock_age():
    fresh = _state(inventory=Inventory(sku_units=2, stock_age_days=10))
    aging = _state(inventory=Inventory(sku_units=2, stock_age_days=300))
    assert seller_value.dynamic_floor(aging) < seller_value.dynamic_floor(fresh)


def test_dynamic_floor_drops_with_stock_level():
    scarce = _state(inventory=Inventory(sku_units=1, stock_age_days=60))
    glut = _state(inventory=Inventory(sku_units=40, stock_age_days=60))
    assert seller_value.dynamic_floor(glut) < seller_value.dynamic_floor(scarce)


def test_dynamic_floor_never_below_cost():
    # Even maximally aged/glutted stock never prices below cost_floor.
    state = _state(cost_floor=1200.0, min_margin=300.0,
                   inventory=Inventory(sku_units=999, stock_age_days=9999))
    assert seller_value.dynamic_floor(state) >= state.cost_floor


def test_surplus_sign():
    state = _state(inventory=Inventory(sku_units=2, stock_age_days=10))
    floor = seller_value.dynamic_floor(state)
    assert seller_value.surplus(floor + 100, state) > 0
    assert seller_value.surplus(floor - 100, state) < 0
    assert abs(seller_value.surplus(floor, state)) < 1e-6


def test_concession_curve_never_below_floor_and_monotone():
    state = _state(inventory=Inventory(sku_units=6, stock_age_days=60))
    floor = seller_value.dynamic_floor(state)
    mins = [seller_value.next_seller_min(state, r, 6) for r in range(7)]
    assert all(m >= floor - 1e-6 for m in mins)          # never sells below floor
    assert all(a >= b - 1e-6 for a, b in zip(mins, mins[1:]))  # concedes downward over rounds
    assert mins[-1] <= floor + 1e-6                      # reaches the floor by the last round


def test_strategic_bonus_only_for_aged_stock():
    fresh = _state(inventory=Inventory(sku_units=20, stock_age_days=30))
    aged = _state(inventory=Inventory(sku_units=20, stock_age_days=300))
    assert seller_value.strategic_bonus(fresh) == 0.0
    assert seller_value.strategic_bonus(aged) > 0.0


def test_capacity_penalty_trades_time_not_money():
    free = _state(capacity=Capacity(lead_time_days=21, at_capacity=False))
    busy = _state(capacity=Capacity(lead_time_days=45, at_capacity=True))
    assert seller_value.capacity_penalty(free) == 0.0
    assert seller_value.capacity_penalty(busy) > 0.0


def test_bundled_ask_includes_addons():
    state = _state(catalog_addons=[AddOn(name="veil", price=120.0), AddOn(name="rush", price=200.0)])
    assert seller_value.bundled_ask(state) == round(state.list_price + 320.0, 2)
