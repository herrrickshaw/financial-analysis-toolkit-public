# Investment incentives: the mechanics behind India's central and state schemes

`finmodel.investment_incentives` — a new domain for the toolkit (government investment-promotion
incentives) built the same way as every other module here: as a small set of generic, exactly-verifiable
arithmetic mechanics, not a bespoke formula per scheme.

## Why a generic engine, not one function per scheme

Indian central and state investment-incentive schemes — Madhya Pradesh's Investment Promotion Assistance
("BIPA"), the equivalent schemes in other states, and central schemes like the Production Linked Incentive
(PLI) — read like dozens of unrelated policies, but their *mechanics* repeat constantly. Every scheme
surveyed for this module (see `docs/INDIA_STATE_INVESTMENT_INCENTIVES.md` and
`docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md` for the actual catalog, with citations) is built from some
combination of:

| Mechanic | Shape | Function |
|---|---|---|
| Capital subsidy | flat % of eligible fixed capital investment (FCI), capped | `capital_investment_subsidy` |
| Interest subsidy | % of interest actually paid, reimbursed yearly up to a per-annum cap, for a fixed tenure | `interest_subsidy_schedule` |
| Net-tax (SGST/VAT) reimbursement | % of net state tax paid, yearly cap AND a cumulative overall cap (often % of FCI) | `net_tax_reimbursement_schedule` |
| Employment generation subsidy | flat amount per eligible employee per month, for a fixed duration, capped | `employment_generation_subsidy` |
| Ad valorem duty exemption | % exemption of an otherwise-payable statutory charge (stamp duty, electricity duty) | `ad_valorem_duty_exemption` |
| Incremental-metric-linked incentive | % of the INCREASE in a metric (typically sales) over a base year, capped — the PLI mechanic | `incremental_metric_linked_incentive` |

A specific scheme is then just a set of parameters fed into these functions — a state's actual policy
document tells you the *rate*, *cap*, and *tenure*; this module supplies the *arithmetic*, which is exactly
verifiable regardless of whose numbers you plug in.

`combined_incentive_package` aggregates any mix of these (each tagged with a scheme name and
`"state"`/`"central"` jurisdiction) into a total, a breakdown by scheme, and a breakdown by jurisdiction — so
a real investment decision can see its full stacked central+state incentive value in one place.
`effective_capex_after_incentives` turns an upfront capital subsidy into the resulting net capex and
effective subsidy percentage.

## Real technique, and why it was built this way

- **The net-tax reimbursement schedule enforces TWO caps at once, not one.** Every year's reimbursement is
  bounded by that year's own cap, but the running cumulative total is *also* bounded by the scheme's overall
  lifetime ceiling (commonly a percentage of FCI) — once that's exhausted, later years pay nothing further
  even if they'd otherwise be within their own annual cap. This is exactly the shape of Madhya Pradesh's
  "Basic/Yearly Investment Promotion Assistance" structure (a yearly assistance figure bounded by a
  multi-year total) and its equivalents elsewhere (Odisha's SGST reimbursement capped at 200% of P&M cost;
  Haryana's block-based net-SGST reimbursement). The test suite verifies the defining property directly:
  cumulative reimbursement never exceeds the overall cap at any point in the schedule, even when no
  individual year's own cap was the binding constraint.
- **The incremental-metric-linked incentive is a genuinely different mechanic from the others, not a relabeled
  capital subsidy.** PLI schemes pay a percentage of the *increase* in sales/turnover over a base year — an
  investment that doesn't grow sales earns nothing, no matter how much capex went in. The module models this
  as its own function rather than reusing `capital_investment_subsidy`, and the test suite confirms a
  below-base-year case earns exactly zero.
- **`combined_incentive_package` and `effective_capex_after_incentives` are aggregation-only** — they take
  already-computed component amounts (from this module or from any other reliable source) and never
  re-derive a rate, so they can't silently double-apply or contradict a per-scheme calculation upstream.

## On the specific numbers

This module contains no hardcoded state or central scheme rates. The example
(`examples/investment_incentives_demo.json`) uses illustrative, hand-verified numbers labeled
"BIPA-style"/"illustrative" — not asserted as any specific state or central scheme's actual current rate.
The real, citation-backed rates this toolkit could confirm (and, just as importantly, the ones it explicitly
could **not** confirm from a primary source) are cataloged separately in
`docs/INDIA_STATE_INVESTMENT_INCENTIVES.md` and `docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md`, each entry
citing its source. Government incentive schemes change frequently and vary by investment vintage, so those
catalogs should be read as a starting point for populating this module's inputs, not as a locked reference —
every entry marked "not confirmed in source" should be checked against the primary policy document before
being relied upon.

## Test coverage

`tests/test_investment_incentives.py` (13 tests, new file) hand-checks every mechanic, including both an
uncapped and a capped case for each, the overall-cap-exhaustion property of the net-tax reimbursement
schedule (with an explicit check that cumulative reimbursement never exceeds the overall cap at any point),
and that the incremental-metric incentive earns nothing below the base year. `tests/test_cli.py` adds a CLI
round-trip test against the example JSON.
