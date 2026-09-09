"""Sample sector/state-level investment financial models: assembling a project's land cost and capex stack,
then netting it against a combined central+state incentive package -- the "precursor calculation" an
investor would sanity-check before commissioning a full feasibility study. No prior representation across
the toolkit's other ~60 modules.

A defensible "effective investment after incentives" figure has to respect WHEN each incentive arrives, not
just sum rupee amounts across schemes of very different timing:

  * An UPFRONT incentive (a capital subsidy disbursed at or shortly after commissioning) reduces capex
    directly -- a day-zero cash inflow against a day-zero cash outflow, no discounting needed.
  * A RECURRING incentive (an interest subsidy, a net-tax reimbursement, an employment subsidy, or a PLI
    payout) arrives across future years. Summing an undiscounted multi-year stream and subtracting it from
    day-zero capex overstates its real value -- a real, common modeling mistake. This module discounts every
    recurring stream to a present value with `finmodel.fin.npv` (Excel-NPV convention: the first supplied
    cash flow is discounted one full period) before netting it against capex, and reports the NOMINAL
    (undiscounted) total alongside the present-value total so the size of that overstatement is visible
    rather than hidden.

This module builds the land-cost and capex-assembly layer and calls `finmodel.investment_incentives` for the
incentive aggregation itself (`combined_incentive_package`) rather than re-implementing it.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import npv, safe_div
from .investment_incentives import combined_incentive_package


def industrial_land_cost(area_acres: float, rate_per_acre: float) -> Dict[str, Any]:
    land_cost = area_acres * rate_per_acre
    return {"area_acres": area_acres, "rate_per_acre": rate_per_acre, "land_cost": land_cost}


def leasehold_land_cost(area_acres: float, base_annual_rent_per_acre: float, lease_term_years: int,
                        discount_rate: float, discount_schedule: Sequence[Dict[str, Any]] = ()) -> Dict[str, Any]:
    """Capitalizes a LEASEHOLD land arrangement -- an ongoing annual rent, not a one-time purchase/lease
    premium -- into a present-value figure comparable to `industrial_land_cost`'s one-time cost, so it can
    feed the same capex stack without misrepresenting a recurring obligation as a day-zero capital outlay
    (the exact confusion this function exists to avoid; see docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md's
    Andaman & Nicobar Islands entry, whose rate is confirmed as annual rent, not a purchase premium).

    `discount_schedule`: an optional list of `{"through_year": int, "rent_discount_pct": float}` entries,
    checked in order -- the first entry whose `through_year` is >= the current lease year sets that year's
    discount off the base rent; years beyond every entry pay the full base rent. This mirrors a real,
    confirmed structure (A&N's own estates: 50% discount for years 1-15, 25% discount for years 16-25, full
    rate thereafter)."""
    annual_rents: List[float] = []
    for year in range(1, lease_term_years + 1):
        discount_pct = 0.0
        for entry in discount_schedule:
            if year <= entry["through_year"]:
                discount_pct = entry["rent_discount_pct"]
                break
        annual_rents.append(base_annual_rent_per_acre * area_acres * (1 - discount_pct))
    capitalized_cost = npv(discount_rate, annual_rents)
    return {"area_acres": area_acres, "base_annual_rent_per_acre": base_annual_rent_per_acre,
            "lease_term_years": lease_term_years, "annual_rent_schedule": annual_rents,
            "nominal_total_rent": sum(annual_rents), "capitalized_cost": capitalized_cost,
            # aliased so this result can drop straight into sample_project_model's `land["land_cost"]` usage,
            # same as industrial_land_cost's one-time figure -- no special-casing needed downstream
            "land_cost": capitalized_cost}


def project_capex_stack(components: Dict[str, float]) -> Dict[str, Any]:
    """`components`: e.g. {"land": 20.0, "plant_and_machinery": 40.0, "building_and_infrastructure": 10.0}."""
    total_capex = sum(components.values())
    return {"components": dict(components), "total_capex": total_capex}


def incentive_present_value(components: Sequence[Dict[str, Any]], discount_rate: float) -> Dict[str, Any]:
    """Each component carries `timing`: "upfront" (an `amount`, netted at face value -- the default when
    `timing` is omitted, matching a lump-sum capital subsidy) or "recurring" (an `annual_amounts` cash-flow
    list, discounted via `finmodel.fin.npv`). Returns both the present-value total (used for netting against
    capex) and the nominal (undiscounted) total via `finmodel.investment_incentives.combined_incentive_package`,
    so the gap between the two is visible."""
    normalized_for_nominal_total: List[Dict[str, Any]] = []
    detail: List[Dict[str, Any]] = []
    upfront_value = 0.0
    pv_of_recurring = 0.0
    for c in components:
        timing = c.get("timing", "upfront")
        if timing == "recurring":
            nominal = sum(c["annual_amounts"])
            pv = npv(discount_rate, c["annual_amounts"])
            pv_of_recurring += pv
            detail.append({"scheme_name": c["scheme_name"], "jurisdiction": c["jurisdiction"], "timing": timing,
                           "nominal_total": nominal, "present_value": pv, "annual_amounts": list(c["annual_amounts"])})
            normalized_for_nominal_total.append({"scheme_name": c["scheme_name"], "jurisdiction": c["jurisdiction"],
                                                 "amount": nominal})
        else:
            upfront_value += c["amount"]
            detail.append({"scheme_name": c["scheme_name"], "jurisdiction": c["jurisdiction"], "timing": timing,
                           "nominal_total": c["amount"], "present_value": c["amount"]})
            normalized_for_nominal_total.append({"scheme_name": c["scheme_name"], "jurisdiction": c["jurisdiction"],
                                                 "amount": c["amount"]})
    nominal_package = combined_incentive_package(normalized_for_nominal_total)
    return {"upfront_value": upfront_value, "pv_of_recurring": pv_of_recurring,
            "total_present_value": upfront_value + pv_of_recurring,
            "nominal_total": nominal_package["total_incentive_value"],
            "by_jurisdiction_nominal": nominal_package["by_jurisdiction"],
            "by_scheme_nominal": nominal_package["by_scheme"], "detail": detail}


def sample_project_model(state: str, sector: str, land: Dict[str, Any], capex_components: Dict[str, float],
                         incentive_components: Sequence[Dict[str, Any]], discount_rate: float,
                         note: str = "") -> Dict[str, Any]:
    capex = project_capex_stack({**capex_components, "land": land["land_cost"]})
    incentives = incentive_present_value(incentive_components, discount_rate)
    net_effective_investment = capex["total_capex"] - incentives["total_present_value"]
    result = {"state": state, "sector": sector, "land": land, "capex": capex, "incentives": incentives,
              "net_effective_investment": net_effective_investment,
              "effective_subsidy_pct_pv_basis": safe_div(incentives["total_present_value"], capex["total_capex"])}
    if note:
        result["note"] = note
    return result


def _land_cost_from_spec(land_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Dispatches a raw land spec to `industrial_land_cost` (default, a one-time purchase/lease premium) or
    `leasehold_land_cost` (when `land_spec["land_type"] == "leasehold"`, an ongoing annual rent that needs
    capitalizing first) -- so callers can mix both land types across a matrix without special-casing."""
    spec = dict(land_spec)
    land_type = spec.pop("land_type", "purchase")
    if land_type == "leasehold":
        return leasehold_land_cost(**spec)
    return industrial_land_cost(**spec)


def sample_project_matrix(entries: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """`entries`: a list of state/sector projects, each shaped like `sample_project_model`'s own arguments
    except `land` is the RAW land spec (this function builds the land cost itself, via
    `_land_cost_from_spec` -- either a one-time `{"area_acres", "rate_per_acre"}` purchase, or, when
    `land["land_type"] == "leasehold"`, an annual-rent spec for `leasehold_land_cost`) and an optional `note`
    carries any data-confidence caveat through to that entry's result. Runs `sample_project_model` once per
    entry and sums capex and incentive present value across all of them -- the state x sector "matrix" of
    sample calculations, in one query."""
    projects: List[Dict[str, Any]] = []
    total_capex = 0.0
    total_incentive_pv = 0.0
    for e in entries:
        land = _land_cost_from_spec(e["land"])
        r = sample_project_model(state=e["state"], sector=e["sector"], land=land,
                                 capex_components=e["capex_components"], incentive_components=e["incentive_components"],
                                 discount_rate=e["discount_rate"], note=e.get("note", ""))
        projects.append(r)
        total_capex += r["capex"]["total_capex"]
        total_incentive_pv += r["incentives"]["total_present_value"]
    return {"projects": projects, "total_capex_across_projects": total_capex,
            "total_incentive_present_value_across_projects": total_incentive_pv}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "industrial_land_cost" in d:
        out["industrial_land_cost"] = industrial_land_cost(**d["industrial_land_cost"])
    if "leasehold_land_cost" in d:
        out["leasehold_land_cost"] = leasehold_land_cost(**d["leasehold_land_cost"])
    if "project_capex_stack" in d:
        out["project_capex_stack"] = project_capex_stack(d["project_capex_stack"])
    if "incentive_present_value" in d:
        p = d["incentive_present_value"]
        out["incentive_present_value"] = incentive_present_value(p["components"], p["discount_rate"])
    if "sample_project_model" in d:
        p = d["sample_project_model"]
        land = _land_cost_from_spec(p["land"])
        out["sample_project_model"] = sample_project_model(state=p["state"], sector=p["sector"], land=land,
                                                            capex_components=p["capex_components"],
                                                            incentive_components=p["incentive_components"],
                                                            discount_rate=p["discount_rate"], note=p.get("note", ""))
    if "sample_project_matrix" in d:
        out["sample_project_matrix"] = sample_project_matrix(d["sample_project_matrix"])
    return out
