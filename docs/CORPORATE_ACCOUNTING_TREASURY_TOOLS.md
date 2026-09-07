# Corporate accounting and treasury tools: leases, FX exposure hedging

A fresh pair of modules rather than another revisit of this session's own deferred list: lease accounting
(ASC 842) and corporate FX transaction-exposure hedging. Both are real, extremely common corporate-finance
disciplines that had no representation across the toolkit's ~50 other modules — checked against what already
exists before being built, to confirm each was genuinely new.

| New module | Real technique | Checked against, and confirmed distinct from |
|---|---|---|
| `finmodel.lease_accounting` | ASC 842 lessee lease classification (finance vs. operating), initial lease-liability/ROU-asset measurement, and the two types' genuinely different subsequent-expense mechanics | `finmodel.tax_provision` (ASC 740) and `finmodel.percentage_of_completion` (ASC 606) are this toolkit's other two directly-implemented accounting standards; leases are a third, structurally unrelated one — no overlap |
| `finmodel.fx_hedging` | The forward-hedge vs. money-market-hedge vs. unhedged comparison for a corporate FX transaction exposure (a future foreign-currency receivable or payable) | `finmodel.carry_trade` (the SAME covered-interest-rate-parity identity, but for a speculative "borrow low, invest high" trade rather than a corporate treasury hedging a real underlying exposure) |

## Real technique, and why it was built this way

- **ASC 842's finance-vs-operating classification** uses the five real criteria in ASC 842-10-25-2:
  ownership transfer, a bargain purchase option reasonably certain to be exercised, an asset so specialized
  it has no alternative use to the lessor, the lease term covering the major part of the asset's remaining
  economic life, and the present value of payments representing substantially all of the asset's fair value.
  `classify_lease()` implements the last two using the 75%/90% thresholds carried forward from the old ASC
  840 bright-line tests — ASC 842 itself is principles-based and doesn't mandate a specific percentage, but
  these thresholds remain the standard, widely-used proxy for "reasonably certain" in practice (documented in
  every Big 4 lease-accounting implementation guide, e.g. KPMG's *Leases Handbook*, Deloitte's *A Roadmap to
  Applying the New Leases Standard*).
- **Both lease types get the SAME initial lease liability and ROU asset** — the real, defining change ASC
  842/IFRS 16 made versus the old rules, which kept operating leases entirely off-balance-sheet. They diverge
  only in subsequent expense recognition: a finance lease behaves like an amortizing loan (front-loaded
  interest declining over time, level straight-line ROU amortization on top — so total expense DECLINES),
  while an operating lease recognizes one FLAT total expense every period (the level average of undiscounted
  payments), with the ROU-asset amortization computed as a plug (that flat expense minus the period's
  interest accretion on the liability) so the balance sheet still reconciles even though the P&L shows one
  number. The toolkit's test suite verifies the front-loaded property for finance leases and, using the clean
  special case of level lease payments (where straight-line expense equals the payment exactly), verifies the
  flat-expense property and the plug's defining identity (it sums to exactly the initial ROU asset).
- **This module deliberately implements ASC 842, not IFRS 16** — a real, easy-to-miss difference the module's
  own docstring calls out explicitly: IFRS 16 removed the lessee operating-lease classification entirely, so
  under IFRS 16 (short-term/low-value exceptions aside) every lease uses the finance-lease mechanic this
  module implements, with no flat-expense operating treatment at all. Reporting under IFRS 16 with this
  module's `operating_lease_schedule()` would be a real, substantive error, not just a labeling difference.
- **The forward hedge and the money-market hedge give EXACTLY the same result** — not approximately, but
  algebraically identically, because covered interest rate parity is precisely the identity that makes the
  two constructions cancel out (the same real result this toolkit's `finmodel.carry_trade.
  break_even_depreciation` already demonstrated from the speculative side of the same identity). The
  toolkit's test suite checks this directly for both a receivable and a payable exposure — a company gets no
  economic benefit from choosing one hedge over the other, only an operational one (which instrument it can
  actually access).

## Test coverage

`tests/test_lease_accounting.py` (10 tests, new file) checks each of the five real ASC 842 finance-lease
triggers individually (including the exact 75%/90% threshold percentages), checks initial measurement against
an independently-summed present value, checks the finance-lease schedule's front-loaded-expense property
alongside an exact first-period interest hand calc, and checks the operating-lease schedule's flat-expense
property and its ROU-amortization-plug identity using the clean level-payment special case.
`tests/test_fx_hedging.py` (5 tests, new file) checks the module's central forward-equals-money-market-hedge
claim directly for both a receivable and a payable exposure, alongside a hand calc of the forward rate itself.
