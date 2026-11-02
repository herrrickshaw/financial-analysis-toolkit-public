# Module sections

Moved verbatim from the former README; each section summarises one module family and links its detailed doc.

## Advisory-services modules (`docs/ADVISORY_SERVICES.md`)

A market survey of what real fractional-CFO firms ([Flipcarbon](https://flipcarbon.com/fractional-cfo-service)),
impact-investing advisories ([Sagana](https://sagana.com/fund-managers/)), VC funds, and MBB strategy
consultants actually sell, turned into five new modules: `finmodel.cap_table` (priced-round dilution with the
option-pool shuffle, and an exit liquidation-preference waterfall), `finmodel.vc_fund_metrics` (DPI/RVPI/TVPI/
IRR LP reporting and a GP/LP carry waterfall), `finmodel.cash_flow_forecast` (13-week rolling direct-method
cash forecasting with covenant-breach flagging), `finmodel.impact_scoring` (2X Criteria gender-lens screening,
the Impact Management Project's ABC classification, GHG intensity), and `finmodel.strategy_frameworks`
(TAM/SAM/SOM market sizing, the BCG Growth-Share Matrix, the GE-McKinsey Nine-Box Matrix). See
`docs/ADVISORY_SERVICES.md` for what was surveyed, what was built, and what was deliberately left out (already
covered elsewhere, or fundamentally qualitative consulting work with no defensible model to write).

## Big 4 financial-modeling and audit-analytics automation (`docs/BIG4_AUTOMATION.md`)

A market survey of what Deloitte, KPMG, EY and PwC actually sell as financial-modeling and audit services, turned
into three new modules: `finmodel.ppa_valuation` (KPMG's own named "purchase price allocation support" service —
relief-from-royalty and MPEEM income-approach intangible valuation, both grossed up by a real Tax Amortization
Benefit factor, feeding a real ASC 805 goodwill residual into `finmodel.merger.PPA`), `finmodel.impairment_testing`
(Deloitte's own named "impairment analysis" service — the real, structurally DIFFERENT ASC 350 goodwill/
ASC 350-30 indefinite-lived-intangible/ASC 360 long-lived-asset tests, including goodwill's real cap at its own
balance and ASC 360's real two-step undiscounted-cash-flow recoverability screen), and `finmodel.audit_analytics`
(the two real, quantitatively implementable techniques every Big 4 audit-analytics platform converges on —
Benford's Law digit-conformity testing with Nigrini's real MAD thresholds, and rule-based journal-entry testing).
See `docs/BIG4_AUTOMATION.md` for what was surveyed, what was built, and what was deliberately left out (already
covered elsewhere, or a proprietary platform/workflow product with no publishable methodology to replicate).

## More CFI/BIWS/Wall Street Prep templates (`docs/MORE_CFI_TEMPLATES.md`)

A follow-up gap analysis against this toolkit's own 636-entry template catalog (`finmodel catalog list`) plus
Wall Street Prep's and Training The Street's course catalogs, turned into nine new modules — every real,
standard technique this survey originally flagged, closed out across four passes: `finmodel.options`
(Black-Scholes-Merton, the Greeks, put-call parity as a real no-arbitrage check, and implied volatility — CFI's
own named "Black Scholes Calculator"/"Put Call Parity Calculator"), `finmodel.project_finance` (DSCR-based debt
sizing and sculpting, LLCR, and cap rate/NOI real-estate valuation — a standalone course at both Wall Street Prep
and BIWS, separate from corporate 3-statement/DCF modeling), `finmodel.portfolio_optimization` (the real Merton
1972 closed-form Markowitz efficient frontier, tangency portfolio, and Capital Allocation Line — CFI's own named
"Efficient Frontier and CAL Template"), `finmodel.restructuring` (the real 11 U.S.C. § 1129(b)(2) absolute-
priority recovery waterfall, fulcrum-security identification, DIP financing sizing, and post-emergence leverage
— Wall Street Prep/Wharton's "Restructuring & Distressed Investing Certificate"), `finmodel.bank_model` (a bank's
real NII/NIM operating economics, CECL-style provisioning, and regulatory capital ratios checked against the
real US Prompt Corrective Action thresholds — CFI's "Bank and FIG Financial Model Template"), `finmodel.
cohort_analysis` (SaaS retention curves, the real GRR-vs-NRR distinction, LTV and LTV:CAC — CFI's "Cohort
Analysis"/"LTV CAC Ratio" templates), `finmodel.insurance_pricing` (combined ratio, the real operating-ratio
refinement, and loss-cost-multiplier rate making — CFI's "InsurTech Pricer Model"), `finmodel.
convertible_bonds` (bond floor plus an embedded call option, directly reusing `finmodel.options` — a real named
category at both CFI and Wall Street Prep), and `finmodel.cmo` (PSA prepayment-speed modeling and sequential-pay
CMO tranching, checked for the two properties every real CMO offering document's PSA-speed table demonstrates:
Weighted Average Life increasing monotonically down the tranche stack, and shortening for every tranche as
prepayment speed rises). All nine are pure Python with no numpy/scipy dependency. See `docs/MORE_CFI_TEMPLATES.md`
for the complete survey — every item it originally flagged is now built.

## Due-diligence tools (`docs/DUE_DILIGENCE_TOOLS.md`)

A different kind of source this time: reviewing a real, external, CFI-formatted project-finance model (a 10-year
LNG-bunkering term-loan facility) surfaced three genuine issues by hand, each generalized into a reusable, tested
tool rather than a one-off fix. `finmodel.dcf.check_unlevered_tax_consistency()` catches a real, easy-to-miss DCF
bug — a "Free cash flow" line that correctly excludes interest but deducts the company's REAL (interest-
deductible) cash tax instead of a hypothetical unlevered one, double-counting the interest tax shield against a
WACC that already carries an after-tax cost of debt term (verified: reconstructs the real file's own $41,716
finding exactly). `finmodel.fin.smooth_ramp()` replaces an implausible front-loaded volume/capacity ramp (a real
264% single-year jump in the reviewed file) with a constant-CAGR path landing on the same plateau — general
enough for any new-capacity or new-cohort assumption, not just LNG bunkering. `finmodel.project_finance` gained
`level_annuity_schedule()`, `interest_only_bullet_schedule()` (the reviewed facility's own real lender terms, not
previously representable), `balloon_coverage_ratio()` (does cash actually accumulated over the interest-only
years cover the bullet, the real question a stand-alone maturity-year DSCR can't answer), and
`compare_debt_structures()` (the real total-interest-vs-cash-flow-relief trade-off, quantified side by side
across all three structures on the same cash flow).

## FP&A template-gallery gap analysis (`docs/FPA_GALLERY_GAP_ANALYSIS.md`)

A survey of ten free-template galleries published by FP&A *software vendors* (Cube Software, the Microsoft
Excel Cloud gallery, Smartsheet, Vertex42, insightsoftware, Vena Solutions, PivotXL, Wall Street Prep,
Coefficient, SCORE.org) — the operating-process templates finance teams reach for once a model leaves the
classroom-CFI world, distinct from the CFI/BIWS catalog surveys above. The full source-to-category-to-
module cross-reference is a machine-readable graph at
[`catalog/fpa_gallery_graph.json`](catalog/fpa_gallery_graph.json). Seven categories were cited by multiple
independent galleries, were genuinely new, and had a real formula-defined technique behind them — all seven
are now built: `finmodel.variance_analysis` (budget-vs-actual price/volume variance, Horngren's multi-
product sales mix/quantity variance, horizontal/vertical statement analysis), `finmodel.fpa_planning`
(headcount cost schedule with staggered start dates, driver-based rolling forecast that re-anchors off the
latest actual), `finmodel.breakeven` (contribution margin, break-even point, margin of safety, degree of
operating leverage), and `finmodel.cap_table.vc_method_valuation()` (Sahlman's VC Method — HBS — working
backward from a target exit value/return to required ownership and implied pre-/post-money valuation). See
`docs/FPA_GALLERY_GAP_ANALYSIS.md` for what else was found and why it was deferred (sales quota planning,
WIP/percentage-of-completion) or ruled out of scope (AOP orchestration, close checklists, trial-balance
automation, personal-finance calculators).

## Operating-finance tools (`docs/OPERATING_FINANCE_TOOLS.md`)

A fourth round of tool-building: real, standard corporate-finance disciplines that recur constantly in
practice but had no representation across the toolkit's other ~35 modules yet, each checked for overlap
with what already exists before being built. `finmodel.loss_reserving` (the actuarial chain-ladder loss
development triangle and IBNR estimate — Casualty Actuarial Society, Friedland — distinct from
`finmodel.insurance_pricing`'s forward-looking rate making), `finmodel.tax_provision` (ASC 740/IAS 12
deferred tax, valuation allowance, and a post-TCJA NOL carryforward that tracks the real pre-2018
100%-offset/20-year-expiration basket separately from the post-2017 80%-cap/no-expiration basket),
`finmodel.real_estate_development` (a ground-up development pro forma — total development cost, a
capitalized-interest construction-loan draw schedule, yield on cost, and development spread — distinct from
`finmodel.project_finance`'s stabilized-asset cap-rate valuation), and `finmodel.working_capital_financing`
(invoice-factoring cost, the classic "2/10, net 30" early-payment-discount APR formula, and asset-based-
lending borrowing-base availability). See `docs/OPERATING_FINANCE_TOOLS.md` for what was checked against
existing modules to avoid duplication, and what was deliberately deferred (an American deal-by-deal PE carry
waterfall, ASC 805 earnout valuation, Bornhuetter-Ferguson reserving).

## Retail-banking and FX tools (`docs/RETAIL_BANKING_TOOLS.md`, `docs/BANKING_LITERATURE_SURVEY.md`)

Two rounds, both direct-requested rather than survey-driven. The fifth: loan (EMI) mechanics, RD/FD deposit
mechanics, loan amortization adjustments, and FX carry-trade economics. `finmodel.retail_loans` (monthly
reducing-balance EMI, amortization schedule, part-prepayment with the real reduce-tenure-vs-reduce-EMI
choice — reduce-tenure provably saves at least as much interest as reduce-EMI for the same prepayment —
floating-rate reset, foreclosure payoff, and FOIR-based loan eligibility, the underwriting metric Indian
banks publish directly in their own lending policies), `finmodel.retail_deposits` (Fixed Deposit compound
interest, Recurring Deposit maturity computed by simulating each monthly installment's own compounding to
maturity rather than trusting one of the inconsistently-derived closed-form "banker's formulas," premature
RD closure, and the real Section 194A rule that TDS withholds the FULL interest amount once the threshold is
crossed, not just the excess), and `finmodel.carry_trade` (covered interest rate parity's no-arbitrage
forward rate, the unhedged FX carry trade's real cash flow, and a break-even depreciation that this toolkit's
own test suite confirms is EXACTLY the CIP forward premium — the textbook "forward premium puzzle" result).
The sixth added `finmodel.revolving_credit` (daily-outstanding-balance interest shared by cash-credit/
overdraft accounts and credit-card billing cycles, and a credit-card minimum-payment schedule that
demonstrates a real negative-amortization trap) and `finmodel.npa_classification` (RBI's IRAC asset-
classification ladder by days-past-due and NPA age, with secured/unsecured provisioning at the published
rates). `docs/RETAIL_BANKING_TOOLS.md` covers what was checked against existing modules to avoid duplication
and what was deliberately deferred (step-up/step-down EMI schedules, balance-transfer break-even analysis, a
hedged carry trade, segment-specific provisioning rates); `docs/BANKING_LITERATURE_SURVEY.md` is the
companion literature survey — the real books, regulatory standards (RBI Master Directions, Basel III, ASC
740, IRC §172, the US CARD Act), and academic papers (Fama's 1984 forward-premium-puzzle paper, Mack's
chain-ladder statistics) behind every banking-related module in the toolkit, a gap `docs/LEARNING_GUIDE.md`
never covered since it's scoped to corporate-finance valuation instead.

## A pipeline of tools (`finmodel.pipeline`, `docs/PIPELINE.md`)

Every module already exposes the same `from_dict(d) -> dict` shape its own CLI command calls, so chaining
modules together needed only a small amount of glue rather than a new execution model: `finmodel.pipeline`
runs a list of `{"name", "module", "inputs"}` steps in order, and any input value written as exactly
`"${step_name.path.to.value}"` is replaced with the real value at that path in an earlier step's actual
output (a dict-key or list-index lookup per dotted segment) before that step runs. `examples/
pipeline_retail_lending_demo.json` chains three different modules into one coherent loan lifecycle: FOIR-
based loan eligibility (`finmodel.retail_loans`) → that EXACT principal's amortization schedule → the real
RBI provisioning the bank would need to hold (`finmodel.npa_classification`) if that specific loan's real
balance 24 months in later turned delinquent — every number flowing from the step before it rather than
being independently made up. See `docs/PIPELINE.md` for what was deliberately left out of scope (a
parallel-execution dependency graph, conditional branching) and why a strict ordered list is the right size
for chaining pure, fast finance calculations rather than a general workflow engine.

## Professor and course survey (`docs/PROFESSOR_COURSE_SURVEY.md`)

A different kind of survey: instead of a template gallery or a reading list, this one cross-references real,
named professors and their real, currently-taught courses (checked live via web search) — Bruce Tuckman's
NYU Stern fixed-income course, P C Narayan's IIM Bangalore banking-risk course, Ohio State's Financial
Institutions syllabus, NYU Stern's real-estate specialization, HEC Paris' financial-engineering electives,
and the P&C actuarial ratemaking/reserving curriculum taught across several universities — against this
toolkit's coverage. Three real, course-confirmed gaps were closed: `finmodel.credit_risk` (expected loss and
the real Basel II/III Foundation IRB risk-weighted-assets formula, verified against Basel's own published
corporate risk-weight reference point), `finmodel.interest_rate_risk` (the repricing-gap model and NII
sensitivity to a rate shock — closing a gap this toolkit's own literature survey had previously flagged as
deferred), and `finmodel.fixed_income_risk` (bond price, Macaulay/modified duration, DV01, and convexity,
verified against a classic textbook reference bond and the exact zero-coupon-duration identity). See
`docs/PROFESSOR_COURSE_SURVEY.md` for the full professor/course list, the complete cross-reference table, and
what was deliberately left out (credit-card/master-trust securitization, FX exotic-derivatives origination).

## Corporate accounting and treasury tools (`docs/CORPORATE_ACCOUNTING_TREASURY_TOOLS.md`)

A fresh pair rather than another revisit: `finmodel.lease_accounting` (ASC 842 lessee lease classification —
the five real finance-lease triggers, including the 75%/90% thresholds carried forward from the old ASC 840
bright-line tests — initial lease-liability/ROU-asset measurement, and the two lease types' genuinely
different subsequent-expense mechanics: a finance lease's front-loaded interest-plus-amortization versus an
operating lease's single flat expense every period, with the ROU-asset amortization computed as a plug. The
module's own docstring flags a real, easy-to-miss point: it implements ASC 842 specifically, not IFRS 16,
which removed the lessee operating-lease classification entirely — using this module's operating-lease
treatment under IFRS 16 would be a substantive error, not just a labeling difference) and
`finmodel.fx_hedging` (the forward-hedge vs. money-market-hedge vs. unhedged comparison for a corporate FX
transaction exposure — the toolkit's own test suite confirms directly that the two hedges give EXACTLY the
same result, since covered interest rate parity is precisely the identity that makes them cancel out
algebraically, the same real result `finmodel.carry_trade` already demonstrated from the speculative side of
the same identity). See `docs/CORPORATE_ACCOUNTING_TREASURY_TOOLS.md` for the full derivation and what each
module was checked against to confirm it was genuinely new.

## Stock-based compensation and bond issuer accounting (`docs/COMPENSATION_AND_DEBT_ACCOUNTING.md`)

A second fresh pair: `finmodel.stock_based_compensation` (ASC 718 RSU and stock-option grant expense — RSU
fair value needs no option-pricing model at all, just shares times grant-date price, while option grants
reuse `finmodel.options.black_scholes` directly rather than re-deriving it; the two real expense-attribution
methods, straight-line versus graded/accelerated vesting, are verified against a hand-traced four-tranche
example to expense EXACTLY the same total by completion while graded vesting front-loads more expense into
early periods) and `finmodel.bond_amortization` (effective-interest premium/discount amortization, ASC
835-30 — the issuer-side counterpart to `finmodel.fixed_income_risk`'s investor-side duration/convexity;
verified that a bond's carrying value converges to EXACTLY face value by maturity regardless of whether it
issued at a premium or a discount). Building this pair's test suite caught and fixed a real (if tiny)
floating-point bug: a par-priced bond's issue price landed a few billionths of a dollar away from face value
after summing a discounted cash-flow series, which a naive strict comparison misclassified as a microscopic
"discount" before a small tolerance band fixed it. See `docs/COMPENSATION_AND_DEBT_ACCOUNTING.md` for the
full detail.

## Foreign currency translation and inventory costing (`docs/TRANSLATION_AND_INVENTORY_ACCOUNTING.md`)

A third fresh pair: `finmodel.foreign_currency_translation` (ASC 830's current rate method for consolidating
a foreign subsidiary — assets/liabilities at the current rate, equity at historical rates, the income
statement at the average rate, with a Cumulative Translation Adjustment computed as the exact plug that
balances the translated balance sheet, verified to be positive when the foreign currency appreciated during
the period and negative when it depreciated — a real, commonly-confused distinction from `finmodel.
fx_hedging`'s transaction-exposure hedging, since translation exposure arises automatically from
consolidation every period and flows through OCI, not net income, whether or not anything is hedged) and
`finmodel.inventory_costing` (FIFO/LIFO/weighted-average cost-flow assumptions, verified against the
universal cost-conservation identity — the three methods only decide how the same total cost of goods
available for sale gets split, never changing the total — and against the classic real property that FIFO
reports the lowest cost of goods sold and LIFO the highest in a period of rising costs). See
`docs/TRANSLATION_AND_INVENTORY_ACCOUNTING.md` for the full detail.

## Pension accounting and the M&A working-capital peg (`docs/PENSION_AND_MA_WORKING_CAPITAL.md`)

A fourth fresh pair: `finmodel.pension_accounting` (ASC 715's PBO and plan-asset roll-forwards, funded
status, and net periodic pension cost — `service_cost` and `actuarial_gain_loss` are caller-supplied inputs,
the same design choice already made for Bornhuetter-Ferguson's a-priori expected loss, since a plan
actuary's own PBO model is the real source of these figures in practice; the module's central real mechanic
is the deliberate gap between the EXPECTED return smoothing the income-statement cost and the ACTUAL return
driving the balance-sheet roll-forward, verified across all four functions using the same underlying numbers
to confirm they cohere) and `finmodel.nwc_peg` (the net-working-capital peg — typically a trailing average of
the target's own historical NWC, since a single snapshot can be seasonally distorted — and the closing
true-up that adjusts the purchase price dollar-for-dollar against that peg, with a real de-minimis threshold
below which small differences don't trigger a settlement; distinct from `finmodel.merger`/`comps`/`lbo`,
which all price a deal at signing but none of which implement the POST-signing adjustment every real
definitive purchase agreement includes). See `docs/PENSION_AND_MA_WORKING_CAPITAL.md` for the full detail.

## EPS calculation and investment securities classification (`docs/EPS_AND_INVESTMENT_SECURITIES.md`)

A fifth fresh pair: `finmodel.eps_calculation` (ASC 260 basic and diluted EPS — the treasury stock method for
options, where an out-of-the-money option contributes exactly zero incremental shares by construction, and
the if-converted method for convertible debt, with the real antidilution rule that a security is only
included if it actually reduces EPS, verified directly with a deliberately antidilutive convertible that
gets correctly excluded — which is also why diluted EPS can never exceed basic EPS) and
`finmodel.investment_securities` (ASC 320's trading/available-for-sale/held-to-maturity classification,
verified by running the SAME cost basis and fair value through all three to confirm they route the identical
unrealized gain/loss to three genuinely different places — net income, OCI, or nowhere at all — plus the real
OCI "recycling" mechanic on an AFS sale, checked to fire only for that one classification). See
`docs/EPS_AND_INVESTMENT_SECURITIES.md` for the full detail.

## Consolidation accounting and debt covenants (`docs/CONSOLIDATION_AND_DEBT_COVENANTS.md`)

A sixth fresh pair: `finmodel.consolidation` (ASC 810's full consolidation of a majority-owned subsidiary —
100% of its net income included, with the Noncontrolling Interest carved OUT afterward rather than only the
parent's proportionate share included from the start, verified against that exact identity; plus NCI's real,
GAAP-specific fair-value measurement at acquisition, documented alongside the real IFRS proportionate-share
alternative the same way ASC 842 vs. IFRS 16 already is in `finmodel.lease_accounting`) and
`finmodel.debt_covenants` (the real leverage/interest-coverage/fixed-charge-coverage covenants governing most
corporate credit agreements, tested from the borrower's own side and distinct from `finmodel.bank_model`'s
unrelated bank regulatory leverage ratio; every test reports a real "headroom" figure, verified exactly at
and just past each covenant's compliance boundary). See `docs/CONSOLIDATION_AND_DEBT_COVENANTS.md` for the
full detail.

## Asset retirement obligations and loss accruals (`docs/ARO_AND_LOSS_ACCRUALS.md`)

A seventh fresh pair: `finmodel.asset_retirement_obligations` (ASC 410's present-value liability recognition
and its own defining identity — accreting the liability at the same rate used to discount it must reproduce
the original estimated future cost EXACTLY by the retirement date, verified directly) and
`finmodel.warranty_and_receivables_allowance` (the warranty reserve's expected-cost roll-forward, made at the
point of SALE rather than when a claim is filed, and CECL's aging-schedule allowance for trade receivables —
distinct from `finmodel.bank_model`'s loan CECL, a different asset class typically estimated with a
statistical PD/LGD approach instead — verified with a small, high-risk bucket that carries more allowance
than a much larger, low-risk one). See `docs/ARO_AND_LOSS_ACCRUALS.md` for the full detail.

## Investment incentives (`docs/INVESTMENT_INCENTIVES.md`)

A new domain for the toolkit: `finmodel.investment_incentives` models the small set of mechanics that
Indian central and state government investment-promotion schemes are actually built from — a capital
subsidy (% of eligible fixed capital investment, capped), an interest subsidy (% of interest paid,
reimbursed yearly up to a cap, for a fixed tenure), a net-tax (SGST/VAT) reimbursement schedule (structurally
the same shape as Madhya Pradesh's "Investment Promotion Assistance"/BIPA — bounded by BOTH a per-year cap
AND a cumulative overall cap, verified directly: cumulative reimbursement never exceeds the overall cap even
when no single year's own cap bound), an employment generation subsidy, an ad valorem duty exemption (stamp
duty, electricity duty), and the central PLI mechanic (a percentage of the *increase* in sales over a base
year, capped — verified to earn exactly nothing below the base year). `combined_incentive_package` stacks any
mix of these, tagged by scheme and by state/central jurisdiction, into one total. The module itself contains
no hardcoded scheme rates; `docs/INDIA_STATE_INVESTMENT_INCENTIVES.md` and
`docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md` separately catalog real schemes (PLI sectors, MSME schemes,
tax incentives, and a dozen states' industrial policies) with citations — and, just as carefully, flag every
number that could NOT be confirmed from a primary source rather than guessing. See
`docs/INVESTMENT_INCENTIVES.md` for the full detail.

## Sample state/sector investment models (`docs/SECTOR_INVESTMENT_MODEL.md`)

`finmodel.sector_investment_model` assembles a project's land cost and capex stack, then nets it against a
combined central+state incentive package — but correctly, by *timing*: an upfront capital subsidy nets
directly against day-zero capex, while a recurring incentive (interest subsidy, net-tax reimbursement, PLI
payout) is discounted to a present value with `finmodel.fin.npv` first, since summing an undiscounted
multi-year stream and subtracting it from day-zero capex is a real, common overstatement (verified directly:
a discounted recurring stream's present value is always strictly less than its nominal sum).
`sample_project_matrix` runs this across a whole list of state/sector projects and sums the results — the
"matrix" query surface. Two research passes (land-cost benchmarks from the central India Industrial Land
Bank — which turned out to expose no usable price field — and a dozen state industrial-development-corporation
portals; land-cost confidence carried through per entry) feed a fully worked 28-state matrix in
`docs/INDIA_STATE_SECTOR_INCENTIVE_MATRIX.md` and `examples/state_sector_matrix_demo.json`, cross-referencing
each state's own confirmed scheme parameters against an illustrative project. One state's result comes out
with incentive value exceeding its capex (Tamil Nadu's apparently FCI-uncapped 100%-for-15-years SGST
reimbursement) — reported and explained rather than smoothed over, since it's a genuine finding about how
much a scheme's *cap structure* matters relative to its headline rate. See `docs/SECTOR_INVESTMENT_MODEL.md`
for the full detail.

## Project bankability and investability ranking (`docs/PROJECT_BANKABILITY.md`)

`finmodel.project_bankability` asks the question a lender or investment committee actually asks — does this
clear our hurdle rate? — twice: once on a project's own capex and cash flow, once with incentive cash flows
added (correctly timed, via `sector_investment_model`'s own per-year detail, never re-assumed).
`rank_projects` ranks a list of state/sector projects by IRR both ways and flags
`incentive_enabled_projects` — every project below the hurdle on its own merits that clears it once
incentives are added. Run over the same 28-state matrix (`examples/project_bankability_demo.json`) at an
illustrative 14% hurdle: Chhattisgarh (15.1% IRR) now tops the ranking purely on its confirmed
near-zero land cost — a pure capex-efficiency story, not an incentive one. Gujarat (4.8% → 23.6% IRR), Odisha
(10.6% → 25.5%), Karnataka (12.2% → 18.9%), and Jharkhand (9.9% → 15.5%) are the four projects incentives
specifically make bankable — every project's IRR improves with incentives (verified as an invariant), but
most don't cross the hurdle even so. Jammu & Kashmir shows zero incentive value despite a nominally rich
central scheme (NCSS 2021) — its registration for new applicants closed in 2024.

The same module also answers the narrower, more concrete question a lender tests before disbursing:
`debt_service_coverage_ratio` checks operating cash flow against a loan's own amortized annual repayment
(`finmodel.fin.pmt`) at a minimum DSCR covenant. Real published lender terms (SBI, IREDA, REC — cataloged
with sourcing and staleness flags in `docs/INDIA_PROJECT_FINANCE_LENDING_TERMS.md`) feed this: IREDA
publishes an explicit, dated 1.2x–1.4x DSCR schedule for renewable-energy projects; SBI and REC disclose no
DSCR floor at all for general project finance, so the 1.20x industry-norm figure used for this toolkit's
(non-RE) 28-state matrix is a general convention, not a lender-specific number. Run at a conservative
70%-debt, 1.20x-covenant, operating-cash-flow-only basis (`examples/dscr_matrix_demo.json`): 14 of 27
states/UTs clear it (Chhattisgarh, Tamil Nadu, Jammu & Kashmir, Puducherry, Karnataka, Ladakh, Goa, Odisha,
West Bengal, Jharkhand, Uttar Pradesh, Madhya Pradesh, Kerala, Uttarakhand) — a genuinely different,
complementary answer to the IRR-based ranking above, since a lender won't necessarily credit incentive
income toward debt-service capacity the way an investor credits it toward IRR. See
`docs/PROJECT_BANKABILITY.md` for the
full detail.

## Investment Promotion Agency (IPA) Support workbook (`docs/INDIA_INCENTIVE_WORKBOOK.md`)

`finmodel india-incentive-workbook reports/india_investment_incentives.xlsx` consolidates all seven India
docs above into one filterable/sortable spreadsheet titled **"Investment Promotion Agency (IPA) Support"**
(the file's own document-properties Title) — playing the same role for an investor that a state or central
IPA (Invest India, Invest MP, Invest Karnataka, APIIC, ...) already plays one state/scheme at a time: State
Incentives (18 rows), Central Incentives (26
rows across PLI/MSME/tax/SEZ/credit-guarantee schemes), Land Cost Benchmarks (36 sourced rates), an
18-State Matrix sheet, Tax Regime Comparison, and Financing Effects. The three catalog sheets are a
structured transcription of their source markdown docs, each row carrying its own Confidence and Source
column; the Matrix, Tax Regime, and Financing sheets are computed **live** from the
same example JSON files and modules used everywhere else in this toolkit, never re-typed — enforced directly
in the test suite by reloading those files independently and checking the workbook's numbers match. The
underlying writer, `finmodel.excel.write_record_tables`, is new and general-purpose: every existing writer in
`finmodel.excel` targets a year-series financial-statement layout, which doesn't fit a flat, row-per-record
catalog — this one does, and any future dataset in this toolkit can reuse it. See
`docs/INDIA_INCENTIVE_WORKBOOK.md` for the full detail.

## State/UT government website index (`docs/INDIA_STATE_GOVERNMENT_WEBSITES.md`)

The "where did these numbers come from" map, one row per state/UT: each state's official industries
department/investment-promotion agency and its industrial land portal, for the 29 states/UTs already
researched — plus the 7 North-East states still in progress toward full coverage, listed by name without a guessed URL rather
than an unverified one. See `docs/INDIA_STATE_GOVERNMENT_WEBSITES.md`.

## Tax regime choice, CGTMSE, and a real IREDA renewable-energy entry (`docs/INDIA_CORPORATE_TAX_AND_CGTMSE.md`)

Three follow-ups on the "IPA support" tooling: `finmodel.india_corporate_tax_regimes` compares a new
manufacturer's Section 115BAB (15% base tax) against 115BAA (22%) and the standard regime (30% base, slab-
dependent surcharge) — exact statutory arithmetic (`base_rate*(1+surcharge)*(1+cess)`), not an estimate —
turning the choice into a post-tax IRR: a 3.88-percentage-point swing on Gujarat's own 28-state-matrix
project, purely from the tax election (MAT explicitly out of scope — flagged, not silently ignored). The
same module's `cgtmse_adjusted_dscr` shows CGTMSE's real effect: not a free DSCR improvement, but a small
annual guarantee-fee cost layered onto the loan's own coverage test — tuned to a boundary case that clears
1.20x on debt service alone but breaches it once the fee is added, the actual trade-off for loan access
without adequate collateral. And `examples/dscr_matrix_ireda_demo.json` finally exercises IREDA's own
disclosed renewable-energy terms (8.65% rate, 1.25x DSCR floor) instead of the generic SBI/REC case — a
Rajasthan solar and Gujarat wind project both clear a comfortable 2.195x, a concrete illustration of why
sector-specific lender matching changes the answer. See `docs/INDIA_CORPORATE_TAX_AND_CGTMSE.md` for the
full detail.

## Income Tax Act depreciation: block of assets, section 50, additional depreciation (`docs/INDIA_DEPRECIATION_SCHEDULE.md`)

`finmodel.india_depreciation_schedule` fills a gap `docs/INDIA_CORPORATE_TAX_AND_CGTMSE.md` had only ever
flagged, not modeled: that a 115BAB/115BAA elector forgoes additional depreciation. `block_depreciation`
computes WDV depreciation the way the Income Tax Act actually computes it — by **block of assets**, not
asset-by-asset — including the half-rate rule for additions used less than 180 days, and section 50's real
consequence when a block's deletions exceed its WDV: depreciation goes to nil and the excess becomes a
short-term capital gain, computed directly rather than special-cased. `additional_depreciation_sec32_1_iia`
computes the 20%-of-new-P&M-cost deduction available to manufacturers under the standard regime (halved to
10% with a next-year carry-forward if used less than 180 days) — the exact mechanic the tax-regime module's
115BAB/115BAA comparison had only described in prose until now. See `docs/INDIA_DEPRECIATION_SCHEDULE.md`
for the full detail.

## Revisiting deferred gaps (`docs/DEFERRED_GAPS_REVISITED.md`)

Every survey doc in this session records what got deliberately left out and why — four times now, this
session has gone back to some of those items and found most of them buildable after re-examining the actual
reason each had been deferred. Round 1: `finmodel.loss_reserving.bornhuetter_ferguson()` blends chain-ladder's own
reporting pattern with a caller-supplied a-priori expected loss (the "real dataset" the original deferral
asked for was never actually needed — it's a normal input, not something the module must ship pre-loaded);
verified to converge exactly to chain-ladder's answer for a fully-developed accident year and to diverge from
it for an immature one, the real stabilizing effect the method exists to provide. `finmodel.earnout_valuation`
implements the two real ASC 805 contingent-consideration methods properly: `scenario_weighted_earnout` for
discrete milestones, and `binary_metric_earnout` for a continuous financial-metric threshold — the
"Monte-Carlo" framing that originally deferred this was the wrong comparison, since a continuous-metric
earnout has a closed-form solution as a cash-or-nothing digital option, reusing `finmodel.options.norm_cdf`
directly. `finmodel.retail_loans.step_up_emi_schedule()` handles the most commonly offered real step-up
structure (a fixed percentage increase at a fixed frequency), bisecting on the base EMI since there's no
closed form for an arbitrary step schedule; verified to always cost strictly more total interest than a flat
EMI for the same loan, the real trade-off behind the product's lower early-year affordability.

Round 2: `finmodel.vc_fund_metrics.american_waterfall()` — the deal-by-deal PE carry structure, paying out
each deal's own tiers as it is realized rather than waiting for whole-fund capital return, and tracking
whether the GP's cumulative carry received exceeds what the fund's cumulative profit actually justifies. The
"full multi-year fund dataset" the original deferral asked for was unnecessary — a small hand-constructed
example (a $1M-to-$3M winner realized before a $1M-to-$200,000 loser) is enough to demonstrate and test the
real CLAWBACK mechanic exactly: the GP's $400,000 carry on the winner alone is later found to exceed what the
now-lower cumulative fund profit justifies by exactly $160,000, which the GP owes back. `finmodel.
percentage_of_completion` — cost-to-cost revenue recognition for long-term contracts, exact and
self-verifying against its own accounting identity (cumulative recognized revenue must equal exactly the
contract price once costs incurred reach 100% of the total estimate), so no external dataset was ever
actually required to build and test it correctly.

Round 3: `finmodel.credit_card_abs` — credit-card master-trust securitization (excess spread, the real
3-month-average early-amortization trigger every master-trust prospectus defines, and the revolving-vs-
amortization cash-flow mechanic under both pass-through and controlled-amortization methods), whose "own
careful, separately-verified formula set" the original deferral worried about turned out to be entirely
hand-verifiable: a $100M receivables pool with an 80M certificate balance stays flat through a 24-month
revolving period, then pays down in exactly 6 months (pass-through) or exactly 10 level months (controlled
amortization). `finmodel.sales_capacity_planning` — rep productivity ramp curves and bookings-capacity
forecasting, built as its own module rather than an extension of `finmodel.cohort_analysis` after
reconsidering that the two track fundamentally different metrics (quota attainment versus customer
retention) on their cohorts, even though both use a cohort-by-tenure structure.

Round 4 (partial): `finmodel.options.geometric_asian_option()` — a closed-form geometric-average Asian
option, re-derived from first principles (a continuous geometric average's logarithm is itself normally
distributed under risk-neutral GBM, reducing the option exactly to a vanilla Black-Scholes price with an
adjusted volatility and cost of carry) rather than trusting a memorized formula by name, and independently
verified against a Monte Carlo simulation of the discretized average. Other exotics (barrier options in
particular) stay deferred — they carry real transcription risk from memory without an equally solid
verification method at hand, so this item is only partially resolved. `finmodel.npa_classification.
provisioning_requirement()` gained a `segment` argument selecting among RBI's real, differentiated
standard-asset rates (general, agriculture/SME, commercial real estate, CRE residential housing, housing
loans at a teaser rate) — the "specific portfolio mix" the original deferral wanted was unnecessary, since a
segment-rate table is a lookup, not a formula with anything to reconcile.

## New-business / startup model (`finmodel.startup_model`, `docs/STARTUP_MODEL.md`)

The mirror image of the real-company checks above: instead of validating the toolkit against a real filer,
`finmodel startup <inputs.json>` generates a hypothetical new business's three-statement projection
(`finmodel.three_statement`) and DCF valuation (`finmodel.dcf`) from a small set of high-level assumptions (a
revenue ramp, a margin trajectory, funding rounds), then checks the plan's assumed exit-year margin against the
REAL per-sector peer data the seven football-field checks above already collected (`data/edgar/*.json`) — so a
founder's assumptions get sanity-checked against real market data, not a fabricated "typical startup" range.
`examples/startup_saas.json` is a worked, fully-illustrative SaaS example, benchmarked against the real software
sector peers from `docs/FOOTBALL_FIELD_CSCO.md`.

