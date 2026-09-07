"""Foreign currency translation under the current rate method (ASC 830 / IAS 21) -- consolidating a foreign
subsidiary's financial statements, prepared in its own functional currency, into the parent's reporting
currency. A real, distinct mechanic from `finmodel.fx_hedging`'s TRANSACTION exposure (a specific future
foreign-currency cash flow a company chooses to hedge): translation exposure arises just from CONSOLIDATING
a subsidiary's statements every period, whether or not anything is hedged, and flows through Other
Comprehensive Income rather than net income.

  * Assets and liabilities translate at the CURRENT (period-end) exchange rate.
  * Equity components (common stock, APIC) translate at their own HISTORICAL rate -- the rate in effect when
    each was originally recorded, not the current rate.
  * Income-statement items translate at the AVERAGE rate for the period (the standard practical convention,
    rather than the theoretically "correct" but impractical rate-at-each-transaction-date approach).
  * The Cumulative Translation Adjustment (CTA) is the PLUG that makes the translated balance sheet balance:
    translated assets must equal translated liabilities plus translated equity plus CTA, by construction --
    and CTA is booked to Other Comprehensive Income, never to net income. This module's own test suite
    verifies that balancing identity directly, and the real, intuitive sign property that CTA is positive
    when the foreign currency has APPRECIATED against the reporting currency during the period (net assets
    translate at a stronger current rate than the historical/average rates they were funded or earned at).
"""
from __future__ import annotations

from typing import Any, Dict


def translate_income_statement(revenue_fc: float, expenses_fc: float, average_rate: float) -> Dict[str, Any]:
    translated_revenue = revenue_fc * average_rate
    translated_expenses = expenses_fc * average_rate
    return {"translated_revenue": translated_revenue, "translated_expenses": translated_expenses,
            "translated_net_income": translated_revenue - translated_expenses}


def translate_balance_sheet(total_assets_fc: float, total_liabilities_fc: float, common_stock_fc: float,
                            historical_rate_common_stock: float, beginning_retained_earnings_reporting_currency: float,
                            translated_net_income: float, current_rate: float) -> Dict[str, Any]:
    translated_assets = total_assets_fc * current_rate
    translated_liabilities = total_liabilities_fc * current_rate
    translated_common_stock = common_stock_fc * historical_rate_common_stock
    translated_retained_earnings = beginning_retained_earnings_reporting_currency + translated_net_income
    implied_equity_needed = translated_assets - translated_liabilities
    cta = implied_equity_needed - translated_common_stock - translated_retained_earnings
    return {"translated_assets": translated_assets, "translated_liabilities": translated_liabilities,
            "translated_common_stock": translated_common_stock, "translated_retained_earnings": translated_retained_earnings,
            "cumulative_translation_adjustment": cta,
            "total_translated_equity": translated_common_stock + translated_retained_earnings + cta}


def current_rate_translation(revenue_fc: float, expenses_fc: float, average_rate: float, total_assets_fc: float,
                             total_liabilities_fc: float, common_stock_fc: float, historical_rate_common_stock: float,
                             beginning_retained_earnings_reporting_currency: float, current_rate: float) -> Dict[str, Any]:
    income = translate_income_statement(revenue_fc, expenses_fc, average_rate)
    balance = translate_balance_sheet(total_assets_fc, total_liabilities_fc, common_stock_fc, historical_rate_common_stock,
                                      beginning_retained_earnings_reporting_currency, income["translated_net_income"], current_rate)
    return {**income, **balance}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "current_rate_translation" in d:
        out["current_rate_translation"] = current_rate_translation(**d["current_rate_translation"])
    return out
