"""Impact/ESG scoring for gender-lens and climate-oriented investing — the kind of advisory work an
impact-investing consultancy (e.g. Sagana's real, named services: "Gender-Smart Integration"/2X alignment,
"Climate Strategy Development", GHG tracking, and "Impact Measurement and Management") does for fund managers
and portfolio companies, distilled to three real, named, public standards rather than an invented scorecard:

  - `x_gender_criteria()` — a simplified implementation of the 2X Challenge / 2X Global "2X Criteria" for
    gender-lens investing (entrepreneurship, leadership, employment, consumption). This is NOT a substitute for
    formal 2X Certification — thresholds here follow the publicly documented 2X Criteria structure but a real
    assessment should confirm against 2xglobal.org's current published criteria.
  - `impact_classification()` — the Impact Management Project's real, public "ABC" framework (Act to avoid
    harm / Benefit stakeholders / Contribute to solutions), the industry-standard classification GIIN and most
    impact funds (including impact-advisory firms) reference.
  - `ghg_intensity()` — GHG Protocol-based emissions-intensity metrics (tCO2e per $M revenue), the standard
    portfolio climate-risk KPI a fund's climate-strategy work tracks.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .fin import safe_div

TWO_X_ELIGIBLE_THRESHOLD = 1  # meeting >=1 of the 4 dimensions is 2X-eligible per the real 2X Criteria structure


@dataclass
class TwoXInputs:
    founder_is_woman_or_cofounded: bool = False                 # entrepreneurship dimension
    women_on_board_pct: float = 0.0
    women_in_senior_management_pct: float = 0.0
    has_gender_inclusive_governance_policy: bool = False         # leadership dimension support
    women_employees_pct: float = 0.0
    workforce_is_historically_male_dominated_sector: bool = False
    has_quality_employment_policies_for_women: bool = False      # employment dimension support
    product_or_service_specifically_benefits_women: bool = False  # consumption dimension


def x_gender_criteria(inp: TwoXInputs, leadership_board_threshold: float = 0.30,
                      leadership_management_threshold: float = 0.30, employment_threshold: float = 0.30) -> Dict[str, Any]:
    """Real, simplified 2X Criteria structure: a company is 2X-eligible if it meets at least one of the four
    dimensions. Returns which dimensions were met and why, not just a single pass/fail bit — the useful output
    for an advisor deciding WHERE a company is already strong and where it would need to improve."""
    dims: Dict[str, bool] = {}
    dims["entrepreneurship"] = inp.founder_is_woman_or_cofounded
    dims["leadership"] = (inp.women_on_board_pct >= leadership_board_threshold
                          or (inp.women_in_senior_management_pct >= leadership_management_threshold and inp.has_gender_inclusive_governance_policy))
    dims["employment"] = ((inp.women_employees_pct >= employment_threshold and inp.workforce_is_historically_male_dominated_sector)
                          or inp.has_quality_employment_policies_for_women)
    dims["consumption"] = inp.product_or_service_specifically_benefits_women
    met = [k for k, v in dims.items() if v]
    return {"dimensions_met": dims, "dimensions_met_list": met, "eligible": len(met) >= TWO_X_ELIGIBLE_THRESHOLD,
            "note": "simplified structure per the public 2X Criteria; confirm against 2xglobal.org for a formal assessment"}


def impact_classification(has_intent_to_benefit_stakeholders: bool, measures_and_manages_outcomes: bool,
                          avoids_or_mitigates_material_harm: bool, contributes_beyond_business_as_usual: bool,
                          contribution_is_evidenced: bool = False) -> Dict[str, Any]:
    """Impact Management Project's real ABC classification, applied as a decision tree: a company/investment
    that doesn't at minimum avoid material harm doesn't qualify for any of the three classes; one that avoids
    harm but has no deliberate stakeholder-benefit intent is "A" (Act to Avoid Harm); one with real intent and
    measurement is "B" (Benefit Stakeholders); "C" (Contribute to Solutions) additionally requires a
    contribution that wouldn't have happened anyway (real additionality), and only WITH evidence for that claim
    — an unevidenced additionality claim is downgraded to B, since an assertion isn't the same as a demonstrated
    contribution."""
    if not avoids_or_mitigates_material_harm:
        return {"class": None, "label": "Does not meet the ABC framework's minimum bar (material harm not addressed)"}
    if not has_intent_to_benefit_stakeholders or not measures_and_manages_outcomes:
        return {"class": "A", "label": "Act to Avoid Harm"}
    if contributes_beyond_business_as_usual and contribution_is_evidenced:
        return {"class": "C", "label": "Contribute to Solutions"}
    downgraded = contributes_beyond_business_as_usual and not contribution_is_evidenced
    return {"class": "B", "label": "Benefit Stakeholders",
            "note": "additionality claimed but not evidenced -- downgraded from C to B" if downgraded else None}


def ghg_intensity(revenue: float, scope1_tco2e: float, scope2_tco2e: float, scope3_tco2e: Optional[float] = None) -> Dict[str, Any]:
    """GHG Protocol-based emissions intensity — tCO2e per $M revenue, the standard portfolio climate-risk KPI.
    Scope 3 is reported separately (not summed into the headline intensity figure) since it's typically
    estimated with far less precision than Scope 1/2 and blending it in silently would misrepresent confidence."""
    revenue_millions = revenue / 1e6
    scope12 = scope1_tco2e + scope2_tco2e
    out = {"revenue": revenue, "scope1_tco2e": scope1_tco2e, "scope2_tco2e": scope2_tco2e,
           "scope1_2_tco2e": scope12, "scope1_2_intensity_per_million_revenue": safe_div(scope12, revenue_millions)}
    if scope3_tco2e is not None:
        out["scope3_tco2e"] = scope3_tco2e
        out["scope1_2_3_tco2e"] = scope12 + scope3_tco2e
        out["scope1_2_3_intensity_per_million_revenue"] = safe_div(scope12 + scope3_tco2e, revenue_millions)
        out["scope3_share_of_total"] = safe_div(scope3_tco2e, scope12 + scope3_tco2e)
    return out


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "two_x" in d:
        out["two_x"] = x_gender_criteria(TwoXInputs(**d["two_x"]))
    if "impact_classification" in d:
        out["impact_classification"] = impact_classification(**d["impact_classification"])
    if "ghg" in d:
        out["ghg"] = ghg_intensity(**d["ghg"])
    return out
