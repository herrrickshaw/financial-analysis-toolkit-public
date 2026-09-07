"""finmodel.foreign_currency_translation: the current-rate method is checked against a full hand-computed
example, including the exact balance-sheet identity the Cumulative Translation Adjustment exists to enforce
(translated assets = translated liabilities + translated equity + CTA), and against the real, intuitive sign
property that CTA is positive when the foreign currency appreciated during the period and negative when it
depreciated."""
import pytest

from finmodel import foreign_currency_translation as FCT


def test_current_rate_translation_matches_full_hand_calc_with_appreciating_currency():
    out = FCT.current_rate_translation(revenue_fc=500_000.0, expenses_fc=400_000.0, average_rate=0.022,
                                       total_assets_fc=1_000_000.0, total_liabilities_fc=400_000.0,
                                       common_stock_fc=300_000.0, historical_rate_common_stock=0.020,
                                       beginning_retained_earnings_reporting_currency=5_000.0, current_rate=0.025)
    assert out["translated_net_income"] == pytest.approx(2_200.0)
    assert out["translated_assets"] == pytest.approx(25_000.0)
    assert out["translated_liabilities"] == pytest.approx(10_000.0)
    assert out["translated_common_stock"] == pytest.approx(6_000.0)
    assert out["translated_retained_earnings"] == pytest.approx(7_200.0)
    assert out["cumulative_translation_adjustment"] == pytest.approx(1_800.0)
    assert out["cumulative_translation_adjustment"] > 0  # the foreign currency appreciated (0.025 > 0.020/0.022)


def test_balance_sheet_identity_holds_exactly():
    out = FCT.current_rate_translation(revenue_fc=800_000.0, expenses_fc=650_000.0, average_rate=0.030,
                                       total_assets_fc=2_500_000.0, total_liabilities_fc=1_100_000.0,
                                       common_stock_fc=500_000.0, historical_rate_common_stock=0.028,
                                       beginning_retained_earnings_reporting_currency=12_000.0, current_rate=0.031)
    assert out["translated_assets"] == pytest.approx(out["translated_liabilities"] + out["total_translated_equity"])


def test_cta_is_negative_when_the_foreign_currency_depreciates():
    out = FCT.current_rate_translation(revenue_fc=500_000.0, expenses_fc=400_000.0, average_rate=0.022,
                                       total_assets_fc=1_000_000.0, total_liabilities_fc=400_000.0,
                                       common_stock_fc=300_000.0, historical_rate_common_stock=0.020,
                                       beginning_retained_earnings_reporting_currency=5_000.0, current_rate=0.018)
    assert out["cumulative_translation_adjustment"] == pytest.approx(-2_400.0)
    assert out["cumulative_translation_adjustment"] < 0


def test_from_dict_bundles_everything():
    out = FCT.from_dict({"current_rate_translation": {
        "revenue_fc": 100.0, "expenses_fc": 80.0, "average_rate": 1.0, "total_assets_fc": 500.0,
        "total_liabilities_fc": 200.0, "common_stock_fc": 200.0, "historical_rate_common_stock": 1.0,
        "beginning_retained_earnings_reporting_currency": 50.0, "current_rate": 1.0}})
    assert out["current_rate_translation"]["translated_net_income"] == pytest.approx(20.0)
