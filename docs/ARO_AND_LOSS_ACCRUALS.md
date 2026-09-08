# Asset retirement obligations and expected-value loss accruals

A seventh fresh pair: asset retirement obligations (ASC 410) and two related expected-value loss accruals —
warranty reserves and the CECL aging-schedule allowance for trade receivables. All real, common calculations
with no prior representation across the toolkit's other ~50 modules, checked against what already exists
before being built.

| New module | Real technique | Checked against, and confirmed distinct from |
|---|---|---|
| `finmodel.asset_retirement_obligations` | ASC 410's present-value liability recognition at an asset's in-service date, the accretion mechanic that grows the liability back to the original estimated cost by retirement, and settlement gain/loss | nothing existing — asset retirement obligations are a wholly new category here |
| `finmodel.warranty_and_receivables_allowance` | The warranty reserve's expected-cost roll-forward (units sold x failure rate x repair cost, less actual costs incurred) and CECL's aging-schedule method for trade receivables (a different expected-loss rate per age bucket) | `finmodel.bank_model`'s CECL provisioning (a different asset class — LOANS, typically estimated with a statistical PD/LGD approach rather than the aging-schedule convention used for trade receivables) |

## Real technique, and why it was built this way

- **Accretion is the exact algebraic reverse of the initial discounting** — the module's own defining
  identity, verified directly in its test suite: an ARO liability recognized at
  `estimated_future_cost / (1 + r)^n` and then accreted at that same rate `r` for `n` years must land back at
  EXACTLY `estimated_future_cost`, since `(1/(1+r)^n) * (1+r)^n = 1`. This is the same kind of exact,
  self-verifying identity this toolkit has leaned on throughout (the percentage-of-completion revenue
  identity, the bond-amortization par-at-maturity identity), rather than a plausibility check.
- **The two liability estimation techniques paired here are genuinely different mechanics, not the same
  formula twice** — ARO's liability is a single point-in-time PV calculation that then accretes forward like
  interest on a loan; a warranty reserve is instead a flow accrual made continuously as units are SOLD (at
  the point of sale, not when a claim is filed, since the repair obligation already exists then); the
  receivables allowance is neither — it's a snapshot expected-loss calculation applied across risk-stratified
  age buckets. Building all three side by side (two in one module, one in another) makes the real distinction
  between them clearer than building any one in isolation would.
- **A small, high-risk receivables bucket can carry more allowance than a much larger, low-risk one** — the
  toolkit's test suite verifies this directly with a bucket ten times smaller but assigned a fifty-times
  higher loss rate, confirming the aging method's real behavior rather than assuming a uniform blanket rate
  would produce the same answer.

## Test coverage

`tests/test_asset_retirement_obligations.py` (5 tests, new file) checks initial recognition against an
independent PV calculation, checks the accretion identity directly, checks that the liability balance rises
monotonically every year, and checks settlement gain/loss in both directions.
`tests/test_warranty_and_receivables_allowance.py` (4 tests, new file) checks the warranty roll-forward and
the aging-method allowance against hand calculations, and checks the small-high-risk-bucket property
directly.
