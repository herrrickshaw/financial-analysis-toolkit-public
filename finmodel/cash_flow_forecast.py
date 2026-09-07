"""13-week rolling cash flow forecast: the direct-method, weekly liquidity-planning tool a fractional-CFO
practice runs for a client every week (Flipcarbon names this specific deliverable — "13-week rolling forecasts
for liquidity planning and working capital optimization" — and it's a staple of treasury and turnaround/
restructuring finance generally, distinct in both granularity and method from the annual, accrual-basis
three-statement model elsewhere in this toolkit).

Direct method: each week's closing cash = opening cash + receipts (by category) − disbursements (by category).
No accrual adjustments, no D&A, no working-capital *schedules* — just real cash in and cash out, because the
whole point of a 13-week cash forecast is near-term liquidity survival, not GAAP-consistent earnings.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div


@dataclass
class WeeklyCashFlow:
    week_ending: str
    receipts: Dict[str, float] = field(default_factory=dict)        # category -> amount, e.g. {"AR collections": ...}
    disbursements: Dict[str, float] = field(default_factory=dict)   # category -> amount, e.g. {"payroll": ...}

    def total_receipts(self) -> float:
        return sum(self.receipts.values())

    def total_disbursements(self) -> float:
        return sum(self.disbursements.values())

    def net(self) -> float:
        return self.total_receipts() - self.total_disbursements()


def rolling_forecast(opening_cash: float, weeks: Sequence[WeeklyCashFlow], min_cash_covenant: Optional[float] = None) -> Dict[str, Any]:
    """Rolls `opening_cash` forward week by week. If `min_cash_covenant` is given, flags every week the
    projected closing balance would fall below it — the real, actionable output of a 13-week forecast (when,
    specifically, does the company need a bridge/draw/collections push, not just "cash is tight sometime soon")."""
    rows: List[Dict[str, Any]] = []
    balance = opening_cash
    breach_weeks: List[str] = []
    receipt_categories = sorted({k for w in weeks for k in w.receipts})
    disbursement_categories = sorted({k for w in weeks for k in w.disbursements})
    for w in weeks:
        opening = balance
        receipts = w.total_receipts()
        disbursements = w.total_disbursements()
        net = receipts - disbursements
        balance = opening + net
        breach = min_cash_covenant is not None and balance < min_cash_covenant
        if breach:
            breach_weeks.append(w.week_ending)
        rows.append({"week_ending": w.week_ending, "opening_cash": opening, "receipts": dict(w.receipts),
                    "total_receipts": receipts, "disbursements": dict(w.disbursements),
                    "total_disbursements": disbursements, "net": net, "closing_cash": balance,
                    "covenant_breach": breach})
    return {"opening_cash": opening_cash, "weeks": rows, "closing_cash": balance,
            "total_receipts": sum(r["total_receipts"] for r in rows),
            "total_disbursements": sum(r["total_disbursements"] for r in rows),
            "min_projected_cash": min((r["closing_cash"] for r in rows), default=opening_cash),
            "min_cash_covenant": min_cash_covenant, "covenant_breach_weeks": breach_weeks,
            "receipt_categories": receipt_categories, "disbursement_categories": disbursement_categories}


def variance_report(forecast_weeks: Sequence[WeeklyCashFlow], actual_weeks: Sequence[WeeklyCashFlow]) -> Dict[str, Any]:
    """Forecast-vs-actual by week — the real, standard treasury discipline of recalibrating a rolling forecast
    against what actually happened, rather than treating the original 13-week plan as fixed for its full life."""
    if len(forecast_weeks) != len(actual_weeks):
        raise ValueError("forecast_weeks and actual_weeks must cover the same weeks")
    rows = []
    for f, a in zip(forecast_weeks, actual_weeks):
        if f.week_ending != a.week_ending:
            raise ValueError(f"week mismatch: forecast {f.week_ending!r} vs actual {a.week_ending!r}")
        receipts_variance = a.total_receipts() - f.total_receipts()
        disbursements_variance = a.total_disbursements() - f.total_disbursements()
        rows.append({"week_ending": f.week_ending, "forecast_net": f.net(), "actual_net": a.net(),
                    "net_variance": a.net() - f.net(), "receipts_variance": receipts_variance,
                    "disbursements_variance": disbursements_variance,
                    "receipts_variance_pct": safe_div(receipts_variance, f.total_receipts()),
                    "disbursements_variance_pct": safe_div(disbursements_variance, f.total_disbursements())})
    return {"weeks": rows, "total_net_variance": sum(r["net_variance"] for r in rows),
            "mean_absolute_receipts_variance_pct": safe_div(sum(abs(r["receipts_variance_pct"]) for r in rows), len(rows)),
            "mean_absolute_disbursements_variance_pct": safe_div(sum(abs(r["disbursements_variance_pct"]) for r in rows), len(rows))}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    weeks = [WeeklyCashFlow(**w) for w in d["weeks"]]
    out: Dict[str, Any] = {"forecast": rolling_forecast(d["opening_cash"], weeks, d.get("min_cash_covenant"))}
    if "actual_weeks" in d:
        actual = [WeeklyCashFlow(**w) for w in d["actual_weeks"]]
        out["variance"] = variance_report(weeks[:len(actual)], actual)
    return out
