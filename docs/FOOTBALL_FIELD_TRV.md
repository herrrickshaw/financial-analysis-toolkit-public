# Seventh real-company check: P&C insurers need book-value-based multiples — and book value itself is what's rate-exposed

Same real-data method as the six prior checks, applied to Travelers (TRV). Like banking, EV/EBITDA doesn't apply — but for a different reason, and the sector-defining real finding here (book value's own rate exposure) is new, not a repeat of the banking or REIT findings.

## Why EV/EBITDA breaks for an insurer (real evidence, a different root cause from banking)

| Filer | FY | `da` tag picked | Value | Problem |
|---|---|---|---|---|
| Chubb Limited | 2025 | *(none populated)* | — | no `da`/`ebitda` tag at all |
| W. R. Berkley | 2025 | `DepreciationAmortizationAndAccretionNet` | -$48.1M | NEGATIVE — this tag bundles bond-portfolio premium/discount accretion for a filer with a large investment book, not real operating depreciation |

A bank's problem was a revenue-tag mismatch; an insurer's is different — `finmodel.edgar`'s D&A tag preference picks up investment-accounting noise instead of (or in addition to) real depreciation once a filer's investment portfolio is large enough. Same conclusion either way: P/B, P/TBV and P/E (all equity-numerator, see `finmodel.comps`), never EV/EBITDA. See `finmodel.sectors.SECTOR_PROFILES['insurance']` for the same finding encoded into the toolkit.

## The real, sector-defining finding: book value itself is rate-exposed, not the multiple or earnings

Verified across five real P&C peers, real FY2021-2023 SEC EDGAR data (W. R. Berkley excluded from this specific table — see the note below):

| Ticker | BVPS 2021 | BVPS 2022 | BVPS 2023 | 2022 decline | 2022 net income |
|---|---|---|---|---|---|
| TRV | 115.18 | 89.95 | 107.33 | -21.9% | $2,842M |
| CB | 131.61 | 119.28 | 143.67 | -9.4% | $5,246M |
| ALL | 83.40 | 64.48 | 67.70 | -22.7% | -$1,289M |
| PGR | 31.05 | 27.07 | 34.51 | -12.8% | $722M |
| CINF | 78.45 | 66.51 | 76.52 | -15.2% | -$487M |

Every one of the five real peers shows a real book-value-per-share decline in FY2022, ranging -9.4% (Chubb) to -22.7% (Allstate) — during that year's historic bond-market selloff (the Fed's rate hikes). Three of five (Travelers, Chubb, Progressive) stayed solidly net-income-positive that same year: the business was fine, book value fell anyway. This is mechanistically different from every prior check: a REIT's operating fundamental (FFO) stayed flat while its trading MULTIPLE moved with rates; a bank's credit losses hit book value AND earnings together. An insurer's available-for-sale bond portfolio marks to fair value through OCI (equity), not net income, under GAAP — so BVPS and EPS can genuinely decouple in a way they structurally cannot for a bank's amortized-cost loan book.

**A real, connected trap for ROE-based residual income**: Travelers' own measured ROE (net_income / equity) actually ROSE in FY2022 to 13.2%, up from 12.7% in FY2021 — not because performance improved, but because the book-value denominator shrank from the same AOCI hit. Anyone pointing `finmodel.sectors` at ROE for an insurer during or after a rate shock should check book value's own trend alongside ROE, not ROE in isolation — an 'improvement' can be a shrunken denominator, not real earnings power.

**A real, unrelated bonus finding surfaced while building the table above**: W. R. Berkley's own `WeightedAverageNumberOfDilutedSharesOutstanding` was filed at roughly 1/1000th its real scale for FY2017-2022 (real, verified against SEC's live XBRL API — e.g. FY2022 shows `419192` where the real figure is `419,192,000`). `finmodel.edgar`'s 'latest filing wins' logic only self-heals this while the bad period still appears as a comparative column in a later 10-K — FY2023's identical error WAS corrected this way (visible in the FY2025 10-K's comparatives), but FY2017-2022 have since aged out of every subsequent filing's comparative window and remain wrong in SEC's own live data today. Excluded from the BVPS table above for exactly this reason, rather than shown wrong.

## Football field

| Method | Low | High | Current price inside range? |
|---|---|---|---|
| Trading comps | 282.28 | 426.45 | yes |
| Precedent transactions | 188.58 | 313.79 | price is above this range |
| Residual income - base case (trailing 3yr average ROE) | 206.74 | 238.91 | price is above this range |
| Residual income - blue sky (FY2025 actual ROE sustained) | 232.67 | 275.42 | price is above this range |
| 52-week range | 246.70 | 340.24 | yes |

Trading comps and 52-week range bracket the actual price.
Ranges the price sits **above**: Precedent transactions (high 313.79), Residual income - base case (trailing 3yr average ROE) (high 238.91), Residual income - blue sky (FY2025 actual ROE sustained) (high 275.42).

## 1. Trading comps (P/B, P/TBV, P/E — real: SEC EDGAR fundamentals + market_data warehouse prices)

Peers: Chubb, Allstate, Progressive, Cincinnati Financial, W. R. Berkley — real large-cap US P&C insurers.

| Ticker | Price | P/B | P/TBV | P/E |
|---|---|---|---|---|
| CB | 358.79 | 1.95x | 3.05x | 13.97x |
| ALL | 248.93 | 2.17x | 2.47x | 6.47x |
| PGR | 229.44 | 4.45x | 4.45x | 11.93x |
| CINF | 191.21 | 1.90x | 1.90x | 12.60x |
| WRB | 71.58 | 2.95x | 3.04x | 16.09x |

| Multiple | 25th | Median | 75th |
|---|---|---|---|
| P/B | 1.95x | 2.17x | 2.95x |
| P/TBV | 2.47x | 3.04x | 3.05x |
| P/E | 11.93x | 12.60x | 13.97x |

## 2. Precedent transactions (real, verifiable, all-cash P&C/reinsurance mergers)

### AIG / Validus Holdings — announced 2018-01-22

All-cash: **$68.00**/target share. Equity value **$5,378M** (79.1M target diluted shares), target book value $3,895M, tangible book value $3,494M, target net income -$48M, target fundamentals from its FY2017 10-K (SEC EDGAR).

**P/B 1.38x, P/TBV 1.54x, P/E NM**.

### Berkshire Hathaway / Alleghany Corporation — announced 2022-03-21

All-cash: **$848.02**/target share. Equity value **$11,754M** (13.9M target diluted shares), target book value $9,187M, tangible book value $7,509M, target net income $1,035M, target fundamentals from its FY2021 10-K (SEC EDGAR).

**P/B 1.28x, P/TBV 1.57x, P/E 11.36x**.

Validus's negative net income isn't a data error — 2017 was a real, well-documented catastrophe-loss year for reinsurers (Hurricanes Harvey, Irma and Maria), and `comps.multiple()`'s NM-cap logic correctly reports its P/E as NM rather than a nonsensical negative multiple.

## 3. Residual income (insurance-appropriate DCF-equivalent — same method as the banking check)

Cost of equity 8.03% (`finmodel wacc examples/wacc_trv.json`); a 15.6% dividend payout ratio (TRV's own FY2025 actual — P&C insurers typically retain most earnings for underwriting capacity and buybacks, not shown here). ROE scenarios use TRV's own RECENT real levels, not a trailing 8-year median — see §4 for why that matters here specifically.

**Residual income - base case (trailing 3yr average ROE)** (ROE target 16.4%, current 19.1%) → implied share price **218.30** (range 206.74 – 238.91).
**Residual income - blue sky (FY2025 actual ROE sustained)** (ROE target 19.1%, current 19.1%) → implied share price **247.75** (range 232.67 – 275.42).

## 4. 52-week trading range (real, market_data warehouse)

$246.70 – $340.24 (2025-07-02 to 2026-07-02, 252 trading days).

## 5. A callback, not a new finding: the trend guard from the software check, on a different sector

`finmodel cycle data/edgar/TRV.json --sector insurance --field net_income --revenue-field equity` — ROE, not the default operating-income margin, correctly required here (same override banking uses):

FY2025 ROE 19.1% vs trailing-8yr median 12.3% (+54.9%) → **peak — trailing multiples built on this year likely UNDERstate the true multiple**.

`trend_diagnostics()` fires **strong** (r=0.85, improving) — the same guard `docs/FOOTBALL_FIELD_CSCO.md` established: TRV's real FY2018-2025 ROE genuinely improved (11.0% → 19.1%), and a trailing-median 'normalization' would misread that real, sustained improvement as a cyclical extreme to revert away from, understating current earning power the same way it would have for Salesforce. Checked, not assumed, that this isn't just the FY2022 denominator artifact from §2: 2024-2025's ROE — the highest in the whole series — comes AFTER book value had already recovered well past its pre-2022 peak, so the broader trend is real, sustained profitability improvement (higher rates flowing through to net investment income, a harder P&C pricing market), not a shrunken-equity illusion.

## Method note

Every book value / tangible book value / net income figure is from an SEC 10-K (via `finmodel.edgar`); every price is a live database query against `market_data`; both deals' per-share cash prices and announcement dates come from the target's own 8-K press releases (public record). Both real precedent targets are delisted and absent from the warehouse, so target-side deal premiums are omitted for the same reason as the banking, REIT and airline checks' precedents.

Regenerate with `python scripts/football_field_trv.py`; chart at `out/charts_football_field_trv.html`.