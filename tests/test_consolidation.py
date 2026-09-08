"""finmodel.consolidation: consolidated net income and the NCI carve-out are checked against hand
calculations and the defining accounting identity (consolidated net income minus NCI's share equals net
income attributable to the parent), and NCI's share is checked to scale linearly with ownership percentage."""
import pytest

from finmodel import consolidation as CONS


def test_consolidated_net_income_matches_hand_calc():
    out = CONS.consolidated_net_income(parent_standalone_net_income=5_000_000.0, subsidiary_net_income=1_000_000.0,
                                       nci_ownership_pct=0.20)
    assert out["nci_share_of_net_income"] == pytest.approx(200_000.0)
    assert out["consolidated_net_income"] == pytest.approx(6_000_000.0)
    assert out["net_income_attributable_to_parent"] == pytest.approx(5_800_000.0)
    # the defining identity: consolidated NI minus NCI's carve-out equals what's attributable to the parent
    assert out["consolidated_net_income"] - out["nci_share_of_net_income"] == pytest.approx(out["net_income_attributable_to_parent"])


def test_nci_share_scales_linearly_with_ownership_pct():
    low = CONS.consolidated_net_income(5_000_000.0, 1_000_000.0, nci_ownership_pct=0.10)
    high = CONS.consolidated_net_income(5_000_000.0, 1_000_000.0, nci_ownership_pct=0.30)
    assert high["nci_share_of_net_income"] == pytest.approx(3 * low["nci_share_of_net_income"])


def test_nci_balance_sheet_matches_hand_calc():
    out = CONS.nci_balance_sheet(subsidiary_total_equity=10_000_000.0, nci_ownership_pct=0.20)
    assert out["nci_balance"] == pytest.approx(2_000_000.0)
    assert out["parent_share_of_subsidiary_equity"] == pytest.approx(8_000_000.0)
    assert out["nci_balance"] + out["parent_share_of_subsidiary_equity"] == pytest.approx(10_000_000.0)


def test_nci_at_acquisition_fair_value_method_matches_hand_calc():
    out = CONS.nci_at_acquisition_fair_value_method(subsidiary_fair_value=20_000_000.0, nci_ownership_pct=0.20)
    assert out["nci_initial_value"] == pytest.approx(4_000_000.0)


def test_from_dict_bundles_everything():
    out = CONS.from_dict({"nci_balance_sheet": {"subsidiary_total_equity": 100.0, "nci_ownership_pct": 0.25}})
    assert out["nci_balance_sheet"]["nci_balance"] == pytest.approx(25.0)
