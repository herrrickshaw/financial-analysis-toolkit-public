# Open-source modules that cover the same ground (survey, 2026-09)

This toolkit re-implements the CFI templates in dependency-free Python so the numbers
reconcile to the spreadsheets cell-for-cell. The packages below are the ones worth
combining with it; `finmodel.integrations` has thin, lazy-imported bridges for the first
four. Install whichever you need — none is required.

| Package | PyPI / repo | What it covers | Use it for | Bridge in this repo |
|---|---|---|---|---|
| **FinanceToolkit** (Jeroen Bouma) | `pip install financetoolkit` (v2.2.0) · https://github.com/JerBouma/FinanceToolkit | 200+ ratios, DuPont, DCF, EV breakdown, Altman Z, WACC, Greeks/Black-Scholes; pulls statements from Financial Modeling Prep with Yahoo Finance fallback | Live historical statements for a listed company → feed `finmodel.ratios.compute` or seed a DCF | `integrations.statements_from_financetoolkit(ticker)` |
| **pyxirr** | `pip install pyxirr` (v0.10.8) · https://github.com/Anexen/pyxirr | Rust XIRR/XNPV/IRR/NPV/FV/PMT…, 10-20x faster than scipy-based xirr, numpy-style broadcasting | Bulk valuation runs, Monte-Carlo on cash-flow dates | `integrations.xirr_fast`, `xnpv_fast` |
| **numpy-financial** | `pip install numpy-financial` (v1.0.0) · https://github.com/numpy/numpy-financial | The old `np.npv/irr/pmt/fv/rate…` family | Cross-checking `finmodel.fin` (note: `npf.npv` puts flow 0 at t=0, Excel's NPV discounts it one period) | `integrations.npf_check` |
| **yfinance** | `pip install yfinance` | Prices, shares outstanding, debt/cash, beta | Market-value block of the DCF | `integrations.market_snapshot` |
| **OpenBB Platform** | `pip install openbb` · https://github.com/OpenBB-finance/OpenBB | Unified data layer (fundamentals, estimates, macro) across 40+ providers | Replacing FMP/Yahoo with a provider you already license | — |
| **QuantStats** | `pip install quantstats` | Portfolio/strategy performance analytics and tear-sheets | Not a modelling library; pairs with the market-pipeline backtests | — |
| **dcf** (PyPI) | `pip install dcf` | Banking-style discount curves, interpolation, compounding, FX | Term-structure discounting instead of a flat WACC | — |
| **pyfinny** | https://github.com/larry-lime/pyfinny | CLI: statements, DCF and comps via FMP API | Reference implementation of a comps table | — |
| **halessi/DCF** | https://github.com/halessi/DCF | Fetch filings + parametrised DCF | Reference only (unmaintained) | — |
| **A Simple Model** free files | https://www.asimplemodel.com/resources/quick-references/free-downloads | 3-statement, DCF (incl. mid-year convention), LBO with scenarios and data tables (xlsx) | Next engines to add: LBO and mid-year DCF | catalog `asimplemodel` |
| **Damodaran spreadsheets** | https://pages.stern.nyu.edu/~adamodar/New_Home_Page/spreadsh.htm | 60+ models: FCFF/FCFE/DDM ginzu, WACC, synthetic rating, APV, optimal capital structure, real options, LBO, synergy, country risk premia datasets | Cost-of-capital and terminal-value inputs; the ginzu models are the natural "advanced DCF" target | catalog `damodaran` (all 59 URLs verified 200) |
| **exinfm.com** | https://exinfm.com/free_spreadsheets.html | 100+ legacy .xls: projections model v6.8.4, LBO/DCF, statements generator, ratio tree, EVA, comps, combination model | Historical reference; convert with `finmodel extract` (LibreOffice converts .xls) | catalog `exinfm` |
| **Wall Street Oasis templates** | https://www.wallstreetoasis.com/resources/templates/excel-financial-modeling | 3-statement, DCF, LBO, M&A templates | Email-gated; not cataloged | — |
| **Vertex42 / SCORE / Smartsheet** | vertex42.com, score.org, smartsheet.com | Small-business projection and P&L templates | Simpler than the CFI projection; SCORE's 2021 file now returns 410 | — |

## What the CFI templates contain vs. this toolkit

| CFI template (local copy) | Sheets | Engine here | Reconciled |
|---|---|---|---|
| CFI-Case-Study-Three-Statement-Model.xlsx | Cover, Three Statement Model (IS/BS/CF + WC, PP&E, debt schedules, 5 hist + 5 fcst) | `finmodel.three_statement` | yes, all forecast rows to 0.01 |
| CFI-DCF-Model-Template-Updated.xlsx | Cover, DCF Model (stub-period XNPV, perpetuity + EV/EBITDA TV, XIRR) | `finmodel.dcf` | yes, EV / per-share / IRR to 1e-9 |
| CFI-Financial-Projection-Template.xlsx | Payroll, Sales, Opex (monthly base year + 4 forecast years), IS, BS, CF, Ratio Analysis | `finmodel.projection`, `finmodel.ratios` | template ships empty (all zeros); engine verified by identities + corrected template bugs |

## CFI member dashboard (login required)

Your dashboard listing is parsed into `catalog/catalog.json`: 196 items downloadable on the free tier,
127 need a paid plan. The `api.corporatefinanceinstitute.com/api/files/<uuid>` endpoint returns 401 without
authentication. The learn.corporatefinanceinstitute.com single-page app authenticates with a Bearer token
(it is NOT a cookie: a credentialed fetch from the logged-in origin still gets 401), so either click the
Download buttons in a logged-in browser (each opens the file), or copy the `Authorization` header from a
logged-in request in DevTools → Network and run:

```bash
finmodel catalog fetch --source cfi --auth "Authorization: Bearer <token>"
```
