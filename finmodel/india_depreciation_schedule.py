"""finmodel.india_depreciation_schedule: Income Tax Act 1961 written-down-value (WDV) depreciation,
computed by BLOCK OF ASSETS (Income-tax Rules 1962, New Appendix I -- rates rationalized/capped at 40% by
Finance Act 2017), plus the additional depreciation new manufacturing/power-generation plant & machinery gets
under section 32(1)(iia). No prior representation across the toolkit's other modules: `.INDIA_CORPORATE_TAX_REGIMES`
explicitly notes that a 115BAB/115BAA elector forgoes additional depreciation, but nothing in this toolkit
actually computed a depreciation schedule under any regime until now.

Block-of-assets mechanics (section 32), not asset-by-asset mechanics:
  * All assets of the same class and depreciation rate form one "block". Depreciation is charged on the
    BLOCK's written-down value, not on individual assets -- so an addition and a deletion within the same
    block in the same year net against each other before the rate is applied.
  * An addition put to use for 180 days or more in the year of acquisition gets the FULL rate; an addition
    used for less than 180 days gets only HALF the rate in that first year (full rate from the following
    year onward, since it then simply becomes part of the opening WDV).
  * Section 50: if sale proceeds/scrap value realized during the year (deletions) exceed the block's WDV
    before depreciation (opening WDV + full-rate additions + half-rate additions), depreciation on that block
    is NIL and the excess is a short-term capital gain -- regardless of whether every asset in the block was
    actually sold. This module computes that identity directly rather than special-casing "block emptied".

Section 32(1)(iia) additional depreciation: 20% of the actual cost of NEW plant & machinery acquired and
installed by a company engaged in manufacturing or power generation/transmission/distribution (excludes
second-hand P&M, office appliances, road transport vehicles, ships, aircraft, and any asset already eligible
for 100% first-year depreciation) -- halved to 10% if put to use for less than 180 days in the year of
acquisition, with the balance 10% allowed in full in the IMMEDIATELY SUCCEEDING year (added by Finance Act
2015, effective AY 2016-17). This is IN ADDITION TO, not instead of, normal WDV depreciation on the same
asset.

Not modeled here: additional depreciation is unavailable to a 115BAB/115BAA elector (see
`docs/INDIA_CORPORATE_TAX_AND_CGTMSE.md`); this module computes the mechanic itself and leaves the
regime-eligibility gating to the caller. Also not modeled: 100%-first-year-depreciation categories (e.g.
certain pollution-control/energy-saving devices), and MAT/book-depreciation differences -- both out of this
module's scope for the same reason `india_corporate_tax_regimes` excludes MAT (no book-income visibility).
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div

# Income-tax Rules 1962, New Appendix I (post Finance Act 2017 rationalization, highest rate capped at 40%).
WDV_RATES: Dict[str, float] = {
    "building_residential": 0.05,
    "building_general": 0.10,
    "building_temporary_structure": 0.40,
    "furniture_and_fittings": 0.10,
    "plant_and_machinery_general": 0.15,
    "motor_vehicles_general": 0.15,
    "motor_vehicles_used_in_hire_business": 0.30,
    "computers_and_computer_software": 0.40,
    "intangible_assets": 0.25,  # know-how, patents, copyrights, trademarks, licences, franchises
}

ADDITIONAL_DEPRECIATION_RATE = 0.20         # sec 32(1)(iia), full rate (used >= 180 days)
ADDITIONAL_DEPRECIATION_HALF_RATE = 0.10    # used < 180 days in year of acquisition; balance carried forward


def block_depreciation(opening_wdv: float, rate: float, full_rate_additions: float = 0.0,
                       half_rate_additions: float = 0.0, deletions: float = 0.0) -> Dict[str, Any]:
    """One block, one year. `full_rate_additions` = new assets used >= 180 days this year;
    `half_rate_additions` = new assets used < 180 days this year; `deletions` = sale/scrap proceeds
    realized on assets transferred out of this block this year (not book cost -- what section 50 actually
    tests against is the money received)."""
    wdv_before_depreciation = opening_wdv + full_rate_additions + half_rate_additions - deletions
    if wdv_before_depreciation <= 0:
        short_term_capital_gain = -wdv_before_depreciation
        return {"depreciation": 0.0, "closing_wdv": 0.0,
                "short_term_capital_gain": short_term_capital_gain, "block_extinguished": True}
    # deletions are applied against the full-rate portion first (opening WDV + full-rate additions);
    # only a shortfall beyond that eats into the half-rate portion.
    full_rate_base = opening_wdv + full_rate_additions - deletions
    if full_rate_base < 0:
        shortfall = -full_rate_base
        full_rate_base = 0.0
        half_rate_base = max(half_rate_additions - shortfall, 0.0)
    else:
        half_rate_base = half_rate_additions
    depreciation_on_full_rate_base = full_rate_base * rate
    depreciation_on_half_rate_base = half_rate_base * (rate / 2)
    total_depreciation = depreciation_on_full_rate_base + depreciation_on_half_rate_base
    closing_wdv = wdv_before_depreciation - total_depreciation
    return {"depreciation": total_depreciation, "closing_wdv": closing_wdv,
            "short_term_capital_gain": 0.0, "block_extinguished": False}


def multi_year_block_schedule(opening_wdv: float, rate: float,
                              yearly_additions: Sequence[Sequence[Dict[str, Any]]],
                              yearly_deletions: Sequence[float] = ()) -> Dict[str, Any]:
    """`yearly_additions[year]` is a list of {"amount": ..., "used_180_days_or_more": bool} for that year's
    new assets in this block (all additions from a prior year are already folded into that year's closing
    WDV, so only the CURRENT year's own new additions go here). `yearly_deletions[year]` is that year's sale
    proceeds, defaulting to 0.0 for any year not supplied."""
    deletions = list(yearly_deletions) + [0.0] * (len(yearly_additions) - len(yearly_deletions))
    rows: List[Dict[str, Any]] = []
    wdv = opening_wdv
    for year, additions in enumerate(yearly_additions, start=1):
        full = sum(a["amount"] for a in additions if a.get("used_180_days_or_more", True))
        half = sum(a["amount"] for a in additions if not a.get("used_180_days_or_more", True))
        result = block_depreciation(wdv, rate, full_rate_additions=full, half_rate_additions=half,
                                    deletions=deletions[year - 1])
        rows.append({"year": year, "opening_wdv": wdv, **result})
        wdv = result["closing_wdv"]
    return {"rows": rows, "final_closing_wdv": wdv,
            "total_depreciation": sum(r["depreciation"] for r in rows),
            "total_short_term_capital_gain": sum(r["short_term_capital_gain"] for r in rows)}


def additional_depreciation_sec32_1_iia(new_plant_and_machinery_cost: float,
                                        used_180_days_or_more: bool = True) -> Dict[str, Any]:
    if used_180_days_or_more:
        return {"current_year": new_plant_and_machinery_cost * ADDITIONAL_DEPRECIATION_RATE,
                "carried_forward_to_next_year": 0.0,
                "total": new_plant_and_machinery_cost * ADDITIONAL_DEPRECIATION_RATE}
    current_year = new_plant_and_machinery_cost * ADDITIONAL_DEPRECIATION_HALF_RATE
    return {"current_year": current_year, "carried_forward_to_next_year": current_year,
            "total": new_plant_and_machinery_cost * ADDITIONAL_DEPRECIATION_RATE}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "block_depreciation" in d:
        out["block_depreciation"] = block_depreciation(**d["block_depreciation"])
    if "multi_year_block_schedule" in d:
        p = d["multi_year_block_schedule"]
        out["multi_year_block_schedule"] = multi_year_block_schedule(
            p["opening_wdv"], p["rate"], p["yearly_additions"], p.get("yearly_deletions", ()))
    if "additional_depreciation_sec32_1_iia" in d:
        out["additional_depreciation_sec32_1_iia"] = additional_depreciation_sec32_1_iia(
            **d["additional_depreciation_sec32_1_iia"])
    return out
