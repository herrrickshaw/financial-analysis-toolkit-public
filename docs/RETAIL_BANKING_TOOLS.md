# Retail-banking and FX tools: loans, deposits, carry trades, revolving credit, NPA norms

A fifth round of tool-building, this time on direct request for retail/consumer-banking and FX-desk
calculations rather than another gallery survey: loan (EMI) mechanics, RD/FD deposit mechanics, loan
amortization adjustments (prepayment and rate resets), and carry-trade economics. A sixth, immediately
following round added two more real "other banking related calculations" from the same request: revolving-
credit (cash-credit/overdraft and credit-card) interest, and RBI's NPA classification and provisioning
norms. `docs/BANKING_LITERATURE_SURVEY.md` is the companion literature survey covering every module in both
rounds (and the earlier `finmodel.bank_model`/`finmodel.project_finance`/`finmodel.tax_provision` etc.) —
the books, regulatory sources, and academic papers behind each. Each new module here was checked against the
toolkit's existing debt/FX-adjacent modules before being built, to confirm it was a genuinely different
context rather than a duplicate:

| New module | Real technique | Checked against, and confirmed distinct from |
|---|---|---|
| `finmodel.retail_loans` | Monthly reducing-balance EMI, amortization schedule, part-prepayment (reduce-tenure vs. reduce-EMI), floating-rate reset, foreclosure payoff, FOIR-based loan eligibility | `finmodel.project_finance.level_annuity_schedule` (an annual, project-finance-tenor loan schedule with no prepayment/reset/foreclosure mechanics — retail lending is monthly and these are real, recurring consumer-loan events project debt never faces) |
| `finmodel.retail_deposits` | Fixed Deposit compound-interest maturity; Recurring Deposit maturity computed by simulating each monthly installment's own compounding to maturity; premature RD closure at a reduced rate; Section 194A TDS withholding | nothing existing — retail time deposits are a wholly new product category here |
| `finmodel.carry_trade` | Covered interest rate parity (the no-arbitrage forward rate), the unhedged FX carry trade's real cash flow, and the break-even depreciation at which the trade stops paying off | `finmodel.options` (equity/index option pricing, not FX rate parity); `finmodel.portfolio_optimization` (equity portfolio theory, not a funding/target currency pair trade) |
| `finmodel.revolving_credit` | Daily-outstanding-balance interest (shared mechanic behind cash-credit/overdraft accounts and credit-card billing cycles), and the credit-card minimum-payment schedule (including a real negative-amortization case) | `finmodel.retail_loans` (a FIXED reducing-balance EMI schedule; revolving credit has a fluctuating balance with no fixed repayment schedule at all — a genuinely different mechanic, not a variant of the same one) |
| `finmodel.npa_classification` | RBI's IRAC asset-classification ladder (Standard/SMA-0/1/2/Sub-standard/Doubtful-1/2/3/Loss) by days-past-due and NPA age, and secured/unsecured provisioning at the published rates | `finmodel.bank_model` (US-style CECL provisioning, a different regulatory regime); `finmodel.loss_reserving` (actuarial claim reserving, not credit-account classification) |

## Real formulas and conventions, and why

- **EMI is the reducing-balance method**, the worldwide standard mandated by RBI for Indian retail lending
  disclosure — interest each month is charged only on the outstanding balance, computed via
  `finmodel.fin.pmt` (already used elsewhere in the toolkit for the same underlying annuity math, sign-flipped
  to read as a positive monthly outflow).
- **Prepayment has two real, mutually exclusive strategies every bank actually offers**: keep the EMI the
  same and shorten the tenure ("reduce_tenure"), or keep the tenure the same and lower the EMI
  ("reduce_emi"). The module's own test suite confirms the textbook result that reduce-tenure always saves
  *at least* as much total interest as reduce-EMI for an identical prepayment amount, because it removes
  interest-bearing months entirely rather than just shrinking each remaining month's charge.
- **FOIR (Fixed Obligation to Income Ratio)** is the underwriting metric Indian retail lenders (SBI, HDFC,
  ICICI and others) publish directly in their own lending policies — not a generic debt-to-income concept
  invented for this toolkit.
- **RD maturity is computed by simulating each installment's own future value**, not by using one of the
  several inconsistently-derived closed-form "banker's RD formulas" that circulate online (they disagree with
  each other on how to handle the fractional-period compounding of a monthly deposit against a quarterly
  compounding cycle). Simulating each installment separately is unambiguous and directly matches what RBI's
  compounding requirement actually means economically.
- **TDS is withheld on the FULL interest amount once the Section 194A threshold is crossed**, not merely the
  excess over the threshold — a real, commonly-misunderstood point of Indian tax law that the module's test
  suite specifically checks (interest of ₹45,000 against a ₹40,000 threshold withholds 10% of the full
  ₹45,000, not 10% of the ₹5,000 excess).
- **The carry-trade break-even depreciation is, by construction, EXACTLY the covered-interest-rate-parity
  forward premium** — the well-known result that an unhedged carry trade's entire economic bet is that the
  future spot rate will NOT move to where the forward rate already prices it (the "forward premium puzzle"
  documented in FX markets since Fama (1984)). The module's test suite checks this identity directly, and
  separately confirms that discounting at exactly the break-even future spot rate zeroes out the trade's
  profit.
- **Cash-credit/overdraft and credit-card interest share one real formula — daily balance x daily rate,
  summed** — a genuinely different mechanic from a fixed EMI loan (no repayment schedule at all; the balance
  fluctuates with the borrower's own draws and repayments). The module's own test suite reproduces the
  classic "minimum-payment trap": a lower minimum-payment percentage always takes strictly longer and costs
  strictly more total interest for the same starting balance and rate, and an explicit negative-amortization
  case (a minimum payment below the interest actually accruing, so the balance GROWS despite a payment being
  made) is demonstrated directly.
- **NPA classification is driven by two different clocks** — days-past-due decides whether an account is
  still Standard/SMA or has crossed into NPA territory at 91+ days, but ONCE it is an NPA, it is the AGE OF
  THAT NPA CLASSIFICATION (not the still-growing DPD count) that buckets it into Sub-standard/Doubtful-1/2/3.
  Provisioning is then charged at markedly different rates on the secured versus unsecured portion of the
  SAME account's outstanding balance — unsecured exposure reaches 100% provisioning a full bucket earlier
  than secured exposure does.

## What was deliberately left out

- ~~**Step-up/step-down EMI schedules**~~ — **RESOLVED**, see `docs/DEFERRED_GAPS_REVISITED.md`: built as
  `finmodel.retail_loans.step_up_emi_schedule()` for the fixed-percentage-step-up structure (the most
  commonly offered real version). The objection above was about the absence of one canonical convention
  across banks, not about the math being unclear — a fixed % step at a fixed frequency has a well-defined
  correct answer (bisected on the base EMI, since there's no closed form for an arbitrary step schedule)
  regardless of which specific bank's product it represents.
- **Balance-transfer break-even analysis** (should a borrower refinance an existing loan elsewhere) — real,
  but it is a thin wrapper: compare `amortization_schedule`'s total interest for the existing loan's remaining
  term against a new `amortization_schedule` at the new lender's rate, net of transfer/processing fees. No new
  formula to add; a worked example belongs in documentation rather than as a new function.
- **Covered (hedged) carry trade with a forward contract** — the covered version is riskless by construction
  once `covered_interest_rate_parity` gives the no-arbitrage forward rate (the whole point of CIP is that a
  hedged carry trade earns exactly zero excess return); there is no separate formula to build beyond what
  `covered_interest_rate_parity` already returns.
- **Segment-specific standard-asset provisioning rates** (RBI's circular sets different standard-provisioning
  percentages for, e.g., commercial real estate versus agriculture versus general advances, rather than one
  flat rate) — `finmodel.npa_classification` uses a single illustrative standard rate and documents that a
  live calculation should be checked against the current circular; a segment-rate table is a real, bounded
  future extension once there's a specific portfolio mix to reconcile it against.
- **DPD-reset-on-partial-payment mechanics** — real banks track complex rules for when a partial payment
  resets or merely reduces the days-past-due clock; `finmodel.npa_classification` takes `days_past_due` and
  `npa_age_days` as direct inputs rather than deriving them from a payment history, which keeps the
  classification/provisioning math itself exact without taking on that separate, bank-policy-specific
  reconstruction problem.

## Test coverage

`tests/test_retail_loans.py` (9 tests) checks EMI against the standard closed-form reducing-balance formula
computed independently of the module's own `finmodel.fin.pmt` call, checks the prepayment strategies'
relative interest savings, checks that a lower floating-rate reset always lowers the recomputed EMI, and
checks the FOIR eligibility result by round-tripping the derived maximum principal back through the EMI
formula to reproduce the exact available EMI capacity. `tests/test_retail_deposits.py` (6 tests) checks FD
maturity against the plain compound-interest formula, checks RD maturity against an independent
re-simulation of the same per-installment compounding plus the defining edge case that the very last
installment earns zero interest, and checks the real TDS full-withholding rule. `tests/test_carry_trade.py`
(6 tests) checks CIP against its closed-form definition, checks that the unhedged carry return at an
unchanged spot equals exactly the one-year rate differential, and checks the break-even-depreciation identity
against CIP's own forward premium. `tests/test_revolving_credit.py` (5 tests) checks daily-balance interest
against a round-trip property (annualizing the effective rate on a constant balance must reproduce the input
annual rate exactly), checks the comparative minimum-payment-percentage property, and checks an explicit
negative-amortization case. `tests/test_npa_classification.py` (9 tests) checks classification at every real
DPD/NPA-age boundary and checks provisioning against the published secured/unsecured rate table, including
the point that unsecured exposure is always provisioned at least as aggressively as secured exposure in the
same bucket.
