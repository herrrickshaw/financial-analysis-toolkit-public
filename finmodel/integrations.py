"""Optional bridges to open-source finance packages (all imports are lazy; nothing here is required).

  pyxirr           fast Rust XIRR/XNPV       -> xirr_fast(), xnpv_fast()
  numpy-financial  reference NPV/IRR/PMT      -> npf_check()
  financetoolkit   live statements (FMP/Yahoo)-> statements_from_financetoolkit() feeds ratios.compute / dcf.run
  yfinance         quick price/shares lookup  -> market_snapshot()
See docs/OPEN_SOURCE_MODULES.md for the survey of what each package covers.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Sequence


def _need(mod: str, pip: str):
    try:
        return __import__(mod)
    except ImportError as e:  # pragma: no cover
        raise ImportError(f"{mod} is not installed: pip install {pip}") from e


def xirr_fast(cashflows: Sequence[float], dates: Sequence) -> float:
    from .fin import to_date
    px = _need("pyxirr", "pyxirr")
    return px.xirr([to_date(d) for d in dates], list(cashflows))


def xnpv_fast(rate: float, cashflows: Sequence[float], dates: Sequence) -> float:
    from .fin import to_date
    px = _need("pyxirr", "pyxirr")
    return px.xnpv(rate, [to_date(d) for d in dates], list(cashflows))


def npf_check(rate: float, cashflows: Sequence[float]) -> Dict[str, float]:
    """Cross-check finmodel.fin against numpy-financial (NPV convention: npf.npv treats flow 0 at t=0)."""
    npf = _need("numpy_financial", "numpy-financial")
    from .fin import npv, irr
    return {"finmodel_npv_excel": npv(rate, cashflows), "npf_npv_t0": float(npf.npv(rate, cashflows)),
            "finmodel_irr": irr(cashflows), "npf_irr": float(npf.irr(cashflows))}


def statements_from_financetoolkit(ticker: str, api_key: Optional[str] = None, year: Optional[int] = None) -> Dict[str, Any]:
    """Pull IS/BS for `ticker` via FinanceToolkit (FMP key optional; falls back to Yahoo) and map to the
    dict shape expected by finmodel.ratios.compute.  Returns {"is": {...}, "bs": {...}, "year": y, "raw": ...}."""
    ft = _need("financetoolkit", "financetoolkit")
    tk = ft.Toolkit([ticker], api_key=api_key) if api_key else ft.Toolkit([ticker])
    inc = tk.get_income_statement()
    bal = tk.get_balance_sheet_statement()
    col = year if year is not None else inc.columns[-1]

    def g(df, row):
        try:
            return float(df.loc[row, col])
        except Exception:  # noqa: BLE001
            return 0.0
    is_ = {"revenue": g(inc, "Revenue"), "cogs": g(inc, "Cost of Goods Sold"), "gross_profit": g(inc, "Gross Profit"),
           "ebit": g(inc, "Operating Income"), "interest": g(inc, "Interest Expense"),
           "ebt": g(inc, "Income Before Tax"), "taxes": g(inc, "Income Tax Expense"), "net_income": g(inc, "Net Income")}
    bs = {"total_assets": g(bal, "Total Assets"), "current_assets": g(bal, "Total Current Assets"),
          "current_liabilities": g(bal, "Total Current Liabilities"), "inventory": g(bal, "Inventory"),
          "ar": g(bal, "Accounts Receivable"), "ap": g(bal, "Accounts Payable"),
          "ppe": g(bal, "Fixed Assets"), "long_term_debt": g(bal, "Long Term Debt"),
          "total_liabilities": g(bal, "Total Liabilities"), "equity": g(bal, "Total Equity")}
    return {"is": is_, "bs": bs, "year": col, "raw": {"income": inc, "balance": bal}}


def market_snapshot(ticker: str) -> Dict[str, Any]:
    yf = _need("yfinance", "yfinance")
    info = yf.Ticker(ticker).info
    return {"price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "shares_outstanding": info.get("sharesOutstanding"), "total_debt": info.get("totalDebt"),
            "total_cash": info.get("totalCash"), "beta": info.get("beta")}
