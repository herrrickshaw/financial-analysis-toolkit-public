# Income Tax Act depreciation: block of assets, section 50, and additional depreciation

`finmodel.india_depreciation_schedule` — written-down-value (WDV) depreciation computed the way the Income
Tax Act 1961 actually computes it: by **block of assets**, not asset by asset. No prior representation
across the toolkit's other ~65 modules: `finmodel.india_corporate_tax_regimes` explicitly notes that a
115BAB/115BAA elector forgoes additional depreciation, but nothing in this toolkit actually computed a
depreciation schedule under any regime until now.

## Why block-of-assets, not asset-by-asset

Section 32 groups all assets of the same class and rate into one **block**. Depreciation is charged on the
block's written-down value as a whole — an addition and a deletion in the same block in the same year net
against each other before the rate is applied, and an individual asset's own "life" stops being tracked once
it enters a block. This is a fundamentally different mechanic from straight-line per-asset depreciation
(e.g. IFRS/US GAAP book depreciation), and conflating the two would misstate both the depreciation deduction
and, in edge cases, trigger a capital-gains consequence that a per-asset model would never surface.

**Rates used** (Income-tax Rules 1962, New Appendix I, post the Finance Act 2017 rationalization that capped
the highest rate at 40%): buildings 5%/10%/40% (residential/general/purely temporary structures), furniture
& fittings 10%, plant & machinery (general) 15%, motor vehicles 15% (30% if used in a hire business),
computers & software 40%, intangible assets 25% (know-how, patents, copyrights, trademarks, licences,
franchises).

## The half-year rule

An addition put to use for **180 days or more** in its year of acquisition gets the full rate that year. An
addition used for **less than 180 days** gets only **half** the rate in that first year — it becomes part of
ordinary opening WDV (full rate) from the following year onward. `block_depreciation` takes
`full_rate_additions` and `half_rate_additions` as separate inputs for exactly this reason, rather than a
single "additions" figure.

## Section 50: when depreciation is nil and a capital gain appears instead

If sale proceeds/scrap value realized on assets sold out of a block during the year (`deletions`) exceed the
block's WDV before depreciation (opening WDV + this year's additions), depreciation on that block is **nil**
and the excess is a **short-term capital gain** under section 50 — regardless of whether every asset in the
block was actually sold, i.e. the block need not literally "empty out" for this to trigger. `block_depreciation`
computes this directly: deletions are first applied against the full-rate base (opening WDV + full-rate
additions); if that goes negative, the shortfall spills into the half-rate base next, and only a shortfall
beyond *both* becomes a reported `short_term_capital_gain`.

`tests/test_india_depreciation_schedule.py` verifies all three regimes of this identity by hand: normal
depreciation, a deletion that spills from the full-rate base into the half-rate base without triggering a
gain, and a deletion large enough to extinguish the whole block and produce a gain.

## Section 32(1)(iia): additional depreciation for new manufacturing plant & machinery

A company engaged in manufacturing or power generation/transmission/distribution gets an *additional*
depreciation of **20% of the actual cost** of new plant & machinery it acquires and installs — on top of,
not instead of, the normal WDV depreciation on the same asset. It excludes second-hand P&M, office
appliances, road transport vehicles, ships, aircraft, and anything already eligible for 100% first-year
depreciation. If the asset is used for less than 180 days in the year of acquisition, only **half** (10%) is
allowed that year, with the **balance 10% allowed in full in the immediately succeeding year** — a rule
added by the Finance Act 2015 (effective AY 2016-17) specifically to stop the half-year restriction from
permanently costing a taxpayer half the deduction, the way it does for ordinary WDV additions.
`additional_depreciation_sec32_1_iia` reports `current_year` and `carried_forward_to_next_year` separately
so a caller can apply the carry-forward in the correct subsequent year rather than losing it.

**Not modeled**: this deduction is unavailable to a 115BAB/115BAA elector (see
`docs/INDIA_CORPORATE_TAX_AND_CGTMSE.md`) — that eligibility gating is the caller's responsibility, this
module only computes the mechanic itself. Also out of scope: 100%-first-year-depreciation asset categories
(e.g. certain pollution-control/energy-saving devices) and MAT/book-depreciation differences, for the same
reason `india_corporate_tax_regimes` excludes MAT — no book-income visibility.

## Test coverage

`tests/test_india_depreciation_schedule.py` (7 tests, new file) hand-verifies `block_depreciation` in its
ordinary case, the deletion-spillover case, and the section 50 block-extinguishment case; verifies
`multi_year_block_schedule` correctly rolls closing WDV into the next year's opening WDV across three years
including a mid-schedule deletion; verifies `additional_depreciation_sec32_1_iia`'s full-rate and
half-rate-with-carry-forward cases sum to the same total either way; and verifies `from_dict` bundles all
three calculations. `tests/test_cli.py` adds a CLI round-trip test against
`examples/india_depreciation_schedule_demo.json`.
