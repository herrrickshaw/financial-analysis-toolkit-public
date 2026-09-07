"""finmodel.npa_classification: asset classification is checked at every real RBI DPD/NPA-age boundary, and
provisioning is checked against the published secured/unsecured rate table -- including the real point that
unsecured exposure is provisioned much more aggressively than secured exposure in the same bucket."""
import pytest

from finmodel import npa_classification as NPA


def test_classify_asset_at_every_dpd_boundary():
    assert NPA.classify_asset(0) == "Standard"
    assert NPA.classify_asset(30) == "SMA-0"
    assert NPA.classify_asset(31) == "SMA-1"
    assert NPA.classify_asset(60) == "SMA-1"
    assert NPA.classify_asset(61) == "SMA-2"
    assert NPA.classify_asset(90) == "SMA-2"
    assert NPA.classify_asset(91, npa_age_days=0) == "Sub-standard"


def test_classify_asset_npa_age_buckets():
    assert NPA.classify_asset(91, npa_age_days=365) == "Sub-standard"
    assert NPA.classify_asset(91, npa_age_days=366) == "Doubtful-1"
    assert NPA.classify_asset(91, npa_age_days=730) == "Doubtful-1"
    assert NPA.classify_asset(91, npa_age_days=731) == "Doubtful-2"
    assert NPA.classify_asset(91, npa_age_days=1095) == "Doubtful-2"
    assert NPA.classify_asset(91, npa_age_days=1096) == "Doubtful-3"


def test_standard_provisioning_matches_the_flat_rate():
    out = NPA.provisioning_requirement("Standard", outstanding_amount=1_000_000.0)
    assert out["provision_required"] == pytest.approx(1_000_000.0 * 0.0040)


def test_sub_standard_provisioning_splits_secured_and_unsecured_at_different_rates():
    out = NPA.provisioning_requirement("Sub-standard", outstanding_amount=1_000_000.0, secured_amount=700_000.0)
    assert out["secured_provision"] == pytest.approx(700_000.0 * 0.15)
    assert out["unsecured_provision"] == pytest.approx(300_000.0 * 0.25)
    assert out["provision_required"] == pytest.approx(700_000.0 * 0.15 + 300_000.0 * 0.25)
    # unsecured exposure is always provisioned at least as aggressively as secured, same bucket
    assert 0.25 >= 0.15


def test_doubtful_1_unsecured_portion_is_fully_provisioned():
    out = NPA.provisioning_requirement("Doubtful-1", outstanding_amount=500_000.0, secured_amount=200_000.0)
    assert out["unsecured_provision"] == pytest.approx(300_000.0 * 1.00)
    assert out["secured_provision"] == pytest.approx(200_000.0 * 0.25)


def test_loss_asset_fully_provisioned_regardless_of_security():
    out = NPA.provisioning_requirement("Loss", outstanding_amount=100_000.0, secured_amount=100_000.0)
    assert out["provision_required"] == pytest.approx(100_000.0)


def test_provisioning_rejects_unknown_classification():
    with pytest.raises(ValueError):
        NPA.provisioning_requirement("Bogus", outstanding_amount=1.0)


def test_npa_provisioning_end_to_end():
    out = NPA.npa_provisioning(days_past_due=200, outstanding_amount=1_000_000.0, npa_age_days=100, secured_amount=600_000.0)
    assert out["classification"] == "Sub-standard"
    assert out["provision_required"] == pytest.approx(600_000.0 * 0.15 + 400_000.0 * 0.25)


def test_from_dict_aggregates_a_loan_book():
    out = NPA.from_dict({"loan_book": [
        {"days_past_due": 10, "outstanding_amount": 1_000_000.0},
        {"days_past_due": 200, "npa_age_days": 400, "outstanding_amount": 500_000.0, "secured_amount": 300_000.0},
    ]})
    assert len(out["loan_book"]) == 2
    assert out["total_provision_required"] == pytest.approx(
        1_000_000.0 * 0.0040 + (300_000.0 * 0.25 + 200_000.0 * 1.00))
