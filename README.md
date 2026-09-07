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
pytest -q                         # 88 tests; the LibreOffice recalc test auto-skips if soffice is absent
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
- `finmodel.sectors` (`finmodel cycle <edgar-json> --sector steel|oil_gas|software|banking|reit [--field --revenue-field]`) — the sector-tuning module all five checks above validate: `cycle_diagnostics()` flags whether a year is a cycle trough/peak/normal relative to its own trailing history (confirmed automatically on STLD FY2025 = trough, PXD FY2022 = peak, CSCO FY2026 = near normal, USB's FY2020 COVID reserve build = trough, O's FFO margin = near normal throughout despite a real rate-driven multiple cycle — the exact readings the docs above found by hand), `dcf_scenarios_from_history()` derives data-driven bear/base/blue-sky scenario targets instead of a hand-picked one, `normalized_comps_metrics()` swaps a raw LTM EBITDA for a through-cycle median, and `trend_diagnostics()` catches the case none of the above should be trusted on: a genuine secular trend (Salesforce's growth-to-profitability shift, ~2%→20% margin over 8 years) rather than mean-reverting cyclicality, where trailing-median normalization would badly misread a sustainable margin as a misleading cyclical extreme. `--field`/`--revenue-field` override the default operating-income/revenue margin with any other ratio — ROE (`net_income`/`equity`) for a bank, FFO margin (`ffo`/`revenue`) for a REIT. Steel, oil & gas, enterprise software, banking and REITs are tuned against real multi-year data so far; everything else uses a clearly-labelled generic default.
- `docs/CASE_STUDY_MA.md` (`scripts/ma_case_study.py`) — Microsoft/Activision, Chevron/Hess and Cisco/Splunk: each party's last standalone year, the merger engine's static pro-forma, and the acquirer's actual statements after closing, with the reasons they differ.
- `docs/GAP_ANALYSIS.md` — feature gap analysis against the 144 GitHub repositories found for financial modelling / valuation and the EUA–ATHENA financial-management toolkit; what was added in response (`edgar`, `scores`, `comps`, `costing`, reverse and Monte-Carlo DCF).
- `docs/PYTHON_PACKAGES.md` — the narrower, complementary survey: existing *installable PyPI packages* for this kind of analysis (EDGAR access, ratios/DCF, core financial math, Excel-formula transpilation). Confirms there's no dedicated comps/precedent-transaction package on PyPI at all, and that the Excel-formula-parsing packages that exist aren't documented as verified against real, complex workbooks the way `finmodel.xlcalc` is.

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
finmodel/          engines + tools (fin, three_statement, dcf, projection, ratios, lbo, merger, comps, scores, costing, edgar, wacc, residual_income, sotp, audit, sectors, xlcalc, charts, excel, extract, catalog, paid_templates, cli)
examples/          JSON inputs (CFI 3-statement, CFI DCF, projection demo, ratios demo, ASM LBO, BIWS merger, STLD comps, STLD scores, university costing, STLD WACC, STLD residual income, conglomerate SOTP)
data/              glossary.json, edgar/ (compact SEC company-facts extracts for the case studies)
scripts/           comps_validation.py, football_field_stld.py, football_field_cvx.py, football_field_csco.py, football_field_usb.py, football_field_o.py, ma_case_study.py (regenerate the real-data docs)
catalog/           source lists (cfi_dashboard_raw.txt, open_sources_verified.txt) -> catalog.json / catalog.md
docs/              OPEN_SOURCE_MODULES.md
tests/             pytest suite (reconciliation, identities, LibreOffice recalc, CLI)
```

## Roadmap

- Monthly roll-forward of the projection engine (currently the base year is monthly, forecast years are annual) — scoped out for now: the 300-line `projection.run()` is reconciled cell-for-cell to a CFI template, and re-architecting every schedule (working-capital days, PP&E, debt) to monthly granularity risks a silent error in a financial calculation without a matching monthly template to reconcile against; worth doing once one is sourced.
