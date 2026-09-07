# Pension accounting and the M&A working-capital peg

A fourth fresh pair: defined-benefit pension accounting (ASC 715) and the net-working-capital peg/true-up
mechanic every real M&A purchase agreement includes. Both real, common mechanics with no prior
representation across the toolkit's other ~50 modules, checked against what already exists before being
built.

| New module | Real technique | Checked against, and confirmed distinct from |
|---|---|---|
| `finmodel.pension_accounting` | ASC 715's PBO roll-forward, plan-asset roll-forward, funded status, and net periodic pension cost — including the real, defining gap between the EXPECTED return used in the income-statement cost and the ACTUAL return used in the balance-sheet roll-forward | nothing existing — defined-benefit pension accounting is a wholly new category here |
| `finmodel.nwc_peg` | The net-working-capital peg (typically a trailing average of the target's own historical NWC) and the closing true-up purchase-price adjustment, including a real de-minimis threshold below which no adjustment triggers | `finmodel.merger`/`finmodel.comps`/`finmodel.lbo` (all price a deal at signing; none implement the POST-signing working-capital adjustment every real definitive purchase agreement includes) |

## Real technique, and why it was built this way

- **`service_cost` and `actuarial_gain_loss` are caller-supplied inputs**, not re-derived from first
  principles — the same design choice this toolkit already made for Bornhuetter-Ferguson's a-priori expected
  loss. A plan actuary's own PBO model is the real source of these figures in practice; building and testing
  the surrounding roll-forward, funded-status, and cost mechanics correctly doesn't require reimplementing
  that actuarial model from scratch.
- **The expected-vs-actual return gap is the module's central real mechanic** — `net_periodic_pension_cost()`
  uses the EXPECTED (long-run assumed) return on plan assets, deliberately smoothing the income-statement
  cost, while `plan_assets_rollforward()` uses the ACTUAL return for the real balance-sheet position. The gap
  between the two, computed by `asset_gain_loss()`, is itself a real actuarial gain or loss that accumulates
  in Other Comprehensive Income rather than hitting net income immediately — the toolkit's test suite verifies
  this gap directly using the same underlying numbers across all four functions, confirming the pieces are
  internally consistent with each other rather than four independently-plausible-looking calculations.
- **The NWC peg is usually a trailing average, not a single snapshot** — the real, standard convention
  (`trailing_average_peg()`) exists specifically because a single point-in-time NWC figure can be seasonally
  distorted (inventory build-ups, collection timing), so negotiating parties instead peg the deal to a
  smoothed historical baseline.
- **The true-up is a real, symmetric dollar-for-dollar mechanism** — `nwc_true_up()` increases the purchase
  price when actual NWC at closing exceeds the peg (the seller delivered more working capital than was priced
  in) and decreases it when actual NWC falls short, with an optional de-minimis threshold (a real, common
  purchase-agreement feature) below which small differences are ignored rather than triggering a formal
  settlement.

## Test coverage

`tests/test_pension_accounting.py` (7 tests, new file) checks the PBO and plan-asset roll-forwards and net
periodic cost against hand calculations, checks funded-status classification in both directions, checks
`asset_gain_loss()` against the real expected-vs-actual gap, and combines all four functions into one
end-to-end period using the same underlying numbers to confirm they cohere. `tests/test_nwc_peg.py` (6 tests,
new file) checks the trailing-average peg and the true-up adjustment against hand calculations for all three
real outcomes: an increase to the seller, a decrease (buyer credit), and no adjustment when the difference
falls inside a de-minimis threshold.
