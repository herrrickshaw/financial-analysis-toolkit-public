"""finmodel.real_estate_development: the construction-loan schedule's capitalized interest is checked
against a hand-rolled period-by-period recomputation, and the full pro forma is checked at an exact
breakeven case (yield on cost equal to the exit cap rate must give a zero IRR and a zero profit) plus a
profitable case with a hand-solvable IRR."""
import pytest

from finmodel import real_estate_development as RE


def test_total_development_cost_matches_hand_calc():
    out = RE.total_development_cost(land_cost=1_000_000.0, hard_costs=5_000_000.0, soft_costs=1_500_000.0, contingency_pct=0.10)
    assert out["contingency"] == pytest.approx(750_000.0)
    assert out["total_development_cost"] == pytest.approx(8_250_000.0)


def test_construction_loan_schedule_capitalizes_interest_on_the_beginning_balance():
    draws = [1_000_000.0, 1_000_000.0, 1_000_000.0]
    rate = 0.08
    out = RE.construction_loan_schedule(draws, interest_rate_annual=rate, periods_per_year=12)
    periodic_rate = rate / 12
    bal = 0.0
    expected_interest = []
    for d in draws:
        interest = bal * periodic_rate
        bal = bal + d + interest
        expected_interest.append(interest)
    assert [p["interest_accrued"] for p in out["periods"]] == pytest.approx(expected_interest)
    assert out["ending_loan_balance"] == pytest.approx(bal)
    assert out["total_capitalized_interest"] == pytest.approx(sum(expected_interest))
    assert out["periods"][0]["interest_accrued"] == pytest.approx(0.0)  # nothing drawn yet at the first draw


def test_development_pro_forma_at_exact_breakeven():
    # yield on cost (15/200 = 7.5%) exactly equals the exit cap rate -> zero development profit, zero IRR
    out = RE.development_pro_forma(draws=[100.0, 100.0], interest_rate_annual=0.0, stabilized_noi=15.0,
                                   exit_cap_rate=0.075, periods_per_year=1)
    assert out["total_cost_basis"] == pytest.approx(200.0)
    assert out["exit_value"] == pytest.approx(200.0)
    assert out["development_profit"] == pytest.approx(0.0, abs=1e-6)
    assert out["yield_on_cost"] == pytest.approx(0.075)
    assert out["development_spread_bps"] == pytest.approx(0.0, abs=1e-6)
    assert out["unlevered_irr_periodic"] == pytest.approx(0.0, abs=1e-6)


def test_development_pro_forma_profitable_case_matches_hand_solvable_irr():
    # draws=[100,100], exit value 400 (NOI 20 / 5% cap) -> cash flows [-100, 300]; -100 + 300/(1+r)=0 -> r=2.0
    out = RE.development_pro_forma(draws=[100.0, 100.0], interest_rate_annual=0.0, stabilized_noi=20.0,
                                   exit_cap_rate=0.05, periods_per_year=1)
    assert out["exit_value"] == pytest.approx(400.0)
    assert out["development_profit"] == pytest.approx(200.0)
    assert out["yield_on_cost"] == pytest.approx(0.10)
    assert out["development_spread_bps"] == pytest.approx(500.0)
    assert out["unlevered_irr_periodic"] == pytest.approx(2.0, rel=1e-6)


def test_from_dict():
    out = RE.from_dict({"total_development_cost": {"land_cost": 1.0, "hard_costs": 2.0, "soft_costs": 3.0}})
    assert out["total_development_cost"]["total_development_cost"] == pytest.approx(6.0)
