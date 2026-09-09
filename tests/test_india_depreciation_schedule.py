"""finmodel.india_depreciation_schedule: block-of-assets WDV depreciation checked against hand calculations,
including the section 50 short-term-capital-gain edge case when deletions exceed the block's WDV, and the
section 32(1)(iia) additional-depreciation half-rate/carry-forward rule."""
import pytest

from finmodel import india_depreciation_schedule as DEP


def test_block_depreciation_full_and_half_rate_additions_net_against_deletions():
    out = DEP.block_depreciation(opening_wdv=100.0, rate=0.15, full_rate_additions=20.0,
                                 half_rate_additions=10.0, deletions=5.0)
    # deletions applied against (opening + full-rate additions) first: 100+20-5=115
    assert out["depreciation"] == pytest.approx(115.0 * 0.15 + 10.0 * 0.075)
    assert out["closing_wdv"] == pytest.approx(125.0 - (115.0 * 0.15 + 10.0 * 0.075))
    assert out["short_term_capital_gain"] == 0.0
    assert out["block_extinguished"] is False


def test_block_depreciation_deletions_exceeding_full_rate_base_spill_into_half_rate_base():
    out = DEP.block_depreciation(opening_wdv=50.0, rate=0.15, half_rate_additions=20.0, deletions=60.0)
    # full-rate base (50-60=-10) goes negative; the 10 shortfall eats into the half-rate additions (20->10)
    assert out["depreciation"] == pytest.approx(10.0 * 0.075)
    assert out["closing_wdv"] == pytest.approx(10.0 - 10.0 * 0.075)
    assert out["short_term_capital_gain"] == 0.0


def test_block_depreciation_deletions_exceeding_entire_block_triggers_section_50_stcg():
    out = DEP.block_depreciation(opening_wdv=50.0, rate=0.15, deletions=80.0)
    assert out["depreciation"] == 0.0
    assert out["closing_wdv"] == 0.0
    assert out["short_term_capital_gain"] == pytest.approx(30.0)
    assert out["block_extinguished"] is True


def test_multi_year_block_schedule_rolls_wdv_forward_across_years():
    yearly_additions = [
        [{"amount": 40.0, "used_180_days_or_more": True}],
        [{"amount": 20.0, "used_180_days_or_more": False}],
    ]
    out = DEP.multi_year_block_schedule(opening_wdv=100.0, rate=0.15, yearly_additions=yearly_additions)
    year1_dep = 140.0 * 0.15
    year1_closing = 140.0 - year1_dep
    year2_dep = year1_closing * 0.15 + 20.0 * 0.075
    year2_closing = (year1_closing + 20.0) - year2_dep
    assert out["rows"][0]["depreciation"] == pytest.approx(year1_dep)
    assert out["rows"][1]["opening_wdv"] == pytest.approx(year1_closing)
    assert out["rows"][1]["depreciation"] == pytest.approx(year2_dep)
    assert out["final_closing_wdv"] == pytest.approx(year2_closing)
    assert out["total_depreciation"] == pytest.approx(year1_dep + year2_dep)
    assert out["total_short_term_capital_gain"] == 0.0


def test_additional_depreciation_full_rate_when_used_180_days_or_more():
    out = DEP.additional_depreciation_sec32_1_iia(new_plant_and_machinery_cost=100.0, used_180_days_or_more=True)
    assert out["current_year"] == pytest.approx(20.0)
    assert out["carried_forward_to_next_year"] == 0.0
    assert out["total"] == pytest.approx(20.0)


def test_additional_depreciation_half_rate_with_carry_forward_when_used_less_than_180_days():
    out = DEP.additional_depreciation_sec32_1_iia(new_plant_and_machinery_cost=100.0, used_180_days_or_more=False)
    assert out["current_year"] == pytest.approx(10.0)
    assert out["carried_forward_to_next_year"] == pytest.approx(10.0)
    # the current-year and carried-forward halves sum to the same total as the full-rate case
    assert out["current_year"] + out["carried_forward_to_next_year"] == pytest.approx(20.0)


def test_from_dict_bundles_all_three_calculations():
    out = DEP.from_dict({
        "block_depreciation": {"opening_wdv": 100.0, "rate": 0.15, "full_rate_additions": 20.0},
        "multi_year_block_schedule": {
            "opening_wdv": 100.0, "rate": 0.15,
            "yearly_additions": [[{"amount": 40.0, "used_180_days_or_more": True}]],
        },
        "additional_depreciation_sec32_1_iia": {"new_plant_and_machinery_cost": 50.0, "used_180_days_or_more": True},
    })
    assert out["block_depreciation"]["depreciation"] == pytest.approx(120.0 * 0.15)
    assert out["multi_year_block_schedule"]["total_depreciation"] == pytest.approx(140.0 * 0.15)
    assert out["additional_depreciation_sec32_1_iia"]["current_year"] == pytest.approx(10.0)
