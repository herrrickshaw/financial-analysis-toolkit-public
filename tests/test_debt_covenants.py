"""finmodel.debt_covenants: each covenant test is checked against hand calculations at and past its
compliance boundary (a leverage ratio exactly at the maximum is compliant; one basis point over is not; the
same boundary logic in the opposite direction for the minimum-type coverage covenants), and the compliance
summary is checked to correctly flag a breach among otherwise-compliant covenants."""
import pytest

from finmodel import debt_covenants as DC


def test_leverage_ratio_covenant_compliant_exactly_at_the_maximum():
    out = DC.leverage_ratio_covenant(total_debt=4_000_000.0, ebitda=1_000_000.0, max_leverage_ratio=4.0)
    assert out["leverage_ratio"] == pytest.approx(4.0)
    assert out["compliant"] is True
    assert out["headroom"] == pytest.approx(0.0)


def test_leverage_ratio_covenant_breaches_just_past_the_maximum():
    out = DC.leverage_ratio_covenant(total_debt=4_100_000.0, ebitda=1_000_000.0, max_leverage_ratio=4.0)
    assert out["leverage_ratio"] == pytest.approx(4.1)
    assert out["compliant"] is False
    assert out["headroom"] < 0


def test_interest_coverage_covenant_compliant_and_breaching():
    compliant = DC.interest_coverage_covenant(ebitda=1_000_000.0, interest_expense=250_000.0, min_interest_coverage=3.0)
    assert compliant["interest_coverage_ratio"] == pytest.approx(4.0)
    assert compliant["compliant"] is True

    breach = DC.interest_coverage_covenant(ebitda=1_000_000.0, interest_expense=400_000.0, min_interest_coverage=3.0)
    assert breach["interest_coverage_ratio"] == pytest.approx(2.5)
    assert breach["compliant"] is False


def test_fixed_charge_coverage_covenant_matches_hand_calc():
    out = DC.fixed_charge_coverage_covenant(ebitda=1_000_000.0, capex=100_000.0, cash_taxes=50_000.0,
                                            interest_expense=200_000.0, scheduled_principal_payments=100_000.0,
                                            min_fccr=1.2)
    expected_ratio = (1_000_000.0 - 100_000.0 - 50_000.0) / (200_000.0 + 100_000.0)
    assert out["fixed_charge_coverage_ratio"] == pytest.approx(expected_ratio)
    assert out["compliant"] is True


def test_covenant_compliance_summary_flags_a_single_breach_among_compliant_covenants():
    covenants = [
        DC.leverage_ratio_covenant(total_debt=4_000_000.0, ebitda=1_000_000.0, max_leverage_ratio=4.0),
        DC.interest_coverage_covenant(ebitda=1_000_000.0, interest_expense=400_000.0, min_interest_coverage=3.0),
        DC.fixed_charge_coverage_covenant(1_000_000.0, 100_000.0, 50_000.0, 200_000.0, 100_000.0, min_fccr=1.2),
    ]
    summary = DC.covenant_compliance_summary(covenants)
    assert summary["total_covenants_tested"] == 3
    assert summary["all_compliant"] is False
    assert len(summary["breaches"]) == 1
    assert summary["breaches"][0]["covenant"] == "interest_coverage_ratio"


def test_from_dict_bundles_everything_and_produces_a_summary():
    out = DC.from_dict({
        "leverage_ratio_covenant": {"total_debt": 4_000_000.0, "ebitda": 1_000_000.0, "max_leverage_ratio": 4.0},
        "interest_coverage_covenant": {"ebitda": 1_000_000.0, "interest_expense": 250_000.0, "min_interest_coverage": 3.0},
    })
    assert out["covenant_compliance_summary"]["all_compliant"] is True
    assert out["covenant_compliance_summary"]["total_covenants_tested"] == 2
