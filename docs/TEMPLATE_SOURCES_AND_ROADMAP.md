# Chart/glossary KB, template sources, layout and roadmap

Moved verbatim from the former README. Note: since commit 7ee1d9a the paid-template knowledge-base contents are scrubbed from `catalog/`; counts below describe the pre-scrub state.

## Charts, glossary, paid-template knowledge base

- `docs/CHARTS.md` — the chart template: for each engine, which data feeds which chart and the analysis question it answers. Rendering follows the data-viz method (validated palette, thin marks, 2px gaps, legends, tooltips, table view, light/dark).
- `docs/GLOSSARY.md` / `data/glossary.json` — 176 terms (CFI Financial Analysis and Modeling glossaries, PwC statement primer, authored valuation/LBO/M&A terms with formulas and toolkit pointers) and a 19-row GAAP-vs-IFRS evaluation table.
- `docs/PAID_TEMPLATES.md` / `catalog/paid_templates.json` — the 127 paid-only CFI titles: category, what they do, public analogues, literature, and how much this toolkit already covers; `catalog/analysis_intent.json` adds the analysis intent per category with the Investopedia, Wall Street Prep, Macabacus and CFI reference pages it was distilled from.

## Template sources

`finmodel catalog list` catalogues 313 verified public files from Damodaran (NYU Stern, 59), Breaking Into
Wall Street (225), exinfm.com (15), A Simple Model (8) and Macabacus (6), each with size and HTTP status, plus
the names of the 323 CFI dashboard template titles (196 free-tier, 127 paid) used for the coverage mapping
below. `catalog/alternatives.md` maps every CFI title to the closest public equivalents (87 of the 127
paid-only titles have at least one). `docs/LEARNING_GUIDE.md` summarises each modelling tool with its formulas
and the books and open university courses that teach it.

This toolkit does not authenticate to CFI's dashboard and does not fetch, mirror or redistribute anything from
behind its login or paid plan — `finmodel catalog fetch` only ever downloads the public, no-login sources above.
`docs/OPEN_SOURCE_MODULES.md` surveys the Python packages that overlap with this toolkit (FinanceToolkit,
pyxirr, numpy-financial, OpenBB, …) and `finmodel/integrations.py` has lazy bridges to them.

Downloaded templates are copyrighted by their publishers and stay in the git-ignored `downloads/` and
`extracted/` folders. The example JSON files carry only the illustrative figures printed in the free CFI
educational templates.

## Layout

```
finmodel/          engines + tools (fin, three_statement, dcf, projection, ratios, lbo, merger, comps, scores, costing, edgar, wacc, residual_income, sotp, startup_model, cap_table, vc_fund_metrics, cash_flow_forecast, impact_scoring, strategy_frameworks, rd_capitalization, project_finance, variance_analysis, fpa_planning, breakeven, loss_reserving, tax_provision, real_estate_development, working_capital_financing, retail_loans, retail_deposits, carry_trade, revolving_credit, npa_classification, pipeline, credit_risk, interest_rate_risk, fixed_income_risk, earnout_valuation, percentage_of_completion, credit_card_abs, sales_capacity_planning, lease_accounting, fx_hedging, stock_based_compensation, bond_amortization, foreign_currency_translation, inventory_costing, pension_accounting, nwc_peg, eps_calculation, investment_securities, consolidation, debt_covenants, asset_retirement_obligations, warranty_and_receivables_allowance, investment_incentives, sector_investment_model, project_bankability, india_incentive_workbook, india_corporate_tax_regimes, audit, sectors, xlcalc, charts, excel, extract, catalog, paid_templates, cli)
examples/          JSON inputs (CFI 3-statement, CFI DCF, projection demo, ratios demo, ASM LBO, BIWS merger, STLD comps, STLD scores, university costing, STLD WACC, STLD residual income, conglomerate SOTP, SaaS startup model)
data/              glossary.json, edgar/ (compact SEC company-facts extracts for the case studies)
scripts/           comps_validation.py, football_field_stld.py, football_field_cvx.py, football_field_csco.py, football_field_usb.py, football_field_o.py, football_field_alk.py, football_field_trv.py, football_field_txn.py, ma_case_study.py (regenerate the real-data docs)
catalog/           source lists (cfi_dashboard_raw.txt, open_sources_verified.txt) -> catalog.json / catalog.md
docs/              OPEN_SOURCE_MODULES.md
tests/             pytest suite (reconciliation, identities, LibreOffice recalc, CLI)
```

## Roadmap

- Monthly roll-forward of the projection engine (currently the base year is monthly, forecast years are annual) — scoped out for now: the 300-line `projection.run()` is reconciled cell-for-cell to a CFI template, and re-architecting every schedule (working-capital days, PP&E, debt) to monthly granularity risks a silent error in a financial calculation without a matching monthly template to reconcile against; worth doing once one is sourced.
