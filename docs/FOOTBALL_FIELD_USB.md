# Fourth real-company check: why the CFI football-field template needs bank-appropriate multiples

Same real-data method as the steel, oil & gas and enterprise-tech checks, applied to US Bancorp (USB) — but this one leads with a negative result: the CFI template's own EV/EBITDA framework does not work for a bank, and this document shows the real data proving it before building the correct alternative.

## Why EV/EBITDA breaks for a bank (real evidence, not a hypothetical)

`finmodel.edgar`'s revenue/operating-income extraction is built for an industrial income statement (revenue → cost of revenue → EBIT). Run on a real bank filer (SunTrust's FY2018 10-K), it gives:

| Filer | FY | "Revenue" (SEC tag) | "Operating income" (SEC tag) | Problem |
|---|---|---|---|---|
| SunTrust Banks | 2018 | $3,226M | $4,638M | operating income EXCEEDS revenue — impossible for a normal income statement |

A bank's core economics are net interest income (interest income minus interest expense) plus fee income, not a cost-of-goods-sold structure — the standard XBRL revenue/operating-income tags this toolkit's EDGAR reader extracts for an industrial filer don't map onto that at all. "Enterprise value" is equally unusable: a bank's balance-sheet "debt" is overwhelmingly customer deposits funding the loan book, not financing debt raised to run the business, so EV = equity + debt − cash produces a number with no economic meaning. See `finmodel.sectors.SECTOR_PROFILES['banking']` for the same warning encoded into the toolkit itself.

## What this check uses instead

**Comps and precedents**: P/B, P/TBV and P/E — all equity-numerator multiples, no EV, no EBITDA. **DCF-equivalent**: residual income (net income − cost of equity × book value), the textbook-correct approach for a bank, using `finmodel.residual_income` with the cost of equity from `finmodel wacc examples/wacc_usb.json` (8.92%).

## Football field

| Method | Low | High | Current price inside range? |
|---|---|---|---|
| Trading comps | 50.70 | 72.69 | yes |
| Precedent transactions | 25.75 | 78.43 | yes |
| Residual income - base case (recent 3yr average ROE) | 44.32 | 47.55 | price is above this range |
| Residual income - blue sky (2021 reserve-release ROE) | 52.09 | 57.86 | price is above this range |
| 52-week range | 42.26 | 61.96 | yes |

Trading comps, Precedent transactions and 52-week range bracket the actual price.
Ranges the price sits **above**: Residual income - base case (recent 3yr average ROE) (high 47.55), Residual income - blue sky (2021 reserve-release ROE) (high 57.86).

## 1. Trading comps (P/B, P/TBV, P/E — real: SEC EDGAR fundamentals + market_data warehouse prices)

Peers: PNC Financial, Truist Financial, M&T Bank, Citizens Financial, Regions Financial, Fifth Third Bancorp.

| Ticker | Price | P/B | P/TBV | P/E |
|---|---|---|---|---|
| PNC | 248.74 | 1.63x | 1.98x | 14.08x |
| TFC | 50.84 | 1.02x | 1.41x | 12.48x |
| MTB | 239.60 | 1.30x | 1.84x | 13.34x |
| CFG | 71.13 | 1.18x | 1.73x | 16.97x |
| RF | 30.29 | 1.43x | 2.06x | 12.59x |
| FITB | 57.21 | 1.77x | 2.30x | 15.26x |

| Multiple | 25th | Median | 75th |
|---|---|---|---|
| P/B | 1.21x | 1.36x | 1.58x |
| P/TBV | 1.75x | 1.91x | 2.04x |
| P/E | 12.78x | 13.71x | 14.96x |

## 2. Precedent transactions (real, verifiable, all-stock bank mergers)

### BB&T / SunTrust (formed Truist Financial) — announced 2019-02-07

All-stock: 1.295 acquirer shares per target share × the acquirer's own price on the announcement/first-trading day = offer **$29.25**/target share. Equity value **$13,602M** (465.0M target diluted shares), target book value $24,280M, tangible book value $15,887M, target fundamentals from its FY2018 10-K (SEC EDGAR).

**P/B 0.56x, P/TBV 0.86x, P/E 4.90x**.

*Source: exchange ratio: publicly disclosed deal terms; BB&T close: market_data warehouse; SunTrust equity/goodwill/intangibles/net income: SEC EDGAR 10-K.*

### Huntington Bancshares / TCF Financial — announced 2020-12-13

All-stock: 3.0028 acquirer shares per target share × the acquirer's own price on the announcement/first-trading day = offer **$29.17**/target share. Equity value **$4,431M** (151.9M target diluted shares), target book value $5,671M, tangible book value $4,211M, target fundamentals from its FY2020 10-K (SEC EDGAR).

**P/B 0.78x, P/TBV 1.05x, P/E 19.89x**.

*Source: exchange ratio: publicly disclosed deal terms; Huntington close: market_data warehouse; TCF equity/goodwill/intangibles/net income: SEC EDGAR 10-K.*

Both real bank M&A deals here priced BELOW tangible book value or barely above it — unlike the richly above-fundamentals multiples in the steel, oil & gas and especially enterprise-tech precedents. Bank M&A often prices this way for a merger-of-equals or a target under earnings pressure, a real structural difference from the control-premium-heavy precedents in the other three sector checks.

## 3. Residual income (illustrative ROE scenarios built from USB's own historical range, not analyst consensus)

Cost of equity 8.92% (`finmodel wacc examples/wacc_usb.json`); a 42% dividend payout ratio (USB's own FY2025 actual); persistence factor 0.5 for the terminal residual income. USB's own ROE ranged 9.3%-14.5% over FY2018-2025 — a real, credit-cycle-driven range (FY2020 COVID loan-loss reserve build was the trough, FY2021's reserve release was the peak), distinct in mechanism from a commodity-price cycle but no less real. The low-high range is a small cost-of-equity (±0.5pt) × persistence (0.3/0.5/0.7) sensitivity grid.

**Residual income - base case (recent 3yr average ROE)** (ROE target 10.7%, current 11.6%) → implied share price **45.62** (range 44.32 – 47.55 across the sensitivity grid).
**Residual income - blue sky (2021 reserve-release ROE)** (ROE target 14.5%, current 11.6%) → implied share price **54.25** (range 52.09 – 57.86 across the sensitivity grid).

## 4. 52-week trading range (real, market_data warehouse)

$42.26 – $61.96 (2025-07-02 to 2026-07-02, 252 trading days).

## 5. Sector-tuned comparison (ROE-based `finmodel.sectors`, not the default EBIT-margin fields)

`finmodel cycle data/edgar/USB.json --sector banking --field net_income --revenue-field equity` — the default `operating_income`/`revenue` fields are meaningless for a bank (§ above), so this is the correct way to call the sector-tuning module for a financial institution, not an optional variant.

FY2025 ROE 11.6% vs trailing-8yr median 11.5% (+0.6%) → near normal.

Data-driven ROE targets from USB's own trailing 8 fiscal years: bear 9.3%, base (trailing median) 11.5%, blue sky (trailing peak) 14.5% — versus the hand-picked 10.7%/14.5% used in the residual-income section above.

| Scenario | Raw (hand-picked ROE) range | Sector-normalized (data-driven ROE) range |
|---|---|---|
| Base case | 44.32 – 47.55 | 45.98 – 49.74 |
| Blue sky | 52.09 – 57.86 | 52.09 – 57.86 |

## Method note

Every book value / tangible book value / net income figure is from an SEC 10-K (via `finmodel.edgar`); every price is a live database query against `market_data`; the two deals' exchange ratios and announcement dates are public record; the two residual-income scenarios are explicitly labelled illustrative ROE assumptions grounded in USB's own historical range, not analyst consensus. Both SunTrust and TCF Financial are delisted and absent from the warehouse, so target-side deal premiums are omitted for the same reason as the first three checks.

Regenerate with `python scripts/football_field_usb.py`; chart at `out/charts_football_field_usb.html`.