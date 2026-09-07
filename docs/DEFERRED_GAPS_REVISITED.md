# Revisiting previously-deferred gaps

Every prior survey this session documented not just what got built but what got deliberately left out, and
why. Three times now, this session has gone back to some of those "deferred" items, re-examined the actual
reason each was deferred, and found most of them buildable after all — either because the original objection
didn't actually apply, or because a genuine formula existed that just hadn't been assembled yet. Round 1
(below) covered Bornhuetter-Ferguson reserving, earnout valuation, and step-up EMI schedules; round 2 covers
an American (deal-by-deal) PE carry waterfall with clawback, and percentage-of-completion revenue
recognition; round 3 covers credit-card master-trust securitization and sales-capacity planning.

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

## Test coverage (round 1)

`tests/test_loss_reserving.py` gained 4 tests for Bornhuetter-Ferguson (the fully-developed-year convergence
property, the immature-year divergence property with a full hand calc, a length-mismatch rejection, and
`from_dict` wiring). `tests/test_earnout_valuation.py` (6 tests, new file) checks the scenario-weighted
method against a hand-computed expected value and its probability-sum validation, and checks the binary
metric method against an independently-computed d1/d2 and the real property that the achievement probability
rises monotonically as the current metric value approaches and then exceeds the threshold.
`tests/test_retail_loans.py` gained 4 tests for the step-up schedule (exact payoff by tenure, the
base-below/final-above-flat-EMI property, the higher-total-interest property, and `from_dict` wiring).

## 4. American (deal-by-deal) PE carry waterfall with clawback (`finmodel.vc_fund_metrics.american_waterfall`)

**Originally deferred in** `docs/OPERATING_FINANCE_TOOLS.md`: "a deal-by-deal alternative is real and used
by some funds, but... a clawback provision needs a full multi-period fund cash-flow history to be
meaningful... Deferred until there's a real multi-year fund dataset to model it against."

**Why it's buildable now.** A "full multi-year fund dataset" was never actually the requirement — what the
clawback mechanic needs to be demonstrated and tested correctly is just two or more deals with different
outcomes, realized at different times, which a small hand-constructed example provides perfectly well.
`american_waterfall()` processes each deal in realization-date order, paying out that deal's own
return-of-capital/preferred-return/GP-catch-up/residual-split tiers as it is realized (unlike
`carry_waterfall`'s whole-fund, point-in-time snapshot), and after every deal checks whether the GP's
cumulative carry received so far exceeds `carry_pct` of the fund's cumulative profit across every deal
realized so far. The toolkit's test suite reproduces the real mechanic exactly by hand: a $1M-to-$3M winner
realized first pays the GP $400,000 in carry (exactly 20% of the fund's $2M cumulative profit at that
point); a $1M-to-$200,000 loser realized second shrinks cumulative fund profit to $1.2M, so only $240,000 of
carry is now justified — the GP owes back the $160,000 difference, a real CLAWBACK, exactly the provision
every American-waterfall fund agreement includes precisely because deal-by-deal payout creates this risk
that a whole-fund waterfall never has.

## 5. Percentage-of-completion revenue recognition (`finmodel.percentage_of_completion`)

**Originally deferred in** `docs/FPA_GALLERY_GAP_ANALYSIS.md`: "a real, standard ASC 606 revenue-recognition
method, but vertical-specific (construction/long-term-contract industries) rather than general-purpose;
deferred for the same reason `docs/ADVISORY_SERVICES.md` deferred other vertical-specific work — no real
dataset on hand to reconcile it against yet."

**Why it's buildable now.** Same pattern as items 1-4 above: the cost-to-cost percentage-of-completion
method is exact and self-verifying against its own accounting identity — once costs incurred reach exactly
100% of the total estimate, cumulative recognized revenue must equal exactly the contract price, with no
external dataset required to prove the formula correct. `finmodel.percentage_of_completion` implements both
the single-period calculation (percent complete, revenue and gross profit to date, and the real
over-billed/under-billed balance-sheet classification every construction company's 10-K reports) and a
multi-period `completion_schedule()`, whose test suite confirms the identity directly: a 3-period cost
schedule summing to exactly the total estimate recognizes exactly the contract price in cumulative revenue,
and the sum of every period's own current-period revenue equals that same total.

## Test coverage (round 2)

`tests/test_vc_fund_metrics.py` gained 4 tests for the American waterfall: the full hand-computed
winner-then-loser clawback scenario above, a two-winners case confirming no clawback ever triggers when
cumulative profit only grows, a check that deals are processed in realization-date order regardless of input
order, and `from_dict` wiring. `tests/test_percentage_of_completion.py` (6 tests, new file) checks the
single-period calculation against hand-computed values for both the over-billed and under-billed cases, and
checks the multi-period schedule against its self-verifying revenue-equals-contract-price identity.

## 6. Credit-card master-trust securitization (`finmodel.credit_card_abs`)

**Originally deferred in** `docs/PROFESSOR_COURSE_SURVEY.md`: "a real, structurally different mechanic...
that would need its own careful, separately-verified formula set rather than a quick extension of the
existing CMO module; flagged as a real future candidate."

**Why it's buildable now.** The "careful, separately-verified formula set" this needed turned out to be
entirely hand-verifiable without a real trust's historical data: excess spread is a direct subtraction
(portfolio yield less certificate rate, servicing fee, and charge-offs), the early-amortization trigger is a
simple trailing rolling average crossing zero (the exact, real convention every card master-trust prospectus
defines), and the revolving-vs-amortization cash-flow walk is a straightforward month-by-month simulation.
`finmodel.credit_card_abs`'s test suite traces a full hand-computed example: a $100M receivables pool with a
15% monthly payment rate, an 80M certificate balance flat through a 24-month revolving period (interest-only
throughout), then paid down in exactly 6 amortization months under a pass-through structure (5 full $15M
months plus one final $5M month) or exactly 10 level $8M months under a controlled-amortization structure.

## 7. Sales capacity planning (`finmodel.sales_capacity_planning`)

**Originally deferred in** `docs/FPA_GALLERY_GAP_ANALYSIS.md`: "its core mechanic (ramping rep productivity
by tenure cohort) is close enough to `finmodel.cohort_analysis`'s existing retention-curve machinery that
it's a natural extension of that module rather than a new one, better done when there's a real sales-comp
dataset to reconcile against."

**Why it's buildable now.** Re-examining the "close enough to cohort_analysis" reasoning: the two modules
track fundamentally different real metrics on their cohorts (customer retention/revenue versus sales-rep
quota attainment), so treating one as a natural extension of the other would have forced an awkward, leaky
abstraction rather than saving real work — a small, clean, standalone module was the more honest design once
that was reconsidered. And, as with every other item in this document, the "real sales-comp dataset" was
never actually required: a hand-traced example with two overlapping hire cohorts moving through a standard
20/50/80/100% quarterly ramp curve is enough to build and verify the capacity-forecasting formula and its
exact inverse (reps needed for a target) correctly.

## Test coverage (round 3)

`tests/test_credit_card_abs.py` (7 tests, new file) checks excess spread against a hand calc, checks the
early-amortization trigger against both a hand-traced rolling-average crossing and a series that never
triggers, and checks the master-trust cash-flow walk against the full hand-computed revolving/amortization
example above under both amortization methods. `tests/test_sales_capacity_planning.py` (5 tests, new file)
checks the capacity schedule against a hand calc tracing two overlapping hire cohorts independently through
the ramp curve, checks that tenure beyond the ramp curve's length holds at full productivity, and checks that
the reps-needed calculation is the exact inverse of the capacity calculation via a round-trip.
