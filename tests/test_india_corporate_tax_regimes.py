"""finmodel.india_corporate_tax_regimes: effective tax rates are checked against the exact statutory
identity (base * (1+surcharge) * (1+cess)) computed independently in the test; post-tax IRR is checked the
rigorous way, by reconstructing the cash-flow stream and confirming its NPV at the module's own returned IRR
is ~0; and the CGTMSE guarantee fee is checked to have exactly the real, small effect the module claims for
it -- tipping a DSCR compliance boundary, not silently improving coverage."""
import pytest

from finmodel import india_corporate_tax_regimes as TAX


def test_effective_corporate_tax_rate_matches_the_statutory_identity():
    bab = TAX.effective_corporate_tax_rate(base_rate=0.15, surcharge_rate=0.10, cess_rate=0.04)
    assert bab["effective_rate"] == pytest.approx(0.15 * 1.10 * 1.04)
    assert bab["effective_rate"] == pytest.approx(0.1716)

    baa = TAX.effective_corporate_tax_rate(base_rate=0.22, surcharge_rate=0.10, cess_rate=0.04)
    assert baa["effective_rate"] == pytest.approx(0.25168)

    standard = TAX.effective_corporate_tax_rate(base_rate=0.30, surcharge_rate=0.07, cess_rate=0.04)
    assert standard["effective_rate"] == pytest.approx(0.33384)


def test_post_tax_project_returns_irr_solves_its_own_npv_to_zero():
    out = TAX.post_tax_project_returns(pre_tax_annual_cash_flow=10.0, total_capex=50.0, project_life_years=10,
                                       effective_tax_rate=0.1716)
    assert out["post_tax_annual_cash_flow"] == pytest.approx(10.0 * (1 - 0.1716))
    cashflow = [-50.0] + [out["post_tax_annual_cash_flow"]] * 10
    npv_at_irr = sum(cf / (1 + out["irr_post_tax"]) ** i for i, cf in enumerate(cashflow))
    assert npv_at_irr == pytest.approx(0.0, abs=1e-6)


def test_tax_regime_comparison_115bab_beats_standard_regime():
    regimes = {
        "115BAB": {"base_rate": 0.15, "surcharge_rate": 0.10, "cess_rate": 0.04},
        "115BAA": {"base_rate": 0.22, "surcharge_rate": 0.10, "cess_rate": 0.04},
        "standard": {"base_rate": 0.30, "surcharge_rate": 0.07, "cess_rate": 0.04},
    }
    out = TAX.tax_regime_comparison(pre_tax_annual_cash_flow=10.0, total_capex=50.0, project_life_years=10,
                                    regimes=regimes)
    # a lower effective tax rate always means higher post-tax cash flow and thus higher IRR, so 115BAB must win
    assert out["best_regime"] == "115BAB"
    assert out["regimes"]["115BAB"]["irr_post_tax"] > out["regimes"]["115BAA"]["irr_post_tax"] > out["regimes"]["standard"]["irr_post_tax"]
    expected_uplift = out["regimes"]["115BAB"]["irr_post_tax"] - out["regimes"]["standard"]["irr_post_tax"]
    assert out["irr_uplift_of_best_vs_worst"] == pytest.approx(expected_uplift)


def test_cgtmse_guarantee_fee_matches_hand_calc():
    out = TAX.cgtmse_guarantee_fee(loan_amount=100.0, annual_fee_rate=0.006)
    assert out["annual_fee"] == pytest.approx(0.6)


def test_cgtmse_adjusted_dscr_fee_tips_compliance_from_ok_to_breach():
    r, n, loan = 0.10, 10, 100.0
    expected_debt_service = loan * r / (1 - (1 + r) ** -n)
    out = TAX.cgtmse_adjusted_dscr(annual_cash_flow=20.0, loan_amount=loan, interest_rate=r, tenure_years=n,
                                   annual_fee_rate=0.006, min_dscr=1.2)
    assert out["annual_debt_service"] == pytest.approx(expected_debt_service)
    assert out["annual_guarantee_fee"] == pytest.approx(0.6)
    assert out["total_annual_debt_service_with_fee"] == pytest.approx(expected_debt_service + 0.6)
    assert out["dscr_without_fee_for_comparison"] == pytest.approx(20.0 / expected_debt_service)
    assert out["dscr_without_fee_for_comparison"] >= 1.2  # compliant without the fee
    assert out["dscr_with_cgtmse_fee"] < 1.2  # the fee's real, small cost tips it into breach
    assert out["compliant"] is False


def test_from_dict_bundles_everything():
    out = TAX.from_dict({
        "cgtmse_adjusted_dscr": {"annual_cash_flow": 20.0, "loan_amount": 100.0, "interest_rate": 0.10,
                                 "tenure_years": 10, "annual_fee_rate": 0.006, "min_dscr": 1.2},
    })
    assert out["cgtmse_adjusted_dscr"]["compliant"] is False
