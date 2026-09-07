"""finmodel.cash_flow_forecast: the weekly cash roll-forward reconciles to hand-computed running balances, the
covenant-breach flag fires exactly on the weeks it should, and the variance report's arithmetic is checked
directly against its inputs."""
import pytest

from finmodel import cash_flow_forecast as CF


def _weeks():
    return [
        CF.WeeklyCashFlow("2026-01-09", receipts={"AR collections": 100_000}, disbursements={"payroll": 60_000, "AP": 30_000}),
        CF.WeeklyCashFlow("2026-01-16", receipts={"AR collections": 40_000}, disbursements={"payroll": 60_000, "AP": 20_000}),
        CF.WeeklyCashFlow("2026-01-23", receipts={"AR collections": 150_000}, disbursements={"payroll": 60_000, "AP": 25_000}),
    ]


def test_rolling_forecast_hand_computed_balances():
    out = CF.rolling_forecast(opening_cash=50_000, weeks=_weeks())
    # week 1: 50,000 + 100,000 - 90,000 = 60,000
    assert out["weeks"][0]["closing_cash"] == pytest.approx(60_000)
    # week 2: 60,000 + 40,000 - 80,000 = 20,000
    assert out["weeks"][1]["closing_cash"] == pytest.approx(20_000)
    # week 3: 20,000 + 150,000 - 85,000 = 85,000
    assert out["weeks"][2]["closing_cash"] == pytest.approx(85_000)
    assert out["closing_cash"] == pytest.approx(85_000)
    assert out["total_receipts"] == pytest.approx(290_000)
    assert out["total_disbursements"] == pytest.approx(255_000)


def test_rolling_forecast_flags_the_exact_covenant_breach_week():
    out = CF.rolling_forecast(opening_cash=50_000, weeks=_weeks(), min_cash_covenant=25_000)
    # only week 2's closing balance (20,000) falls below the 25,000 covenant
    assert out["covenant_breach_weeks"] == ["2026-01-16"]
    assert out["min_projected_cash"] == pytest.approx(20_000)


def test_rolling_forecast_no_breach_when_covenant_is_none():
    out = CF.rolling_forecast(opening_cash=50_000, weeks=_weeks(), min_cash_covenant=None)
    assert out["covenant_breach_weeks"] == []


def test_variance_report_matches_direct_arithmetic():
    forecast = _weeks()
    actual = [
        CF.WeeklyCashFlow("2026-01-09", receipts={"AR collections": 90_000}, disbursements={"payroll": 60_000, "AP": 30_000}),
        CF.WeeklyCashFlow("2026-01-16", receipts={"AR collections": 45_000}, disbursements={"payroll": 62_000, "AP": 20_000}),
        CF.WeeklyCashFlow("2026-01-23", receipts={"AR collections": 150_000}, disbursements={"payroll": 60_000, "AP": 25_000}),
    ]
    v = CF.variance_report(forecast, actual)
    assert v["weeks"][0]["receipts_variance"] == pytest.approx(-10_000)
    assert v["weeks"][0]["net_variance"] == pytest.approx(-10_000)  # receipts down $10K, disbursements unchanged
    assert v["weeks"][1]["disbursements_variance"] == pytest.approx(2_000)
    assert v["weeks"][2]["net_variance"] == pytest.approx(0.0)  # week 3 was forecast exactly
    assert v["total_net_variance"] == pytest.approx(sum(w["net_variance"] for w in v["weeks"]))


def test_variance_report_rejects_mismatched_week_labels():
    forecast = _weeks()
    actual = [CF.WeeklyCashFlow("2099-01-01", receipts={}, disbursements={})] * 3
    with pytest.raises(ValueError, match="week mismatch"):
        CF.variance_report(forecast, actual)


def test_from_dict_end_to_end():
    out = CF.from_dict({
        "opening_cash": 50_000,
        "weeks": [{"week_ending": "2026-01-09", "receipts": {"AR collections": 100_000}, "disbursements": {"payroll": 60_000}}],
    })
    assert out["forecast"]["closing_cash"] == pytest.approx(90_000)
    assert "variance" not in out
