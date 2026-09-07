"""finmodel.strategy_frameworks: TAM/SAM/SOM arithmetic is hand-checked both ways (top-down and bottom-up), the
BCG matrix's four quadrants are checked at and around their real boundary (relative share = 1.0, growth =
threshold), and the GE-McKinsey nine-box's weighted scoring + tercile bucketing + zone lookup are each checked
independently so a bug in one doesn't hide behind a coincidentally-correct end-to-end result."""
import pytest

from finmodel import strategy_frameworks as SF


def test_market_sizing_top_down_hand_computed():
    out = SF.market_sizing_top_down(tam=1_000_000_000, sam_pct_of_tam=0.30, som_pct_of_sam=0.05)
    assert out["sam"] == pytest.approx(300_000_000)
    assert out["som"] == pytest.approx(15_000_000)
    assert out["som_pct_of_tam"] == pytest.approx(0.015)


def test_market_sizing_bottom_up_hand_computed():
    segments = [
        SF.CustomerSegment("Enterprise", customer_count=1_000, penetration_pct=0.10, annual_price_per_customer=50_000),
        SF.CustomerSegment("SMB", customer_count=100_000, penetration_pct=0.02, annual_price_per_customer=2_000),
    ]
    out = SF.market_sizing_bottom_up(segments)
    # Enterprise TAM = 1,000 * 50,000 = 50,000,000; SOM = 5,000,000
    # SMB TAM = 100,000 * 2,000 = 200,000,000; SOM = 4,000,000
    assert out["tam"] == pytest.approx(250_000_000)
    assert out["som"] == pytest.approx(9_000_000)
    assert out["segments"][0]["segment_tam"] == pytest.approx(50_000_000)
    assert out["segments"][1]["segment_som"] == pytest.approx(4_000_000)


def test_bcg_classify_all_four_quadrants():
    assert SF.bcg_classify(relative_market_share=1.5, market_growth_rate=0.15) == "Star"
    assert SF.bcg_classify(relative_market_share=1.5, market_growth_rate=0.05) == "Cash Cow"
    assert SF.bcg_classify(relative_market_share=0.5, market_growth_rate=0.15) == "Question Mark"
    assert SF.bcg_classify(relative_market_share=0.5, market_growth_rate=0.05) == "Dog"


def test_bcg_classify_at_the_real_boundary_values():
    # exactly at the share=1.0 / growth=10% boundary counts as "high" on both axes (>=, not >)
    assert SF.bcg_classify(relative_market_share=1.0, market_growth_rate=0.10) == "Star"
    assert SF.bcg_classify(relative_market_share=0.999999, market_growth_rate=0.10) == "Question Mark"
    assert SF.bcg_classify(relative_market_share=1.0, market_growth_rate=0.099999) == "Cash Cow"


def test_bcg_matrix_revenue_mix_sums_to_one():
    units = [
        {"name": "A", "relative_market_share": 1.5, "market_growth_rate": 0.15, "revenue": 100},
        {"name": "B", "relative_market_share": 1.5, "market_growth_rate": 0.05, "revenue": 200},
        {"name": "C", "relative_market_share": 0.5, "market_growth_rate": 0.05, "revenue": 300},
    ]
    out = SF.bcg_matrix(units)
    assert out["units"][0]["classification"] == "Star"
    assert out["revenue_mix_by_classification"]["Star"] == pytest.approx(100 / 600)
    assert out["revenue_mix_by_classification"]["Dog"] == pytest.approx(300 / 600)
    assert sum(out["revenue_mix_by_classification"].values()) == pytest.approx(1.0)


def test_ge_mckinsey_weighted_score_normalizes_weights_not_requiring_exactly_1():
    # weights (2, 1, 1) should behave identically to (0.5, 0.25, 0.25) -- normalization, not a strict-sum check
    factors_raw = {"a": (5.0, 2), "b": (1.0, 1), "c": (1.0, 1)}
    factors_normalized = {"a": (5.0, 0.5), "b": (1.0, 0.25), "c": (1.0, 0.25)}
    assert SF._weighted_score(factors_raw) == pytest.approx(SF._weighted_score(factors_normalized))
    assert SF._weighted_score(factors_raw) == pytest.approx(3.0)  # 5*0.5 + 1*0.25 + 1*0.25


def test_ge_mckinsey_bucket_terciles():
    assert SF._bucket(5.0) == "High"
    assert SF._bucket(11 / 3) == "High"
    assert SF._bucket(11 / 3 - 0.01) == "Medium"
    assert SF._bucket(3.0) == "Medium"
    assert SF._bucket(7 / 3) == "Medium"
    assert SF._bucket(7 / 3 - 0.01) == "Low"
    assert SF._bucket(1.0) == "Low"


def test_ge_mckinsey_classify_invest_grow_zone():
    out = SF.ge_mckinsey_classify(
        industry_attractiveness_factors={"market_size": (5.0, 1), "growth": (5.0, 1)},
        business_strength_factors={"share": (5.0, 1), "brand": (5.0, 1)})
    assert out["industry_attractiveness_bucket"] == "High"
    assert out["business_strength_bucket"] == "High"
    assert out["zone"] == "Invest/Grow"


def test_ge_mckinsey_classify_harvest_divest_zone():
    out = SF.ge_mckinsey_classify(
        industry_attractiveness_factors={"market_size": (1.0, 1)},
        business_strength_factors={"share": (1.0, 1)})
    assert out["zone"] == "Harvest/Divest"


def test_from_dict_end_to_end():
    out = SF.from_dict({
        "market_sizing_top_down": {"tam": 1_000_000_000, "sam_pct_of_tam": 0.3, "som_pct_of_sam": 0.05},
        "bcg_matrix": {"business_units": [{"name": "A", "relative_market_share": 1.5, "market_growth_rate": 0.15, "revenue": 100}]},
        "ge_mckinsey_matrix": {"business_units": [{"name": "A",
            "industry_attractiveness_factors": {"size": [5, 1]}, "business_strength_factors": {"share": [5, 1]}}]},
    })
    assert out["market_sizing_top_down"]["som"] == pytest.approx(15_000_000)
    assert out["bcg_matrix"]["units"][0]["classification"] == "Star"
    assert out["ge_mckinsey_matrix"]["units"][0]["zone"] == "Invest/Grow"
