# More CFI/BIWS/Wall Street Prep templates: eight real, standard techniques not yet in this toolkit

A follow-up gap analysis: this toolkit already carries a 636-entry catalog of CFI, BIWS, Macabacus, Damodaran,
A Simple Model and exinfm templates (`finmodel catalog list`), with 127 paid CFI titles individually checked
against toolkit coverage (`finmodel catalog paid` → `docs/PAID_TEMPLATES.md`) — 59 fully covered, 50 partially
(mostly individual ratio templates already subsumed by `finmodel.ratios`), 14 not applicable (soft-skills/career
content), and 4 with no coverage at all. This pass re-surveyed those 4 gaps plus Wall Street Prep's and Training
The Street's own course catalogs (not just CFI's) for real, standard, quantitatively defensible techniques worth
building — not soft-skills content, not another individually-named ratio template `finmodel.ratios` already
computes generically.

## What was surveyed

- **CFI's uncovered ("none") titles**: Bank and FIG Financial Model Template, Cohort Analysis, InsurTech Pricer
  Model, NOPAT Template (`catalog/paid_templates.json`, coverage="none"). NOPAT is trivial and already computed
  inline wherever `finmodel.residual_income`/`finmodel.wacc` need it (NOPAT = EBIT × (1 − tax rate)) — not worth
  a dedicated module. The other three are real but narrower categories (see "What wasn't built" below).
- **CFI's own named option-pricing and portfolio-theory templates**: a **Black-Scholes Calculator** and a
  **Put-Call Parity** calculator (both confirmed real, standard CFI resources), and an **Efficient Frontier and
  CAL Template** (Markowitz mean-variance optimization + the Capital Allocation Line) — none of these had any
  toolkit equivalent at all; this toolkit had zero derivatives-pricing or portfolio-theory capability before this
  pass.
- **Wall Street Prep's course catalog**: a standalone **Project Finance** course (CFADS, DSCR, LLCR, debt
  sculpting, equity IRR for non-recourse infrastructure/renewable-energy financing — explicitly separate from
  WSP's own corporate 3-statement/DCF tracks) and a **Financial Restructuring / Distressed Investing** certificate
  (liquidity analysis, capital structure modeling, liability-management exercises, DIP financing, plan-of-
  reorganization mechanics, Section 363 sales). BIWS runs a parallel "Project Finance & Infrastructure Modeling"
  course, confirming project finance is a real, independently-recognized curriculum area at two separate training
  platforms, not a CFI idiosyncrasy.
- **Training The Street's course catalog**: core financial modeling/valuation, private equity, capital markets
  and Excel — no distinctive category beyond what CFI/WSP already cover and this toolkit already replicates.

Eight threads were concrete, real, and clean enough to build as tested code, across three passes: **option
pricing**, **project finance**, **portfolio optimization**, **financial restructuring / distressed investing**
(the one category the first pass deferred as substantial enough to deserve its own build), and — closing out
every remaining item this survey originally flagged — a **bank/FIG operating model**, **SaaS cohort analysis**,
**insurance pricing**, and **convertible bonds** (the last of which reuses `finmodel.options` directly).

## The eight new modules

### 1. `finmodel.options` — Black-Scholes, the Greeks, put-call parity, implied volatility

The real, standard Black-Scholes-Merton closed form (dividend-adjusted), checked against Hull's own textbook
reference case (S=K=$100, r=5%, vol=20%, T=1yr → call $10.45, put $5.57 — `tests/test_options.py` pins this
exactly). The five Greeks (delta, gamma, vega, theta, rho), checked against two real, exact analytic identities
(call delta − put delta = e^(−qT); gamma and vega are identical for a call and put at the same strike) rather
than just plausibility bounds. Put-call parity as an explicit no-arbitrage CHECK (not just a formula) — a real
market maker's actual use case, flagging a genuine, tradeable mispricing when the identity fails beyond a
tolerance. Implied volatility via bisection (real property: Black-Scholes price is monotonic in vol, since
Vega > 0 always, so bisection is guaranteed to converge without a derivative-based solver). Pure Python
(`math.erf` for the normal CDF) — no numpy/scipy dependency, consistent with the rest of this toolkit.

```bash
finmodel options examples/options_demo.json
```

### 2. `finmodel.project_finance` — DSCR-based debt sizing/sculpting, LLCR, cap rate/NOI valuation

The real, distinct project-finance sizing convention: rather than a corporate loan's flat amortization, a
project's non-recourse debt is SCULPTED (uneven repayment) so DSCR sits at exactly the lender's minimum covenant
every period, maximizing what the project's own cash flow can support. `size_debt_by_dscr()` computes the
maximum sized debt (PV of each period's CFADS/target-DSCR capacity, discounted at the debt's own rate);
`sculpted_amortization()` builds the actual period-by-period schedule and is checked for its own defining real
property — a debt sized this way fully self-amortizes by construction, with DSCR held EXACTLY at the target
every single period (verified in `tests/test_project_finance.py`, not just plausible-looking output). LLCR (Loan
Life Coverage Ratio — the forward-looking cousin of DSCR lenders also covenant on) and the real-estate
income-approach pair (cap rate valuation = NOI / cap rate, and its inverse) round out the module.

```bash
finmodel project-finance examples/project_finance_demo.json
```

### 3. `finmodel.portfolio_optimization` — Markowitz efficient frontier, tangency portfolio, Capital Allocation Line

The real Merton (1972) closed-form solution for the mean-variance efficient frontier (given expected returns and
a covariance matrix, the minimum-variance portfolio for any target return), implemented with a from-scratch
Gauss-Jordan matrix inverse (no numpy/scipy). Checked for a real, defining internal-consistency property: the
frontier's closed form, evaluated at the global-minimum-variance portfolio's own expected return, must exactly
reproduce the INDEPENDENTLY-computed global-minimum-variance weights and variance — a much stronger check than
"the numbers look plausible." The tangency (maximum-Sharpe) portfolio and Capital Allocation Line are checked
against the real property that gives the tangency portfolio its name: it must have a strictly higher Sharpe
ratio than the (unconstrained) global-minimum-variance portfolio, since it's defined as the Sharpe-maximizing one.

```bash
finmodel portfolio examples/portfolio_demo.json
```

### 4. `finmodel.restructuring` — absolute-priority recovery waterfall, fulcrum security, DIP financing, post-emergence leverage

The real, defining distressed-investing technique: reorganization value distributed strictly by seniority under
the real 11 U.S.C. § 1129(b)(2) absolute priority rule (the same doctrine behind every real Chapter 11 cramdown
fight) — the most senior claims paid in full before any junior claim sees a dollar, claims of the same seniority
(pari passu) split pro rata. `identify_fulcrum()` finds the real, standard "fulcrum security" — the most senior
tranche that does NOT recover in full, whose holders are the ones who typically end up owning the reorganized
company's new equity in a real debt-for-equity restructuring — checked at all three real cases (a mid-stack
fulcrum, full coverage leaving a residual to equity, and near-total wipeout where even the most senior tranche is
the fulcrum). `check_absolute_priority_departure()` is a mechanical fact-pattern check (explicitly NOT a legal
opinion — real bankruptcy law has narrow, real exceptions like unanimous class consent) for the same departure
every real cramdown objection is built on: a junior claim recovering something while a senior claim doesn't.
`dip_financing_sizing()` sizes debtor-in-possession financing to the worst point a cash flow forecast dips below
a minimum-liquidity covenant — not just the ending balance. `post_emergence_capital_structure()` sizes new debt
off a target leverage ratio, not the pre-petition load that drove the distress.

```bash
finmodel restructuring examples/restructuring_demo.json
```

### 5. `finmodel.bank_model` — bank operating model: NII/NIM, provision for credit losses, regulatory capital

CFI's own named "Bank and FIG Financial Model Template", real and distinct from what the banking sector check
(`docs/FOOTBALL_FIELD_USB.md`) already built (comps/valuation — P/B, P/TBV, residual income — not a forward
operating projection). A bank's income statement runs on the SPREAD between what it earns on assets and pays on
liabilities: `net_interest_income()` computes NII and NIM from earning-asset and interest-bearing-liability
balances and their respective yields; `provision_for_credit_losses()` is a real, forward-looking (CECL-style)
charge taken through the income statement, not a lagging write-off. `regulatory_capital_ratios()` checks CET1/
Tier 1/Total capital against risk-weighted assets plus the (non-risk-weighted) Tier 1 leverage ratio against the
real US Prompt Corrective Action "well capitalized" thresholds (12 CFR 324.403), verified on both a bank that
clears them and one that doesn't.

```bash
finmodel bank-model examples/bank_model_demo.json
```

### 6. `finmodel.cohort_analysis` — SaaS cohort retention, GRR/NRR, LTV, LTV:CAC

CFI's own named "Cohort Analysis" and "LTV CAC Ratio" templates, a natural extension of `finmodel.startup_model`
for subscription-business unit economics specifically. `ltv_from_retention_curve()` (the real, exact form — sum
of each future period's retained revenue, discounted) is checked against `ltv_simplified()` (the real, standard
closed-form ARPU × margin ÷ churn-rate approximation assuming constant geometric churn). `revenue_retention()`
is checked for the real, defining difference between GRR and NRR: NRR credits back expansion/upsell revenue from
the SAME existing customers and can exceed 100%, while GRR (churn/contraction only) cannot — a real, easy point
of confusion this toolkit's tests pin down explicitly. `cohort_revenue_projection()` aggregates multiple cohorts'
own (offset) retention curves into one calendar-period forecast, the real mechanic that makes cohort-based
forecasting different from applying one blended growth rate to total revenue.

```bash
finmodel cohort examples/cohort_analysis_demo.json
```

### 7. `finmodel.insurance_pricing` — combined ratio, operating ratio, loss-cost-multiplier rate making

CFI's own named "InsurTech Pricer Model", distinct from the insurance sector check's VALUATION focus
(`docs/FOOTBALL_FIELD_TRV.md`). `combined_ratio()` is the real, standard P&C underwriting-profitability metric
(loss ratio + expense ratio; below 100% is an underwriting profit). `operating_ratio()` is checked for the real
refinement that matters in practice: a real insurer can run a combined ratio modestly ABOVE 100% and still be
overall profitable once float/investment income is credited back — verified as an explicit test case, not just
described. `rate_making_premium()` implements the real, standard loss-cost-multiplier actuarial pricing formula.

```bash
finmodel insurance-pricing examples/insurance_pricing_demo.json
```

### 8. `finmodel.convertible_bonds` — bond floor + embedded option, a real integration with `finmodel.options`

A real, named fixed-income category at both CFI and Wall Street Prep, and a natural real use of the option-
pricing module built earlier this pass: by real market convention, a convertible bond IS a straight bond plus an
embedded call option on the issuer's own stock. `bond_floor()` computes the PV of the bond's cash flows at a
comparable straight-debt yield; `convertible_bond_value()` implements the real, standard two-component
practitioner approximation (bond floor + `finmodel.options.black_scholes`'s call value, scaled by the conversion
ratio), checked for the real, exact property that makes it economically sane: the estimated value can never fall
below immediate conversion value (you could always convert right now), and a deep out-of-the-money convertible
should trade close to its bond floor — both verified explicitly, not just plausible-looking output.

```bash
finmodel convertible examples/convertible_bonds_demo.json
```

## What wasn't built, and why

- **CMO (Collateralized Mortgage Obligation) models** — a real, named category at these platforms, but a
  genuinely more specialized structured-credit topic (tranching, real prepayment-speed modeling like PSA/CPR
  conventions) than the rest of this toolkit's corporate-finance/valuation focus; flagged as real but out of
  scope.
- **Training The Street** surfaced no distinctive gap beyond what CFI/WSP already cover.

## Sources

- [CFI Black-Scholes Calculator](https://corporatefinanceinstitute.com/resources/financial-modeling/black-scholes-calculator/)
- [CFI Put-Call Parity](https://corporatefinanceinstitute.com/resources/derivatives/put-call-parity/)
- [CFI Efficient Frontier and CAL Template](https://corporatefinanceinstitute.com/resources/financial-modeling/efficient-frontier-and-cal-template)
- [Wall Street Prep: Project Finance](https://www.wallstreetprep.com/knowledge/demystifying-project-finance/)
- [BIWS: Debt Service Coverage Ratio](https://breakingintowallstreet.com/kb/project-finance/debt-service-coverage-ratio/)
- [BIWS: Project Finance Modeling](https://breakingintowallstreet.com/project-finance-modeling/)
- [Wall Street Prep / Wharton: Restructuring & Distressed Investing Certificate](https://wallstreetprep.wharton.upenn.edu/restructuring-distressed-investing-certificate/)
- [Wall Street Prep: Financial Restructuring (free lesson)](https://www.wallstreetprep.com/knowledge/quick-lesson-demystifying-financial-restructuring/)
- [Wall Street Prep: Fixed Income Markets Certification](https://www.wallstreetprep.com/self-study-programs/fixed-income-markets-certification-program/)
- [Training The Street course catalog](https://trainingthestreet.com/download-the-training-the-street-catalog/)
- Hull, *Options, Futures and Other Derivatives* — the S=K=$100/r=5%/vol=20%/T=1yr Black-Scholes reference case
  this toolkit's tests are pinned against.
- 11 U.S.C. § 1129(b)(2) — the absolute priority rule `finmodel.restructuring`'s recovery waterfall implements.
- 12 CFR § 324.403 — the US Prompt Corrective Action "well capitalized" thresholds `finmodel.bank_model` checks.
- CFI's own catalog entries for "Bank and FIG Financial Model Template", "Cohort Analysis", "LTV CAC Ratio", and
  "InsurTech Pricer Model" (`catalog/paid_templates.json`).
