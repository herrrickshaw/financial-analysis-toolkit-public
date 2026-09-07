"""finmodel.earnout_valuation: the scenario-weighted method is checked against a hand-computed
probability-weighted expected value and its own input-validation (probabilities must sum to 1); the binary
metric-earnout method is checked against an independent d1/d2 computation and for the real, defining
property that the risk-neutral probability of achieving the metric rises as the current metric value
approaches or exceeds the threshold."""
import math

import pytest

from finmodel import earnout_valuation as EO
from finmodel.options import norm_cdf


def test_scenario_weighted_earnout_matches_hand_calc():
    scenarios = [{"probability": 0.5, "payout": 10_000_000.0},
                 {"probability": 0.3, "payout": 5_000_000.0},
                 {"probability": 0.2, "payout": 0.0}]
    out = EO.scenario_weighted_earnout(scenarios, discount_rate=0.10, years_to_payout=2.0)
    expected_payout = 0.5 * 10_000_000.0 + 0.3 * 5_000_000.0
    assert out["expected_payout"] == pytest.approx(expected_payout)
    assert out["present_value"] == pytest.approx(expected_payout / 1.10 ** 2)


def test_scenario_weighted_earnout_rejects_probabilities_not_summing_to_one():
    with pytest.raises(ValueError):
        EO.scenario_weighted_earnout([{"probability": 0.5, "payout": 1.0}, {"probability": 0.4, "payout": 2.0}],
                                     discount_rate=0.1, years_to_payout=1.0)


def test_binary_metric_earnout_matches_independent_d1_d2_calc():
    metric, threshold, vol, rate, years, payout = 40_000_000.0, 50_000_000.0, 0.30, 0.05, 2.0, 10_000_000.0
    d1 = (math.log(metric / threshold) + (rate + vol ** 2 / 2) * years) / (vol * math.sqrt(years))
    d2 = d1 - vol * math.sqrt(years)
    out = EO.binary_metric_earnout(metric, threshold, vol, rate, years, payout)
    assert out["risk_neutral_probability_achieved"] == pytest.approx(norm_cdf(d2))
    assert out["discount_factor"] == pytest.approx(math.exp(-rate * years))
    assert out["present_value"] == pytest.approx(payout * math.exp(-rate * years) * norm_cdf(d2))


def test_binary_metric_earnout_probability_rises_as_metric_approaches_threshold():
    kwargs = dict(threshold=50_000_000.0, volatility=0.30, risk_free_rate=0.05, years_to_measurement=2.0, payout_if_achieved=10_000_000.0)
    far_below = EO.binary_metric_earnout(metric_current_value=20_000_000.0, **kwargs)
    near = EO.binary_metric_earnout(metric_current_value=48_000_000.0, **kwargs)
    above = EO.binary_metric_earnout(metric_current_value=70_000_000.0, **kwargs)
    assert far_below["risk_neutral_probability_achieved"] < near["risk_neutral_probability_achieved"] < above["risk_neutral_probability_achieved"]
    assert above["risk_neutral_probability_achieved"] > 0.5  # already past the threshold today


def test_binary_metric_earnout_rejects_non_positive_years_or_volatility():
    with pytest.raises(ValueError):
        EO.binary_metric_earnout(40.0, 50.0, 0.3, 0.05, 0.0, 10.0)
    with pytest.raises(ValueError):
        EO.binary_metric_earnout(40.0, 50.0, 0.0, 0.05, 2.0, 10.0)


def test_from_dict_bundles_everything():
    out = EO.from_dict({"scenario_weighted_earnout": {"scenarios": [{"probability": 1.0, "payout": 100.0}],
                                                       "discount_rate": 0.1, "years_to_payout": 1.0}})
    assert out["scenario_weighted_earnout"]["expected_payout"] == pytest.approx(100.0)
