# Indian project-finance lending terms (SBI, IREDA, REC)

Real published lending terms from three major Indian project-finance lenders, feeding
`finmodel.project_bankability.debt_service_coverage_ratio` and its worked 12-state application
(`examples/dscr_matrix_demo.json`). As with every other catalog in this toolkit: every number is sourced and
dated, and every gap is flagged explicitly rather than filled with a guess.

## State Bank of India (SBI)

| Parameter | Value | Source / as-of |
|---|---|---|
| MCLR (various tenors) | O/N & 1M 7.85% · 3M 8.25% · 6M 8.60% · 1Y 8.70% · 2Y 8.75% · 3Y 8.80% | sbi.bank.in/web/interest-rates/interest-rates/mclr, effective 15.08.2026 |
| EBLR (repo-linked) | Repo (5.25%) + 2.65% fixed markup = 7.90% floor, **plus** a borrower-specific Credit Risk Premium (CRP) and Business Strategy Premium (BSP) | sbi.bank.in/web/interest-rates/external-benchmark-based-lending-rate, effective 15.12.2025 — the newest figure found; ~9 months old as of this research, no newer revision located |
| RBI repo rate (underlying) | 5.25%, unchanged, unanimous 6-0, neutral stance | RBI MPC, 3–5 Aug 2026 (next meeting 5–7 Oct 2026) |
| Rate type | Floating — EBLR resets with every repo change; MCLR resets per the loan's chosen tenor | sbi.bank.in |
| Project finance rate range | ~8.5%–16% p.a. depending on project risk | **secondary aggregator (msmeloans.in), not SBI's own disclosure — indicative only** |
| Debt:equity | **Not disclosed by SBI.** The commonly cited 70:30/75:25 figure is a general market norm, not SBI-published | — |
| DSCR covenant | **Not publicly disclosed.** SBI appraises project finance case-by-case via its Project Finance SBU, not against a published DSCR floor | — |
| Tenure | Not numerically published; SBI's Industrial Sector page describes appraisal basis (project viability + promoter credit standing + SPV structuring) with no stated tenor | sbi.bank.in/web/business/corporate-banking/products-and-services/industrial-sector |

Flag: SBI's own "SME Segment" rate page still shows 2018 MCLR-based spreads, last updated 24.02.2020 —
clearly stale, not used for any figure above.

**Illustrative all-in derivation (not an SBI-published figure):** EBLR floor 7.90% + an assumed CRP of
1–4%+ for a project/SPV borrower ≈ **9%–12%+ all-in**, roughly consistent with the (unverified) aggregator
range. `examples/dscr_matrix_demo.json` uses **10.5%** (the midpoint of this derived range) as its
illustrative interest rate — explicitly not SBI's own disclosed number, since SBI doesn't publish one.

## IREDA (Indian Renewable Energy Development Agency)

The most concrete and current of the three — a dated, explicit rate card. Source: IREDA "Financing Norms
and Schemes" (Doc No. IREDA/FG/Part-1, Issue No. 33, updated 12.06.2026), rates effective 01.06.2026.

| Sector | Rate | Debt:equity | DSCR covenant (IREDA's own, published) |
|---|---|---|---|
| Rooftop/Wind/Grid Solar/Hybrid/Floating Solar (private) | 8.65% (Grade I) – 9.65% (Grade V) | 70:30 standard; up to 4:1 (80% loan) with conditions | ≥1.25x (loan ≤75%) · ≥1.2x (loan ≤80%, D:E 4:1) |
| Hydro ≤25MW | 9.05%–10.05% (+25bps if >25MW) | as above | ≥1.3x (loan ≤75%) |
| Biomass/Co-gen/Waste-to-Energy | 9.20%–10.20% | as above | ≥1.3x (loan ≤75%) |
| Transmission | 8.65%–9.65% | as above | — |
| RE Manufacturing (incl. battery, excl. standalone solar-PV-module) | 9.20% (≥500MW/TPD) – 9.95% (<200MW/TPD) | up to 4:1 with conditions | ≥1.4x |
| CPSU/State PSU/JV, RE project-specific | 8.45% (AAA–AA) – 8.95% (BBB+/BBB) | — | — |

Rate type: administered/graded (5-grade rating scale I–V), reset at commissioning or 1 year from first
disbursement (whichever earlier), then annually — not continuously repo-linked. Tenure: solar/wind/
transmission/hydro repayment is cash-flow/PPA/DSCR-based, amortized within 80% of useful life (IREDA holds a
call option after 15 years); other sectors ≤15 years. Moratorium: 6 months–1.5 years from COD.

**This is the only one of the three lenders with a fully sourced, dated, lender-disclosed DSCR schedule** —
safe to cite with confidence for renewable-energy projects specifically (none of the 12 states in this
toolkit's current matrix are RE projects, so IREDA's rates don't directly apply there yet; they would be the
right source the day a solar/wind entry is added).

## REC Limited (Rural Electrification Corporation)

**Staleness flag, read first:** REC's most recent publicly available rate circular (Loan Policy Circular
004/2023-24, 20.09.2023, "effective till further notification") is **~3 years old as of this research** —
no newer circular is listed on REC's own site. The figures below should not be read as REC's current
pricing; they're reported for completeness with this flag attached.

| Parameter | Value (Sept-2023 circular — stale) |
|---|---|
| Non-Conventional Generation (Wind/Solar) | State Sector 8.95%(A++)–9.70%(A) · Private Sector 9.20%(IR1)–9.70%(IR3) |
| Conventional Generation | 10.40%–11.40% (State) / 10.90%–11.40% (Private) |
| Transmission | 9.50%–10.25% (State) / 10.00%–10.50% (Private) |
| Project-specific funding / RE equipment manufacturing / small hydro / biomass | base NCG-RE rate + 50bps |
| Debt:equity | 70:30 (private sector default), capped at 3:1 max — per REC's undated "Financing Norms for Renewable Energy Projects" |
| Tenure | ≤12 years after moratorium (COD+6mo, up to 1.5yr solar/wind, up to 6yr small hydro) |
| DSCR covenant | **Not mentioned anywhere in REC's own Financing Norms document** — no figure found in any REC primary source |

## Cross-lender summary and what this toolkit uses

| | SBI | IREDA | REC |
|---|---|---|---|
| Benchmark type | Floating, repo/MCLR-linked | Administered, graded, annual reset | Administered, graded, 1/3/10-yr reset |
| Current, dated rate | Yes (15.08.2026 MCLR; 15.12.2025 EBLR) | Yes (01.06.2026) | **No — stale, 20.09.2023** |
| Debt:equity | Not disclosed (norm: 70:30/75:25) | 70:30 standard; up to 4:1 for select RE sectors | 70:30 (private default) |
| DSCR — lender's own disclosed figure | None | **1.2x–1.4x, explicit and dated** | None |
| DSCR — general industry norm (not lender-specific) | 1.20x–1.25x | (has its own, doesn't need the norm) | 1.20x–1.25x |

`examples/dscr_matrix_demo.json` models all 12 states' projects against the **generic SBI/REC-style case**
(70% debt:equity, an illustrative 10.5% derived interest rate, 1.20x minimum DSCR — the conservative end of
the general industry norm, since neither SBI nor REC discloses its own floor), computed using only each
project's *operating* cash flow (not incentive income) as the conservative, bank-side cash flow available
for debt service — lenders typically don't credit uncertain subsidy income toward a DSCR test the way they
credit contracted revenue. Only **Tamil Nadu, Odisha, and Uttar Pradesh** clear this conservative 1.20x
covenant on operating cash flow alone; the other 9 states' illustrative projects would need either a smaller
loan (more promoter equity), a longer tenure, or bankable incentive cash flow layered in before a lender in
this generic mold would extend 70% leverage — a genuinely different question from the IRR-based
"bankability" in `docs/PROJECT_BANKABILITY.md`, and one worth reading alongside it rather than instead of it.

The day a renewable-energy sector entry is added to the matrix, it should use IREDA's own disclosed rate and
DSCR figures above rather than this generic case, since IREDA's terms are lender-specific, dated, and
directly on point for that sector.
