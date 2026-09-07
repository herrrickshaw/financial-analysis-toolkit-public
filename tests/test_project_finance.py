"""finmodel.project_finance: debt sizing and sculpting are checked for their defining real property (DSCR held
EXACTLY at the covenant every period, and the sized debt fully self-amortizes by construction), LLCR and cap-rate
valuation are checked against hand-computed values."""
import pytest

from finmodel import project_finance as PF


def test_dscr_list():
    assert PF.dscr([130, 130], [100, 100]) == pytest.approx([1.3, 1.3])


def test_size_debt_by_dscr_matches_hand_calc():
    # PV of (cfads/target_dscr) at the interest rate -- Excel NPV convention, first flow discounted one period
    out = PF.size_debt_by_dscr(cfads=[130.0, 130.0], target_dscr=1.3, interest_rate=0.10)
    expected = 100 / 1.10 + 100 / 1.10 ** 2
    assert out["max_debt_sized"] == pytest.approx(expected)


def test_sculpted_amortization_holds_dscr_exactly_at_target_every_period():
    cfads = [12_000_000, 12_500_000, 13_000_000, 13_500_000, 14_000_000]
    sized = PF.size_debt_by_dscr(cfads, target_dscr=1.30, interest_rate=0.06)
    out = PF.sculpted_amortization(cfads, initial_debt=sized["max_debt_sized"], target_dscr=1.30, interest_rate=0.06)
    for row in out["schedule"]:
        assert row["dscr"] == pytest.approx(1.30, abs=1e-6)


def test_sculpted_amortization_fully_self_amortizes_when_sized_correctly():
    # the real, defining property this module is built around: a debt PV-sized to the same target DSCR and rate
    # fully repays itself by construction -- no leftover balance, no early shortfall.
    cfads = [12_000_000, 12_500_000, 13_000_000, 13_500_000, 14_000_000]
    sized = PF.size_debt_by_dscr(cfads, target_dscr=1.30, interest_rate=0.06)
    out = PF.sculpted_amortization(cfads, initial_debt=sized["max_debt_sized"], target_dscr=1.30, interest_rate=0.06)
    assert out["fully_repaid"] is True
    assert out["ending_balance"] == pytest.approx(0.0, abs=1.0)


def test_sculpted_amortization_principal_grows_each_period():
    # the defining SHAPE of a sculpted schedule versus flat corporate amortization: as the balance (and interest
    # charge) shrinks, more of each period's fixed-DSCR capacity goes to principal.
    cfads = [12_000_000, 12_500_000, 13_000_000, 13_500_000, 14_000_000]
    sized = PF.size_debt_by_dscr(cfads, target_dscr=1.30, interest_rate=0.06)
    out = PF.sculpted_amortization(cfads, initial_debt=sized["max_debt_sized"], target_dscr=1.30, interest_rate=0.06)
    principals = [row["principal"] for row in out["schedule"]]
    assert principals == sorted(principals)


def test_llcr_matches_hand_calc():
    out = PF.llcr(cfads_remaining=[100.0, 100.0], outstanding_debt=150.0, discount_rate=0.10)
    expected_pv = 100 / 1.10 + 100 / 1.10 ** 2
    assert out["pv_remaining_cfads"] == pytest.approx(expected_pv)
    assert out["llcr"] == pytest.approx(expected_pv / 150.0)


def test_cap_rate_valuation_and_implied_cap_rate_are_inverses():
    v = PF.cap_rate_valuation(noi=5_000_000, cap_rate=0.065)
    back = PF.implied_cap_rate(noi=5_000_000, price=v["value"])
    assert back["implied_cap_rate"] == pytest.approx(0.065)


def test_cap_rate_rejects_nonpositive_rate():
    with pytest.raises(ValueError):
        PF.cap_rate_valuation(noi=1000, cap_rate=0)


def test_levered_cash_on_cash():
    out = PF.levered_cash_on_cash(noi=5_000_000, debt_service=3_000_000, equity_invested=20_000_000)
    assert out["levered_cash_flow"] == 2_000_000
    assert out["cash_on_cash_return"] == pytest.approx(0.10)


def test_from_dict_bundles_everything():
    d = {"cap_rate_valuation": {"noi": 1000.0, "cap_rate": 0.05}, "levered_cash_on_cash": {"noi": 1000.0, "debt_service": 400.0, "equity_invested": 8000.0}}
    out = PF.from_dict(d)
    assert out["cap_rate_valuation"]["value"] == 20000.0
    assert out["levered_cash_on_cash"]["cash_on_cash_return"] == pytest.approx(0.075)
