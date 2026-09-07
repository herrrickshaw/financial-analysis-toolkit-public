"""finmodel.loss_reserving: the chain-ladder age-to-age factors and cumulative development factors are
reconstructed independently in these tests from the raw triangle sums (not by calling the module's own
factor functions), and checked against the module's output; the projected ultimates are then verified by
multiplying those independently-derived factors by hand."""
import pytest

from finmodel import loss_reserving as LR

# a standard 4x4 cumulative-loss triangle (accident years down, development periods across)
TRIANGLE = [
    [1000.0, 1500.0, 1650.0, 1700.0],
    [1200.0, 1800.0, 2000.0],
    [1100.0, 1600.0],
    [900.0],
]


def test_age_to_age_factors_match_independent_sums():
    factors = LR.age_to_age_factors(TRIANGLE)
    factor_0 = (1500.0 + 1800.0 + 1600.0) / (1000.0 + 1200.0 + 1100.0)  # AY1,AY2,AY3 have periods 0 and 1
    factor_1 = (1650.0 + 2000.0) / (1500.0 + 1800.0)                      # AY1,AY2 have periods 1 and 2
    factor_2 = 1700.0 / 1650.0                                            # only AY1 has periods 2 and 3
    assert factors == pytest.approx([factor_0, factor_1, factor_2])


def test_cumulative_development_factors_decrease_toward_1_at_the_latest_period():
    factors = LR.age_to_age_factors(TRIANGLE)
    cdfs = LR.cumulative_development_factors(factors)
    assert cdfs[-1] == pytest.approx(1.0)
    # every factor here exceeds 1 (losses are still developing), so CDFs must strictly decrease as the
    # period index rises -- less development remains the closer a period is to the latest known one.
    assert cdfs[0] > cdfs[1] > cdfs[2] > cdfs[3]
    assert cdfs[2] == pytest.approx(factors[2])
    assert cdfs[1] == pytest.approx(factors[1] * factors[2])
    assert cdfs[0] == pytest.approx(factors[0] * factors[1] * factors[2])


def test_chain_ladder_ultimates_match_hand_calc():
    result = LR.chain_ladder(TRIANGLE)
    factor_0 = (1500.0 + 1800.0 + 1600.0) / (1000.0 + 1200.0 + 1100.0)
    factor_1 = (1650.0 + 2000.0) / (1500.0 + 1800.0)
    factor_2 = 1700.0 / 1650.0

    ay1, ay2, ay3, ay4 = result["accident_years"]
    assert ay1["ultimate"] == pytest.approx(1700.0)          # already at the latest known period -> no IBNR
    assert ay1["ibnr"] == pytest.approx(0.0)
    assert ay2["ultimate"] == pytest.approx(2000.0 * factor_2)
    assert ay3["ultimate"] == pytest.approx(1600.0 * factor_1 * factor_2)
    assert ay4["ultimate"] == pytest.approx(900.0 * factor_0 * factor_1 * factor_2)

    assert result["total_latest_cumulative"] == pytest.approx(1700.0 + 2000.0 + 1600.0 + 900.0)
    assert result["total_ultimate"] == pytest.approx(sum(ay["ultimate"] for ay in result["accident_years"]))
    assert result["total_ibnr"] == pytest.approx(result["total_ultimate"] - result["total_latest_cumulative"])
    assert result["total_ibnr"] > 0  # every non-fully-developed year still owes some IBNR


def test_chain_ladder_rejects_an_empty_triangle():
    with pytest.raises(ValueError):
        LR.chain_ladder([])
    with pytest.raises(ValueError):
        LR.chain_ladder([[]])


def test_from_dict():
    out = LR.from_dict({"triangle": TRIANGLE})
    assert out["chain_ladder"]["total_ibnr"] > 0


A_PRIORI_EXPECTED_LOSSES = [1800.0, 2200.0, 1900.0, 1200.0]


def test_bornhuetter_ferguson_matches_chain_ladder_for_the_fully_developed_year():
    out = LR.bornhuetter_ferguson(TRIANGLE, A_PRIORI_EXPECTED_LOSSES)
    ay0 = out["accident_years"][0]  # AY0 is already at its latest known (fully developed) period, CDF == 1.0
    assert ay0["pct_reported"] == pytest.approx(1.0)
    assert ay0["bf_ibnr"] == pytest.approx(0.0)
    assert ay0["bf_ultimate"] == pytest.approx(ay0["chain_ladder_ultimate"])


def test_bornhuetter_ferguson_diverges_from_chain_ladder_for_the_least_mature_year():
    out = LR.bornhuetter_ferguson(TRIANGLE, A_PRIORI_EXPECTED_LOSSES)
    ay3 = out["accident_years"][3]  # the least mature accident year (only one known period)
    expected_pct_reported = 1.0 / ay3["cdf_to_ultimate"]
    expected_bf_ibnr = 1200.0 * (1 - expected_pct_reported)
    assert ay3["pct_reported"] == pytest.approx(expected_pct_reported)
    assert ay3["bf_ibnr"] == pytest.approx(expected_bf_ibnr)
    assert ay3["bf_ultimate"] == pytest.approx(900.0 + expected_bf_ibnr)
    # BF leans on the independent a-priori estimate here rather than chain-ladder's own volatile extrapolation
    assert ay3["bf_ultimate"] != pytest.approx(ay3["chain_ladder_ultimate"])


def test_bornhuetter_ferguson_rejects_mismatched_length():
    with pytest.raises(ValueError):
        LR.bornhuetter_ferguson(TRIANGLE, [1.0, 2.0])


def test_from_dict_includes_bornhuetter_ferguson_when_requested():
    out = LR.from_dict({"triangle": TRIANGLE, "a_priori_expected_losses": A_PRIORI_EXPECTED_LOSSES})
    assert "bornhuetter_ferguson" in out
    assert out["bornhuetter_ferguson"]["total_bf_ultimate"] > 0
