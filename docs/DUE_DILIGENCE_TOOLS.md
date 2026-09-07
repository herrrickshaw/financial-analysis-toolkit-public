# Due-diligence tools: three real fixes from reviewing an actual third-party model, generalized

Unlike the rest of this toolkit's additions (built from CFI/BIWS/Big 4 template surveys), this pass came from a
different direction: a real, external, CFI-formatted project-finance model (a 10-year LNG-bunkering term-loan
facility, reviewed at the user's request) surfaced three genuine issues by hand — a double-counted tax shield in
its DCF, an implausible front-loaded volume ramp, and a debt structure the model couldn't natively represent
(interest-only with a bullet repayment). Each fix generalizes past that one file into a reusable, tested tool.

## 1. `finmodel.dcf.check_unlevered_tax_consistency()` — catches a real, easy-to-miss DCF bug

The reviewed model's "Free cash flow" line correctly excluded interest expense (a proper unlevered build) but
deducted the company's REAL cash tax bill — computed on Earnings Before Taxes, i.e. after deducting interest —
rather than a hypothetical unlevered tax (EBIT taxed directly). Discounting that cash flow at a WACC which
*also* carries an after-tax cost of debt term double-counts the interest tax shield: once via lower taxes in the
numerator, once via the discount rate in the denominator. Quantified on the real file: a $41,716 shield, ~1.1%
of enterprise value — small here, but the same mistake scales with leverage and doesn't announce itself; nothing
looks wrong until you trace where the tax figure in the FCF line actually comes from.

`unlevered_tax_schedule()` builds the correct tax line (EBIT taxed directly, with its own independent loss-
carryforward chain — real NOLs are tracked on EBIT, not EBIT-less-interest). `check_unlevered_tax_consistency()`
compares it against whatever tax figure a model's FCF build actually uses and flags the gap, verified against the
real reference case above (reconstructs the exact $41,716 finding) and against a correctly-built unlevered case
(reports no gap at all).

```bash
finmodel dcf-diagnostics examples/dcf_diagnostics_demo.json
```

## 2. `finmodel.fin.smooth_ramp()` — replaces an implausible ramp with a constant-CAGR path

The reviewed model's marine-bunkering volume assumption jumped 264% in a single year (year 1 to year 2), then
decelerated toward a plateau — a real, common artifact of building a ramp year-by-year in a spreadsheet without
checking the growth-rate SHAPE it implies. `smooth_ramp(start, plateau, periods)` replaces that with a constant
compound growth rate connecting the same two endpoints (snapped exactly onto the plateau to avoid rounding
drift), verified against the real fixed case (5,000 → 47,303 over 5 years becomes a steady ~56.7%/yr instead of
one outlier spike). Not LNG-specific — the same shape problem shows up in any new-capacity or new-cohort ramp
assumption (`finmodel.startup_model`, `finmodel.cohort_analysis`), which is why this lives in `finmodel.fin`
alongside the other general financial-math primitives (`cagr`, `pmt`, `xirr`) rather than in a sector module.

A real, related lesson from the same fix, not (yet) automated: smoothing a volume ramp down in the early years
without also revisiting a dependent cost assumption calibrated to the OLD, faster ramp can flip a real business
case into an artificial multi-year loss. The reviewed model's own operating-expense schedule had to be
re-derived from its own implied opex/revenue ratio applied to the new volumes — a reminder that `smooth_ramp()`
fixes one assumption, not the whole dependency chain around it.

## 3. `finmodel.project_finance` — interest-only/bullet debt, and a structure comparison tool

The reviewed facility's real, actual lender terms (interest-only annual payments, a single bullet principal
repayment at maturity) had no equivalent in this module, which only supported a DSCR-sculpted structure.
`level_annuity_schedule()` (the standard corporate-loan baseline) and `interest_only_bullet_schedule()` (real,
standard shorter-facility/refinancing-expected terms) fill that gap. `balloon_coverage_ratio()` answers the real
question a bullet structure raises that a standalone DSCR reading can't: does cash actually ACCUMULATED over the
interest-only years cover the bullet on its own, without assuming refinancing — verified on the real file's own
figures (a 2.53x real coverage ratio, from real accumulated cash of $2.53M against a $1M bullet).

`compare_debt_structures()` runs the SAME project cash flow through all three structures side by side — the
real trade-off a borrower and lender negotiate over, quantified rather than argued in the abstract: DSCR-
sculpting costs the least total interest (fastest paydown at the covenant), interest-only/bullet costs the most
(the full balance keeps accruing interest for the whole tenure) but frees up the most near-term cash, with a
level annuity in between — verified on the real reference case that this ordering holds.

```bash
finmodel project-finance examples/project_finance_demo.json   # now includes compare_debt_structures
```

## Sources

Every figure above is a real, verified result from this toolkit's own review of an actual third-party financial
model — not a hypothetical or invented case. The `dcf_diagnostics_demo.json` and the `compare_debt_structures`
block in `project_finance_demo.json` reproduce that real model's own numbers exactly.
