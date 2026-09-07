"""finmodel.sales_capacity_planning: the capacity schedule is checked against a hand calc that traces two
overlapping hire cohorts through the ramp curve independently, and the reps-needed calculation is checked as
its exact inverse."""
import pytest

from finmodel import sales_capacity_planning as SCP

RAMP = [0.2, 0.5, 0.8, 1.0]


def test_sales_capacity_schedule_matches_hand_calc_with_two_overlapping_cohorts():
    out = SCP.sales_capacity_schedule(hiring_plan=[2, 0, 0, 3], ramp_curve=RAMP, quota_per_rep_per_period=100_000.0)
    periods = out["periods"]
    assert periods[0]["bookings_capacity"] == pytest.approx(2 * 0.2 * 100_000.0)
    assert periods[1]["bookings_capacity"] == pytest.approx(2 * 0.5 * 100_000.0)
    assert periods[2]["bookings_capacity"] == pytest.approx(2 * 0.8 * 100_000.0)
    # period 4: the original cohort is fully ramped (tenure 3 -> 1.0), plus a brand-new cohort at tenure 0
    assert periods[3]["bookings_capacity"] == pytest.approx(2 * 1.0 * 100_000.0 + 3 * 0.2 * 100_000.0)
    assert periods[3]["headcount"] == pytest.approx(5.0)
    assert out["total_capacity"] == pytest.approx(sum(p["bookings_capacity"] for p in periods))


def test_sales_capacity_schedule_holds_ramp_at_full_productivity_beyond_the_curve():
    out = SCP.sales_capacity_schedule(hiring_plan=[1, 0, 0, 0, 0, 0], ramp_curve=RAMP, quota_per_rep_per_period=100_000.0)
    # tenure 4 and 5 exceed the 4-entry ramp curve -> both hold at the curve's last value (1.0)
    assert out["periods"][4]["bookings_capacity"] == pytest.approx(100_000.0)
    assert out["periods"][5]["bookings_capacity"] == pytest.approx(100_000.0)


def test_reps_needed_for_target_is_the_exact_inverse_of_the_capacity_calc():
    out = SCP.reps_needed_for_target(target_bookings_per_period=500_000.0, ramp_curve=RAMP,
                                     quota_per_rep_per_period=100_000.0, periods_since_hire=3)
    assert out["ramp_fraction_at_target_period"] == pytest.approx(1.0)
    assert out["reps_needed"] == pytest.approx(5.0)
    # round-trip: that many reps, hired in period 0, produce exactly the target capacity 3 periods later
    schedule = SCP.sales_capacity_schedule(hiring_plan=[out["reps_needed"], 0, 0, 0], ramp_curve=RAMP, quota_per_rep_per_period=100_000.0)
    assert schedule["periods"][3]["bookings_capacity"] == pytest.approx(500_000.0)


def test_reps_needed_for_target_uses_a_partial_ramp_fraction_before_full_productivity():
    out = SCP.reps_needed_for_target(target_bookings_per_period=100_000.0, ramp_curve=RAMP,
                                     quota_per_rep_per_period=100_000.0, periods_since_hire=0)
    assert out["ramp_fraction_at_target_period"] == pytest.approx(0.2)
    assert out["reps_needed"] == pytest.approx(5.0)  # need 5x the headcount at only 20% productivity


def test_from_dict_bundles_everything():
    out = SCP.from_dict({"reps_needed_for_target": {"target_bookings_per_period": 100.0, "ramp_curve": RAMP,
                                                     "quota_per_rep_per_period": 100.0, "periods_since_hire": 3}})
    assert out["reps_needed_for_target"]["reps_needed"] == pytest.approx(1.0)
