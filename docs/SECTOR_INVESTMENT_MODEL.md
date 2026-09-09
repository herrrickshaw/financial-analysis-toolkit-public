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

`sample_project_matrix` runs `sample_project_model` across a whole list of state/sector entries and sums
capex and incentive present value across all of them — the state × sector × central/state-scheme "matrix"
requested as a precursor calculation, worked in full for 18 states/UTs in
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

`tests/test_sector_investment_model.py` (7 tests, new file) checks land cost and capex-stack arithmetic by
hand, checks `incentive_present_value` against an NPV expression written independently of the module's own
`npv()` call (not just re-deriving the same formula), checks the always-less-than-nominal property of a
discounted recurring stream, checks the full `sample_project_model` end-to-end result against a hand
calculation, and checks that `sample_project_matrix` sums correctly across entries and carries each entry's
`note` through untouched. `tests/test_cli.py` adds two CLI round-trip tests, including one against the full
18-state matrix demo file.
