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

## Worked example: the 12-state matrix

`examples/project_bankability_demo.json` runs this over the same 12-state matrix from
`docs/INDIA_STATE_SECTOR_INCENTIVE_MATRIX.md`, holding one more thing constant across every state for
comparability: an illustrative annual operating cash flow of ₹7.6 crore (20% of the ₹38cr non-land FCI used
throughout that matrix — a flat assumption, not a real revenue forecast for any of these sectors), a 10-year
project life, and an illustrative 14% hurdle rate (a common corporate WACC-range assumption, not sourced for
any specific state or lender). Run via `finmodel project-bankability examples/project_bankability_demo.json`.

**Highest ROI without any government support:** Tamil Nadu (Textiles & Apparel, 14.1% IRR) and Odisha
(General Manufacturing, 10.6% IRR) lead purely on low land cost — this is largely their capex efficiency
showing through, not incentive generosity. (Tamil Nadu's #1 spot should be read alongside the caveat already
flagged in `docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md`: its land rate is anomalously low compared to
every other state and may not be a like-for-like comparison.)

**Projects incentives make bankable, not just cheaper:** at a 14% hurdle, **Gujarat** (4.8% IRR on its own
economics → 23.6% with its confirmed net-SGST-reimbursement scheme and the central Auto PLI) and **Odisha**
(10.6% → 25.5% with its confirmed 100%-of-net-SGST, 200%-of-P&M-cap reimbursement) both cross from
unbankable to comfortably bankable. Every other state's IRR improves with incentives too (incentives never
make IRR worse, by construction — the test suite checks this directly), but Karnataka, Andhra Pradesh, Madhya
Pradesh, Telangana, Maharashtra, Haryana, Rajasthan, and Punjab all remain below the illustrative hurdle even
after incentives, in this particular illustrative scenario — their capex (chiefly land cost) or their
confirmed incentive parameters aren't strong enough to close the gap at these assumed cash-flow and hurdle
levels.

**This ranking is exactly as reliable as its two illustrative inputs** (the flat assumed cash flow and the
hurdle rate) **and exactly as reliable as each state's own incentive-catalog confidence** (see
`docs/INDIA_STATE_SECTOR_INCENTIVE_MATRIX.md`'s per-state notes for which land rates and scheme rates are
confirmed vs. illustrative placeholders). Change either assumption and the ranking — especially which
projects fall in `incentive_enabled_projects` — will shift; the value of this module is the calculation
machinery and the specific insight it surfaces, not these particular numbers as investment advice.

## Test coverage

`tests/test_project_bankability.py` (6 tests, new file) checks `annual_incentive_cashflow`'s year-by-year
summation by hand, verifies both IRR values the rigorous way — by reconstructing each cash-flow stream
independently and confirming its NPV at the module's own returned IRR is ~0, the literal definition of an
internal rate of return, rather than trusting a hand-typed decimal — checks the simple ROI/payback formulas
by hand, and checks `rank_projects`' sorting and its incentive-enabled flagging against a 3-project scenario
designed so exactly one project crosses the hurdle only with incentives. `tests/test_cli.py` adds a CLI
round-trip test against the full 12-state ranking, including the invariant that IRR-with-incentives is never
below IRR-without for any project.
