# Operating-finance tools: reserving, tax provision, development, trade finance

A fourth round of "keep building more tools like this," picking up where `docs/FPA_GALLERY_GAP_ANALYSIS.md`
left off. Rather than surveying another external template gallery, this pass looked across the toolkit's
own ~35 modules for real, standard corporate-finance disciplines that recur constantly in practice but had
no representation yet — each is a named, textbook-defined technique, not a generalization of a one-off
finding, and each was checked for overlap with what already exists before being built:

| New module | Real technique | Checked against, and confirmed distinct from |
|---|---|---|
| `finmodel.loss_reserving` | Chain-ladder loss development triangle / IBNR (Casualty Actuarial Society, Friedland ch. 7) | `finmodel.insurance_pricing` (prices a policy going forward; this reserves for claims already incurred) |
| `finmodel.tax_provision` | ASC 740/IAS 12 deferred tax, valuation allowance, and post-TCJA NOL carryforward (two vintage baskets: pre-2018 100%-offset/20-year expiration vs. post-2017 80%-cap/no expiration) | `finmodel.dcf.unlevered_tax_schedule` (a DCF diagnostic with a simple uncapped loss carryforward, no statutory usage limits); `finmodel.ppa_valuation`'s one-time acquisition DTL (not a recurring provision) |
| `finmodel.real_estate_development` | Ground-up development pro forma: total development cost, a capitalized-interest construction-loan draw schedule, yield on cost, and the development spread against market cap rates (Geltner/Miller/Clayton & Eichholtz; Linneman) | `finmodel.project_finance.cap_rate_valuation` (prices an already-stabilized asset, not a ground-up build) |
| `finmodel.working_capital_financing` | Invoice-factoring effective cost, the classic early-payment-discount APR formula ("2/10, net 30"; Brealey/Myers/Allen), and asset-based-lending borrowing-base availability | `finmodel.ratios`' cash-conversion-cycle *diagnostics* (days-based; this module instead prices the financing instruments that fund that cycle) |

## What was deliberately left out

- **American (deal-by-deal) PE carry waterfall with clawback** — `finmodel.vc_fund_metrics.carry_waterfall` already implements the European (whole-fund) structure with a GP catch-up; a deal-by-deal alternative is real and used by some funds, but shares nearly all of the same tier mechanics, and a clawback provision needs a full multi-period fund cash-flow history to be meaningful rather than the point-in-time snapshot this toolkit's other waterfalls take. Deferred until there's a real multi-year fund dataset to model it against.
- **Earnout / contingent-consideration valuation (ASC 805)** — real and distinct from anything built, but the standard implementations are either a simple scenario-probability-weighted expected value (a thin wrapper with no new formula) or a full Monte-Carlo/option-pricing treatment (a much larger undertaking that would need its own random-scenario infrastructure this toolkit doesn't have yet). Flagged as a real future candidate rather than built now.
- **Bornhuetter-Ferguson reserving** — the natural next step after chain-ladder (blends a chain-ladder projection with an a-priori expected-loss-ratio estimate, useful when a recent accident year's chain-ladder projection is unstable due to thin data) — deferred as a direct, well-scoped extension of `finmodel.loss_reserving` rather than a new module, once there's a real dataset with an a-priori loss ratio to reconcile it against.

## Test coverage

`tests/test_loss_reserving.py` (5 tests) reconstructs the age-to-age factors independently from the raw
triangle sums (not by calling the module's own factor function) and checks the cumulative development
factors' defining property — they must decrease monotonically toward 1.0 as a period nears the latest known
one, whenever the underlying development factors all exceed 1. `tests/test_tax_provision.py` (10 tests)
checks the deferred-tax and rate-reconciliation math against hand calculations, and separately verifies the
NOL schedule's two real statutory behaviors: a post-2017 balance is capped at exactly 80% of the income
remaining after the pre-2018 balance is used, and a pre-2018 balance that runs out its counted years expires
unused rather than continuing to offset income. `tests/test_real_estate_development.py` (5 tests) checks the
construction-loan schedule's capitalized interest against a hand-rolled period-by-period recomputation, and
checks the full pro forma at an exact breakeven case (yield on cost equal to the exit cap rate must give a
zero IRR and zero profit) plus a profitable case with a hand-solvable IRR (`-100 + 300/(1+r) = 0` → `r = 2.0`
exactly). `tests/test_working_capital_financing.py` (5 tests) checks the factoring and ABL math against hand
calculations, and confirms the discount-APR formula reproduces the standard textbook figure (~37.2%) for the
classic "2/10, net 30" trade-credit terms.
