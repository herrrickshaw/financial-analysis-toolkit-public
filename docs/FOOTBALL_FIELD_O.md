# Fifth real-company check: REITs need FFO-based multiples, not P/E — and a real blind spot in this toolkit's own cycle tool

Same real-data method as the steel, oil & gas, enterprise-tech and banking checks, applied to Realty Income (O). Unlike the banking check, EV/EBITDA isn't the failure here — a REIT's enterprise value is computable. The failure is in the equity multiple itself: net income.

## Why P/E breaks for a REIT (real evidence, not a hypothetical)

Real estate depreciation is a large non-cash GAAP charge against an asset that, unlike a factory or a delivery fleet, usually *appreciates*. Nareit's response to this, decades old and industry-standard, is FFO (funds from operations = net income + real-estate depreciation & amortization) as the metric analysts actually price REITs on. Verified on real FY2025 SEC EDGAR data across six real net-lease REITs, priced at real 2026-07-02 market_data closes:

| Ticker | Price | P/E | P/FFO |
|---|---|---|---|
| NNN | 47.49 | 22.91x | 13.56x |
| WPC | 71.37 | 33.84x | 15.98x |
| ADC | 77.51 | 42.18x | 19.43x |
| EPRT | 30.80 | 24.11x | 15.23x |
| FCPT | 24.95 | 22.86x | 14.94x |
| O (target) | 63.34 | 54.35x | 16.06x |

*(O is the target of this check, not a peer in its own comps set — shown in the table above for the full six-company range, not as part of the peer statistics.)*

P/E ranges **22.9x-54.3x** across these six real companies; P/FFO sits in a much tighter, saner **13.6x-19.4x** band across the SAME six companies. A P/E-based comp set would make Realty Income look either wildly overvalued or roughly in line with peers depending entirely on which REIT you compared it to — an artifact of depreciation policy and acquisition history, not real relative value. See `finmodel.sectors.SECTOR_PROFILES['reit']` for the same finding encoded into the toolkit itself.

**A real data-availability ceiling, documented rather than patched around**: Nareit's official FFO definition also excludes gains/losses on real-estate sales (no clean, consistent XBRL tag for that across filers), and AFFO — which further backs out straight-line rent and recurring capex — has no standardized XBRL tag at all. The FFO figure in this check is therefore a real, honest proxy (net income + D&A), not the exact Nareit-reconciled number a REIT publishes in its own earnings release.

**A second real data gap — filer-by-filer, not sector-wide**: this check uses only equity-numerator multiples (P/E, P/FFO), not EV/EBITDA, partly by choice (P/FFO is the sector-standard metric) and partly because net debt isn't reliably available: `finmodel.edgar`'s debt tags return `None` for FY2025 for the target (O) and 2 of 5 peers (NNN, Agree Realty). Realty Income itself last reported the aggregate `LongTermDebt` XBRL tag in FY2016; since then it reports debt only through disaggregated `SecuredDebt`/`UnsecuredDebt`/`NotesPayable` tags — ADDITIVE components (a filer's true total debt is their sum), not alternative tags for the same concept, so summing them correctly needs a different TAGS design than this module's first-tag-wins fallback tuples. But this is real variation between individual filers, not a REIT-wide pattern: the other 3 of 5 peers (W. P. Carey, Essential Properties, Four Corners) DO report a populated `debt_total` for FY2025 — this check simply didn't need to lean on that, since P/E and P/FFO are equity-numerator multiples by design.

## Football field

| Method | Low | High | Current price inside range? |
|---|---|---|---|
| Trading comps | 26.70 | 63.03 | price is above this range |
| Precedent transactions | 23.90 | 41.81 | price is above this range |
| DDM - bear case (trailing 3yr dividend CAGR, growth decelerating) | 58.02 | 58.02 | price is above this range |
| DDM - blue sky (11yr historical dividend CAGR) | 60.02 | 60.02 | price is above this range |
| 52-week range | 53.18 | 66.39 | yes |

52-week range brackets the actual price.
Ranges the price sits **above**: Trading comps (high 63.03), Precedent transactions (high 41.81), DDM - bear case (trailing 3yr dividend CAGR, growth decelerating) (high 58.02), DDM - blue sky (11yr historical dividend CAGR) (high 60.02).

## 1. Trading comps (P/E, P/FFO — real: SEC EDGAR fundamentals + market_data warehouse prices)

Peers: NNN REIT, W. P. Carey, Agree Realty, Essential Properties Realty Trust, Four Corners Property Trust — all real single-tenant net-lease REITs, the same business model as Realty Income.

| Multiple | 25th | Median | 75th |
|---|---|---|---|
| P/E | 22.91x | 24.11x | 33.84x |
| P/FFO | 14.94x | 15.23x | 15.98x |

## 2. Precedent transactions (real, verifiable, all-stock net-lease REIT mergers)

### Realty Income / VEREIT — announced 2021-04-29

All-stock: 0.705 Realty Income shares per target share × Realty Income's own price on the announcement day = offer **$36.27**/target share. Equity value **$7,901M** (217.9M target diluted shares), target net income $201M, FFO proxy $670M, target fundamentals from its FY2020 10-K (SEC EDGAR).

**P/E 39.28x, P/FFO 11.79x**.

### Realty Income / Spirit Realty Capital — announced 2023-10-30

All-stock: 0.762 Realty Income shares per target share × Realty Income's own price on the announcement day = offer **$30.22**/target share. Equity value **$4,069M** (134.6M target diluted shares), target net income $286M, FFO proxy $579M, target fundamentals from its FY2022 10-K (SEC EDGAR).

**P/E 14.25x, P/FFO 7.03x**.

Both real deal-implied P/FFO multiples (11.79x, 7.03x) sit BELOW the peer trading range (14.9x-16.0x p25-p75) — worth being honest about why, since it isn't the same reason for both. Realty Income's own stock barely moved around the VEREIT announcement ($50.91 the prior trading day → $51.44 on announcement day). For Spirit Realty, O's stock fell a real, verified ~5.7% on the announcement itself ($42.04 on 2023-10-27, the prior trading day, to $39.66 on 2023-10-30) — a real market reaction to stock-deal dilution that mechanically pulls this precedent's implied multiple down further than VEREIT's, on top of the same real FFO-vs-net-income distortion driving the rest of this check. Using the pre-announcement price instead would show a higher implied multiple for Spirit specifically; this check uses the announcement-day close for both, for the same reason the banking check did — consistency with how the other three sector checks in this project define "the acquirer's price at announcement."

## 3. Dividend discount model (REIT-appropriate DCF-equivalent)

Cost of equity 8.25% (`finmodel wacc examples/wacc_o.json`); 2-stage Gordon growth, 5 explicit years then a 2.5% terminal growth rate, discounted at cost of equity. REITs must distribute >=90% of taxable income as dividends, so the dividend stream is a direct, textbook-appropriate cash-flow-to-equity proxy. Growth assumptions are O's own real historical dividend-per-share CAGRs, not analyst consensus: 2.77%/yr over the trailing 3 years (bear case — real, and reflects real deceleration from heavy stock issuance funding the VEREIT and Spirit Realty deals) vs 3.55%/yr over the trailing 11 years (blue sky — O's older, faster growth rate).

**DDM - bear case (trailing 3yr dividend CAGR, growth decelerating)** (2.77%/yr growth) → implied share price **$58.02** (-8.4% vs the real $63.34 price).
**DDM - blue sky (11yr historical dividend CAGR)** (3.55%/yr growth) → implied share price **$60.02** (-5.3% vs the real $63.34 price).

## 4. 52-week trading range (real, market_data warehouse)

$53.18 – $66.39 (2025-07-02 to 2026-07-02, 252 trading days).

## 5. The real blind spot: this toolkit's cycle tool can't see a REIT's actual cycle

`finmodel cycle data/edgar/O.json --sector reit --field ffo --revenue-field revenue` — FFO margin, the operating fundamental this module normalizes, was genuinely stable over FY2018-2025:

FY2025 FFO margin 62.3% vs trailing-8yr median 66.5% (-6.3%) → **near normal**, trend **weak/none**.

Yet Realty Income's real year-end P/FFO multiple swung hard over the exact same window — driven by the interest-rate cycle, not by anything in its own operating fundamentals:

| Year-end | FFO/share | Price | P/FFO |
|---|---|---|---|
| 2018 | 3.12 | 42.55 | 13.66x |
| 2019 | 3.26 | 51.60 | 15.83x |
| 2020 | 3.11 | 45.62 | 14.69x |
| 2021 | 3.03 | 56.55 | 18.66x |
| 2022 | 4.15 | 52.38 | 12.63x |
| 2023 | 3.99 | 50.00 | 12.52x |
| 2024 | 3.77 | 48.95 | 12.98x |
| 2025 | 3.94 | 54.93 | 13.93x |

P/FFO ranged **12.5x (2023, after aggressive Fed hikes) to 18.7x (2021, near-zero rates)** — a >45% swing — while `cycle_diagnostics()` on the fundamental correctly reports no cycle at all. This isn't a false negative to fix: the module only ever looks at a company's own EDGAR history, never its market price or trading multiple, so a valuation cycle that lives entirely in the multiple (as a REIT's does, being unusually rate-sensitive) is structurally outside what it can detect. Anyone using this module on a REIT should look at the real trading-multiple history directly, the way this table does, rather than trusting `cycle_diagnostics()`'s 'near normal' as evidence nothing cyclical is happening.

## Method note

Every net income / D&A / dividend figure is from an SEC 10-K (via `finmodel.edgar`); every price is a live database query against `market_data`; the two deals' exchange ratios and announcement dates come from Realty Income's own 8-K press releases (public record). VEREIT and Spirit Realty Capital are both delisted and absent from the warehouse, so target-side deal premiums are omitted for the same reason as the banking check's precedents.

Regenerate with `python scripts/football_field_o.py`; chart at `out/charts_football_field_o.html`.