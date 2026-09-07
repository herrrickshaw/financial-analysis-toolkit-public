"""finmodel.cohort_analysis: the retention curve and both LTV forms are checked by hand, GRR/NRR are checked for
their real, defining difference (NRR can exceed 100%, GRR cannot), and the cohort revenue projection is checked
for correctly staggering each cohort's own retention curve by its own starting period."""
import pytest

from finmodel import cohort_analysis as C


def test_retention_curve_matches_hand_calc():
    out = C.cohort_retention_curve(1000.0, [1000.0, 800.0, 600.0])
    assert out["retention_pct"] == [1.0, 0.8, 0.6]


def test_ltv_from_retention_curve_matches_hand_calc_no_discounting():
    out = C.ltv_from_retention_curve([1.0, 0.5], arpu=100.0, gross_margin=0.5, discount_rate=0.0)
    assert out["periods"] == [50.0, 25.0]
    assert out["ltv"] == 75.0


def test_ltv_simplified_matches_closed_form():
    out = C.ltv_simplified(arpu=50.0, gross_margin=0.8, monthly_churn_rate=0.05)
    assert out["ltv"] == pytest.approx(50.0 * 0.8 / 0.05)
    assert out["average_customer_lifetime_months"] == 20.0


def test_ltv_simplified_rejects_nonpositive_churn():
    with pytest.raises(ValueError):
        C.ltv_simplified(arpu=50.0, gross_margin=0.8, monthly_churn_rate=0.0)


def test_nrr_can_exceed_one_hundred_percent_grr_cannot():
    # the real, defining difference between the two metrics: NRR credits expansion revenue back in, GRR doesn't.
    out = C.revenue_retention(beginning_revenue=1000.0, expansion=300.0, contraction=50.0, churned=50.0)
    assert out["net_revenue_retention"] == pytest.approx(1.20)
    assert out["gross_revenue_retention"] == pytest.approx(0.90)
    assert out["gross_revenue_retention"] <= 1.0


def test_ltv_to_cac_ratio():
    out = C.ltv_to_cac(ltv=900.0, cac=300.0)
    assert out["ratio"] == 3.0


def test_cac_payback_months_matches_hand_calc():
    out = C.cac_payback_months(cac=300.0, arpu=50.0, gross_margin=0.8)
    assert out["monthly_gross_profit"] == 40.0
    assert out["cac_payback_months"] == 7.5


def test_cohort_revenue_projection_staggers_each_cohort_by_its_own_start():
    cohorts = [{"starting_period": 0, "size": 100.0, "retention_pct": [1.0, 0.5], "arpu": 10.0},
               {"starting_period": 1, "size": 100.0, "retention_pct": [1.0, 0.5], "arpu": 10.0}]
    out = C.cohort_revenue_projection(cohorts, periods=3)
    # period 0: only cohort A at 100% -> 100*10=1000
    # period 1: cohort A at 50% (500) + cohort B at 100% (1000) = 1500
    # period 2: cohort B at 50% -> 500
    assert out["revenue_by_period"] == pytest.approx([1000.0, 1500.0, 500.0])


def test_cohort_revenue_projection_drops_periods_beyond_the_horizon():
    cohorts = [{"starting_period": 2, "size": 100.0, "retention_pct": [1.0, 1.0, 1.0], "arpu": 10.0}]
    out = C.cohort_revenue_projection(cohorts, periods=3)
    assert out["revenue_by_period"] == [0.0, 0.0, 1000.0]  # periods 3 and 4 fall outside the 3-period horizon


def test_from_dict_bundles_everything():
    d = {"ltv_simplified": {"arpu": 50.0, "gross_margin": 0.8, "monthly_churn_rate": 0.05},
         "revenue_retention": {"beginning_revenue": 1000.0, "expansion": 100.0, "contraction": 50.0, "churned": 50.0}}
    out = C.from_dict(d)
    assert out["ltv_simplified"]["ltv"] == pytest.approx(800.0)
    assert out["revenue_retention"]["net_revenue_retention"] == 1.0
