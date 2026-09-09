# Project bankability and investability ranking

`finmodel.project_bankability` — ranks state/sector investability by IRR, ROI, and payback, computed both
with and without incentives, and flags the specific projects that incentives make *bankable* rather than
merely cheaper.

## The real point: incentives can change whether a project clears the bar, not just how much it costs

`finmodel.sector_investment_model` already nets incentives against capex correctly by timing (upfront vs.
present-valued recurring). This module goes one step further: it puts an assumed operating cash flow behind
each project and asks the question a lender or investment committee actually asks — **does this clear our
hurdle rate?** — twice: once on the project's own capex and cash flow alone, and once with the incentive cash
flows (still correctly timed: an upfront subsidy reduces the day-zero outflow, a recurring incentive like a
PLI payout or a net-tax reimbursement adds to the relevant future year's cash flow, taken directly from
`sector_investment_model.incentive_present_value`'s own per-year `annual_amounts` — never re-assumed here).

`rank_projects` sorts a list of state/sector projects by IRR twice (without and with incentives) and computes
one more thing neither ranking shows on its own: **`incentive_enabled_projects`** — every project whose IRR
is below the hurdle rate on its own merits but clears it once incentives are added. That is the literal
answer to "how do lower-feasibility projects become more feasible with incentives" — not a vague statement
that incentives help, but the specific list of which projects cross the specific line.

## Worked example: the 28-state matrix

`examples/project_bankability_demo.json` runs this over the same 28-state matrix from
`docs/INDIA_STATE_SECTOR_INCENTIVE_MATRIX.md`, holding one more thing constant across every state for
comparability: an illustrative annual operating cash flow of ₹7.6 crore (20% of the ₹38cr non-land FCI used
throughout that matrix — a flat assumption, not a real revenue forecast for any of these sectors), a 10-year
project life, and an illustrative 14% hurdle rate (a common corporate WACC-range assumption, not sourced for
any specific state or lender). Run via `finmodel project-bankability examples/project_bankability_demo.json`.

**Highest ROI without any government support: Chhattisgarh (15.1% IRR)** now tops the ranking — not from any
incentive, but because its land is confirmed policy-subsidized to near-zero (100% land-premium exemption
under IDP 2024-30). Tamil Nadu (14.1%) and Jammu & Kashmir (12.6%) follow. This is the clearest illustration
yet that land-cost policy can matter as much as, or more than, capital incentives — Chhattisgarh's ranking
is a pure capex-efficiency story. (Tamil Nadu's spot should still be read alongside the caveat already
flagged in `docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md`: its land rate is anomalously low.)

**Projects incentives make bankable, not just cheaper:** at a 14% hurdle, **Gujarat** (4.8% → 23.6%),
**Odisha** (10.6% → 25.5%), **Karnataka** (12.2% → 18.9%), and now **Jharkhand** (9.9% → 15.5%, on its
confirmed 25%-of-FCI capital subsidy) all cross from unbankable to comfortably bankable. Every other state's
IRR improves with incentives too (incentives never make IRR worse, by construction — the test suite checks
this directly).

**The two worst entries in the entire matrix, on every measure at once, remain Delhi and Chandigarh** — the
highest and third-highest land costs of all 28 states/UTs (₹42.54cr/acre and ₹30.30cr/acre) *and* zero
state-tier incentive to offset it. **Jammu & Kashmir adds a new, distinct story**: real land cost, a
genuinely rich central scheme on paper (NCSS 2021, ₹28,400cr) — but its registration window for new
applicants closed 30.09.2024, so its incentive value here is also zero, despite the scheme being far from
absent in the way Delhi/Chandigarh's is. **Ladakh** likewise shows zero incentive, but for yet another
reason — its own UT policy was keyword-searched directly and confirmed to have no capital/interest/GST
mechanic at all, even though it has the best-sourced (and lowest) land rate in the whole matrix.

**This ranking is exactly as reliable as its two illustrative inputs** (the flat assumed cash flow and the
hurdle rate) **and exactly as reliable as each state's own incentive-catalog confidence** (see
`docs/INDIA_STATE_SECTOR_INCENTIVE_MATRIX.md`'s per-state notes for which land rates and scheme rates are
confirmed vs. illustrative placeholders). Change either assumption and the ranking — especially which
projects fall in `incentive_enabled_projects` — will shift; the value of this module is the calculation
machinery and the specific insight it surfaces, not these particular numbers as investment advice.

## DSCR: the covenant a lender actually tests

IRR answers "is this a good investment"; it doesn't answer the narrower, more concrete question a lender
asks before disbursing a loan: **is operating cash flow enough to cover this year's loan repayment, by the
required margin?** `debt_service_coverage_ratio` computes exactly that — annual debt service via
`finmodel.fin.pmt`'s amortization math, and the ratio of cash flow to that debt service against a minimum
covenant. Real lender terms differ in an important way this function is built to respect: IREDA (for
renewable-energy projects) publishes an explicit, dated DSCR schedule (1.2x–1.4x by sector and loan
structure); SBI and REC disclose no DSCR floor at all for general project finance, so a 1.20x–1.25x figure
used for those cases is a general industry convention, not a specific lender's disclosed number.
`docs/INDIA_PROJECT_FINANCE_LENDING_TERMS.md` catalogs exactly which is which, with sourcing and staleness
flags (REC's own published rate card is ~3 years old).

Run over the same 28-state matrix against the generic SBI/REC-style case (70% debt:equity, an illustrative
10.5% rate, 1.20x minimum DSCR, using only *operating* cash flow — not incentive income — as the
conservative bank-side view) via `examples/dscr_matrix_demo.json`: **Chhattisgarh, Tamil Nadu, Jammu &
Kashmir, Puducherry, Karnataka, Ladakh, Goa, Odisha, West Bengal, Jharkhand, Uttar Pradesh, Madhya Pradesh,
Kerala, Uttarakhand, and Andaman & Nicobar Islands** — 15 of 28 — clear the covenant. This is a genuinely
different, complementary question to the IRR-based bankability above: J&K and Ladakh both clear DSCR
comfortably despite showing zero incentive value in the IRR ranking (a project can be "bankable" in the
narrow debt-service sense purely on its own land cost and cash flow, independent of whether any incentive
exists to support it), while a project can have an attractive IRR-with-incentives and still fail a lender's
DSCR test if the bank won't credit that incentive income toward debt service. Andaman & Nicobar Islands
clears comfortably too (1.411x) — its leasehold land cost, capitalized rather than purchased, still nets to
a modest enough capex that operating cash flow alone covers debt service, even with zero incentive support.
Delhi and Chandigarh remain the two worst DSCR results in the matrix (0.141x and 0.192x) — their extreme
land cost alone makes debt service on 70% leverage essentially impossible at this illustrative cash-flow
level.

## Beyond capital incentives: tax election and loan-access effects

Two further mechanics change a project's real bankability beyond the capital incentives and generic DSCR
covenant above, both in `finmodel.india_corporate_tax_regimes` (see
`docs/INDIA_CORPORATE_TAX_AND_CGTMSE.md`): a new manufacturer's Section 115BAB vs 115BAA vs standard-regime
tax election (a 3.88-percentage-point IRR swing on Gujarat's own project, purely from which regime is
elected) and the CGTMSE guarantee fee's real, small effect on DSCR (a boundary case that clears 1.20x on
debt service alone but breaches it once the fee is added — CGTMSE's actual value is loan access without
adequate collateral, not a free DSCR improvement). And `examples/dscr_matrix_ireda_demo.json` (see
`docs/INDIA_PROJECT_FINANCE_LENDING_TERMS.md`) finally exercises IREDA's own disclosed renewable-energy
terms instead of the generic SBI/REC case — a Rajasthan solar and Gujarat wind project both clear a
comfortable 2.195x against IREDA's own 1.25x floor, a direct illustration of how much sector-specific lender
matching changes the answer.

## Test coverage

`tests/test_project_bankability.py` (8 tests, new file) checks `annual_incentive_cashflow`'s year-by-year
summation by hand, verifies both IRR values the rigorous way — by reconstructing each cash-flow stream
independently and confirming its NPV at the module's own returned IRR is ~0, the literal definition of an
internal rate of return, rather than trusting a hand-typed decimal — checks the simple ROI/payback formulas
by hand, checks `rank_projects`' sorting and its incentive-enabled flagging against a 3-project scenario
designed so exactly one project crosses the hurdle only with incentives, and checks
`debt_service_coverage_ratio` against an independently-written annuity formula (not the module's own `pmt()`
call) at both a compliant and a non-compliant covenant threshold. `tests/test_cli.py` adds CLI round-trip
tests against the full 18-state IRR ranking (including the invariant that IRR-with-incentives is never below
IRR-without for any project) and the 18-state DSCR matrix.
