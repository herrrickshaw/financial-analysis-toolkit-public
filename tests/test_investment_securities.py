"""finmodel.investment_securities: the three classifications are checked against the SAME cost basis and
fair value to confirm they route the identical unrealized gain/loss to three genuinely different places
(net income, OCI, or nowhere at all), and the OCI reclassification-on-sale mechanic is checked to fire only
for available-for-sale securities."""
import pytest

from finmodel import investment_securities as IS


def test_trading_security_routes_unrealized_gain_to_net_income():
    out = IS.classify_and_measure(cost_basis=100_000.0, fair_value=115_000.0, classification="trading")
    assert out["unrealized_gain_loss"] == pytest.approx(15_000.0)
    assert out["carrying_value"] == pytest.approx(115_000.0)
    assert out["income_statement_impact"] == pytest.approx(15_000.0)
    assert out["oci_impact"] == pytest.approx(0.0)


def test_afs_security_routes_the_same_unrealized_gain_to_oci_instead():
    out = IS.classify_and_measure(cost_basis=100_000.0, fair_value=115_000.0, classification="available_for_sale")
    assert out["unrealized_gain_loss"] == pytest.approx(15_000.0)
    assert out["carrying_value"] == pytest.approx(115_000.0)
    assert out["income_statement_impact"] == pytest.approx(0.0)
    assert out["oci_impact"] == pytest.approx(15_000.0)


def test_htm_security_recognizes_no_unrealized_gain_anywhere():
    out = IS.classify_and_measure(cost_basis=100_000.0, fair_value=115_000.0, classification="held_to_maturity")
    assert out["carrying_value"] == pytest.approx(100_000.0)  # amortized cost, not fair value
    assert out["income_statement_impact"] == pytest.approx(0.0)
    assert out["oci_impact"] == pytest.approx(0.0)


def test_rejects_unknown_classification():
    with pytest.raises(ValueError):
        IS.classify_and_measure(100.0, 110.0, classification="bogus")


def test_reclassification_from_oci_fires_only_for_available_for_sale():
    afs = IS.realized_gain_loss_on_sale(cost_basis=100_000.0, sale_price=120_000.0, classification="available_for_sale",
                                        cumulative_oci_recognized=15_000.0)
    assert afs["realized_gain_loss"] == pytest.approx(20_000.0)
    assert afs["reclassification_adjustment_from_oci"] == pytest.approx(15_000.0)

    trading = IS.realized_gain_loss_on_sale(cost_basis=100_000.0, sale_price=120_000.0, classification="trading",
                                            cumulative_oci_recognized=15_000.0)
    assert trading["reclassification_adjustment_from_oci"] == pytest.approx(0.0)  # already in net income, nothing to recycle


def test_from_dict_bundles_everything():
    out = IS.from_dict({"classify_and_measure": {"cost_basis": 100.0, "fair_value": 110.0, "classification": "trading"}})
    assert out["classify_and_measure"]["income_statement_impact"] == pytest.approx(10.0)
