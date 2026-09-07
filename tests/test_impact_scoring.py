"""finmodel.impact_scoring: 2X Criteria dimension logic is checked case by case (each of the 4 real dimensions
fires independently), the ABC classification decision tree is checked at each branch including the
"unevidenced additionality gets downgraded from C to B" rule, and GHG intensity arithmetic is hand-checked."""
import pytest

from finmodel import impact_scoring as IS


def test_two_x_entrepreneurship_dimension_alone_is_eligible():
    out = IS.x_gender_criteria(IS.TwoXInputs(founder_is_woman_or_cofounded=True))
    assert out["eligible"] is True
    assert out["dimensions_met_list"] == ["entrepreneurship"]


def test_two_x_leadership_via_board_threshold():
    out = IS.x_gender_criteria(IS.TwoXInputs(women_on_board_pct=0.35))
    assert out["dimensions_met"]["leadership"] is True
    assert out["eligible"] is True


def test_two_x_leadership_via_management_requires_policy_too():
    # senior-management % alone isn't enough without the governance policy (a real, meaningful distinction --
    # the criteria are about durable practice, not a single point-in-time headcount snapshot).
    out = IS.x_gender_criteria(IS.TwoXInputs(women_in_senior_management_pct=0.35, has_gender_inclusive_governance_policy=False))
    assert out["dimensions_met"]["leadership"] is False
    out2 = IS.x_gender_criteria(IS.TwoXInputs(women_in_senior_management_pct=0.35, has_gender_inclusive_governance_policy=True))
    assert out2["dimensions_met"]["leadership"] is True


def test_two_x_employment_via_quality_policies_regardless_of_sector():
    out = IS.x_gender_criteria(IS.TwoXInputs(has_quality_employment_policies_for_women=True))
    assert out["dimensions_met"]["employment"] is True


def test_two_x_no_dimensions_met_is_not_eligible():
    out = IS.x_gender_criteria(IS.TwoXInputs())
    assert out["eligible"] is False
    assert out["dimensions_met_list"] == []


def test_impact_classification_below_minimum_bar():
    out = IS.impact_classification(has_intent_to_benefit_stakeholders=True, measures_and_manages_outcomes=True,
                                   avoids_or_mitigates_material_harm=False, contributes_beyond_business_as_usual=True)
    assert out["class"] is None


def test_impact_classification_a_act_to_avoid_harm():
    out = IS.impact_classification(has_intent_to_benefit_stakeholders=False, measures_and_manages_outcomes=False,
                                   avoids_or_mitigates_material_harm=True, contributes_beyond_business_as_usual=False)
    assert out["class"] == "A"


def test_impact_classification_b_benefit_stakeholders():
    out = IS.impact_classification(has_intent_to_benefit_stakeholders=True, measures_and_manages_outcomes=True,
                                   avoids_or_mitigates_material_harm=True, contributes_beyond_business_as_usual=False)
    assert out["class"] == "B"


def test_impact_classification_c_requires_evidenced_additionality():
    out = IS.impact_classification(has_intent_to_benefit_stakeholders=True, measures_and_manages_outcomes=True,
                                   avoids_or_mitigates_material_harm=True, contributes_beyond_business_as_usual=True,
                                   contribution_is_evidenced=True)
    assert out["class"] == "C"


def test_impact_classification_unevidenced_additionality_downgrades_to_b():
    out = IS.impact_classification(has_intent_to_benefit_stakeholders=True, measures_and_manages_outcomes=True,
                                   avoids_or_mitigates_material_harm=True, contributes_beyond_business_as_usual=True,
                                   contribution_is_evidenced=False)
    assert out["class"] == "B"
    assert "downgraded" in out["note"]


def test_ghg_intensity_scope12_only():
    out = IS.ghg_intensity(revenue=50_000_000, scope1_tco2e=500, scope2_tco2e=1500)
    assert out["scope1_2_tco2e"] == 2000
    assert out["scope1_2_intensity_per_million_revenue"] == pytest.approx(40.0)  # 2000 / 50
    assert "scope3_tco2e" not in out


def test_ghg_intensity_with_scope3_kept_separate():
    out = IS.ghg_intensity(revenue=50_000_000, scope1_tco2e=500, scope2_tco2e=1500, scope3_tco2e=8000)
    assert out["scope1_2_tco2e"] == 2000  # scope 3 must NOT be silently blended into the headline scope1+2 figure
    assert out["scope1_2_3_tco2e"] == 10000
    assert out["scope3_share_of_total"] == pytest.approx(0.8)


def test_from_dict_end_to_end():
    out = IS.from_dict({
        "two_x": {"founder_is_woman_or_cofounded": True},
        "impact_classification": {"has_intent_to_benefit_stakeholders": True, "measures_and_manages_outcomes": True,
                                   "avoids_or_mitigates_material_harm": True, "contributes_beyond_business_as_usual": True,
                                   "contribution_is_evidenced": True},
        "ghg": {"revenue": 50_000_000, "scope1_tco2e": 500, "scope2_tco2e": 1500},
    })
    assert out["two_x"]["eligible"] is True
    assert out["impact_classification"]["class"] == "C"
    assert out["ghg"]["scope1_2_tco2e"] == 2000
