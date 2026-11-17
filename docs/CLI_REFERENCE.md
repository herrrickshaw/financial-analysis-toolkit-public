# CLI and Python quick reference

Moved verbatim from the former README ("Install" and "Quick start" sections).

## Install

```bash
git clone https://github.com/herrrickshaw/financial-analysis-toolkit && cd financial-analysis-toolkit
pip install -e ".[test]"          # only openpyxl is required at runtime
pytest -q                         # 651 tests; the LibreOffice recalc test auto-skips if soffice is absent
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
finmodel options examples/options_demo.json                              # Black-Scholes, the Greeks, put-call parity, implied volatility, geometric Asian option, barrier options (Reiner-Rubinstein)
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
finmodel lease-accounting examples/lease_accounting_demo.json            # ASC 842 lease classification, initial measurement, finance/operating expense schedules
finmodel fx-hedging examples/fx_hedging_demo.json                        # corporate FX exposure hedging: forward vs money-market vs unhedged
finmodel stock-based-compensation examples/stock_based_compensation_demo.json  # ASC 718 RSU/option grant fair value, straight-line vs graded-vesting expense
finmodel bond-amortization examples/bond_amortization_demo.json          # effective-interest bond premium/discount amortization schedule
finmodel fx-translation examples/fx_translation_demo.json                # ASC 830 current-rate translation of a foreign subsidiary, with the CTA plug
finmodel inventory-costing examples/inventory_costing_demo.json          # FIFO/LIFO/weighted-average cost of goods sold and ending inventory
finmodel pension-accounting examples/pension_accounting_demo.json        # ASC 715 PBO/plan-asset roll-forwards, funded status, net periodic pension cost
finmodel nwc-peg examples/nwc_peg_demo.json                              # M&A net-working-capital peg and closing true-up purchase-price adjustment
finmodel eps examples/eps_demo.json                                      # ASC 260 basic/diluted EPS: treasury stock method, if-converted method, antidilution test
finmodel investment-securities examples/investment_securities_demo.json  # ASC 320 trading/AFS/HTM classification, OCI reclassification on sale
finmodel consolidation examples/consolidation_demo.json                  # ASC 810 consolidated net income, NCI carve-out, NCI at acquisition
finmodel debt-covenants examples/debt_covenants_demo.json                # leverage/interest-coverage/fixed-charge-coverage covenant compliance testing
finmodel aro examples/aro_demo.json                                       # ASC 410 asset retirement obligation: PV recognition, accretion schedule, settlement gain/loss
finmodel warranty-receivables examples/warranty_receivables_demo.json    # warranty reserve roll-forward and CECL aging-method receivables allowance
finmodel investment-incentives examples/investment_incentives_demo.json  # capital/interest/net-tax/employment investment-incentive mechanics (India central + state schemes)
finmodel sector-investment-model examples/state_sector_matrix_demo.json  # 28-state precursor model: land cost (purchase or capitalized leasehold rent) + capex netted against a discounted incentive package, per state/sector
finmodel project-bankability examples/project_bankability_demo.json      # IRR/ROI/payback with and without incentives, ranked by state/sector, flagging incentive-enabled projects
finmodel project-bankability examples/dscr_matrix_demo.json              # DSCR covenant check (SBI/REC-style 70% leverage) across all 28 states/UTs, using real lender debt:equity + industry-norm covenant
finmodel india-incentive-workbook reports/india_investment_incentives.xlsx  # consolidated state/central/land-cost/matrix Excel workbook (reports/ is gitignored; regenerate on demand)
finmodel india-tax-regimes examples/india_corporate_tax_regimes_demo.json   # Section 115BAB/115BAA/standard post-tax IRR comparison + CGTMSE guarantee-fee DSCR effect
finmodel india-depreciation-schedule examples/india_depreciation_schedule_demo.json  # Income Tax Act WDV block-of-assets depreciation, section 50 STCG on block extinguishment, section 32(1)(iia) additional depreciation
finmodel project-bankability examples/dscr_matrix_ireda_demo.json          # DSCR check using IREDA's own disclosed renewable-energy rate/covenant (Rajasthan solar, Gujarat wind)
finmodel audit downloads/macabacus/merger-model.xlsx --recompute         # error values, hard-coded plugs, inconsistent formulas, recompute check
finmodel transpile downloads/macabacus/merger-model.xlsx -o out/py       # 15,323 formulas -> Python, 100% match to cached values
finmodel charts lbo examples/lbo_asm.json -o out/charts_lbo.html         # chart template -> HTML report
finmodel glossary "cash sweep"                                           # definition, formula, GAAP vs IFRS, toolkit pointer
finmodel catalog paid --title comps                                      # what a paid CFI template does + public analogues
finmodel ratios examples/ratios_demo.json
finmodel extract path/to/AnyTemplate.xlsx -o extracted/         # JSON + Markdown spec of the workbook
finmodel catalog list --source damodaran                        # 59 verified public spreadsheets
finmodel catalog fetch --source damodaran asimplemodel exinfm   # downloads/<source>/ (git-ignored)
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

