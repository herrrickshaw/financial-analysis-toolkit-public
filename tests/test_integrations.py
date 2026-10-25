"""Tests for finmodel.integrations with stand-in modules (no network, optional packages not required)."""
import sys
import types
from datetime import date

import pytest

from finmodel import integrations as I


class _DF:
    """Minimal DataFrame stand-in: .loc[row, col] and .columns."""

    def __init__(self, data, columns):
        self._d, self.columns = data, columns
        outer = self

        class _Loc:
            def __getitem__(self, key):
                return outer._d[key[0]][key[1]]
        self.loc = _Loc()


def test_missing_package_message(monkeypatch):
    monkeypatch.setitem(sys.modules, "pyxirr", None)          # import -> ImportError
    with pytest.raises(ImportError, match="pip install pyxirr"):
        I.xirr_fast([-100, 110], ["2020-01-01", "2021-01-01"])


def test_xirr_fast_passes_dates_then_flows(monkeypatch):
    seen = {}
    fake = types.ModuleType("pyxirr")
    fake.xirr = lambda ds, cfs: seen.update(ds=ds, cfs=cfs) or 0.1
    monkeypatch.setitem(sys.modules, "pyxirr", fake)
    assert I.xirr_fast([-100, 110], ["2020-01-01", "2021-01-01"]) == 0.1
    assert seen["ds"] == [date(2020, 1, 1), date(2021, 1, 1)] and seen["cfs"] == [-100, 110]


def test_statements_from_financetoolkit_maps_rows(monkeypatch):
    inc = _DF({"Revenue": {"2023": 100.0, "2024": 120.0}, "Net Income": {"2024": 12.0},
               "Operating Income": {"2024": 20.0}}, ["2023", "2024"])
    bal = _DF({"Total Assets": {"2024": 300.0}, "Total Equity": {"2024": 150.0}}, ["2023", "2024"])

    class Toolkit:
        def __init__(self, tickers, api_key=None):
            self.tickers, self.api_key = tickers, api_key
        def get_income_statement(self): return inc
        def get_balance_sheet_statement(self): return bal
    fake = types.ModuleType("financetoolkit"); fake.Toolkit = Toolkit
    monkeypatch.setitem(sys.modules, "financetoolkit", fake)
    out = I.statements_from_financetoolkit("XYZ")
    assert out["year"] == "2024"                                 # latest column by default
    assert out["is"]["revenue"] == 120.0 and out["is"]["ebit"] == 20.0 and out["is"]["net_income"] == 12.0
    assert out["is"]["cogs"] == 0.0                              # missing row -> 0.0
    assert out["bs"]["total_assets"] == 300.0 and out["bs"]["equity"] == 150.0
    assert I.statements_from_financetoolkit("XYZ", year="2023")["is"]["revenue"] == 100.0


def test_market_snapshot_price_fallback(monkeypatch):
    class Ticker:
        def __init__(self, t): self.info = {"regularMarketPrice": 9.5, "sharesOutstanding": 10, "beta": 1.1}
    fake = types.ModuleType("yfinance"); fake.Ticker = Ticker
    monkeypatch.setitem(sys.modules, "yfinance", fake)
    snap = I.market_snapshot("XYZ")
    assert snap["price"] == 9.5 and snap["shares_outstanding"] == 10 and snap["total_debt"] is None
