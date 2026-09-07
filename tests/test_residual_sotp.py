import pytest
from finmodel.residual_income import residual_income, eva, from_dict
from finmodel.sotp import Segment, sotp
from finmodel import sotp as S


def test_residual_income_hand_calc():
    r = residual_income(100, [12, 13], [4, 4], 0.10, terminal="none", shares=10, price=12)
    # RI1 = 12 - 10 = 2 ; B1 = 108 ; RI2 = 13 - 10.8 = 2.2
    assert r["residual_income"] == pytest.approx([2, 2.2]) and r["book_value"] == pytest.approx([100, 108, 117])
    assert r["equity_value"] == pytest.approx(100 + 2 / 1.1 + 2.2 / 1.21) and r["value_per_share"] == pytest.approx(r["equity_value"] / 10)
    p = residual_income(100, [12, 13], [4, 4], 0.10, terminal="persistence", persistence=0.5)
    assert p["terminal_residual_income_value"] == pytest.approx(2.2 * 0.5 / (1.1 - 0.5))
    g = residual_income(100, [12, 13], [4, 4], 0.10, terminal="growth", terminal_growth=0.02)
    assert g["terminal_residual_income_value"] == pytest.approx(2.2 * 1.02 / 0.08)
    with pytest.raises(ValueError): residual_income(100, [1], [1], 0.05, terminal="growth", terminal_growth=0.06)


def test_eva_reconciles_with_zero_spread():
    # ROIC == WACC every year → EVA 0 → firm value == invested capital
    r = eva(1000, [100, 100], [0, 0], 0.10, net_debt=300, shares=70)
    assert r["eva"] == pytest.approx([0, 0]) and r["firm_value"] == pytest.approx(1000) and r["equity_value"] == pytest.approx(700) and r["value_per_share"] == pytest.approx(10)
    r2 = eva(1000, [150, 150], [50, 0], 0.10, terminal_growth=0.0)
    assert r2["eva"] == pytest.approx([50, 150 - 105]) and r2["mva"] > 0
    assert set(from_dict({"eva": {"invested_capital_0": 1, "nopat": [0.1], "net_investment": [0], "wacc": 0.1}})) == {"eva"}


def test_sotp_bridge():
    r = sotp([Segment("Cloud", 200, 12), Segment("Hardware", 100, 6), Segment("Listed sub", value=500, ownership=0.6, metric=50)],
             corporate_costs=30, corporate_cost_multiple=8, net_debt=400, other_adjustments={"Pension deficit": -50}, conglomerate_discount=0.1, shares=100, price=20)
    gross = 2400 + 600 + 300
    assert r["gross_enterprise_value"] == pytest.approx(gross) and r["capitalised_corporate_costs"] == -240
    ev_before = gross - 240; assert r["enterprise_value"] == pytest.approx(ev_before * 0.9)
    assert r["equity_value"] == pytest.approx(ev_before * 0.9 - 400 - 50) and r["value_per_share"] == pytest.approx(r["equity_value"] / 100)
    assert r["segments"][2]["multiple"] == pytest.approx(10) and r["bridge"][-1][1] == pytest.approx(r["equity_value"])
    assert S.from_dict({"segments": [{"name": "A", "metric": 10, "multiple": 5}], "net_debt": 10})["equity_value"] == 40
