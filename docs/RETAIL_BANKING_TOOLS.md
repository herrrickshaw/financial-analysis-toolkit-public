# Retail-banking and FX tools: loans, deposits, carry trades

A fifth round of tool-building, this time on direct request for retail/consumer-banking and FX-desk
calculations rather than another gallery survey: loan (EMI) mechanics, RD/FD deposit mechanics, loan
amortization adjustments (prepayment and rate resets), and carry-trade economics. Each was checked against
the toolkit's existing debt/FX-adjacent modules before being built, to confirm it was a genuinely different
context rather than a duplicate:

| New module | Real technique | Checked against, and confirmed distinct from |
|---|---|---|
| `finmodel.retail_loans` | Monthly reducing-balance EMI, amortization schedule, part-prepayment (reduce-tenure vs. reduce-EMI), floating-rate reset, foreclosure payoff, FOIR-based loan eligibility | `finmodel.project_finance.level_annuity_schedule` (an annual, project-finance-tenor loan schedule with no prepayment/reset/foreclosure mechanics — retail lending is monthly and these are real, recurring consumer-loan events project debt never faces) |
| `finmodel.retail_deposits` | Fixed Deposit compound-interest maturity; Recurring Deposit maturity computed by simulating each monthly installment's own compounding to maturity; premature RD closure at a reduced rate; Section 194A TDS withholding | nothing existing — retail time deposits are a wholly new product category here |
| `finmodel.carry_trade` | Covered interest rate parity (the no-arbitrage forward rate), the unhedged FX carry trade's real cash flow, and the break-even depreciation at which the trade stops paying off | `finmodel.options` (equity/index option pricing, not FX rate parity); `finmodel.portfolio_optimization` (equity portfolio theory, not a funding/target currency pair trade) |

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

## What was deliberately left out

- **Step-up/step-down EMI schedules** (a real product for early-career or near-retirement borrowers, where
  the EMI itself grows or shrinks on a schedule rather than staying level) — a real and distinct amortization
  shape, but every bank implements the step schedule differently (a fixed annual % step, or a manually
  specified path); deferred until there's a real product term sheet to reconcile a specific implementation
  against, rather than inventing a generic step convention with no bank's actual disclosure to check it
  against.
- **Balance-transfer break-even analysis** (should a borrower refinance an existing loan elsewhere) — real,
  but it is a thin wrapper: compare `amortization_schedule`'s total interest for the existing loan's remaining
  term against a new `amortization_schedule` at the new lender's rate, net of transfer/processing fees. No new
  formula to add; a worked example belongs in documentation rather than as a new function.
- **Covered (hedged) carry trade with a forward contract** — the covered version is riskless by construction
  once `covered_interest_rate_parity` gives the no-arbitrage forward rate (the whole point of CIP is that a
  hedged carry trade earns exactly zero excess return); there is no separate formula to build beyond what
  `covered_interest_rate_parity` already returns.

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
against CIP's own forward premium.
