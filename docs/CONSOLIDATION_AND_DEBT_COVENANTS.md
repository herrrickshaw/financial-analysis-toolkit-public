# Consolidation accounting and debt covenant compliance

A sixth fresh pair: consolidation/noncontrolling-interest accounting (ASC 810) and borrower-side debt
covenant compliance testing. Both real, common calculations with no prior representation across the
toolkit's other ~50 modules, checked against what already exists before being built.

| New module | Real technique | Checked against, and confirmed distinct from |
|---|---|---|
| `finmodel.consolidation` | ASC 810 full consolidation of a majority-owned subsidiary, with the Noncontrolling Interest (NCI) carve-out on both the income statement and balance sheet, and NCI's real, GAAP-specific fair-value measurement at acquisition | `finmodel.merger`/`finmodel.ppa_valuation` (both price and structure a deal; neither consolidates a less-than-wholly-owned subsidiary afterward) |
| `finmodel.debt_covenants` | The real leverage, interest-coverage, and fixed-charge-coverage covenants that govern most corporate term loans and revolving credit facilities, tested from the BORROWER's own side, each reporting a real "headroom" figure | `finmodel.bank_model`'s leverage ratio (a BANK's own Tier 1 regulatory capital ratio — a completely different concept); `finmodel.cash_flow_forecast`'s minimum-cash covenant (a pure liquidity test, not an income-statement-driven leverage/coverage test) |

## Real technique, and why it was built this way

- **Consolidated net income includes 100% of the subsidiary, with NCI carved OUT afterward** — not merely
  the parent's proportionate share included from the start. This is the real, defining mechanic ASC 810
  requires, and the toolkit's test suite checks the identity directly: consolidated net income minus NCI's
  carve-out must equal exactly what's attributable to the parent (the number that actually drives the
  parent's own EPS).
- **NCI's fair-value measurement at acquisition is a real, deliberately different US-GAAP convention** — the
  module's docstring documents the real IFRS alternative (measuring NCI at its proportionate share of
  identifiable net assets instead) explicitly, the same pattern already used for ASC 842 vs. IFRS 16 in
  `finmodel.lease_accounting` and for pre-2018 vs. post-2017 NOL rules in `finmodel.tax_provision` — a
  standard I've now applied consistently whenever a US-GAAP-specific module has a real, named, differently-
  computed international counterpart.
- **Every covenant test reports a headroom figure, not just a pass/fail flag** — the real number a
  borrower's own treasury function tracks quarter to quarter, since a covenant that is merely compliant today
  with shrinking headroom is a materially different credit risk than one sitting on a wide, stable buffer.
  The test suite checks each covenant's compliance boundary directly (a leverage ratio exactly at the maximum
  passes; one basis point past it fails), the same care given to every threshold-based check elsewhere in
  this toolkit (RBI's NPA DPD buckets, Basel's IRB maturity floor).
- **Fixed charge coverage is a real, deliberately stricter covenant layered on top of interest coverage** —
  a borrower can service pure interest comfortably while still being unable to cover the actual combined cash
  burden of capex, taxes, and mandatory principal amortization, which is exactly why credit agreements
  commonly require both tests rather than relying on interest coverage alone.

## Test coverage

`tests/test_consolidation.py` (5 tests, new file) checks consolidated net income and the NCI carve-out
against hand calculations and the defining consolidation identity, and checks that NCI's share scales
linearly with ownership percentage. `tests/test_debt_covenants.py` (6 tests, new file) checks each covenant
against hand calculations exactly at and just past its real compliance boundary, and checks that the
compliance summary correctly isolates a single breach among otherwise-compliant covenants.
