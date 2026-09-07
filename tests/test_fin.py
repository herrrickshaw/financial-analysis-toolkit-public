from datetime import date
import math
import pytest
from finmodel import fin


def test_yearfrac_basis0_matches_excel_stub_period():
    assert fin.yearfrac("2017-12-31", "2018-06-30") == pytest.approx(0.5)
    assert fin.yearfrac("2018-06-30", "2019-06-30") == pytest.approx(1.0)
    assert fin.yearfrac(date(2020, 1, 31), date(2020, 3, 31)) == pytest.approx(60 / 360)
    assert fin.yearfrac(date(2019, 2, 28), date(2019, 3, 31)) == pytest.approx(30 / 360)  # Feb-end rule


def test_networkdays_matches_excel():
    assert fin.networkdays("2018-01-01", "2018-12-31") == 261
    assert fin.networkdays("2020-01-01", "2020-12-31") == 262
    assert fin.networkdays("2018-01-01", "2018-01-31") == 23
    assert fin.networkdays("2018-01-01", "2018-01-31", holidays=["2018-01-01"]) == 22


def test_npv_irr_xnpv_xirr_roundtrip():
    cfs = [-1000, 300, 400, 500]
    r = fin.irr(cfs)
    assert abs(sum(cf / (1 + r) ** i for i, cf in enumerate(cfs))) < 1e-6
    assert fin.npv(0.1, [100, 100]) == pytest.approx(100 / 1.1 + 100 / 1.21)
    dates = ["2020-01-01", "2020-07-01", "2021-01-01", "2021-07-01"]
    x = fin.xirr(cfs, dates)
    assert abs(fin.xnpv(x, cfs, dates)) < 1e-6
    assert fin.xnpv(0.1, [-100, 110], ["2020-01-01", "2021-01-01"]) == pytest.approx(-100 + 110 / 1.1 ** (366 / 365))


def test_pmt_matches_excel():
    assert fin.pmt(0.05 / 12, 360, 200000) == pytest.approx(-1073.64, abs=0.01)
    assert fin.pmt(0, 10, 1000) == -100


def test_eomonth_edate():
    assert fin.eomonth("2018-02-10") == date(2018, 2, 28)
    assert fin.eomonth("2020-01-31", 1) == date(2020, 2, 29)
    assert fin.edate("2020-01-31", 1) == date(2020, 2, 29)
    assert fin.cagr(100, 200, 5) == pytest.approx(2 ** 0.2 - 1)


def test_smooth_ramp_matches_a_real_case_from_the_unnic_due_diligence_pass():
    # real, verified reference case: a marine-bunkering volume ramp from 5,000 to a 47,303 plateau over 5 years,
    # replacing an original 264%-then-decelerating spike with a constant ~56.7%/yr growth rate.
    out = fin.smooth_ramp(5000, 47303, 5)
    assert out["path"][0] == 5000.0
    assert out["path"][-1] == 47303.0
    assert out["constant_growth_rate"] == pytest.approx(0.5674, abs=1e-3)
    # constant growth rate: every step should compound by the same factor
    ratios = [out["path"][i + 1] / out["path"][i] for i in range(5)]
    assert ratios[0] == pytest.approx(ratios[-1], rel=1e-9)


def test_smooth_ramp_hold_periods_append_the_plateau():
    out = fin.smooth_ramp(100, 200, 3, hold_periods=2)
    assert len(out["path"]) == 3 + 1 + 2  # start + 3 ramp steps + 2 held periods
    assert out["path"][-2:] == [200.0, 200.0]


def test_smooth_ramp_rejects_nonpositive_inputs():
    with pytest.raises(ValueError):
        fin.smooth_ramp(0, 100, 5)
    with pytest.raises(ValueError):
        fin.smooth_ramp(100, 200, 0)
