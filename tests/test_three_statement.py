"""Reconcile the engine to the cached values of the CFI 'Case Study - Three Statement Model' workbook."""
import pytest
from finmodel import three_statement as ts

# forecast columns I..M of the CFI workbook (2025..2029)
CFI = {
    "Revenue": [165849.2, 182434.12, 200677.532, 220745.285, 242819.814],
    "Cost of Goods Sold": [69656.664, 85744.036, 100338.766, 79468.303, 84986.935],
    "Net Earnings": [26543.392, 24400.984, 25209.121, 52749.495, 61838.566],
    "Cash": [161049.75, 179174.498, 177826.62, 232675.868, 292139.909],
    "Total Assets": [223884.478, 249916.237, 256604.824, 307238.683, 369636.672],
    "Total Liabilities": [37061.086, 38691.861, 20171.327, 18055.691, 18615.114],
    "Shareholder's Equity": [186823.392, 211224.376, 236433.497, 289182.992, 351021.558],
    "Cash from Operations": [36500.75, 33124.749, 33652.121, 69849.248, 74464.041],
    "Net Working Capital (NWC)": [16384.992, 21447.255, 27215.172, 24602.516, 26643.654],
    "Change in NWC": [3174.992, 5062.263, 5767.917, -2612.657, 2041.138],
    "PPE Closing": [39388.65, 40602.623, 41391.705, 41904.608, 42237.995],
    "Debt Closing": [30000, 30000, 10000, 10000, 10000],
    "Interest Expense": [3000, 3000, 2000, 1000, 1000],
    "Property & Equipment": [39388.65, 40602.623, 41391.705, 41904.608, 42237.995],
}
HIST = {
    "Net Earnings": [2474, 11791, 21075, 26713, 28227],
    "Total Assets": [126376, 139065, 140252, 167319, 195950],
    "Cash from Operations": [12971, 28239, 37505, 42355, 43479],
    "Closing Cash Balance": [67971, 81210, 83715, 111070, 139549],
}


def test_reconciles_to_cfi_workbook(three_statement_inputs):
    r = ts.from_dict(three_statement_inputs)
    assert r.years == list(range(2020, 2030))
    for k, exp in CFI.items():
        got = r.rows[k][5:]
        for g, e in zip(got, exp):
            assert g == pytest.approx(e, abs=0.01), k
    for k, exp in HIST.items():
        assert r.rows[k][:5] == pytest.approx(exp, abs=0.01), k
    assert r.balanced
    assert all(abs(x) < 1e-6 for x in r.rows["Balance Sheet Check"])


def test_implied_assumptions(three_statement_inputs):
    r = ts.from_dict(three_statement_inputs)
    a = r.assumptions
    assert a["COGS % Revenue"][0] == pytest.approx(39023 / 102007)
    assert a["Revenue Growth"][1] == pytest.approx(118086 / 102007 - 1)
    assert a["AR Days"][4] == pytest.approx(7538 / 150772 * 365)
    assert a["Tax Rate"][5] == pytest.approx(0.28)


def test_scalar_and_list_assumptions_and_errors():
    fc = ts.ForecastAssumptions(years=3, revenue_growth=[0.1, 0.2, 0.3])
    assert fc.expanded()["revenue_growth"] == [0.1, 0.2, 0.3]
    with pytest.raises(ValueError):
        ts.ForecastAssumptions(years=3, revenue_growth=[0.1, 0.2]).expanded()
    with pytest.raises(ValueError):
        ts.run([], ts.ForecastAssumptions(years=1))


def test_table_renders(three_statement_inputs):
    r = ts.from_dict(three_statement_inputs)
    txt = r.table("income_statement")
    assert "Revenue" in txt and "2029" in txt
