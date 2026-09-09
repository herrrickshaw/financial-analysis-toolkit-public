# Corporate tax regime choice and the CGTMSE guarantee fee

`finmodel.india_corporate_tax_regimes` — two real financing/tax mechanics that change a project's actual
bankability beyond the state/central capital incentives already modeled in
`finmodel.investment_incentives` and `finmodel.project_bankability`.

## Section 115BAB vs 115BAA vs the standard regime

A new manufacturing company can elect **Section 115BAB** (15% base tax) instead of **Section 115BAA**
(22%, for existing domestic companies generally) or the pre-2019 **standard regime** (30% base, plus a
surcharge that itself varies by income slab) — but only if incorporated on/after 1.10.2019 and it commenced
manufacturing by the statutory cutoff this toolkit's own research found (31.3.2024; see
`docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md`), and only by forgoing most other deductions, including
additional depreciation.

The effective rate in every case is exact statutory arithmetic, not an estimate:

```
effective_rate = base_rate * (1 + surcharge_rate) * (1 + cess_rate)
```

`tax_regime_comparison` computes this for each regime, then the resulting post-tax annual cash flow and IRR,
so the real choice shows up as an IRR number rather than a rate table. Run against a real project from this
toolkit's own 18-state matrix — Gujarat's automobile & auto-components project (₹59.33cr capex, the same
flat ₹7.6cr/year illustrative operating cash flow used throughout this toolkit) —
`examples/india_corporate_tax_regimes_demo.json` shows 115BAB clearing a positive IRR (1.10%) while 115BAA
(-0.76%) and the standard regime (-2.78%) both remain negative at this illustrative cash-flow level — a
**3.88 percentage-point IRR swing purely from the tax election**, on top of whatever state/central capital
incentives already apply.

**Minimum Alternate Tax (MAT) is explicitly out of scope.** MAT doesn't apply to 115BAA/115BAB electors, but
it can bind a standard-regime company whose book profit exceeds its taxable income — since that depends on
book-vs-tax income differences this toolkit has no visibility into, the standard-regime effective rate
computed here should be read as a **floor**, not a ceiling, for a company that would otherwise be MAT-bound
(i.e. the real standard-regime tax burden could be higher than what this module reports).

## CGTMSE: loan access, not a DSCR improvement

CGTMSE (Credit Guarantee Fund Trust for Micro and Small Enterprises) doesn't lower a project's cost of debt
— its real value is letting a lender extend a loan **without adequate collateral**, at the cost of an annual
guarantee fee (0.37%–1.20% p.a. of the covered loan amount, per its own published fee schedule; see
`docs/INDIA_PROJECT_FINANCE_LENDING_TERMS.md`). `cgtmse_adjusted_dscr` reuses the same amortization math as
`finmodel.project_bankability.debt_service_coverage_ratio`, but adds that fee as a real annual cash outflow
on top of the loan's own repayment, and reports the DSCR with and without the fee side by side — so the
fee's real (usually small) cost is visible rather than the scheme being modeled as a free improvement.

`examples/india_corporate_tax_regimes_demo.json`'s CGTMSE example is deliberately tuned to land right on the
boundary: a ₹5cr MSME loan at 10.5%/7yrs clears a 1.20x DSCR covenant on its debt service alone (1.216x) but
**breaches it once the guarantee fee is added** (1.174x) — the exact, real trade-off CGTMSE represents:
access to a loan that might not exist at all without it, at a small ongoing coverage cost.

## Test coverage

`tests/test_india_corporate_tax_regimes.py` (6 tests, new file) checks every effective tax rate against the
statutory identity computed independently in the test, checks post-tax IRR the rigorous way — reconstructing
the cash-flow stream and confirming its NPV at the module's own returned IRR is ~0 — checks that a lower tax
rate always produces a strictly higher IRR (115BAB > 115BAA > standard, by construction), and checks that the
CGTMSE fee tips a boundary case from compliant to breach. `tests/test_cli.py` adds a CLI round-trip test.
