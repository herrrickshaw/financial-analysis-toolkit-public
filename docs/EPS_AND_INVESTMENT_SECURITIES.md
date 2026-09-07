# EPS calculation and investment securities classification

A fifth fresh pair: earnings per share (ASC 260) and investment securities classification (ASC 320). Both
real, extremely common corporate accounting calculations with no prior representation across the toolkit's
other ~50 modules, checked against what already exists before being built.

| New module | Real technique | Checked against, and confirmed distinct from |
|---|---|---|
| `finmodel.eps_calculation` | ASC 260 basic and diluted EPS — the treasury stock method for options/warrants, the if-converted method for convertible debt, and the real antidilution rule every diluted-EPS calculation must apply | nothing existing — EPS is a wholly new calculation category here, despite the toolkit already touching related instruments (`finmodel.options`, `finmodel.convertible_bonds`) from a pricing rather than a share-count lens |
| `finmodel.investment_securities` | ASC 320's trading/available-for-sale/held-to-maturity classification and the structurally different way each routes unrealized gains and losses (net income, OCI, or nowhere at all), plus the OCI reclassification-on-sale mechanic | nothing existing — investment securities classification is a wholly new accounting category here |

## Real technique, and why it was built this way

- **Out-of-the-money options are never dilutive, by construction** — `treasury_stock_method_incremental_
  shares()` returns exactly zero whenever the strike price is at or above the average market price, since
  exercising them would never make economic sense and so could never actually happen. This isn't a special
  case bolted on; it falls directly out of the real treasury-stock-method mechanic (shares repurchased with
  the exercise proceeds can never exceed the shares issued when the strike is above market).
- **A dilutive security is only included if it actually reduces EPS** — the real ASC 260 antidilution rule,
  verified directly in this module's test suite with a deliberately constructed antidilutive convertible (a
  high coupon rate funding very few converted shares, which would INCREASE EPS and so must be excluded
  entirely). This is also, by construction, why diluted EPS can never exceed basic EPS — the toolkit's test
  suite checks that inequality directly on the dilutive example rather than assuming it.
- **The same unrealized gain or loss lands in three different places depending only on classification** —
  `classify_and_measure()`'s test suite runs the identical cost basis and fair value through all three
  classifications to confirm trading routes it to net income, available-for-sale routes the SAME dollar
  amount to OCI instead, and held-to-maturity recognizes it nowhere at all (carried at amortized cost). The
  real reclassification mechanic this sets up — an AFS security's cumulative OCI balance gets "recycled" into
  net income only once the security is actually sold — is checked to fire exclusively for AFS securities,
  since a trading security's gain is already in net income with nothing left in OCI to recycle.

## Test coverage

`tests/test_eps_calculation.py` (7 tests, new file) checks basic EPS, the treasury stock method (both
in-the-money and out-of-the-money), and the if-converted method against hand calculations, checks a full
diluted-EPS example combining both dilutive security types against an independently-computed numerator and
denominator, and checks the antidilution exclusion case directly.
`tests/test_investment_securities.py` (6 tests, new file) checks all three classifications against the same
underlying cost basis and fair value, checks the classification-rejection error path, and checks that the
OCI reclassification adjustment fires only for available-for-sale securities.
