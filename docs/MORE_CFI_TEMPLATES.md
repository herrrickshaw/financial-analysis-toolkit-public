# More CFI/BIWS/Wall Street Prep templates: four real, standard techniques not yet in this toolkit

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

Four threads were concrete, real, and clean enough to build as tested code: **option pricing**, **project
finance**, **portfolio optimization**, and — in a dedicated follow-up pass — **financial restructuring /
distressed investing**, the one category the first pass deferred as substantial enough to deserve its own build.

## The four new modules

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

## What wasn't built, and why

- **Bank and FIG Financial Model Template** (CFI) — a full bank OPERATING/projection model (deposit and loan
  book growth, net interest margin, provision for credit losses, regulatory capital ratios) is real and distinct
  from what the banking sector check (`docs/FOOTBALL_FIELD_USB.md`) already built, which covered comps/valuation
  (P/B, P/TBV, residual income) rather than a forward 3-statement projection — a real, defensible future
  extension, not attempted here to keep this pass's scope to genuinely NEW capability categories.
- **Cohort analysis** (CFI) — a real, standard SaaS/subscription retention-and-LTV-by-cohort technique; a
  natural extension of `finmodel.startup_model` specifically, left for a future pass focused on that module
  rather than bundled into this broader toolkit-gap survey.
- **InsurTech Pricer Model** (CFI) — insurance premium/loss-ratio pricing; the insurance sector check
  (`docs/FOOTBALL_FIELD_TRV.md`) already covers P&C insurer VALUATION (P/B, P/TBV, residual income), and a
  genuine pricing-actuarial model is a different, more specialized discipline than the corporate-finance/
  valuation focus of the rest of this toolkit.
- **Convertible bonds and CMO (Collateralized Mortgage Obligation) models** — real, named categories at these
  platforms, but genuinely more specialized fixed-income/structured-credit topics with real, non-trivial
  prepayment/tranching mechanics; flagged as real but out of scope for this pass.
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
