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

- ~~**American (deal-by-deal) PE carry waterfall with clawback**~~ — **RESOLVED**, see `docs/DEFERRED_GAPS_REVISITED.md`: built as `finmodel.vc_fund_metrics.american_waterfall()`. The "full multi-year fund dataset" the original deferral asked for was unnecessary — a small hand-constructed example (a winner realized before a loser) is enough to demonstrate and test the real clawback mechanic.
- ~~**Earnout / contingent-consideration valuation (ASC 805)**~~ — **RESOLVED**, see `docs/DEFERRED_GAPS_REVISITED.md`: built as `finmodel.earnout_valuation` (scenario-weighted expected value for discrete milestones, plus a binary-digital-option method for continuous financial-metric thresholds reusing `finmodel.options.norm_cdf`) — the "Monte-Carlo" framing above was the wrong comparison; a continuous-metric earnout has a closed-form solution.
- ~~**Bornhuetter-Ferguson reserving**~~ — **RESOLVED**, see `docs/DEFERRED_GAPS_REVISITED.md`: built as `finmodel.loss_reserving.bornhuetter_ferguson()`. The "real dataset" requirement above was unnecessary — the a-priori expected loss is a caller-supplied input, not something the module needs pre-loaded.

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
