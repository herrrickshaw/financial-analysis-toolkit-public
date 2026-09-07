"""finmodel.restructuring: the recovery waterfall is checked against the real absolute-priority property (a
senior claim is never shorted while a junior one gets paid), the fulcrum security is checked at each of its three
real cases (mid-stack, fully-covered, fully-wiped-out), the priority-departure check is exercised on both a
clean and a violating capital structure, and DIP sizing/post-emergence leverage are checked by hand."""
import pytest

from finmodel import restructuring as R


def _tranches():
    return [R.Tranche("Secured", 200.0, 1), R.Tranche("Senior Unsecured", 150.0, 2), R.Tranche("Subordinated", 100.0, 3)]


def test_recovery_waterfall_pays_senior_in_full_before_junior_sees_anything():
    wf = R.recovery_waterfall(300.0, _tranches())
    rows = {r["name"]: r for r in wf["tranches"]}
    assert rows["Secured"]["recovery_pct"] == 1.0
    assert rows["Senior Unsecured"]["recovery_pct"] == pytest.approx(100 / 150)
    assert rows["Subordinated"]["recovery_pct"] == 0.0
    assert wf["residual_to_equity"] == 0.0


def test_recovery_waterfall_conserves_total_value():
    wf = R.recovery_waterfall(300.0, _tranches())
    assert sum(r["recovery"] for r in wf["tranches"]) + wf["residual_to_equity"] == pytest.approx(300.0)


def test_recovery_waterfall_pari_passu_split_within_same_seniority():
    tranches = [R.Tranche("Bank A", 100.0, 1), R.Tranche("Bank B", 100.0, 1)]
    wf = R.recovery_waterfall(150.0, tranches)
    assert wf["tranches"][0]["recovery"] == pytest.approx(75.0)
    assert wf["tranches"][1]["recovery"] == pytest.approx(75.0)


def test_recovery_waterfall_full_coverage_leaves_a_residual_to_equity():
    wf = R.recovery_waterfall(500.0, _tranches())
    assert all(r["recovery_pct"] == 1.0 for r in wf["tranches"])
    assert wf["residual_to_equity"] == pytest.approx(50.0)


def test_fulcrum_is_the_partially_recovering_mid_stack_tranche():
    wf = R.recovery_waterfall(300.0, _tranches())
    f = R.identify_fulcrum(wf)
    assert f["name"] == "Senior Unsecured"


def test_fulcrum_is_none_when_every_claim_is_covered_in_full():
    wf = R.recovery_waterfall(500.0, _tranches())
    f = R.identify_fulcrum(wf)
    assert f["name"] is None


def test_fulcrum_is_the_most_senior_tranche_when_reorg_value_is_near_zero():
    wf = R.recovery_waterfall(10.0, _tranches())
    f = R.identify_fulcrum(wf)
    assert f["name"] == "Secured"


def test_absolute_priority_departure_flags_a_real_violation():
    wf = {"tranches": [{"name": "Secured", "seniority": 1, "recovery_pct": 1.0},
                        {"name": "Unsecured", "seniority": 2, "recovery_pct": 0.5},
                        {"name": "Sub", "seniority": 3, "recovery_pct": 0.2}]}
    out = R.check_absolute_priority_departure(wf)
    assert out["absolute_priority_respected"] is False
    assert out["departures"][0]["junior_claim"] == "Sub"


def test_absolute_priority_respected_on_a_clean_waterfall():
    wf = R.recovery_waterfall(300.0, _tranches())
    out = R.check_absolute_priority_departure(wf)
    assert out["absolute_priority_respected"] is True


def test_dip_financing_sizing_matches_hand_calc():
    # opening 40, running: 40-10=30, 30-25=5 (the trough), 5+20=25 -- min cash is 5, covenant 15 -> need 10 more
    out = R.dip_financing_sizing(cash_flows=[-10, -25, 20], minimum_liquidity=15, opening_cash=40)
    assert out["minimum_projected_cash"] == 5
    assert out["required_dip_facility"] == 10


def test_dip_financing_sizing_is_zero_when_covenant_never_binds():
    out = R.dip_financing_sizing(cash_flows=[5, 5, 5], minimum_liquidity=1, opening_cash=10)
    assert out["required_dip_facility"] == 0.0


def test_post_emergence_capital_structure():
    out = R.post_emergence_capital_structure(emergence_ebitda=50.0, target_net_debt_to_ebitda=2.5)
    assert out["new_debt"] == 125.0


def test_from_dict_bundles_waterfall_fulcrum_and_priority_check():
    d = {"recovery_waterfall": {"reorg_value": 300.0, "tranches": [{"name": "Secured", "claim_amount": 200.0, "seniority": 1},
                                                                    {"name": "Senior Unsecured", "claim_amount": 150.0, "seniority": 2},
                                                                    {"name": "Subordinated", "claim_amount": 100.0, "seniority": 3}]},
         "dip_financing_sizing": {"cash_flows": [-10, -25, 20], "minimum_liquidity": 15, "opening_cash": 40},
         "post_emergence_capital_structure": {"emergence_ebitda": 50.0, "target_net_debt_to_ebitda": 2.5}}
    out = R.from_dict(d)
    assert out["fulcrum_security"]["name"] == "Senior Unsecured"
    assert out["absolute_priority_check"]["absolute_priority_respected"] is True
    assert out["dip_financing_sizing"]["required_dip_facility"] == 10
    assert out["post_emergence_capital_structure"]["new_debt"] == 125.0
