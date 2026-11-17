# Financial analysis toolkit (`finmodel`)

A from-scratch Python toolkit of corporate-finance and valuation engines: three-statement, DCF, LBO, merger, trading
comps and precedent transactions, a SEC EDGAR company-facts reader, sector-specific tuning, and an Excel-formula
transpiler. It is for analysts, students and developers who want auditable, dependency-light models; it produces JSON
results, formula-driven `.xlsx` workbooks, SVG/HTML chart reports and Markdown case studies on real company filings.

> Status: maintained public snapshot. Educational use only; not investment advice. Example inputs carry only the
> illustrative figures printed in free educational templates; third-party templates are never committed
> (`downloads/` and `extracted/` are git-ignored). New here? See [HOW_TO_USE_WITH_AI.md](HOW_TO_USE_WITH_AI.md).

## What it does
- Runs 80 CLI sub-commands (`finmodel <command> <input.json>`) over 85 modules in `finmodel/`, with 84 example inputs in `examples/`.
- Core valuation engines: `three_statement`, `dcf` (stub-period `XNPV`/`XIRR`), `lbo` (sweep, PIK, revolver, sponsor IRR/MOIC), `merger` (accretion/dilution, purchase-price allocation), `comps` (peers, precedents, football field).
- `finmodel.edgar` turns SEC XBRL company facts into annual series that feed `ratios`, `comps`, `scores` (Altman Z, Piotroski F, Beneish M) and `sectors` (cycle diagnostics for ten sector profiles).
- `finmodel.xlcalc` parses Excel A1 formulas, evaluates them with Excel semantics (about 90 functions, circular references by iteration), verifies against cached values and emits standalone Python.
- `finmodel.excel` writes live-formula workbooks; `finmodel.charts` renders dependency-free SVG into an HTML report.
- Applied modules for accounting (ASC 842/718/715/320/810/410), banking, insurance, project finance and India investment-incentive analysis (see [docs/MODULE_SECTIONS.md](docs/MODULE_SECTIONS.md)).

## Quick start
```bash
git clone https://github.com/herrrickshaw/financial-analysis-toolkit-public.git
cd financial-analysis-toolkit-public
python -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"            # only openpyxl is needed at runtime
finmodel demo                       # runs every engine on the bundled examples -> out/*.xlsx
```
Individual engines: `finmodel dcf examples/cfi_dcf.json --sensitivity`, `finmodel lbo examples/lbo_asm.json`,
`finmodel merger examples/merger_biws.json`, `finmodel comps examples/comps_stld.json`. The full command list is in
[docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md).

```python
import json
from finmodel import comps, edgar
result = comps.from_dict(json.load(open("examples/comps_stld.json")))   # trading comps + precedents + football field
rows = edgar.annual(edgar.fetch(1022671, user_agent="me name@example.com"))   # live call; see "Dependency injection"
```

## How it works
Each engine is a module with a dataclass of inputs, a pure `run()`/`from_dict()` that returns plain dicts, and a CLI
handler in `finmodel/cli.py` that does the file and console I/O.

| Stage | Module | Output |
|---|---|---|
| Source data | `edgar` (SEC company facts), `extract` (any `.xlsx` to JSON/Markdown spec) | annual rows keyed by fiscal-year end |
| Normalise | `sectors`, `rd_capitalization`, `ratios`, `scores` | cycle-adjusted inputs, ratios, scores |
| Value | `dcf`, `comps`, `lbo`, `merger`, `three_statement`, `projection`, `residual_income`, `sotp` | result dicts |
| Present | `excel`, `charts`, `cli` | workbooks, HTML/SVG reports, console tables |

Design points:
- **Strategy registries.** `comps.METHODS` holds the football-field valuation methods (trading comps, precedents); `register_method()` adds one without editing `from_dict()`. `dcf.TERMINAL_VALUE_METHODS` does the same for terminal-value rules (`average`, `perpetuity`, `multiple`).
- **Dependency injection.** `edgar.fetch(..., source=...)` accepts any object with `get(cik) -> dict` (`edgar.FactsSource`). `SecHttpSource` is the only code that touches the network; `DiskCachedSource` wraps any source with an on-disk cache.
- **Excel is the oracle.** Engines are reconciled cell-for-cell to the source workbooks (details in [docs/ENGINES_AND_VALIDATION.md](docs/ENGINES_AND_VALIDATION.md)); the projection engine corrects four documented template bugs.
- **Golden tests.** `tests/golden/*.json` pin the comps, DCF, LBO, merger and EDGAR outputs on tracked inputs, so refactors cannot change numbers silently.

## Repository layout
| Path | Purpose |
|---|---|
| `finmodel/` | Engines and tools (`dcf.py`, `lbo.py`, `merger.py`, `comps.py`, `edgar.py`, `sectors.py`, `xlcalc.py`, `cli.py`, ...) |
| `examples/` | JSON inputs for every CLI command |
| `scripts/` | Regenerate the real-data case studies (`football_field_<ticker>.py`, `comps_validation.py`, `ma_case_study.py`) |
| `data/` | `glossary.json` and `edgar/` compact SEC company-facts extracts used by the case studies and `startup` benchmarks |
| `catalog/` | Template-source catalogues (see Limitations) |
| `docs/` | One document per module family, the case studies, and the material moved out of the former README |
| `tests/` | pytest suite: reconciliation, identities, CLI, golden characterisation tests |

## Data sources
| Source | What is taken | Access route | Licence / caveat |
|---|---|---|---|
| SEC EDGAR XBRL company facts | Annual 10-K/20-F/40-F facts | `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` via `finmodel edgar` | Public domain; SEC requires a descriptive User-Agent with a contact e-mail and at most 10 requests/second |
| Damodaran, Breaking Into Wall Street, exinfm, A Simple Model, Macabacus | Public template spreadsheets for reconciliation | `finmodel catalog fetch` into git-ignored `downloads/` | Copyright of their publishers; never committed or redistributed |
| Free CFI educational templates | Illustrative figures in `examples/*.json` | Hand-copied | Figures only; no workbook is redistributed |

## Configuration
No environment variables or secrets are needed. `finmodel edgar` takes `--user-agent` (required by the SEC) and an
optional `--cache-dir`. Outputs go where `--xlsx`/`--json-out`/`-o` point; `out/` and `reports/` are git-ignored.

## Testing
```bash
pytest -q          # 686 collected; the LibreOffice recalc test skips if soffice is absent
ruff check .       # syntax errors + pyflakes (also run in CI)
```
Tests never call SEC EDGAR or any other live service (the EDGAR tests use an injected fake source).

## Limitations and known issues
- 3 tests in `tests/test_catalog.py` fail on a clean checkout: they expect the CFI paid-template data that was deliberately removed in commit `7ee1d9a` (paywall-bypass tooling and scraped content). `catalog/paid_templates.json` and `docs/PAID_TEMPLATES.md` are now mostly empty, and some older prose still counts the removed titles.
- Running the test suite rewrites tracked files under `catalog/` and `docs/PAID_TEMPLATES.md`; run `git checkout -- catalog docs` afterwards.
- `finmodel/cli.py` is a single 1,500-line module with one handler per command; `lbo.run()` and `xlcalc.py` are long and tightly coupled (splitting them is planned, see the roadmap).
- The projection engine has a monthly base year and annual forecast years; a monthly roll-forward is deferred until a matching monthly template exists to reconcile against.
- `audit.py` failed to import on Python 3.10/3.11 until this refactor (an f-string backslash); CI pins 3.10 and 3.12.
- Real-company case studies depend on figures extracted from SEC filings in `data/edgar/`; sector findings are specific to the peers and years studied.

## Related repositories
None required. The toolkit is self-contained.

## Licence
MIT; see [LICENSE](LICENSE).

---
More detail: [CLI reference](docs/CLI_REFERENCE.md) | [engines and validation](docs/ENGINES_AND_VALIDATION.md) |
[module sections](docs/MODULE_SECTIONS.md) | [template sources, layout and roadmap](docs/TEMPLATE_SOURCES_AND_ROADMAP.md) |
[learning guide](docs/LEARNING_GUIDE.md) | [glossary](docs/GLOSSARY.md)
