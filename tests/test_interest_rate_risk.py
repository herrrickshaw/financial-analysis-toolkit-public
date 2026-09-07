"""finmodel.interest_rate_risk: the repricing gap and its cumulative running total are checked against hand
calculations, and NII sensitivity is checked for the real, defining directional property -- an
asset-sensitive (positive-gap) bank's NII rises when rates rise, while a liability-sensitive (negative-gap)
bank's NII falls."""
import pytest

from finmodel import interest_rate_risk as IRR


def test_repricing_gap_matches_hand_calc():
    buckets = [
        {"name": "0-3m", "rate_sensitive_assets": 500.0, "rate_sensitive_liabilities": 300.0},
        {"name": "3-12m", "rate_sensitive_assets": 200.0, "rate_sensitive_liabilities": 250.0},
    ]
    out = IRR.repricing_gap(buckets)
    assert out["buckets"][0]["gap"] == pytest.approx(200.0)
    assert out["buckets"][0]["cumulative_gap"] == pytest.approx(200.0)
    assert out["buckets"][1]["gap"] == pytest.approx(-50.0)
    assert out["buckets"][1]["cumulative_gap"] == pytest.approx(150.0)
    assert out["total_gap"] == pytest.approx(150.0)
    assert out["gap_ratio"] == pytest.approx(150.0 / 700.0)


def test_asset_sensitive_bank_nii_rises_with_rates():
    buckets = [{"name": "0-3m", "rate_sensitive_assets": 500.0, "rate_sensitive_liabilities": 300.0}]
    out = IRR.nii_sensitivity(buckets, rate_shock=0.01)
    assert out["nii_rises_with_rates"] is True
    assert out["delta_nii"] == pytest.approx(200.0 * 0.01)


def test_liability_sensitive_bank_nii_falls_with_rate_increases():
    buckets = [{"name": "0-3m", "rate_sensitive_assets": 300.0, "rate_sensitive_liabilities": 500.0}]
    out = IRR.nii_sensitivity(buckets, rate_shock=0.01)
    assert out["nii_rises_with_rates"] is False
    assert out["delta_nii"] < 0


def test_from_dict_bundles_everything():
    out = IRR.from_dict({"repricing_gap": {"buckets": [
        {"name": "a", "rate_sensitive_assets": 100.0, "rate_sensitive_liabilities": 60.0}]}})
    assert out["repricing_gap"]["total_gap"] == pytest.approx(40.0)
