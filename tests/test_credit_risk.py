"""finmodel.credit_risk: the inverse-normal-CDF helper is checked against published exact standard-normal
quantiles; the Basel IRB formula is checked against its own well-known, widely-published corporate
risk-weight reference point (PD=1%, LGD=45%, M=2.5 years -> ~92.3% risk weight) and for the real property
that the risk weight rises monotonically with PD over the normal working range."""
import pytest

from finmodel import credit_risk as CR


def test_norm_ppf_matches_published_exact_quantiles():
    assert CR.norm_ppf(0.5) == pytest.approx(0.0, abs=1e-9)
    assert CR.norm_ppf(0.975) == pytest.approx(1.959963986, abs=1e-8)
    assert CR.norm_ppf(0.999) == pytest.approx(3.090232306, abs=1e-7)
    assert CR.norm_ppf(0.025) == pytest.approx(-1.959963986, abs=1e-8)
    assert CR.norm_ppf(0.1) == pytest.approx(-1.281551566, abs=1e-8)


def test_norm_ppf_rejects_out_of_range():
    with pytest.raises(ValueError):
        CR.norm_ppf(0.0)
    with pytest.raises(ValueError):
        CR.norm_ppf(1.0)


def test_expected_loss_matches_hand_calc():
    out = CR.expected_loss(pd=0.02, lgd=0.45, ead=1_000_000.0)
    assert out["expected_loss"] == pytest.approx(0.02 * 0.45 * 1_000_000.0)


def test_basel_irb_corporate_matches_the_published_reference_risk_weight():
    # the well-known Basel II corporate IRB reference point: PD=1%, LGD=45%, M=2.5yr floor -> ~92.3% RW
    out = CR.basel_irb_corporate(pd=0.01, lgd=0.45, ead=1.0, maturity_years=2.5)
    assert out["risk_weight_pct"] == pytest.approx(0.923, abs=0.01)
    assert out["risk_weighted_assets"] == pytest.approx(out["risk_weight_pct"], abs=1e-6)  # ead=1.0
    assert out["minimum_capital_required"] == pytest.approx(out["risk_weighted_assets"] * 0.08)


def test_basel_irb_risk_weight_rises_with_pd():
    weights = [CR.basel_irb_corporate(pd=p, lgd=0.45, ead=1.0)["risk_weight_pct"]
              for p in (0.001, 0.005, 0.01, 0.02, 0.05, 0.10)]
    assert weights == sorted(weights)  # strictly increasing risk weight as PD rises


def test_basel_irb_rejects_pd_out_of_range():
    with pytest.raises(ValueError):
        CR.basel_irb_corporate(pd=0.0, lgd=0.45, ead=1.0)
    with pytest.raises(ValueError):
        CR.basel_irb_corporate(pd=1.0, lgd=0.45, ead=1.0)


def test_from_dict_bundles_everything():
    out = CR.from_dict({"expected_loss": {"pd": 0.01, "lgd": 0.5, "ead": 100.0}})
    assert out["expected_loss"]["expected_loss"] == pytest.approx(0.5)
