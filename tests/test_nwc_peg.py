"""finmodel.nwc_peg: the trailing-average peg and the true-up adjustment are checked against hand
calculations for all three real directions (increase to seller, decrease/buyer credit, and no adjustment
when the difference falls inside a real de-minimis threshold)."""
import pytest

from finmodel import nwc_peg as NWC


def test_trailing_average_peg_matches_hand_calc():
    assert NWC.trailing_average_peg([100.0, 120.0, 110.0, 130.0]) == pytest.approx(115.0)


def test_true_up_increases_price_when_actual_exceeds_the_peg():
    out = NWC.nwc_true_up(actual_nwc_at_closing=130.0, peg_nwc=115.0)
    assert out["difference"] == pytest.approx(15.0)
    assert out["purchase_price_adjustment"] == pytest.approx(15.0)
    assert out["direction"] == "increase to seller"


def test_true_up_decreases_price_when_actual_falls_short_of_the_peg():
    out = NWC.nwc_true_up(actual_nwc_at_closing=100.0, peg_nwc=115.0)
    assert out["difference"] == pytest.approx(-15.0)
    assert out["purchase_price_adjustment"] == pytest.approx(-15.0)
    assert out["direction"] == "decrease (buyer credit)"


def test_true_up_below_threshold_triggers_no_adjustment():
    out = NWC.nwc_true_up(actual_nwc_at_closing=116.0, peg_nwc=115.0, threshold=5.0)
    assert out["difference"] == pytest.approx(1.0)
    assert out["purchase_price_adjustment"] == pytest.approx(0.0)
    assert out["direction"] == "no adjustment"


def test_working_capital_adjustment_combines_peg_and_true_up():
    out = NWC.working_capital_adjustment(historical_nwc_values=[100.0, 120.0, 110.0, 130.0], actual_nwc_at_closing=140.0)
    assert out["peg_nwc"] == pytest.approx(115.0)
    assert out["difference"] == pytest.approx(25.0)
    assert out["purchase_price_adjustment"] == pytest.approx(25.0)


def test_from_dict_bundles_everything():
    out = NWC.from_dict({"nwc_true_up": {"actual_nwc_at_closing": 100.0, "peg_nwc": 100.0}})
    assert out["nwc_true_up"]["direction"] == "no adjustment"
