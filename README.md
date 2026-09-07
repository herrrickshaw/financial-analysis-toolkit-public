# financial-analysis-toolkit

Financial modelling engines distilled from Corporate Finance Institute (CFI) Excel templates,
re-implemented in dependency-free Python and reconciled to the spreadsheets cell-for-cell.

| Engine | Source template | What it does |
|---|---|---|
| `finmodel.three_statement` | CFI Case Study – 3-Statement Model | Linked IS / BS / CF with working-capital, PP&E and debt schedules; N historical + N forecast years driven by ratio assumptions; balance check |
| `finmodel.dcf` | CFI DCF Model Template (Updated) | Unlevered FCF, stub-period `YEARFRAC`, `XNPV` enterprise value, perpetuity-growth + EV/EBITDA terminal value (average / either), equity bridge, `XIRR`, WACC × g sensitivity |
| `finmodel.projection` | CFI Financial Projection Template | Bottom-up: products × units, employees × hours (NETWORKDAYS), opex by category → IS → BS → CF → ratios, 1 monthly base year + N forecast years |
| `finmodel.lbo` | A Simple Model *Simple LBO (scenarios & data tables)* + BIWS sweep/PIK examples | Sources & uses, purchase accounting, tranche schedules (scheduled amortisation, cash sweep, PIK, revolver), depreciation waves, exit at EV/EBITDA, sponsor and mezzanine IRR/MOIC via XIRR, scenario × exit-multiple table; reconciled to the workbook (88 cells + both 42-cell data tables) |
| `finmodel.merger` | BIWS *Equity value / EV in M&A deals* + BIWS/Macabacus merger models | Deal-level accretion/dilution (premium, cash/debt/stock mix, foregone interest, new shares), premium × %stock sensitivity; multi-year pro forma with purchase price allocation (write-ups, DTL, goodwill), synergies, integration costs, acquisition debt, adjusted EPS |
| `finmodel.xlcalc` | any workbook | **Excel-formula transpiler and evaluator**: parses A1 formulas, compiles them to Python, evaluates with Excel semantics (~90 functions, lazy IF/IFERROR, ranges, names, circular refs by iteration), verifies against cached values, emits standalone Python modules |
| `finmodel.charts` | — | Chart templates per engine (KPI tiles, stacked/grouped columns, lines, waterfalls, heatmaps, football field) rendered as dependency-free SVG into a themed HTML report with legends, tooltips and table views |
| `finmodel.paid_templates` | CFI dashboard | Knowledge base of the 127 paid-only CFI titles: category, what each does (scraped CFI description), public analogues, literature, toolkit coverage |
| `finmodel.ratios` | CFI Financial Ratio Analysis | Profitability, efficiency (turnover + days + funding gap), liquidity, leverage, coverage |
| `finmodel.fin` | — | Excel-exact `YEARFRAC` (basis 0–4), `XNPV`, `XIRR`, `NPV`, `IRR`, `NETWORKDAYS`, `EOMONTH`, `PMT` |
| `finmodel.excel` | — | Writes the 3-statement and DCF models as **live-formula** workbooks in the CFI layout (blue inputs / black formulas); LibreOffice headless recalc for verification |
| `finmodel.extract` | — | Turns any `.xlsx`/`.xls` template into a JSON + Markdown spec (labels, inputs, formulas, R1C1 patterns, cross-sheet links) |
| `finmodel.catalog` | — | Catalog / verify / fetch template sources: CFI dashboard (login), Damodaran, A Simple Model, exinfm |

## Install

```bash
git clone https://github.com/herrrickshaw/financial-analysis-toolkit && cd financial-analysis-toolkit
pip install -e ".[test]"          # only openpyxl is required at runtime
pytest -q                         # 504 tests; the LibreOffice recalc test auto-skips if soffice is absent
```

## Quick start

```bash
finmodel demo                                                   # runs all engines on the bundled examples -> out/*.xlsx
finmodel three-statement examples/cfi_three_statement.json --table all --xlsx out/3s.xlsx
finmodel dcf examples/cfi_dcf.json --sensitivity --xlsx out/dcf.xlsx
finmodel projection examples/projection_demo.json --xlsx out/proj.xlsx
finmodel lbo examples/lbo_asm.json --xlsx out/lbo.xlsx                  # sponsor IRR 30.7%, sub-debt IRR 17.2%, data table
finmodel merger examples/merger_biws.json                               # deal accretion +15.4%, pro forma by year
finmodel comps examples/comps_stld.json --xlsx out/comps.xlsx            # trading comps, precedents, implied value, football field
finmodel scores examples/scores_stld.json                                # Altman Z, Piotroski F, Beneish M
finmodel costing examples/costing_university.json                        # EUA-style resource allocation, full costing, income diversification
finmodel edgar 1022671 --user-agent "me name@example.com" --years 5      # SEC EDGAR annual statements for a CIK (Steel Dynamics)
finmodel cycle data/edgar/STLD.json --sector steel                       # where an LTM year sits in its own margin cycle; data-driven DCF scenario targets
finmodel wacc examples/wacc_stld.json                                    # CAPM cost of equity, synthetic-rating cost of debt, WACC
finmodel residual-income examples/residual_income_stld.json              # residual-income (EBO) / EVA equity valuation
finmodel sotp examples/sotp_conglomerate.json                            # sum-of-the-parts across segments
finmodel startup examples/startup_saas.json                              # new-business 3-statement + DCF, benchmarked against real sector peer data
finmodel cap-table examples/cap_table_series_ab.json                     # priced-round dilution (option-pool shuffle) + exit waterfall
finmodel vc-fund examples/vc_fund_demo.json                               # DPI/RVPI/TVPI/IRR, deal MOIC, European or American (deal-by-deal, with clawback) carry waterfall
finmodel cash-flow-forecast examples/cash_flow_forecast_13wk.json        # 13-week rolling direct-method cash forecast, covenant flags
finmodel impact examples/impact_scoring_demo.json                        # 2X Criteria, Impact Management Project ABC class, GHG intensity
finmodel strategy examples/strategy_frameworks_demo.json                 # TAM/SAM/SOM, BCG growth-share matrix, GE-McKinsey nine-box
finmodel ppa examples/ppa_demo.json                                      # purchase price allocation: relief-from-royalty, MPEEM, ASC 805 goodwill residual
finmodel impairment examples/impairment_demo.json                        # ASC 350 goodwill / ASC 350-30 indefinite-lived / ASC 360 long-lived-asset impairment tests
finmodel audit-analytics examples/audit_analytics_demo.json              # Benford's Law digit-conformity test, rule-based journal-entry testing
finmodel options examples/options_demo.json                              # Black-Scholes, the Greeks, put-call parity, implied volatility, geometric Asian option
finmodel project-finance examples/project_finance_demo.json              # DSCR-based debt sizing/sculpting, LLCR, cap rate/NOI real-estate valuation
finmodel portfolio examples/portfolio_demo.json                          # Markowitz efficient frontier, tangency portfolio, Capital Allocation Line
finmodel restructuring examples/restructuring_demo.json                  # absolute-priority recovery waterfall, fulcrum security, DIP financing sizing
finmodel bank-model examples/bank_model_demo.json                        # bank operating model: NII/NIM, provision for credit losses, regulatory capital ratios
finmodel cohort examples/cohort_analysis_demo.json                       # SaaS cohort retention, GRR/NRR, LTV, LTV:CAC, CAC payback
finmodel insurance-pricing examples/insurance_pricing_demo.json          # combined ratio, operating ratio, loss-cost-multiplier rate making
finmodel convertible examples/convertible_bonds_demo.json                # convertible bond: bond floor + embedded option (two-component) valuation
finmodel cmo examples/cmo_demo.json                                       # CMO: PSA prepayment modeling, sequential-pay tranching, weighted average life
finmodel dcf-diagnostics examples/dcf_diagnostics_demo.json               # flags a DCF that double-counts the interest tax shield
finmodel variance-analysis examples/variance_analysis_demo.json          # budget-vs-actual + sales mix/quantity variance, horizontal/vertical analysis
finmodel fpa-planning examples/fpa_planning_demo.json                     # headcount cost schedule, driver-based rolling forecast
finmodel breakeven examples/breakeven_demo.json                          # break-even units/revenue, margin of safety, degree of operating leverage
finmodel cap-table examples/vc_method_demo.json                          # VC Method: required multiple/ownership -> implied pre-/post-money valuation
finmodel loss-reserving examples/loss_reserving_demo.json                # chain-ladder loss development triangle: age-to-age factors, ultimates, IBNR
finmodel tax-provision examples/tax_provision_demo.json                  # deferred tax, valuation allowance, NOL carryforward (pre-2018/post-2017 baskets)
finmodel real-estate-development examples/real_estate_development_demo.json  # development pro forma: TDC, draw schedule, yield on cost, unlevered IRR
finmodel working-capital-financing examples/working_capital_financing_demo.json  # factoring cost, early-payment discount APR, ABL borrowing base
finmodel retail-loans examples/retail_loans_demo.json                    # EMI, amortization, prepayment (reduce-tenure/reduce-EMI), rate reset, foreclosure, FOIR eligibility
finmodel retail-deposits examples/retail_deposits_demo.json              # FD/RD maturity (per-installment compounding), premature RD closure, Section 194A TDS
finmodel carry-trade examples/carry_trade_demo.json                      # covered interest rate parity, unhedged FX carry return, break-even depreciation
finmodel revolving-credit examples/revolving_credit_demo.json            # cash-credit/overdraft daily-balance interest, credit-card minimum-payment trap
finmodel npa-classification examples/npa_classification_demo.json        # RBI IRAC asset classification (Standard/SMA/NPA) and secured/unsecured provisioning
finmodel pipeline examples/pipeline_retail_lending_demo.json             # chain modules together: FOIR eligibility -> amortization -> NPA provisioning
finmodel credit-risk examples/credit_risk_demo.json                      # expected loss (PD x LGD x EAD) and the Basel IRB risk-weighted-assets formula
finmodel interest-rate-risk examples/interest_rate_risk_demo.json        # bank repricing gap and NII sensitivity to a rate shock
finmodel fixed-income-risk examples/fixed_income_risk_demo.json          # bond price, Macaulay/modified duration, DV01, convexity
finmodel earnout-valuation examples/earnout_valuation_demo.json          # M&A contingent-consideration fair value: scenario-weighted or binary-digital-option
finmodel percentage-of-completion examples/percentage_of_completion_demo.json  # cost-to-cost revenue recognition for long-term contracts
finmodel credit-card-abs examples/credit_card_abs_demo.json              # credit-card master trust: excess spread, early-amortization trigger, revolving/amortization cash flows
finmodel sales-capacity-planning examples/sales_capacity_planning_demo.json  # rep productivity ramp curves, bookings-capacity forecasting
finmodel audit downloads/macabacus/merger-model.xlsx --recompute         # error values, hard-coded plugs, inconsistent formulas, recompute check
finmodel transpile downloads/macabacus/merger-model.xlsx -o out/py       # 15,323 formulas -> Python, 100% match to cached values
finmodel charts lbo examples/lbo_asm.json -o out/charts_lbo.html         # chart template -> HTML report
finmodel glossary "cash sweep"                                           # definition, formula, GAAP vs IFRS, toolkit pointer
finmodel catalog paid --title comps                                      # what a paid CFI template does + public analogues
finmodel ratios examples/ratios_demo.json
finmodel extract path/to/AnyTemplate.xlsx -o extracted/         # JSON + Markdown spec of the workbook
finmodel catalog list --source damodaran                        # 59 verified public spreadsheets
finmodel catalog fetch --source damodaran asimplemodel exinfm   # downloads/<source>/ (git-ignored)
finmodel catalog fetch-signed --urls signed.txt              # CFI dashboard: pre-signed S3 links captured from a logged-in browser
```

Python:

```python
from finmodel import three_statement as ts, dcf
r = ts.from_dict(json.load(open("examples/cfi_three_statement.json")))
print(r.table("balance_sheet")); assert r.balanced

v = dcf.run(dcf.DCFInputs(ebit=[...], da=[...], change_nwc=[...], capex=15000, discount_rate=0.12,
                          perpetual_growth=0.03, ev_ebitda_multiple=7, transaction_date="2017-12-31",
                          fiscal_year_end="2018-06-30", current_price=25, shares_outstanding=20000, debt=30000, cash=0))
v["equity_value_per_share"], v["irr"]
```

## Excel formulas → Python (`finmodel.xlcalc`)

`XlModel(path)` loads a workbook, transpiles every formula (tokeniser → recursive-descent parser → Python
expression over `C(sheet,cell)`, `R(sheet,a,b)`, `N(name)` and ~90 Excel functions), evaluates lazily with
memoisation and Excel-style iteration for circular references, and `verify()` compares every formula cell with
the value Excel cached in the file. `to_python_source()` writes an importable module (inputs + transpiled
formulas + a `Workbook` class with `.set()`/`.recalc()`). Verified 100% on: CFI 3-statement (515 formulas) and
DCF (69), A Simple Model LBO (623), LBO II (1,756, 66 circular cells) and DCF (909), BIWS simple LBO, PIK, cash
sweep, acquisition projections, income-statement combination (2,790), merger interview model, Macabacus
short-form LBO (7,022), operating model (1,824) and merger model (15,323), Damodaran fcffsimpleginzu (1,231).

## Reconciliation to the CFI workbooks

`tests/test_three_statement.py` and `tests/test_dcf.py` assert the engines against the cached values in the
CFI files (forecast rows to ±0.01, DCF outputs to 1e-9). `tests/test_excel.py` writes the formula workbooks,
recalculates them with LibreOffice and checks every year's net earnings, total assets, closing cash, the
balance check, and the DCF EV / per-share / IRR against the engine.

The projection template ships with empty inputs (every cached value is 0), so `finmodel.projection` is
verified through accounting identities instead, and it **corrects four template bugs**:

1. forecast wages omit the hours-per-day factor (`avg wage × headcount × workdays`) — restored;
2. the D&A-rate cell points at interest ÷ opening debt (copy-paste) — uses base D&A ÷ opening PP&E;
3. employee bonuses are shown but never deducted from EBT — deducted;
4. prepaid and accrued expenses grow but are excluded from working capital, so the balance sheet cannot balance — included.

Also: wage expense defaults to gross wages (`wage_expense_basis="gross"`); pass `"net_pay"` to reproduce the template.

## Real-data validation and applied case studies

- `docs/VALIDATION_REAL_DATA.md` (`scripts/comps_validation.py`) — the comps engine on the US steel peer set with SEC EDGAR fundamentals and warehouse prices, cross-checked against the market-pipeline's independent P/E ledger; Altman / Piotroski / Beneish on the same filings.
- `docs/FOOTBALL_FIELD_STLD.md` (`scripts/football_field_stld.py`) — the CFI football-field template (comps + precedents + DCF + 52-week range) populated with real Steel Dynamics data: real peer multiples, two real verifiable steel M&A precedents (Nippon Steel/U.S. Steel, Cleveland-Cliffs/AK Steel) built from SEC EDGAR filings, two DCF scenarios grounded in STLD's own historical margin range, and the real trailing 52-week price range — checked against STLD's actual price. Only the trading-comps and 52-week ranges bracket it; both DCF scenarios and both precedents sit below. §5 rebuilds every input with `finmodel.sectors`' through-cycle normalization and finds it doesn't close the gap here — the whole steel sector shares the same 2025 trough, so normalizing both sides of each trade moves them together.
- `docs/FOOTBALL_FIELD_CVX.md` (`scripts/football_field_cvx.py`) — the same check on Chevron, a different industry (oil & gas majors), with two different real precedent deals (ExxonMobil/Pioneer Natural Resources, ConocoPhillips/Marathon Oil): four of five methods bracket the price, a genuinely different result from STLD that shows the method isn't tuned to one outcome. §5's sector normalization does change the answer here: correcting the two precedent targets' 2022/2023 cycle-peak years pushes the precedent-implied range up so far it stops bracketing the price.
- `docs/FOOTBALL_FIELD_CSCO.md` (`scripts/football_field_csco.py`) — a third sector, enterprise technology/software (Cisco vs Microsoft/Oracle/IBM/Adobe/Salesforce, plus the real Broadcom/VMware and IBM/Red Hat all-cash precedent deals): 3 of 5 methods bracket the price, both DCF scenarios undershoot it. §5 adds a trend-detection guard before normalizing — Salesforce's own history is a genuine secular margin-expansion trend, not cyclicality, and naively normalizing it would badly understate its multiple; the script checks `trend_diagnostics()` per peer first and skips normalization for the ones on a real trend rather than Cisco's own peer group.
- `docs/FOOTBALL_FIELD_USB.md` (`scripts/football_field_usb.py`) — a fourth sector, banking, that leads with a negative result: EV/EBITDA doesn't work for a bank at all, and the doc shows the real evidence (a real SunTrust 10-K where "operating income" exceeds "revenue" — the standard industrial tags don't map onto a bank's income statement). Rebuilds the whole check on P/B, P/TBV and P/E multiples plus a residual-income (ROE vs. cost of equity) valuation instead of EV-based comps and an unlevered DCF; the two real precedent deals (BB&T/SunTrust, Huntington/TCF) both priced near or below tangible book value, the opposite pattern from the control-premium-heavy tech and steel precedents. 3 of 5 methods bracket the price.
- `docs/FOOTBALL_FIELD_O.md` (`scripts/football_field_o.py`) — a fifth sector, REITs (Realty Income vs NNN/W. P. Carey/Agree Realty/Essential Properties/Four Corners, plus the real Realty Income/VEREIT and Realty Income/Spirit Realty Capital all-stock precedent mergers): unlike the banking check, EV/EBITDA isn't the failure here, P/E is — real-estate depreciation understates net income against an appreciating asset, so P/E ranged 22.9x-54.3x across six real REITs while P/FFO (the REIT-standard non-GAAP metric) sat in a saner 13.6x-19.4x band over the same six. Rebuilds the check on P/E and P/FFO multiples plus a dividend-discount model (REITs must distribute ≥90% of taxable income). Also surfaces a real blind spot in `finmodel.sectors` itself: `cycle_diagnostics()` correctly reports "near normal" in Realty Income's FFO-margin history, because it only ever looks at fundamentals — but the real P/FFO trading multiple swung 12.5x-18.7x with the interest-rate cycle over the same window, which the module has no way to see.
- `docs/FOOTBALL_FIELD_ALK.md` (`scripts/football_field_alk.py`) — a sixth sector, airlines (Alaska Air Group vs Southwest/Delta/United/American/JetBlue, plus the real Alaska/Virgin America and Alaska/Hawaiian Holdings all-cash precedent mergers): unlike banking or REITs, EV/EBITDA isn't meaningless here, it's just missing the lease adjustment credit analysts have made for airlines for decades — EV/EBITDAR (add back operating lease cost; add the real ASC-842-disclosed lease liability to EV) compresses the multiple 1-22% across 4 of 5 peers (Southwest's own XBRL doesn't disaggregate a clean operating-lease-cost figure at all). The 2016 Virgin America deal's own press release explicitly capitalized aircraft rent at an implied ~7x multiple — a real, quoted confirmation of the old pre-ASC-842 rule of thumb. Also finds a real trap in `finmodel.sectors` itself: its usual `periods=8` default returns FY2020's pandemic-collapse margin as a DCF "bear case," and a short window ending right after that crash makes `trend_diagnostics()` flag a "strong declining trend" that a longer, recovery-inclusive window correctly resolves back to none.
- `docs/FOOTBALL_FIELD_TRV.md` (`scripts/football_field_trv.py`) — a seventh sector, P&C insurance (Travelers vs Chubb/Allstate/Progressive/Cincinnati Financial/W. R. Berkley, plus the real AIG/Validus Holdings and Berkshire Hathaway/Alleghany all-cash precedent mergers): EV/EBITDA fails for a different reason than banking (Chubb reports no D&A tag at all; W. R. Berkley's own D&A tag is genuinely NEGATIVE because it bundles bond-portfolio accretion) — same fix, P/B/P/TBV/P/E. The real, sector-defining finding: book value itself, not the trading multiple (REITs) or earnings moving with it (banking), is what's directly rate-exposed — every one of 5 real peers shows a real book-value-per-share decline in FY2022 (the historic bond selloff) via AOCI, even while 3 of 5 stayed solidly profitable, because AFS bond fair-value moves run through OCI, not net income, under GAAP. A connected trap: Travelers' own ROE mechanically ROSE in FY2022 purely because its book-value denominator shrank, not from real improvement — verified this doesn't taint the real, broader multi-year ROE trend, which `trend_diagnostics()` correctly flags as a genuine improving trend (the same guard the software check established, now confirmed on a financial-services sector). Also surfaces a real, persistent XBRL filer-scale bug (W. R. Berkley's diluted share count filed ~1000x too small for FY2017-2022, uncorrected in SEC's live API today).
- `docs/FOOTBALL_FIELD_TXN.md` (`scripts/football_field_txn.py`) — an eighth sector, semiconductors (Texas Instruments vs Analog Devices/Microchip/NXP/ON/Skyworks, plus the real NVIDIA/Mellanox and Infineon/Cypress Semiconductor all-cash 2019 precedent mergers): EV/EBIT is directionally right here, but GAAP expenses R&D immediately though it creates a multi-year asset — introduces `finmodel.rd_capitalization` (reconciled to CFI's real `RD-Capitalization.xlsx` template, generalized to Damodaran's cross-sectional method), which raises adjusted EBIT for 5 of 6 real peers with growing R&D budgets and compresses both real precedent deals' EV/EBIT by ~35% once capitalized. ON Semiconductor is the real counter-example (its own R&D spend has declined since FY2021, so the same adjustment lowers its EBIT). Also finds TXN's own real capex/revenue ratio (25.7%, from a real, disclosed capacity-expansion supercycle) needs the same normalization fix the airline check's fleet-renewal capex needed, and a sixth distinct real cyclicality mechanism (the "silicon cycle" inventory bullwhip).
- `docs/FOOTBALL_FIELD_DUK.md` (`scripts/football_field_duk.py`) — a ninth sector, regulated electric & gas utilities (Duke Energy vs Southern Company/AEP/Dominion/Exelon/Xcel Energy, plus the real Exelon/Pepco Holdings and Southern Company/AGL Resources all-cash precedent mergers): the deliberate low-cyclicality bookend, and — unlike banking/REITs/insurance — the standard EV-based comps framework needs no override. The real, sector-defining finding: DUK's real capex ran 39.6%-45.7% of revenue every year FY2019-2025 (persistently ~1.8-2.1x D&A, not a temporary supercycle like the semiconductor check's), leaving unlevered FCF negative in 2 of 7 years — not distress, but the entire regulated rate-base-growth mechanism working as designed. With FCF this thin, terminal value dominates enterprise value so completely that a generic 2.5% terminal growth rate produces a NEGATIVE implied equity value; anchoring it instead to Duke's own real, disclosed 5-7% long-run EPS guidance (off a $103B 2026-2030 capital plan) fixes it. Also finds a real mismatch in `finmodel.wacc.synthetic_rating()`: DUK's thin 2.37x interest coverage maps to a synthetic junk rating, while its real rating is investment-grade (BBB/Baa2) — regulated utilities are allowed structurally low coverage because rate-of-return regulation all but guarantees debt-service recovery. Peer Xcel Energy separately shows a real ROE-dilution mechanism (a disclosed forward equity offering funding its capital plan) distinct from every other sector's cyclicality driver.
- `docs/FOOTBALL_FIELD_ABBV.md` (`scripts/football_field_abbv.py`) — a tenth sector, pharmaceuticals (AbbVie vs Pfizer/Merck/Bristol-Myers Squibb/Eli Lilly, plus the real Pfizer/Seagen and Amgen/Horizon Therapeutics all-cash precedent mergers): like airlines/semiconductors/utilities, the standard EV-based comps framework needs no override — but ABBV's real GAAP-mandated acquired-in-process-R&D write-offs (ASC 730-10-25-2c, up to $5.0B/8.2 margin points in FY2025 alone, from the 2024-closed ImmunoGen/Cerevel deals) distort the raw margin trend until added back, a real ADJUSTMENT need distinct from "wrong field" (banking/REIT/insurance) and "no fix needed" (airlines/semiconductors/utilities) — and mechanically different from the semiconductor check's capitalization of ORGANIC R&D. The real, sector-defining finding: AbbVie's genuine Humira patent cliff (real global revenue $21.2B FY2022 → $8.99B FY2024) never dragged total company revenue down more than 6.4% in any year, because its own disclosed Skyrizi+Rinvoq pipeline grew fast enough to offset it (~$16B → $25.9B in one year) — a real lesson that a naive cliff assumption is right for a single-product biotech (the Seagen precedent, genuinely pre-profitability with negative EBIT/EBITDA) and wrong for a diversified major pharma with a real, funded pipeline. Also fixes a real EDGAR extraction gap (AbbVie's and Merck's own "da" tag silently dropped real intangible amortization — now a real additive fix in `finmodel.edgar`) and documents a real, unrelated `market_data` warehouse bug (duplicate, unpurged OHLC batches specific to the ABBV ticker, the same class of bug this repo's own recent OHLC-cache fix addressed elsewhere).
- `finmodel.sectors` (`finmodel cycle <edgar-json> --sector steel|oil_gas|software|banking|reit|airline|insurance|semiconductor|utility|pharma [--field --revenue-field] [--periods]`) — the sector-tuning module all ten checks above validate: `cycle_diagnostics()` flags whether a year is a cycle trough/peak/normal relative to its own trailing history (confirmed automatically on STLD FY2025 = trough, PXD FY2022 = peak, CSCO FY2026 = near normal, USB's FY2020 COVID reserve build = trough, O's FFO margin = near normal throughout despite a real rate-driven multiple cycle, ALK's FY2020 EBIT margin = an extreme trough driven by a demand shock rather than a repeating cycle, TRV's ROE = a real "peak" flag on a genuinely improving trend, TXN's FY2025 EBIT margin = near normal after a real pandemic-chip-shortage peak — the exact readings the docs above found by hand), `dcf_scenarios_from_history()` derives data-driven bear/base/blue-sky scenario targets instead of a hand-picked one (and, per the airline check, needs `--periods` set explicitly when the default 8-year lookback would smuggle a black-swan year in as a "bear case"), `normalized_comps_metrics()` swaps a raw LTM EBITDA for a through-cycle median, and `trend_diagnostics()` catches two distinct failure modes: a genuine secular trend (Salesforce's growth-to-profitability shift, ~2%→20% margin over 8 years, and Travelers' real ROE improvement, 11%→19%) that trailing-median normalization would misread as a cyclical extreme, and — the airline check's finding — a short window ending right after a one-off shock, which can look exactly like a real trend to a correlation coefficient until a longer, recovery-inclusive window resolves it. `--field`/`--revenue-field` override the default operating-income/revenue margin with any other ratio — ROE (`net_income`/`equity`) for a bank or an insurer, FFO margin (`ffo`/`revenue`) for a REIT — though airlines, semiconductors, utilities and pharma are the four sectors so far where the DEFAULT fields need no override (pharma still needs a real IPR&D adjustment before its history can be trusted — see docs/FOOTBALL_FIELD_ABBV.md). Steel, oil & gas, enterprise software, banking, REITs, airlines, P&C insurance, semiconductors, regulated utilities and pharmaceuticals are tuned against real multi-year data so far; everything else uses a clearly-labelled generic default.
- `finmodel.rd_capitalization` — R&D-as-a-capital-asset restatement (Damodaran's cross-sectional method for the trailing-year rolling schedule; the single-vintage straight-line schedule reconciles exactly to CFI's real `RD-Capitalization.xlsx` template). `capitalize_rd(rd_history, life_years)` returns the current-year R&D asset and amortization; `restate()` wraps EBIT/invested-capital adjustment together. Not semiconductor-specific — usable for any R&D-intensive company (software, pharma) that has real, multi-year R&D history in `data/edgar/`.
- `docs/CASE_STUDY_MA.md` (`scripts/ma_case_study.py`) — Microsoft/Activision, Chevron/Hess and Cisco/Splunk: each party's last standalone year, the merger engine's static pro-forma, and the acquirer's actual statements after closing, with the reasons they differ.
- `docs/GAP_ANALYSIS.md` — feature gap analysis against the 144 GitHub repositories found for financial modelling / valuation and the EUA–ATHENA financial-management toolkit; what was added in response (`edgar`, `scores`, `comps`, `costing`, reverse and Monte-Carlo DCF).
- `docs/PYTHON_PACKAGES.md` — the narrower, complementary survey: existing *installable PyPI packages* for this kind of analysis (EDGAR access, ratios/DCF, core financial math, Excel-formula transpilation). Confirms there's no dedicated comps/precedent-transaction package on PyPI at all, and that the Excel-formula-parsing packages that exist aren't documented as verified against real, complex workbooks the way `finmodel.xlcalc` is.

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

## Charts, glossary, paid-template knowledge base

- `docs/CHARTS.md` — the chart template: for each engine, which data feeds which chart and the analysis question it answers. Rendering follows the data-viz method (validated palette, thin marks, 2px gaps, legends, tooltips, table view, light/dark).
- `docs/GLOSSARY.md` / `data/glossary.json` — 176 terms (CFI Financial Analysis and Modeling glossaries, PwC statement primer, authored valuation/LBO/M&A terms with formulas and toolkit pointers) and a 19-row GAAP-vs-IFRS evaluation table.
- `docs/PAID_TEMPLATES.md` / `catalog/paid_templates.json` — the 127 paid-only CFI titles: category, what they do, public analogues, literature, and how much this toolkit already covers; `catalog/analysis_intent.json` adds the analysis intent per category with the Investopedia, Wall Street Prep, Macabacus and CFI reference pages it was distilled from.

## Template sources

`catalog/catalog.md` lists 636 entries: 323 CFI dashboard items (196 free-tier downloads, 127 paid) and 313
verified public files from Damodaran (NYU Stern, 59), Breaking Into Wall Street (225), exinfm.com (15),
A Simple Model (8) and Macabacus (6), each with size and HTTP status. `catalog/alternatives.md` maps every CFI
title to the closest public equivalents (87 of the 127 paid-only titles have at least one).
`docs/LEARNING_GUIDE.md` summarises each modelling tool with its formulas and the books and open university
courses that teach it.

**Fetching the CFI dashboard files.** The learn.corporatefinanceinstitute.com app authenticates with a Bearer
token, so `api/files/<uuid>` returns 401 to scripts, but a top-level navigation in a logged-in browser answers
with a 302 to a 60-second pre-signed S3 link. Capture those links from the browser's network log (the Chrome
extension, DevTools or a HAR export) into a text file and run `finmodel catalog fetch-signed --urls links.txt`;
the S3 leg needs no credentials. All 196 free-tier files were fetched this way on 2026-09-06 (169 xlsx,
15 pdf, 11 docx, 2 pptx) and checksummed in `downloads/manifest.json`.
`docs/OPEN_SOURCE_MODULES.md` surveys the Python packages that overlap with this toolkit (FinanceToolkit,
pyxirr, numpy-financial, OpenBB, …) and `finmodel/integrations.py` has lazy bridges to them.

Downloaded templates are copyrighted by their publishers and stay in the git-ignored `downloads/` and
`extracted/` folders. The example JSON files carry only the illustrative figures printed in the free CFI
educational templates.

## Layout

```
finmodel/          engines + tools (fin, three_statement, dcf, projection, ratios, lbo, merger, comps, scores, costing, edgar, wacc, residual_income, sotp, startup_model, cap_table, vc_fund_metrics, cash_flow_forecast, impact_scoring, strategy_frameworks, rd_capitalization, project_finance, variance_analysis, fpa_planning, breakeven, loss_reserving, tax_provision, real_estate_development, working_capital_financing, retail_loans, retail_deposits, carry_trade, revolving_credit, npa_classification, pipeline, credit_risk, interest_rate_risk, fixed_income_risk, earnout_valuation, percentage_of_completion, credit_card_abs, sales_capacity_planning, audit, sectors, xlcalc, charts, excel, extract, catalog, paid_templates, cli)
examples/          JSON inputs (CFI 3-statement, CFI DCF, projection demo, ratios demo, ASM LBO, BIWS merger, STLD comps, STLD scores, university costing, STLD WACC, STLD residual income, conglomerate SOTP, SaaS startup model)
data/              glossary.json, edgar/ (compact SEC company-facts extracts for the case studies)
scripts/           comps_validation.py, football_field_stld.py, football_field_cvx.py, football_field_csco.py, football_field_usb.py, football_field_o.py, football_field_alk.py, football_field_trv.py, football_field_txn.py, ma_case_study.py (regenerate the real-data docs)
catalog/           source lists (cfi_dashboard_raw.txt, open_sources_verified.txt) -> catalog.json / catalog.md
docs/              OPEN_SOURCE_MODULES.md
tests/             pytest suite (reconciliation, identities, LibreOffice recalc, CLI)
```

## Roadmap

- Monthly roll-forward of the projection engine (currently the base year is monthly, forecast years are annual) — scoped out for now: the 300-line `projection.run()` is reconciled cell-for-cell to a CFI template, and re-architecting every schedule (working-capital days, PP&E, debt) to monthly granularity risks a silent error in a financial calculation without a matching monthly template to reconcile against; worth doing once one is sourced.
