"""finmodel.rd_capitalization: amortization_schedule() reconciles exactly to the CFI 'RD-Capitalization.xlsx'
template's single-vintage schedule; capitalize_rd() reproduces the well-known Damodaran steady-state result
(constant real R&D -> amortization equals current spend, EBIT barely moves) and the expected uplift for a
growing R&D budget (amortization of older, smaller vintages lags current spend, so adjusted EBIT rises)."""
import pytest

from finmodel import rd_capitalization as RD


def test_amortization_schedule_reconciles_to_cfi_template():
    # downloads/cfi/RD-Capitalization.xlsx: spend=100000, residual=20000, life=5 -> $16,000/yr straight line
    rows = RD.amortization_schedule(spend=100_000, life_years=5, residual_value=20_000)
    assert len(rows) == 5
    assert rows[0].asset_value_start == 100_000
    for r in rows:
        assert r.amortization == pytest.approx(16_000)
    assert rows[-1].asset_value_end == pytest.approx(20_000)
    # the CFI sheet's own check cell: "Does Residual Value = Asset Value at the end of the Commercial Life?"
    assert rows[-1].asset_value_end == 20_000


def test_amortization_schedule_zero_residual_ends_at_zero():
    rows = RD.amortization_schedule(spend=50_000, life_years=4, residual_value=0.0)
    assert rows[-1].asset_value_end == pytest.approx(0.0)
    assert sum(r.amortization for r in rows) == pytest.approx(50_000)


def test_capitalize_rd_steady_state_amortization_equals_current_spend():
    # Damodaran's well-known steady-state result: with constant real R&D spend, current-year amortization
    # converges to exactly the current year's R&D expense (one vintage's worth always fully depletes each
    # year) -- so a stable, mature company's adjusted EBIT should barely differ from its reported EBIT.
    life = 5
    history = [100.0] * (life + 1)  # need life_years+1 years for the oldest vintage's final tranche
    cap = RD.capitalize_rd(history, life_years=life)
    assert cap["current_year_amortization"] == pytest.approx(100.0)
    assert cap["rd_asset"] == pytest.approx(300.0)  # 100*(5+4+3+2+1)/5


def test_capitalize_rd_current_year_spend_is_fully_unamortized():
    cap = RD.capitalize_rd([10.0, 20.0, 30.0], life_years=5)
    # the current year's own vintage (age 0) contributes its full spend to the asset and zero amortization
    current_vintage = next(v for v in cap["per_vintage"] if v["years_ago"] == 0)
    assert current_vintage["remaining_value"] == pytest.approx(30.0)
    assert current_vintage["original_spend"] == 30.0


def test_capitalize_rd_growing_spend_produces_a_positive_ebit_uplift():
    # a growing R&D budget: amortization (based on older, smaller vintages) lags the current, larger expense,
    # so capitalizing R&D should raise adjusted EBIT above reported EBIT -- the real, generalizable finding
    # this module exists to quantify for an R&D-intensive, growing company.
    growing = [50.0, 60.0, 70.0, 85.0, 100.0, 120.0]  # 6 years, life_years=5 -> uses the final-tranche adjustment
    out = RD.restate(growing, reported_ebit=200.0, reported_invested_capital=1000.0, life_years=5)
    assert out["ebit_uplift"] > 0
    assert out["adjusted_ebit"] > out["reported_ebit"]
    assert out["adjusted_invested_capital"] > out["reported_invested_capital"]
    assert out["adjusted_roic_proxy"] != out["reported_roic_proxy"]


def test_capitalize_rd_declining_spend_produces_a_negative_ebit_uplift():
    declining = [120.0, 100.0, 85.0, 70.0, 60.0, 50.0]
    out = RD.restate(declining, reported_ebit=200.0, reported_invested_capital=1000.0, life_years=5)
    assert out["ebit_uplift"] < 0


def test_capitalize_rd_rejects_empty_history():
    with pytest.raises(ValueError):
        RD.capitalize_rd([], life_years=5)


def test_capitalize_rd_rejects_nonpositive_life():
    with pytest.raises(ValueError):
        RD.capitalize_rd([10.0], life_years=0)
