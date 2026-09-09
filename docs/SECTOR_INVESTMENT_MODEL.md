# Sample state/sector investment models: land + capex + discounted incentives

`finmodel.sector_investment_model` — the "precursor calculation" layer that assembles a project's land cost
and capex stack, then nets it against a combined central+state incentive package, producing the kind of
sample number an investor would sanity-check before commissioning a full feasibility study.

## The real modeling point: incentive timing, not just incentive size

Summing incentive rupee amounts across schemes of very different timing and calling the result "total
benefit" is a common, real modeling mistake. A capital subsidy paid at commissioning and a PLI payout spread
across 5 future years are not worth the same amount per rupee:

- An **upfront** incentive (a capital subsidy) is a day-zero cash inflow against a day-zero capex outflow —
  it nets directly, no discounting needed.
- A **recurring** incentive (interest subsidy, net-tax reimbursement, employment subsidy, PLI payout) arrives
  over future years and must be discounted to a present value with `finmodel.fin.npv` before it can be
  meaningfully netted against day-zero capex. `incentive_present_value` reports the nominal (undiscounted)
  total *and* the present-value total side by side specifically so the size of that gap — and the error of
  ignoring it — is visible rather than hidden. The test suite verifies directly that a recurring stream's
  present value is always strictly less than its nominal sum at any positive discount rate.

`sample_project_model` ties this together: `industrial_land_cost` (area × per-acre rate) feeds into
`project_capex_stack` alongside plant & machinery / building costs, and `incentive_present_value` nets
against that capex total to produce `net_effective_investment` and an `effective_subsidy_pct_pv_basis`. The
incentive aggregation itself is delegated to `finmodel.investment_incentives.combined_incentive_package` —
this module builds the land/capex/timing layer around it, not a second copy of the aggregation logic.

## Land cost: purchase or leasehold

`industrial_land_cost(area_acres, rate_per_acre)` handles the common case — a one-time purchase premium.
Some jurisdictions (Andaman & Nicobar Islands is the one confirmed case in this toolkit's catalog, via
Garacharama industrial estate) allot land only on **lease at an annual rent**, never outright sale. Treating
an annual rent as if it were a one-time purchase price would misrepresent the cost by an order of magnitude
in either direction depending on the lease term, so `leasehold_land_cost(area_acres,
base_annual_rent_per_acre, lease_term_years, discount_rate, discount_schedule=())` instead **capitalizes**
the rent stream into a comparable present-value figure via `finmodel.fin.npv`, optionally applying a
year-by-year discount schedule (e.g. a promotional 50% rent discount for the first 15 years, tapering to 25%
for years 16-25, matching A&N's actual Industrial Land Allotment Policy 2023 terms). It returns
`capitalized_cost` aliased as `land_cost`, so it drops into `project_capex_stack` exactly like
`industrial_land_cost`'s output.

`_land_cost_from_spec(land_spec)` is the dispatcher: it reads an optional `"land_type"` key (`"purchase"`
default, or `"leasehold"`) off a matrix entry's `land` dict and routes to the right function, so
`sample_project_matrix` and `from_dict` can mix purchase-land and leasehold-land entries in the same matrix
without the caller needing to branch.

`sample_project_matrix` runs `sample_project_model` across a whole list of state/sector entries and sums
capex and incentive present value across all of them — the state × sector × central/state-scheme "matrix"
requested as a precursor calculation, worked in full for 28 states/UTs in
`docs/INDIA_STATE_SECTOR_INCENTIVE_MATRIX.md` and `examples/state_sector_matrix_demo.json`. Each entry can
carry an optional `note`, which the aggregator carries through untouched into that entry's own result — so a
data-confidence caveat (an unverified land rate, an assumption behind a scheme parameter) travels with the
number it qualifies, rather than living only in a separate document a caller might not read.

## On the specific numbers

Like `finmodel.investment_incentives`, this module contains no hardcoded land rates or scheme amounts. The
example (`examples/sector_investment_model_demo.json`) is fully illustrative (labeled as such) and matches
its own hand-computed test values exactly. Real land-cost benchmarks and their sourcing/confidence are
cataloged in `docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md`; the state × sector × scheme cross-reference
that ties land cost, state incentives, and central incentives together into worked sample calculations is in
`docs/INDIA_STATE_SECTOR_INCENTIVE_MATRIX.md`.

## Test coverage

`tests/test_sector_investment_model.py` (11 tests) checks land cost and capex-stack arithmetic by
hand, checks `incentive_present_value` against an NPV expression written independently of the module's own
`npv()` call (not just re-deriving the same formula), checks the always-less-than-nominal property of a
discounted recurring stream, checks the full `sample_project_model` end-to-end result against a hand
calculation, checks that `sample_project_matrix` sums correctly across entries and carries each entry's
`note` through untouched, and separately checks `leasehold_land_cost`'s year-by-year discount-schedule
application, its capitalized value against an independently-written NPV expression, its no-schedule
full-rent case, and that `sample_project_matrix` dispatches leasehold and purchase land entries side by side
via `_land_cost_from_spec`. `tests/test_cli.py` adds CLI round-trip tests, including one against the full
28-state matrix demo file (which mixes 27 purchase-land entries with one leasehold entry, Andaman & Nicobar
Islands) and a standalone one for `leasehold_land_cost` using A&N's real Garacharama rent figures
(`examples/leasehold_land_cost_demo.json`).
