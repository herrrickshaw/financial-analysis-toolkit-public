import pytest
from finmodel import wacc as W


def test_capm_and_betas():
    assert W.cost_of_equity(0.04, 1.2, 0.05) == pytest.approx(0.10)
    bu = W.unlever_beta(1.2, 0.5, 0.25)
    assert W.relever_beta(bu, 0.5, 0.25) == pytest.approx(1.2)
    b = W.bottom_up_beta([{"beta": 1.1, "debt_to_equity": 0.3}, {"beta": 1.3, "debt_to_equity": 0.5}], 0.4, 0.25)
    assert len(b["peer_unlevered_betas"]) == 2 and b["relevered_beta"] > b["average_unlevered_beta"]


def test_synthetic_rating_boundaries():
    assert W.synthetic_rating(100, 10)["rating"] == "AAA"
    assert W.synthetic_rating(100, 40)["rating"] == "BBB"          # 2.5x
    assert W.synthetic_rating(100, 0)["rating"] == "AAA"           # no interest
    assert W.synthetic_rating(-10, 10)["rating"] == "D"
    assert W.synthetic_rating(100, 40, large_firm=False)["rating"] == "B+"


def test_wacc_weights_and_synthetic_kd():
    r = W.wacc(W.WACCInputs(risk_free=0.04, equity_risk_premium=0.05, beta=1.0, market_cap=800, debt=200, tax_rate=0.25, ebit=60, interest_expense=10))
    assert r["weights"] == pytest.approx({"equity": 0.8, "debt": 0.2, "preferred": 0.0})
    assert r["synthetic_rating"]["rating"] == "A+" and r["cost_of_debt_pretax"] == pytest.approx(0.04 + 0.0092)   # coverage 6.0x falls in the [5.50, 6.50) A+ band
    assert r["wacc"] == pytest.approx(0.8 * 0.09 + 0.2 * (0.04 + 0.0092) * 0.75)
    out = W.from_dict({"peers": [{"beta": 1.1, "debt_to_equity": 0.3}], "wacc": {"risk_free": 0.04, "equity_risk_premium": 0.05, "market_cap": 800, "debt": 200, "tax_rate": 0.25, "cost_of_debt": 0.06}})
    assert "bottom_up_beta" in out and out["wacc"]["cost_of_debt_pretax"] == 0.06
    with pytest.raises(ValueError):
        W.wacc(W.WACCInputs(0.04, 0.05, 1.0, 800, 200, 0.25))
