"""Collateralized Mortgage Obligations (CMOs): PSA prepayment modeling and sequential-pay tranching — the one
real, named structured-credit category `docs/MORE_CFI_TEMPLATES.md` flagged as more specialized than the rest of
this toolkit's corporate-finance focus, but genuinely well-defined and quantitatively concrete once built.

  CPR -> SMM             — the real, standard prepayment-speed conversion: CPR (Conditional Prepayment Rate, an
                          ANNUALIZED rate) converts to SMM (Single Monthly Mortality, the rate actually applied
                          each month) via SMM = 1 − (1 − CPR)^(1/12).
  PSA benchmark          — the real, industry-standard prepayment curve (Public Securities Association, now
                          SIFMA): CPR ramps linearly from 0% to 6% over a pool's first 30 months of age, then
                          holds flat at 6% for the rest of its life — "100% PSA". Other speeds scale this whole
                          ramp/plateau by a multiple (e.g. 150% PSA ramps to, and plateaus at, 9%).
  Pool cash flows        — a standard level-payment (annuity) mortgage pool, with SMM-driven prepayment applied
                          each month to the balance remaining AFTER that month's scheduled principal — so a
                          pool that prepays faster amortizes on a shorter, front-loaded principal profile than
                          its own original amortization schedule implies.
  Sequential-pay tranche — the defining CMO structure: interest is paid pro rata to EVERY outstanding tranche on
                          its own balance every month (unlike a bankruptcy waterfall, junior tranches keep
                          getting paid interest even while senior principal is still outstanding), but ALL
                          principal (scheduled + prepaid) cascades to the most senior tranche with a remaining
                          balance until it's fully retired, only then moving to the next — concentrating
                          prepayment risk unevenly, the entire reason a CMO exists rather than just selling
                          pro-rata pass-through certificates.
  Weighted Average Life  — the real, standard summary statistic (in years) per tranche, and the number every
                          real CMO offering document's PSA-speed sensitivity table is built around: a senior
                          tranche's WAL is short and prepayment-insensitive; a junior/support tranche's WAL is
                          long and highly sensitive to the assumed PSA speed."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def cpr_to_smm(cpr: float) -> float:
    return 1 - (1 - cpr) ** (1 / 12)


def psa_cpr_schedule(months: int, psa_pct: float = 1.0) -> List[float]:
    """month 1..months, pool age in months. 100% PSA (psa_pct=1.0) ramps CPR linearly 0.2%/month up to 6% at
    month 30, then holds flat at 6%; other speeds scale that same ramp/plateau by `psa_pct`."""
    return [min(m, 30) * 0.002 * psa_pct for m in range(1, months + 1)]


def level_payment(principal: float, monthly_rate: float, term_months: int) -> float:
    if monthly_rate == 0:
        return principal / term_months
    return principal * monthly_rate / (1 - (1 + monthly_rate) ** (-term_months))


def pool_cash_flows(principal: float, annual_rate: float, term_months: int, psa_pct: float = 1.0) -> List[Dict[str, Any]]:
    """A standard level-payment mortgage pool's monthly cash flows, with PSA-driven prepayment applied to the
    balance remaining after that month's scheduled principal (the real, standard MBS cash-flow convention)."""
    monthly_rate = annual_rate / 12
    payment = level_payment(principal, monthly_rate, term_months)
    cpr_schedule = psa_cpr_schedule(term_months, psa_pct)
    balance = float(principal)
    rows: List[Dict[str, Any]] = []
    for m in range(1, term_months + 1):
        if balance <= 1e-8:
            break
        beginning_balance = balance
        interest = beginning_balance * monthly_rate
        scheduled_principal = min(beginning_balance, max(0.0, payment - interest))
        smm = cpr_to_smm(cpr_schedule[m - 1])
        prepayment = (beginning_balance - scheduled_principal) * smm
        total_principal = min(beginning_balance, scheduled_principal + prepayment)
        balance = beginning_balance - total_principal
        rows.append({"month": m, "beginning_balance": beginning_balance, "interest": interest,
                     "scheduled_principal": scheduled_principal, "prepayment": prepayment,
                     "total_principal": total_principal, "ending_balance": balance})
    return rows


def sequential_pay_tranches(cash_flows: Sequence[Dict[str, Any]], tranche_balances: Dict[str, float], annual_rate: float) -> Dict[str, List[Dict[str, Any]]]:
    """tranche_balances: an ORDERED mapping {name: original_balance}, most senior first (Python dicts preserve
    insertion order). Interest accrues pro rata on each tranche's own balance every month; principal cascades
    strictly in priority order, so a junior tranche sees zero principal until every tranche senior to it has
    been fully retired."""
    monthly_rate = annual_rate / 12
    names = list(tranche_balances.keys())
    balances = {name: float(bal) for name, bal in tranche_balances.items()}
    schedules: Dict[str, List[Dict[str, Any]]] = {name: [] for name in names}
    for row in cash_flows:
        remaining_principal = row["total_principal"]
        for name in names:
            beginning_balance = balances[name]
            interest = beginning_balance * monthly_rate
            principal_paid = min(beginning_balance, remaining_principal) if beginning_balance > 0 else 0.0
            remaining_principal -= principal_paid
            balances[name] = beginning_balance - principal_paid
            schedules[name].append({"month": row["month"], "beginning_balance": beginning_balance, "interest": interest,
                                    "principal": principal_paid, "ending_balance": balances[name]})
    return schedules


def weighted_average_life(schedule: Sequence[Dict[str, Any]]) -> float:
    """WAL, in years: the principal-weighted average time to repayment — the real, standard tranche-comparison
    statistic (short and stable for a senior tranche, long and PSA-sensitive for a junior/support tranche)."""
    total_principal = sum(r["principal"] for r in schedule)
    if total_principal <= 0:
        return 0.0
    return sum((r["month"] / 12) * r["principal"] for r in schedule) / total_principal


def cmo_deal(principal: float, annual_rate: float, term_months: int, psa_pct: float, tranches: Dict[str, float]) -> Dict[str, Any]:
    cash_flows = pool_cash_flows(principal, annual_rate, term_months, psa_pct)
    schedules = sequential_pay_tranches(cash_flows, tranches, annual_rate)
    wal = {name: weighted_average_life(sched) for name, sched in schedules.items()}
    return {"pool_cash_flows": cash_flows, "tranche_schedules": schedules, "weighted_average_life": wal, "psa_pct": psa_pct}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "cmo_deal" in d:
        out["cmo_deal"] = cmo_deal(**d["cmo_deal"])
    if "psa_sensitivity" in d:
        p = d["psa_sensitivity"]
        results = {}
        for psa in p["psa_speeds"]:
            deal = cmo_deal(p["principal"], p["annual_rate"], p["term_months"], psa, p["tranches"])
            results[f"{psa:.0%} PSA"] = deal["weighted_average_life"]
        out["psa_sensitivity"] = results
    return out
