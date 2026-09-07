# Revisiting three previously-deferred gaps

Every prior survey this session documented not just what got built but what got deliberately left out, and
why. This round went back to three of those "deferred" items, re-examined the actual reason each was
deferred, and found each one was buildable after all — either because the original objection didn't
actually apply, or because a genuine formula existed that just hadn't been assembled yet.

## 1. Bornhuetter-Ferguson reserving (`finmodel.loss_reserving.bornhuetter_ferguson`)

**Originally deferred in** `docs/OPERATING_FINANCE_TOOLS.md`: "the natural next step after chain-ladder...
deferred as a direct, well-scoped extension of `finmodel.loss_reserving`, once there's a real dataset with an
a-priori loss ratio to reconcile it against."

**Why it's buildable now.** The "real dataset" requirement was never actually necessary — Bornhuetter &
Ferguson's method (1972, "The Actuary and IBNR") takes the a-priori expected loss as an INPUT the caller
supplies (from pricing or an exposure base), not something the module needs to have pre-loaded. The existing
chain-ladder triangle from `docs/OPERATING_FINANCE_TOOLS.md`'s own worked example, paired with an
illustrative a-priori expected-loss figure per accident year, is sufficient to build and test the formula
correctly: BF ultimate = actual reported to date + (a-priori expected losses x the % of losses chain-ladder's
own reporting pattern implies are still unreported). The toolkit's test suite confirms the method's two
defining properties: it converges exactly to the chain-ladder answer for a fully-developed accident year (no
unreported losses left to estimate), and it diverges from chain-ladder's own volatile extrapolation for the
least mature accident year, leaning on the independent a-priori estimate instead — precisely the stabilizing
effect the method exists to provide.

## 2. Earnout / contingent-consideration valuation (`finmodel.earnout_valuation`)

**Originally deferred in** `docs/OPERATING_FINANCE_TOOLS.md`: "the standard implementations are either a
simple scenario-probability-weighted expected value (a thin wrapper with no new formula) or a full
Monte-Carlo/option-pricing treatment (a much larger undertaking that would need its own random-scenario
infrastructure this toolkit doesn't have yet)."

**Why it's buildable now.** The "Monte-Carlo" framing was the wrong comparison — a continuous-metric earnout
(pay X if a financial metric exceeds a threshold at a future date) doesn't need Monte-Carlo simulation at
all under the standard lognormal-diffusion assumption; it has a closed-form solution as a cash-or-nothing
DIGITAL option, exactly the same closed form Black-Scholes already provides. `finmodel.earnout_valuation`
implements both real methods properly: `scenario_weighted_earnout` for a small number of enumerable discrete
outcomes (genuinely a thin formula, but a real and commonly-used one for milestone-based earnouts, so worth
having on its own), and `binary_metric_earnout` for a continuous financial-metric earnout, reusing this
toolkit's own `finmodel.options.norm_cdf` — the real, standard approach every Big 4 valuation practice uses
for market-condition or performance-condition contingent consideration under ASC 805/820.

## 3. Step-up EMI schedules (`finmodel.retail_loans.step_up_emi_schedule`)

**Originally deferred in** `docs/RETAIL_BANKING_TOOLS.md`: "every bank implements the step schedule
differently (a fixed annual % step, or a manually specified path); deferred until there's a real product
term sheet to reconcile a specific implementation against."

**Why it's buildable now.** The objection was really about the ABSENCE of a single canonical step
convention, not about the underlying math being unclear — a fixed-percentage step-up at a fixed frequency
(the most commonly offered real structure, e.g. a 5% EMI increase every 12 months) has a well-defined
correct answer regardless of which specific bank's product it represents: whatever base EMI, stepped up on
that schedule, exactly amortizes the loan by its stated tenure. There's no closed form for an arbitrary step
schedule, so `step_up_emi_schedule` bisects on the base EMI (the loan's final balance is a monotonically
decreasing function of the base payment, so bisection converges to the exact answer). The toolkit's test
suite confirms the real, defining trade-off this product structure has: it always costs strictly more total
interest than a flat EMI for the same loan, because deferring principal repayment leaves the balance
outstanding for longer — the price of the lower early-year affordability the product is designed to offer.

## Test coverage

`tests/test_loss_reserving.py` gained 4 tests for Bornhuetter-Ferguson (the fully-developed-year convergence
property, the immature-year divergence property with a full hand calc, a length-mismatch rejection, and
`from_dict` wiring). `tests/test_earnout_valuation.py` (6 tests, new file) checks the scenario-weighted
method against a hand-computed expected value and its probability-sum validation, and checks the binary
metric method against an independently-computed d1/d2 and the real property that the achievement probability
rises monotonically as the current metric value approaches and then exceeds the threshold.
`tests/test_retail_loans.py` gained 4 tests for the step-up schedule (exact payoff by tenure, the
base-below/final-above-flat-EMI property, the higher-total-interest property, and `from_dict` wiring).
