# Investment Promotion Agency (IPA) Support workbook

`finmodel.india_incentive_workbook` consolidates every piece of this toolkit's India investment-incentive
research — state schemes, central schemes, land-cost benchmarks, and the worked 18-state matrix — into a
single, multi-sheet `.xlsx` titled **"Investment Promotion Agency (IPA) Support"** (set as the file's own
document-properties Title, not just its filename). The role it fills is the one a state or central IPA
itself plays for an investor — Invest India, Invest MP, Invest Karnataka, APIIC, and their counterparts each
publish and explain their own state's/sector's incentives one at a time; this workbook consolidates that
same kind of information across states and the centre in one place, filterable and sortable directly, rather
than reading six separate markdown docs or visiting a dozen separate IPA portals. Generate it with:

```
finmodel india-incentive-workbook reports/india_investment_incentives.xlsx
```

(`reports/` is gitignored — regenerate the file rather than expecting it to already exist in a fresh clone.)

## Two different sheets, built two different ways

- **State Incentives, Central Incentives, and Land Cost Benchmarks** are a structured *transcription* of
  `docs/INDIA_STATE_INVESTMENT_INCENTIVES.md`, `docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md`, and
  `docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md`. Those markdown docs, with their full citation URLs and
  every "not confirmed in source" flag, remain the authoritative narrative; this workbook is an index into
  the same facts for filtering/sorting, not a new, independently-sourced dataset. Every row carries its own
  `Confidence` and `Source` column, so no row asserts a number more confidently than its source document
  does — a "Low" confidence row is exactly as uncertain in the spreadsheet as it is in the prose.
- **The 12-State Matrix sheet is computed LIVE** at build time, from the same example JSON files
  (`examples/state_sector_matrix_demo.json`, `examples/project_bankability_demo.json`,
  `examples/dscr_matrix_demo.json`) and the same `finmodel.sector_investment_model` /
  `finmodel.project_bankability` modules used everywhere else in this toolkit — never re-typed into this
  module. This is enforced directly in the test suite: `tests/test_india_incentive_workbook.py` reloads the
  same example files independently and checks the workbook's numbers match the modules' own output exactly,
  so the workbook can never silently drift from what `finmodel sector-investment-model` /
  `finmodel project-bankability` themselves would print.

## What's on each sheet

| Sheet | Rows | Columns |
|---|---|---|
| State Incentives | 12 (one per state) | Policy name/year, primary mechanic, rate, cap, tenure, other incentives, confidence, source |
| Central Incentives | 26 (14 PLI sectors + 4 MSME + 3 tax + 2 SEZ/EOU + 3 credit-guarantee) | Category, outlay/cap, mechanic/rate, tenure, confidence, source |
| Land Cost Benchmarks | 36 (every sourced rate across all 18 states/UTs) | Industrial area/park, sector character, rate as quoted, converted Rs cr/acre, confidence tier, source |
| 18-State Matrix | 18 states/UTs + 1 total | Land rate, total capex, incentive PV, net effective investment, effective subsidy %, IRR with/without incentives, DSCR, DSCR compliance |
| Tax Regime Comparison | 3 (115BAB / 115BAA / standard) | Base/surcharge/cess rate, effective rate, post-tax cash flow, post-tax IRR, best-regime flag |
| Financing Effects | 4 (2 CGTMSE + 2 IREDA) | Lender/scheme, loan, rate, tenure, cash flow, DSCR, minimum DSCR required, compliance, a note on what each row illustrates |

A README sheet is written first, explaining the sheet layout and pointing back to the seven source docs for
full narrative detail and citations. Like the Matrix sheet, Tax Regime Comparison and Financing Effects are
both computed **live** at build time from `finmodel.india_corporate_tax_regimes` and
`finmodel.project_bankability`, never re-typed.

## `finmodel.excel.write_record_tables`

The underlying writer is new and general-purpose (not specific to India or incentives): every other writer
in `finmodel.excel` (`write_three_statement`, `write_dcf`, `write_projection`, `write_generic`) is built for
a *year-series financial statement* layout, which doesn't fit a flat, row-per-record catalog like this one.
`write_record_tables(path, sheets, readme_lines=...)` writes one or more plain header-row-plus-data-rows
tables, each with a bold header row, frozen top row, and autosized columns — the shape any future
row-per-item dataset in this toolkit (a scheme catalog, a benchmark list, a comps universe) can reuse without
forcing it into the financial-statement writer.

## Test coverage

`tests/test_excel.py` adds two tests for `write_record_tables` itself (headers/rows/README sheet ordering,
and the no-README single-sheet-active case). `tests/test_india_incentive_workbook.py` (4 tests, new file)
checks every transcribed row's column count matches its sheet's header, checks all 18 states/UTs are covered,
and — the most important check — verifies the 12-State Matrix sheet's numbers against the underlying
modules computed independently in the test, not against a hand-typed expectation. `tests/test_cli.py` adds a
CLI round-trip test.
