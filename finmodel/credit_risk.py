"""Credit-risk quantification: expected loss and the Basel II/III Internal Ratings-Based (IRB) regulatory
capital formula -- the framework every "credit risk management" course (TU Delft's Advanced Credit Risk
Management, the GARP FRM Part II Credit Risk curriculum, IIM Bangalore's Banking and Financial Markets: A
Risk Management Perspective) teaches, and a real gap this toolkit had: finmodel.npa_classification covers
India's RBI provisioning norms and finmodel.bank_model covers a CECL-style provisioning walk, but neither
computes the Basel IRB risk-weighted-asset formula banks actually use to size regulatory capital against an
individual credit exposure.

  * Expected loss = PD x LGD x EAD (probability of default x loss given default x exposure at default) --
    the universal building block behind every credit-risk metric.
  * The Basel IRB formula (Basel Committee on Banking Supervision, *International Convergence of Capital
    Measurement and Capital Standards: A Revised Framework*, June 2006, paragraph 272 for corporate
    exposures) converts a PD into a regulatory capital requirement via a single-factor Vasicek/Merton
    asset-correlation model: a borrower is assumed to default when a latent asset-value variable (correlated
    with one systematic risk factor at a PD-dependent correlation R) falls below a threshold, and the formula
    prices the capital a bank must hold to cover unexpected losses at a 99.9% confidence level over a year.
    `norm_ppf` below (Peter J. Acklam's rational approximation to the inverse standard normal CDF) is
    verified in this module's own test suite against published exact quantiles, and the whole formula is
    verified against Basel's own well-known published corporate risk-weight curve (e.g. PD=1%, LGD=45%,
    M=2.5 years -> a ~92% risk weight).
"""
from __future__ import annotations

import math
from typing import Any, Dict

from .options import norm_cdf


def norm_ppf(p: float) -> float:
    """Acklam's rational approximation to the inverse standard normal CDF (~1.15e-9 relative error) -- no
    scipy/numpy dependency, consistent with the rest of this toolkit."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be strictly between 0 and 1")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    p_low = 0.02425
    p_high = 1 - p_low
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5]) * q / \
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
            ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


def expected_loss(pd: float, lgd: float, ead: float) -> Dict[str, Any]:
    return {"pd": pd, "lgd": lgd, "ead": ead, "expected_loss": pd * lgd * ead}


def basel_irb_corporate(pd: float, lgd: float, ead: float, maturity_years: float = 2.5) -> Dict[str, Any]:
    """Basel's Foundation/Advanced IRB formula for corporate (non-retail) exposures. `pd` and `lgd` are
    decimal fractions (e.g. 0.01, 0.45); `maturity_years` defaults to Basel's own 2.5-year floor."""
    if not 0.0 < pd < 1.0:
        raise ValueError("pd must be strictly between 0 and 1")
    correlation = 0.12 * (1 - math.exp(-50 * pd)) / (1 - math.exp(-50)) + \
                  0.24 * (1 - (1 - math.exp(-50 * pd)) / (1 - math.exp(-50)))
    maturity_adjustment_b = (0.11852 - 0.05478 * math.log(pd)) ** 2
    maturity_factor = (1 + (maturity_years - 2.5) * maturity_adjustment_b) / (1 - 1.5 * maturity_adjustment_b)
    z = (norm_ppf(pd) + math.sqrt(correlation) * norm_ppf(0.999)) / math.sqrt(1 - correlation)
    capital_requirement_k = (lgd * norm_cdf(z) - pd * lgd) * maturity_factor
    risk_weighted_assets = capital_requirement_k * 12.5 * ead
    return {"pd": pd, "lgd": lgd, "ead": ead, "correlation": correlation,
            "maturity_adjustment_b": maturity_adjustment_b, "capital_requirement_k": capital_requirement_k,
            "risk_weight_pct": risk_weighted_assets / ead if ead else 0.0,
            "risk_weighted_assets": risk_weighted_assets, "minimum_capital_required": risk_weighted_assets * 0.08}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "expected_loss" in d:
        out["expected_loss"] = expected_loss(**d["expected_loss"])
    if "basel_irb_corporate" in d:
        out["basel_irb_corporate"] = basel_irb_corporate(**d["basel_irb_corporate"])
    return out
