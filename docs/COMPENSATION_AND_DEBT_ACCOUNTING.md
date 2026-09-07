# Stock-based compensation and bond issuer accounting

Another fresh pair, continuing from `docs/CORPORATE_ACCOUNTING_TREASURY_TOOLS.md`: stock-based compensation
expense (ASC 718) and bond premium/discount amortization (ASC 835-30). Both are real, common corporate
accounting mechanics that had no representation across the toolkit's other ~50 modules, checked against what
already exists before being built.

| New module | Real technique | Checked against, and confirmed distinct from |
|---|---|---|
| `finmodel.stock_based_compensation` | ASC 718 RSU and stock-option grant expense: grant-date fair value (reusing `finmodel.options.black_scholes` directly for options rather than reimplementing option pricing) and the two real expense-attribution methods (straight-line vs. graded/accelerated) | `finmodel.cap_table` (VC/PE cap-table dilution and exit waterfalls — a financing-round lens, not a compensation-expense lens on the SAME instrument type) |
| `finmodel.bond_amortization` | Effective-interest bond premium/discount amortization (ASC 835-30) — the issuer's own accounting for a bond it sold above or below face value | `finmodel.fixed_income_risk` (the investor's duration/convexity risk metrics on the SAME instrument, not the issuer's amortization accounting) |

## Real technique, and why it was built this way

- **An RSU's fair value needs no option-pricing model at all** — it is simply shares granted times the
  grant-date share price, since an RSU carries no strike price or optionality. A stock option's fair value
  DOES need an option-pricing model, so `stock_option_grant_fair_value()` calls this toolkit's own
  `finmodel.options.black_scholes` directly rather than re-deriving Black-Scholes a second time — the
  toolkit's test suite confirms the two functions produce identical results for identical inputs, proving
  it's a genuine reuse rather than a parallel, possibly-diverging implementation.
- **Straight-line and graded/accelerated vesting must expense the exact same total, but on different
  timelines** — a real, defining ASC 718 fact this module's test suite verifies directly with a hand-traced
  four-tranche example (a standard 25%/25%/25%/25% award vesting at 12/24/36/48 months): graded vesting's
  first-month expense (~$43,403) is more than double straight-line's constant $20,833/month, because every
  tranche is actively vesting in month 1, while by month 48 only the longest tranche remains, so graded
  vesting's expense there ($5,208) is well BELOW the straight-line constant — yet both methods' cumulative
  totals converge to exactly the same $1,000,000 by the end.
- **A bond's issue price discounts its cash flows at the MARKET rate, not its own coupon rate** — the whole
  reason a bond can issue above or below face value in the first place. Interest expense each period is then
  the carrying value times that SAME market rate (not the coupon rate), which is the entire point of the
  effective-interest method versus the simpler (and, under US GAAP, generally disallowed) straight-line
  amortization alternative.
- **A real bug this module's own test suite caught before it shipped**: a par-priced bond (coupon rate
  exactly equal to the market rate) should classify as `"par"`, but summing a 10-period discounted cash-flow
  series in floating point left the computed issue price a few billionths of a dollar away from the exact
  face value, which a naive strict `>`/`<` comparison misclassified as a microscopic "discount." Fixed with a
  small relative tolerance band around par — a real, if tiny, correctness fix the test suite is what actually
  surfaced.

## Test coverage

`tests/test_stock_based_compensation.py` (7 tests, new file) checks RSU fair value by hand, checks the
option-grant fair value against `finmodel.options.black_scholes` directly, checks the graded-vesting schedule
against the hand-traced four-tranche example above (including the exact month-13 and month-48 transition
points as tranches roll off), and checks the front-loading and equal-total-by-completion properties directly
against the straight-line method. `tests/test_bond_amortization.py` (5 tests, new file) checks the issue
price and first-period interest expense against an independent recomputation of the same formulas, checks
that a discount bond's carrying value strictly increases toward face value while a premium bond's strictly
decreases, checks that both converge to EXACTLY face value by the final period, and checks the par-bond
classification (the case that caught the floating-point bug above).
