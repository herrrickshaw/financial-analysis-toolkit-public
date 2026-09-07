# Existing Python packages for this kind of financial analysis

`docs/GAP_ANALYSIS.md` surveyed *GitHub repositories* doing similar financial modelling. This is the narrower,
complementary question: what's already **installable via `pip`** for the specific things `finmodel` does — SEC
EDGAR ingestion, ratio/DCF/valuation analysis, core financial math (NPV/IRR/XIRR), and Excel-formula
parsing/transpilation? Researched 2026-09-06; star counts and "last active" dates are as observed that day, not
guaranteed current.

## 1. SEC EDGAR / SEC data access — closest to `finmodel.edgar`

| Package | What it does | Stars | Maintained? |
|---|---|---|---|
| **edgartools** (`dgunning/edgartools`) | Typed Python objects over the full EDGAR corpus — 10-K/8-K/XBRL financials, Forms 3/4/5, 13F, ADV. Free, no API key. | 2,671 | Yes — pushed same day as this survey |
| **secedgar** (PyPI `secedgar`) | Bulk-downloads periodic reports/filings/forms from EDGAR by CIK/ticker/form type. | 1,413 | Yes — last push ~9 months ago |
| **datamule** (`john-friedman/datamule-python`) | Bulk full-text and structured SEC-submission access via the datamule mirror/endpoints. | 556 | Yes — recently pushed |
| **sec-edgar-downloader** (`jadchaar`) | Simple downloader for raw filings by ticker/CIK — files only, no XBRL parsing. | 717 | Yes |
| **sec-api** (`sec-api-io/sec-api-python`) | SDK for the commercial SEC-API.io service (XBRL-to-JSON, insider trades, 13F, full-text search). | 318 | Yes, but **requires a paid API key** |
| **python-edgar** (`edouardswiac`) | Downloads only the EDGAR full-index files since 1993 — no filing content/XBRL. | 355 | Stale (~2+ years) |
| **sec-edgar-api** (`jadchaar`) | Thin wrapper for the raw EDGAR REST endpoints. | 107 | Stale |

**Where `finmodel.edgar` differs**: none of these normalize a filer's XBRL facts into a fixed annual-statement
shape with tag-precedence and fallback logic the way `finmodel.edgar` does (per-year "first tag with data wins",
restatements replace originals, derived EBITDA/net-debt, and the `net_income / eps_diluted` fallback added after
Exxon Mobil's recent 10-Ks turned out not to tag diluted share count directly — see `docs/FOOTBALL_FIELD_CVX.md`).
`edgartools` is the closest analog (free, well-typed, actively maintained) but is a general filing reader, not a
modeling-ready statement normalizer; `secedgar`/`datamule`/`sec-edgar-downloader` are bulk-download tools with no
XBRL parsing at all; `sec-api` covers similar ground but is paid.

## 2. Financial-statement analysis, ratios, valuation

- **financetoolkit** (`JerBouma/FinanceToolkit`, PyPI `financetoolkit`) — confirmed on PyPI, 5,298 stars, actively
  released. 200+ ratios/indicators with visible formulas, a DCF and WACC/cost-of-capital layer, plus a companion
  300k+-ticker "Finance Database." The closest single overlap with `finmodel` as a whole. Key difference: it's a
  **data + ratio layer over a paid FinancialModelingPrep API key**, not a from-scratch modeling engine — no
  LBO, merger/accretion-dilution, comps/precedent-transaction analysis, Monte Carlo DCF, or Excel formula engine.
- **ffn** (`pmorissette/ffn`) — 2,638 stars, active. Portfolio/return performance statistics (Sharpe, drawdown,
  CAGR) — not fundamental ratios or DCF.
- **ta** (`bukosabino/ta`, 5,186 stars) / **stockstats** (`jealous/stockstats`, 1,486 stars) — technical-analysis
  indicators (RSI, MACD, Bollinger). No overlap with fundamentals or valuation.
- **OpenBB** (`OpenBB-finance/OpenBB`) — 72,714 stars, very active. A large open data-aggregation platform
  (equities, macro, crypto, fundamentals) with an extension ecosystem — a data/terminal platform, not a modeling
  engine; it has no DCF/LBO/merger-model logic of its own.
- **Comparable-company / precedent-transaction-specific package**: confirmed there is **no dedicated PyPI
  package** for this. The space is served only by generic finance-data packages plus custom analyst scripts —
  `finmodel.comps` (and the sector-tuning work in `finmodel.sectors`) appears to fill a genuine, otherwise-empty
  gap in the ecosystem.

## 3. Core financial math — overlaps `finmodel.fin`

- **numpy-financial** — 408 stars; PyPI hasn't shipped since Oct 2019 (spun out of core NumPy). Effectively
  stable/dormant. `npv`/`irr`/`pmt` only — no XIRR, no mid-year convention, no reverse-DCF solving.
- **pyxirr** (`Anexen/pyxirr`) — 221 stars, Rust-backed, fast native XNPV/XIRR/IRR. Last release ~10 months ago
  (third-party trackers flag it as inactive). Faster than `finmodel.fin`'s pure-Python XIRR bisection, but doesn't
  wrap into a modeling layer (mid-year discounting, reverse DCF, Monte Carlo) the way `finmodel.dcf` does.

## 4. Excel-formula parsing/transpilation — closest to `finmodel.xlcalc`

| Package | Stars | Maintained? |
|---|---|---|
| **formulas** (`vinci1it2000/formulas`) | 502 | Yes — released this year |
| **pycel** (`dgorissen/pycel`) | 631 | GitHub active, but **PyPI stalled since Oct 2021** (still pre-release `1.0b30`) |
| **xlcalculator** (`bradbase`) | 162 | Semi-stale — PyPI last shipped Feb 2023 |
| **koala2** | — | Effectively abandoned (2019); its own successor says it was superseded by xlcalculator |

No documented evidence any of the four verify against real, complex commercial workbooks (CFI/BIWS/Macabacus
scale, 15,000+ formulas) the way `finmodel.xlcalc` does — their public tests reference synthetic or small example
sheets. `finmodel.xlcalc`'s 100%-match reconciliation across 14 real downloaded workbooks (one with over 15,000
formulas — `downloads/macabacus/merger-model.xlsx`) looks like a genuine, verifiable differentiator, based on
public documentation rather than a line-by-line audit of their test suites.

## 5. Adjacent, out-of-scope quant/portfolio packages

For reference only — none of these overlap `finmodel`'s scope (corporate valuation and modeling), they're
portfolio/derivatives/backtesting tools:

- **pyfolio** (Quantopian, 6,415 stars) — portfolio/risk tearsheets, **abandoned** (no push since Dec 2023;
  community fork `pyfolio-reloaded` exists)
- **empyrical** (Quantopian, 1,510 stars) — risk/performance metrics, largely dormant (fork: `empyrical-reloaded`)
- **QuantLib** (7,580 stars) — the canonical C++/Python derivatives-pricing and fixed-income library, active
- **zipline** (Quantopian, 20,081 stars) — backtesting engine, **abandoned** (fork: `zipline-reloaded`)
- **Riskfolio-Lib** (4,481 stars) — portfolio optimization (mean-variance, risk parity), active
- **quantstats** (`ranaroussi`, 7,619 stars) — portfolio performance/tearsheet reporting, active

## Synthesis

The four closest-overlap packages are **edgartools** (EDGAR ingestion), **financetoolkit** (ratios/DCF/WACC),
**numpy-financial**/**pyxirr** (core NPV/IRR math), and the **pycel/formulas/xlcalculator** cluster (Excel-formula
transpilation). None of them combine what `finmodel` does end to end: `edgartools` doesn't normalize into a
modeling-ready statement shape; `financetoolkit` gets ratios and a DCF/WACC layer but is gated behind a paid data
API and has no LBO/merger/comps/xlcalc/sector-cycle layer; the numeric-math packages give primitives, not a
modeling framework; the Excel-parsing packages are either stalled on PyPI or unverified against real, complex
workbooks at the scale `finmodel.xlcalc` reconciles against. The clearest gaps `finmodel` fills relative to the
whole ecosystem: **(1)** a free, no-API-key EDGAR-to-normalized-statement pipeline with documented filer-quirk
fallbacks, **(2)** LBO/merger/comps/precedent-transaction modeling as code — nothing on PyPI does this at all,
and **(3)** an from-scratch, workbook-verified Excel formula engine.

*Research method: an agent surveyed PyPI/GitHub for each category above; findings are as reported, not
independently re-verified line-by-line against every package's source or test suite.*
