"""P&C insurance pricing and underwriting profitability — CFI's own named "InsurTech Pricer Model" (this
toolkit's catalog flagged it as a real, uncovered title; `docs/FOOTBALL_FIELD_TRV.md` already covers a P&C
insurer's VALUATION — P/B, P/TBV, residual income — but not the actuarial pricing/underwriting side).

  Loss ratio + Expense ratio = Combined ratio — the real, standard P&C underwriting-profitability metric: below
                              100% means the insurer made an underwriting profit BEFORE investment income; above
                              100% means premiums alone didn't cover losses and costs (real, common for many
                              real insurers in a soft market, made up for by investment income on the float).
  Operating ratio            = combined ratio − investment income ratio — the real refinement that accounts for
                              the float income an insurer earns while holding reserves before claims are paid;
                              an insurer can run a combined ratio modestly above 100% and still be profitable
                              overall once float income is counted.
  Loss cost multiplier       — the real, standard actuarial rate-making formula: gross premium = pure premium
                              (expected loss cost) / (1 − expense ratio − target underwriting profit margin)."""
from __future__ import annotations

from typing import Any, Dict

from .fin import safe_div


def loss_ratio(incurred_losses: float, earned_premium: float) -> float:
    return safe_div(incurred_losses, earned_premium)


def expense_ratio(underwriting_expenses: float, earned_premium: float) -> float:
    return safe_div(underwriting_expenses, earned_premium)


def combined_ratio(incurred_losses: float, underwriting_expenses: float, earned_premium: float) -> Dict[str, Any]:
    lr = loss_ratio(incurred_losses, earned_premium)
    er = expense_ratio(underwriting_expenses, earned_premium)
    cr = lr + er
    return {"loss_ratio": lr, "expense_ratio": er, "combined_ratio": cr, "underwriting_profitable": cr < 1.0}


def operating_ratio(combined_ratio_value: float, investment_income: float, earned_premium: float) -> Dict[str, Any]:
    investment_income_ratio = safe_div(investment_income, earned_premium)
    op_ratio = combined_ratio_value - investment_income_ratio
    return {"combined_ratio": combined_ratio_value, "investment_income_ratio": investment_income_ratio,
            "operating_ratio": op_ratio, "overall_profitable": op_ratio < 1.0}


def rate_making_premium(pure_premium: float, expense_ratio_value: float, target_profit_margin: float) -> Dict[str, Any]:
    """The real, standard loss-cost-multiplier rate-making method: gross premium grosses up the expected loss
    cost so that, after paying real expenses and taking the target underwriting margin, the pure premium is
    fully covered."""
    denom = 1 - expense_ratio_value - target_profit_margin
    if denom <= 0:
        raise ValueError("expense_ratio + target_profit_margin must be below 1.0")
    gross_premium = pure_premium / denom
    return {"pure_premium": pure_premium, "expense_ratio": expense_ratio_value, "target_profit_margin": target_profit_margin,
            "loss_cost_multiplier": 1 / denom, "gross_premium": gross_premium}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "combined_ratio" in d:
        out["combined_ratio"] = combined_ratio(**d["combined_ratio"])
    if "operating_ratio" in d:
        p = dict(d["operating_ratio"])
        if "combined_ratio_value" not in p and "combined_ratio" in out:
            p["combined_ratio_value"] = out["combined_ratio"]["combined_ratio"]
        out["operating_ratio"] = operating_ratio(**p)
    if "rate_making_premium" in d:
        out["rate_making_premium"] = rate_making_premium(**d["rate_making_premium"])
    return out
