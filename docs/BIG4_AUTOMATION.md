# Big 4 financial-modeling and audit-analytics services, built as code

A market survey of what Deloitte, KPMG, EY and PwC actually sell as financial-modeling and audit services — real,
named methodologies, not an invented feature list — turned into three new, tested `finmodel` modules.

## What was surveyed

- **Deal-advisory / valuation modeling** (all four firms, via public service pages and industry coverage):
  Deloitte emphasizes model validation, assumption traceability and impairment analysis; PwC emphasizes
  audit-friendly, transaction-ready model documentation; KPMG names **purchase price allocation support**,
  synergy/integration modeling and scenario-based valuation explicitly; EY offers deal-integrated valuation
  modeling with governance workflows.
- **Audit analytics / assurance automation**: Deloitte's Omnia and Argus platforms; PwC's disclosed >$1.5B AI
  investment in its next-generation assurance framework; EY's own proprietary audit-analytics platform;
  third-party tools (DataSnipper for OCR/evidence-matching, CaseWare/TeamMate+ for workpapers) used across all
  four firms per public reporting; and, cutting across every platform, the same underlying real techniques:
  process mining, exception-based population-level testing, journal-entry testing and Benford's Law screening.

Two threads were concrete and quantitative enough to build as real, testable code: **purchase price allocation**
(KPMG's own named service, a standardized ASC 805/IFRS 3 exercise) and **impairment testing** (Deloitte's own
named service, a standardized ASC 350/360 exercise). A third — the audit-analytics techniques every platform
converges on — is real and buildable at the level of Benford's Law and rule-based journal-entry testing, even
though the platforms themselves (Omnia, DataSnipper, etc.) are proprietary products, not published methodologies.

## The three new modules

### 1. `finmodel.ppa_valuation` — purchase price allocation (KPMG's named service)

`finmodel.merger.PPA` already allocates a purchase price given an `intangibles_writeup` figure — but it takes
that number as an assumption. This module **derives** it with the real, named ASC 805 income-approach methods:
**relief-from-royalty** (trade names, technology — value = PV of after-tax royalty payments avoided by owning
the asset instead of licensing it) and **MPEEM** (customer relationships — value = PV of "excess earnings" left
over once every *other* contributory asset has earned its own required return), both grossed up by a real,
standard **Tax Amortization Benefit (TAB)** factor (IRC §197's 15-year straight-line tax amortization), plus a
cost-approach fallback for assets with no defensible income/market approach (assembled workforce). `allocate()`
then applies the real ASC 805 residual principle: goodwill is whatever's left over after every identifiable
asset — tangible and now-valued intangible — is allocated at fair value, never a hand-picked plug. Its output
feeds directly into `finmodel.merger.PPA(intangibles_writeup=...)`.

```bash
finmodel ppa examples/ppa_demo.json
```

### 2. `finmodel.impairment_testing` — goodwill and long-lived-asset impairment (Deloitte's named service)

Three deliberately different real tests, not one generic formula: **ASC 350 goodwill** (post-ASU 2017-04
single-step — impairment capped at the goodwill balance itself, since goodwill can't go negative), **ASC 350-30
indefinite-lived intangibles** (the same direct fair-value-vs-carrying-value comparison, no recoverability
screen), and **ASC 360 long-lived assets held and used** — a genuinely different two-step structure where Step 1
compares *undiscounted* cash flows to carrying value, and only a Step-1 failure triggers a Step-2
fair-value-based loss measurement. That undiscounted-cash-flow screen is real, deliberately conservative, and
the single most commonly confused detail in practice: an asset can be worth less than its carrying value on a
fair-value basis and still pass Step 1 (both directions are exercised in `tests/test_impairment_testing.py`). A
DCF (`finmodel.dcf`) is a natural, real source for the fair-value input every test here needs.

```bash
finmodel impairment examples/impairment_demo.json
```

### 3. `finmodel.audit_analytics` — Benford's Law and rule-based journal-entry testing

The two real, well-documented, quantitatively implementable techniques every Big 4 audit-analytics platform
converges on. **Benford's Law**: the leading digit of many naturally occurring numerical populations follows
P(d) = log10(1 + 1/d), not a uniform 1/9 — deviation, measured via Nigrini's real, published Mean Absolute
Deviation (MAD) statistic and its conformity thresholds (<0.006 close, 0.006-0.012 acceptable, 0.012-0.015
marginal, >0.015 nonconformity), is a standard forensic-accounting screen to prioritize scrutiny, not proof of
fraud by itself. **Rule-based journal-entry testing (JET)**: a real ISA 240/AS 2401 fraud-risk-response
procedure — scan the *entire population* of entries (not a sample) for round-dollar amounts, weekend/after-hours
postings, and amounts sitting just under a disclosed approval threshold.

```bash
finmodel audit-analytics examples/audit_analytics_demo.json
```

## What wasn't built, and why

Several real Big 4 services are either already covered elsewhere in this toolkit or are proprietary products/
workflow features with no publishable, replicable methodology to build against:

- **Synergy/integration modeling** and **scenario-based valuation** (KPMG) — already covered by
  `finmodel.merger`'s cost-synergy fields and by the sensitivity/scenario functions every DCF-based check in
  this toolkit already runs (`finmodel.dcf.sensitivity`, the bear/base/blue-sky pattern used across all nine
  sector checks).
- **Model validation / assumption traceability** (Deloitte) — this is what `finmodel.audit` (workbook formula,
  plug and hidden-sheet auditing) already does for a spreadsheet model.
- **Deal-integrated valuation with governance workflows** (EY) and **audit-friendly documentation** (PwC) — real
  services, but process/workflow products, not a model or calculation to replicate in code.
- **Omnia, Argus, DataSnipper, CaseWare, TeamMate+** — real, named platforms, but proprietary software products
  (OCR, evidence-matching, workpaper management) rather than a published methodology; the underlying techniques
  they operationalize (Benford's Law, rule-based JE testing) are what this pass built instead.
- **Process mining / RPA** — a real, named audit-automation technique across all four firms, but it's an
  infrastructure/tooling category (event-log mining against a client's own ERP data), not a standalone
  calculation with a defensible, citable formula the way Benford's Law or MPEEM have.

## Sources

- [KPMG: Purchase Price Allocation](https://kpmg.com) (service description, market survey via WebSearch)
- [The McLean Group: Purchase Price Allocations Under ASC 805](https://mcleanllc.com/purchase-price-allocation-under-asc-805/)
- [Redwood Valuation: The Evolving Role of Purchase Price Allocation in M&A](https://www.redwoodvaluation.com/blog/tkrilwr2n2v640q165jtkeydda2t5k)
- Deloitte, PwC, EY public service pages and industry coverage of audit-analytics platforms (Omnia, Argus,
  DataSnipper, CaseWare, TeamMate+) — market survey via WebSearch, September 2026.
- Nigrini's Mean Absolute Deviation conformity thresholds for Benford's Law — widely cited forensic-accounting
  convention (see [MetricGate: Benford's Law Anomaly Detection](https://metricgate.com/docs/benfords-law/)).
