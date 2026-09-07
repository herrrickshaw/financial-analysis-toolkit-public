"""A bank/FIG operating model — CFI's own named "Bank and FIG Financial Model Template" (this toolkit's catalog
flagged it as a real, uncovered title; `docs/FOOTBALL_FIELD_USB.md` already covers a bank's VALUATION — P/B,
P/TBV, residual income — but not a forward operating projection). A bank's income statement doesn't run on
revenue and COGS: it runs on the SPREAD between what it earns on assets and what it pays on liabilities, sized
against risk-weighted regulatory capital, not just a leverage ratio.

  Net Interest Income (NII) = interest income (earning assets x yield) − interest expense (interest-bearing
                              liabilities x cost of funds); Net Interest Margin (NIM) = NII / average earning
                              assets — the bank-specific analogue of a normal company's gross margin.
  Provision for credit losses — a real, forward-looking (CECL) charge against expected loan losses, taken
                              through the income statement BEFORE net income, not an after-the-fact write-off.
  Efficiency ratio            = non-interest expense / (NII + non-interest income) — the standard bank cost-
                              control metric (lower is better, the mirror image of a normal opex ratio).
  Regulatory capital ratios   — CET1/Tier 1/Total capital ÷ risk-weighted assets, plus the (non-risk-weighted)
                              Tier 1 leverage ratio, checked against the real US Prompt Corrective Action "well
                              capitalized" thresholds (12 CFR 324.403: CET1 >= 6.5%, Tier 1 >= 8%, Total >= 10%,
                              leverage >= 5%)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .fin import safe_div

WELL_CAPITALIZED_THRESHOLDS = {"cet1_ratio": 0.065, "tier1_ratio": 0.08, "total_capital_ratio": 0.10, "leverage_ratio": 0.05}


def net_interest_income(avg_earning_assets: float, asset_yield: float, avg_interest_bearing_liabilities: float, cost_of_funds: float) -> Dict[str, Any]:
    interest_income = avg_earning_assets * asset_yield
    interest_expense = avg_interest_bearing_liabilities * cost_of_funds
    nii = interest_income - interest_expense
    return {"interest_income": interest_income, "interest_expense": interest_expense, "nii": nii,
            "nim": safe_div(nii, avg_earning_assets)}


def provision_for_credit_losses(loans: float, expected_loss_rate: float) -> Dict[str, Any]:
    """A simplified CECL-style (Current Expected Credit Loss) charge: expected lifetime losses on the loan book,
    taken as a real, forward-looking income-statement provision, not a lagging write-off of losses already
    incurred (the pre-2020 incurred-loss model this superseded)."""
    return {"loans": loans, "expected_loss_rate": expected_loss_rate, "provision": loans * expected_loss_rate}


def efficiency_ratio(noninterest_expense: float, nii: float, noninterest_income: float) -> float:
    return safe_div(noninterest_expense, nii + noninterest_income)


def bank_income_statement(avg_earning_assets: float, asset_yield: float, avg_interest_bearing_liabilities: float, cost_of_funds: float,
                          loans: float, expected_loss_rate: float, noninterest_income: float, noninterest_expense: float,
                          tax_rate: float) -> Dict[str, Any]:
    nii_result = net_interest_income(avg_earning_assets, asset_yield, avg_interest_bearing_liabilities, cost_of_funds)
    provision = provision_for_credit_losses(loans, expected_loss_rate)["provision"]
    pretax_income = nii_result["nii"] - provision + noninterest_income - noninterest_expense
    tax = pretax_income * tax_rate
    net_income = pretax_income - tax
    return {"nii": nii_result["nii"], "nim": nii_result["nim"], "interest_income": nii_result["interest_income"], "interest_expense": nii_result["interest_expense"],
            "provision": provision, "noninterest_income": noninterest_income, "noninterest_expense": noninterest_expense,
            "efficiency_ratio": efficiency_ratio(noninterest_expense, nii_result["nii"], noninterest_income),
            "pretax_income": pretax_income, "tax": tax, "net_income": net_income}


def project_bank(years: int, avg_earning_assets_0: float, asset_yield: float, avg_interest_bearing_liabilities_0: float,
                 cost_of_funds: float, loan_growth: float, loans_0: float, expected_loss_rate: float,
                 noninterest_income_0: float, noninterest_expense_0: float, tax_rate: float, opex_growth: float = 0.0) -> List[Dict[str, Any]]:
    """A simple multi-year wrapper: the balance sheet (earning assets, interest-bearing liabilities, loans) grows
    at `loan_growth` each year; non-interest income/expense grow at `opex_growth` (defaults to flat)."""
    rows = []
    assets, liabs, loans, ni_inc, ni_exp = avg_earning_assets_0, avg_interest_bearing_liabilities_0, loans_0, noninterest_income_0, noninterest_expense_0
    for t in range(years):
        row = bank_income_statement(assets, asset_yield, liabs, cost_of_funds, loans, expected_loss_rate, ni_inc, ni_exp, tax_rate)
        row["year"] = t + 1
        rows.append(row)
        assets *= (1 + loan_growth); liabs *= (1 + loan_growth); loans *= (1 + loan_growth)
        ni_inc *= (1 + opex_growth); ni_exp *= (1 + opex_growth)
    return rows


def regulatory_capital_ratios(cet1_capital: float, tier1_capital: float, total_capital: float, risk_weighted_assets: float,
                              average_total_assets: float) -> Dict[str, Any]:
    cet1_ratio = safe_div(cet1_capital, risk_weighted_assets)
    tier1_ratio = safe_div(tier1_capital, risk_weighted_assets)
    total_capital_ratio = safe_div(total_capital, risk_weighted_assets)
    leverage_ratio = safe_div(tier1_capital, average_total_assets)
    t = WELL_CAPITALIZED_THRESHOLDS
    well_capitalized = (cet1_ratio >= t["cet1_ratio"] and tier1_ratio >= t["tier1_ratio"]
                        and total_capital_ratio >= t["total_capital_ratio"] and leverage_ratio >= t["leverage_ratio"])
    return {"cet1_ratio": cet1_ratio, "tier1_ratio": tier1_ratio, "total_capital_ratio": total_capital_ratio,
            "leverage_ratio": leverage_ratio, "well_capitalized": well_capitalized, "thresholds": dict(t)}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "income_statement" in d:
        out["income_statement"] = bank_income_statement(**d["income_statement"])
    if "projection" in d:
        out["projection"] = project_bank(**d["projection"])
    if "regulatory_capital_ratios" in d:
        out["regulatory_capital_ratios"] = regulatory_capital_ratios(**d["regulatory_capital_ratios"])
    return out
