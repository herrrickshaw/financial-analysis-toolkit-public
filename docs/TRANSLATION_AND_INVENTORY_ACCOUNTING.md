# Foreign currency translation and inventory costing

A third fresh pair, continuing from `docs/CORPORATE_ACCOUNTING_TREASURY_TOOLS.md` and
`docs/COMPENSATION_AND_DEBT_ACCOUNTING.md`: foreign currency translation (ASC 830) and inventory costing
(FIFO/LIFO/weighted average). Both real, common accounting mechanics with no prior representation across the
toolkit's other ~50 modules, checked against what already exists before being built.

| New module | Real technique | Checked against, and confirmed distinct from |
|---|---|---|
| `finmodel.foreign_currency_translation` | ASC 830's current rate method for consolidating a foreign subsidiary — assets/liabilities at the current rate, equity at historical rates, the income statement at the average rate, with a Cumulative Translation Adjustment plug through OCI | `finmodel.fx_hedging` (a specific TRANSACTION exposure a company chooses to hedge — translation exposure instead arises automatically every period just from consolidating a subsidiary's statements, whether or not anything is hedged, and flows through OCI rather than net income) |
| `finmodel.inventory_costing` | FIFO, LIFO, and weighted-average cost-flow assumptions for splitting the cost of goods available for sale between cost of goods sold and ending inventory | nothing existing — inventory costing is a wholly new accounting category here |

## Real technique, and why it was built this way

- **Translation exposure is not the same thing as transaction exposure.** `finmodel.fx_hedging` (built in the
  prior round) prices hedges for a SPECIFIC future foreign-currency cash flow a company deliberately takes
  on and can choose to hedge or not. Translation exposure, by contrast, arises automatically every reporting
  period the moment a company consolidates a foreign subsidiary's financial statements — there is no
  transaction to hedge, and the resulting Cumulative Translation Adjustment goes to Other Comprehensive
  Income, never to net income. Building both modules side by side makes this real, commonly-confused
  distinction concrete rather than leaving it as a definitional footnote.
- **The Cumulative Translation Adjustment is a plug, by construction** — `translate_balance_sheet()`
  computes it as whatever value makes translated assets equal translated liabilities plus translated equity
  exactly, which the module's own test suite verifies as an identity rather than an approximation. The real,
  intuitive sign check that also comes free from this construction: CTA is positive when the foreign currency
  APPRECIATED during the period (net assets translate at a stronger current rate than the historical/average
  rates they were funded or earned at) and negative when it depreciated — verified directly with matching
  appreciation and depreciation examples built from the same underlying numbers.
- **Every inventory-costing method must conserve the exact same total cost** — FIFO, LIFO, and weighted
  average only decide how the cost of goods available for sale gets SPLIT between cost of goods sold and
  ending inventory; none of them can change that total. The toolkit's test suite checks this identity
  directly for all three methods on the same three-layer, rising-cost example, alongside the real, classic
  accounting-textbook property it also produces: FIFO reports the lowest cost of goods sold (and so the
  highest gross profit) in a period of rising costs, LIFO the highest, and weighted average lands exactly in
  between.

## Test coverage

`tests/test_foreign_currency_translation.py` (4 tests, new file) checks the current-rate method against a
full hand-computed example, checks the balance-sheet identity the CTA plug exists to enforce, and checks the
CTA sign property against both an appreciating- and a depreciating-currency version of the same numbers.
`tests/test_inventory_costing.py` (6 tests, new file) checks each of the three methods against a hand-traced
three-layer purchase history, checks the cost-conservation identity for all three, checks the real
FIFO-lowest/LIFO-highest directional property, and checks that selling more units than are available is
rejected.
