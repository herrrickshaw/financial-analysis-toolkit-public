"""finmodel.cmo: CPR->SMM and the PSA ramp/plateau are checked against their exact real definitions, pool cash
flows are checked for the real property that faster prepayment pays off a pool sooner (and conserves total
principal exactly), and sequential-pay tranching is checked for the two defining real CMO properties: WAL
increases monotonically down the tranche stack, and every tranche's WAL shortens as the assumed PSA speed rises."""
import pytest

from finmodel import cmo as C


def test_cpr_to_smm_matches_known_100pct_psa_plateau_value():
    # the real, well-known reference value: 100% PSA's 6% CPR plateau converts to ~0.514% SMM
    assert C.cpr_to_smm(0.06) == pytest.approx(0.005143, abs=1e-6)


def test_cpr_to_smm_zero_is_zero():
    assert C.cpr_to_smm(0.0) == 0.0


def test_psa_schedule_ramps_linearly_then_plateaus_at_6pct():
    sched = C.psa_cpr_schedule(months=36, psa_pct=1.0)
    assert sched[0] == pytest.approx(0.002)          # month 1: 0.2%
    assert sched[14] == pytest.approx(0.030)         # month 15: 3.0% (halfway up the ramp)
    assert sched[29] == pytest.approx(0.06)           # month 30: 6.0% (top of the ramp)
    assert sched[30] == pytest.approx(0.06)           # month 31: still 6.0% (plateau)
    assert sched[35] == pytest.approx(0.06)           # month 36: still plateaued


def test_psa_schedule_scales_by_speed_multiple():
    sched_100 = C.psa_cpr_schedule(months=30, psa_pct=1.0)
    sched_200 = C.psa_cpr_schedule(months=30, psa_pct=2.0)
    assert sched_200[-1] == pytest.approx(2 * sched_100[-1])


def test_level_payment_matches_hand_calc():
    # a real, simple check: a 1-year, 12% annual (1%/month) loan of 1200 should have a payment recognizable from
    # a standard annuity table
    pmt = C.level_payment(1200.0, 0.01, 12)
    assert pmt == pytest.approx(106.62, abs=0.01)


def test_pool_cash_flows_conserve_total_principal():
    pool = C.pool_cash_flows(principal=1_000_000.0, annual_rate=0.06, term_months=360, psa_pct=1.0)
    assert sum(r["total_principal"] for r in pool) == pytest.approx(1_000_000.0)


def test_faster_prepayment_shortens_the_pool_life():
    slow = C.pool_cash_flows(principal=1_000_000.0, annual_rate=0.06, term_months=360, psa_pct=1.0)
    fast = C.pool_cash_flows(principal=1_000_000.0, annual_rate=0.06, term_months=360, psa_pct=3.0)
    assert len(fast) < len(slow)


def test_zero_psa_matches_a_standard_amortization_schedule_length():
    # 0% PSA means no prepayment at all -- the pool should run the FULL term
    pool = C.pool_cash_flows(principal=1_000_000.0, annual_rate=0.06, term_months=360, psa_pct=0.0)
    assert len(pool) == 360
    assert pool[-1]["ending_balance"] == pytest.approx(0.0, abs=1.0)


def test_sequential_pay_wal_increases_monotonically_down_the_stack():
    # the defining real CMO property: the most senior tranche has the shortest WAL, each successive tranche
    # longer, since ALL principal cascades to the senior-most outstanding tranche first.
    deal = C.cmo_deal(100_000_000.0, 0.06, 360, 1.0, {"A": 40_000_000.0, "B": 30_000_000.0, "C": 30_000_000.0})
    wal = deal["weighted_average_life"]
    assert wal["A"] < wal["B"] < wal["C"]


def test_sequential_pay_conserves_principal_with_the_pool_every_month():
    deal = C.cmo_deal(100_000_000.0, 0.06, 360, 1.0, {"A": 40_000_000.0, "B": 30_000_000.0, "C": 30_000_000.0})
    for i, pool_row in enumerate(deal["pool_cash_flows"]):
        tranche_principal_this_month = sum(deal["tranche_schedules"][name][i]["principal"] for name in ("A", "B", "C"))
        assert tranche_principal_this_month == pytest.approx(pool_row["total_principal"], abs=1e-3)


def test_junior_tranche_gets_zero_principal_while_senior_tranches_remain_outstanding():
    deal = C.cmo_deal(100_000_000.0, 0.06, 360, 1.0, {"A": 40_000_000.0, "B": 30_000_000.0, "C": 30_000_000.0})
    b_schedule = deal["tranche_schedules"]["B"]
    a_schedule = deal["tranche_schedules"]["A"]
    for i in range(len(a_schedule)):
        if a_schedule[i]["ending_balance"] > 1.0:  # A still has a balance after this month's paydown
            assert b_schedule[i]["principal"] == pytest.approx(0.0, abs=1e-6)


def test_higher_psa_speed_shortens_wal_for_every_tranche():
    # the real, standard PSA-sensitivity property every CMO offering document's table demonstrates
    slow = C.cmo_deal(100_000_000.0, 0.06, 360, 1.0, {"A": 40_000_000.0, "B": 30_000_000.0, "C": 30_000_000.0})["weighted_average_life"]
    fast = C.cmo_deal(100_000_000.0, 0.06, 360, 2.0, {"A": 40_000_000.0, "B": 30_000_000.0, "C": 30_000_000.0})["weighted_average_life"]
    for name in ("A", "B", "C"):
        assert fast[name] < slow[name]


def test_from_dict_bundles_deal_and_psa_sensitivity():
    d = {"cmo_deal": {"principal": 1_000_000.0, "annual_rate": 0.06, "term_months": 60, "psa_pct": 1.0, "tranches": {"A": 600_000.0, "B": 400_000.0}},
         "psa_sensitivity": {"principal": 1_000_000.0, "annual_rate": 0.06, "term_months": 60, "tranches": {"A": 600_000.0, "B": 400_000.0}, "psa_speeds": [1.0, 2.0]}}
    out = C.from_dict(d)
    assert out["cmo_deal"]["weighted_average_life"]["A"] < out["cmo_deal"]["weighted_average_life"]["B"]
    assert "100% PSA" in out["psa_sensitivity"] and "200% PSA" in out["psa_sensitivity"]
