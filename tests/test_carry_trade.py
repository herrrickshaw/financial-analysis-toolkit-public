"""finmodel.carry_trade: covered interest rate parity is checked against its own closed-form definition;
the unhedged carry return is checked at an unchanged spot rate, where it must equal exactly the one-year
interest-rate differential; and break-even depreciation is checked for the module's defining, real identity
-- it must equal EXACTLY the CIP forward premium, and profit at that exact break-even future spot must be
zero."""
import pytest

from finmodel import carry_trade as CT


def test_covered_interest_rate_parity_matches_closed_form():
    out = CT.covered_interest_rate_parity(spot_rate=100.0, domestic_rate=0.05, foreign_rate=0.02, tenor_years=1.0)
    expected_forward = 100.0 * 1.05 / 1.02
    assert out["forward_rate"] == pytest.approx(expected_forward)
    assert out["forward_premium_pct"] == pytest.approx(1.05 / 1.02 - 1)


def test_uncovered_carry_return_at_unchanged_spot_equals_the_rate_differential():
    # tenor = 1 year -> (1+foreign)^1 - (1+domestic)^1 = foreign - domestic exactly
    out = CT.uncovered_carry_return(spot_rate=100.0, expected_future_spot_rate=100.0, domestic_rate=0.01,
                                    foreign_rate=0.05, tenor_years=1.0, notional=1_000_000.0)
    assert out["return_pct"] == pytest.approx(0.05 - 0.01)
    assert out["profit"] == pytest.approx(1_000_000.0 * (0.05 - 0.01))


def test_uncovered_carry_return_turns_negative_if_the_target_currency_depreciates_enough():
    baseline = CT.uncovered_carry_return(spot_rate=100.0, expected_future_spot_rate=100.0, domestic_rate=0.01,
                                         foreign_rate=0.05, tenor_years=1.0)
    depreciated = CT.uncovered_carry_return(spot_rate=100.0, expected_future_spot_rate=90.0, domestic_rate=0.01,
                                            foreign_rate=0.05, tenor_years=1.0)
    assert depreciated["profit"] < baseline["profit"]
    assert depreciated["profit"] < 0


def test_break_even_depreciation_equals_the_cip_forward_premium_exactly():
    domestic_rate, foreign_rate, tenor = 0.01, 0.05, 1.5
    cip = CT.covered_interest_rate_parity(spot_rate=100.0, domestic_rate=domestic_rate, foreign_rate=foreign_rate, tenor_years=tenor)
    be = CT.break_even_depreciation(domestic_rate=domestic_rate, foreign_rate=foreign_rate, tenor_years=tenor)
    assert be["break_even_depreciation_pct"] == pytest.approx(cip["forward_premium_pct"])
    assert be["break_even_future_spot_over_spot"] == pytest.approx(cip["forward_rate"] / 100.0)


def test_profit_is_exactly_zero_at_the_break_even_future_spot():
    spot, domestic_rate, foreign_rate, tenor = 100.0, 0.01, 0.05, 1.5
    be = CT.break_even_depreciation(domestic_rate, foreign_rate, tenor)
    future_spot = spot * be["break_even_future_spot_over_spot"]
    out = CT.uncovered_carry_return(spot_rate=spot, expected_future_spot_rate=future_spot, domestic_rate=domestic_rate,
                                    foreign_rate=foreign_rate, tenor_years=tenor)
    assert out["profit"] == pytest.approx(0.0, abs=1e-6)


def test_from_dict_bundles_everything():
    out = CT.from_dict({"covered_interest_rate_parity": {"spot_rate": 80.0, "domestic_rate": 0.03, "foreign_rate": 0.01, "tenor_years": 1.0}})
    assert out["covered_interest_rate_parity"]["forward_rate"] > 80.0
