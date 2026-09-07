# Second real-company check: the CFI football-field template against Chevron (CVX)

Same method as `docs/FOOTBALL_FIELD_STLD.md`, applied to a different industry (oil & gas majors instead of steel) to check the method generalizes rather than being tuned to one sector. Real peer trading comps, two real verifiable E&P precedent deals, two DCF scenarios grounded in Chevron's own margin history, and Chevron's real 52-week range — compared to Chevron's actual price of **$168.24** (warehouse close, 2026-07-02).

## Football field

| Method | Low | High | Current price inside range? |
|---|---|---|---|
| Trading comps | 104.43 | 306.63 | yes |
| Precedent transactions | 57.57 | 289.37 | yes |
| DCF - base case (margin near 2023-25 average) | 140.83 | 200.63 | yes |
| DCF - blue sky (margin recovers toward 2022 peak) | 207.99 | 296.92 | price is below this range |
| 52-week range | 141.47 | 209.23 | yes |

Only Trading comps, Precedent transactions, DCF - base case (margin near 2023-25 average) and 52-week range bracket the actual price.

Ranges the price sits **below** (implied values too high): DCF - blue sky (margin recovers toward 2022 peak) (low 207.99).

## 1. Trading comps (real: SEC EDGAR fundamentals + market_data warehouse prices)

Peers: ExxonMobil, ConocoPhillips, EOG Resources, Occidental Petroleum — FY2025 fundamentals, 2026-07-02 closing prices.

| Ticker | Price | EV/Revenue | EV/EBITDA | EV/EBIT | P/E |
|---|---|---|---|---|---|
| XOM | 137.19 | 1.90x | 9.29x | 15.06x | 20.48x |
| COP | 103.63 | 2.48x | 5.85x | 10.82x | 16.26x |
| EOG | 130.00 | 3.34x | 6.96x | 11.83x | 14.25x |
| OXY | 48.48 | 3.17x | 5.83x | 16.28x | 20.47x |

| Multiple | 25th | Median | 75th |
|---|---|---|---|
| EV / Revenue LTM | 2.34x | 2.83x | 3.21x |
| EV / EBITDA LTM | 5.85x | 6.41x | 7.55x |
| EV / EBIT LTM | 11.58x | 13.45x | 15.37x |

## 2. Precedent transactions (real, verifiable deals)

### ExxonMobil / Pioneer Natural Resources — announced 2023-10-11

All-stock: 2.3234 acquirer shares per target share x the acquirer's own warehouse closing price on the announcement date = offer **$225.65**/target share. Enterprise value **$60,736M** = equity value $56,864M (252.0M target diluted shares) + net debt $3,872M, target fundamentals from its FY2022 10-K (SEC EDGAR).

LTM revenue $24,294M, LTM EBITDA $12,609M, LTM EBIT $10,079M → **EV/Revenue 2.50x, EV/EBITDA 4.82x, EV/EBIT 6.03x**.

*Source: exchange ratio: publicly disclosed deal terms; XOM close: market_data warehouse; PXD revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K.*

### ConocoPhillips / Marathon Oil — announced 2024-05-29

All-stock: 0.255 acquirer shares per target share x the acquirer's own warehouse closing price on the announcement date = offer **$27.59**/target share. Enterprise value **$21,595M** = equity value $16,772M (608.0M target diluted shares) + net debt $4,823M, target fundamentals from its FY2023 10-K (SEC EDGAR).

LTM revenue $6,697M, LTM EBITDA $4,459M, LTM EBIT $2,248M → **EV/Revenue 3.22x, EV/EBITDA 4.84x, EV/EBIT 9.61x**.

*Source: exchange ratio: publicly disclosed deal terms; COP close: market_data warehouse; MRO revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K.*

Note the direction of the earnings-cycle distortion here is the **opposite** of the steel precedents in `docs/FOOTBALL_FIELD_STLD.md`: both target fiscal years (PXD FY2022, MRO FY2023) fell in or just after the 2022 oil-and-gas price spike, so LTM EBITDA was unusually *high* — this makes the resulting EV/EBITDA multiples look unusually *cheap* rather than expensive, the mirror image of steel's 2025 trough-earnings problem. Trailing multiples get distorted by the cycle in both directions; which direction depends on when the deal happened to close relative to the target's own earnings cycle, not on any property of the target's business.

## 3. DCF (illustrative scenarios built from Chevron's own historical range, not analyst consensus)

Discount rate 8.26% for both scenarios (`finmodel wacc examples/wacc_cvx.json`); terminal growth 2.5%, perpetuity method. Chevron's own EBIT margin ranged from -7.1% (2020, COVID demand collapse) to +20.4% (2022, post-invasion oil price spike) over FY2018-2025 — an even wider real range than steel's, since a commodity producer's margin swings with a price it does not control. The low-high range is a small discount-rate (±0.5pt) x terminal-growth (2.0%/2.5%/3.0%) sensitivity grid.

**DCF - base case (margin near 2023-25 average)**: revenue grows 2%/yr, EBIT margin reaches 13.5% by year 5 (FY2025 was 11.1%) → implied share price **165.57** (range 140.83 – 200.63 across the sensitivity grid).

**DCF - blue sky (margin recovers toward 2022 peak)**: revenue grows 5%/yr, EBIT margin reaches 20.0% by year 5 (FY2025 was 11.1%) → implied share price **244.77** (range 207.99 – 296.92 across the sensitivity grid).


## 4. 52-week trading range (real, market_data warehouse)

$141.47 – $209.23 (2025-07-02 to 2026-07-02, 252 trading days).

## 5. Sector-tuned comparison: does cycle-normalizing the inputs change the answer?

The same `finmodel.sectors` treatment as `docs/FOOTBALL_FIELD_STLD.md`, applied here. Chevron's own FY2025 margin sits only modestly below its own trailing 8-year median (`finmodel cycle data/edgar/CVX.json --sector oil_gas` calls it 'near normal', not a trough) — a real, useful contrast with STLD, where FY2025 WAS flagged as a trough. The precedent-deal targets are a different story: both PXD (as of FY2022) and MRO (as of FY2023) sit at or near their own historical peaks. This section rebuilds every input with each company's own trailing-history median EBIT/EBITDA instead of its raw LTM year, holding every other assumption identical.

| Method | Raw LTM range | Sector-normalized range | Normalized brackets price? |
|---|---|---|---|
| Trading comps | 104.43 – 306.63 | 104.43 – 306.63 | yes |
| Precedent transactions | 57.57 – 289.37 | 208.39 – 519.46 | no |
| DCF - base case | 140.83 – 200.63 | 139.02 – 198.06 | yes |
| DCF - blue sky | 207.99 – 296.92 | 211.74 – 302.26 | no |
| 52-week range | 141.47 – 209.23 | 141.47 – 209.23 (unchanged — real price history) | yes |

Data-driven margin targets from Chevron's own trailing 8 fiscal years (`finmodel cycle`): bear -7.1%, base (trailing median) 13.3%, blue sky (trailing peak, FY2022) 20.4% — versus the hand-picked 13.5%/20.0% used in the raw run above.

Normalizing changes which methods bracket the price: raw run → Trading comps, Precedent transactions, DCF - base case (margin near 2023-25 average) and 52-week range; normalized run → Trading comps, DCF - base case (sector-normalized: trailing median margin) and 52-week range.

The trading comps and both DCF scenarios barely move — Chevron's own peer set and its own margin history were never far from normal, so there was little to correct. The precedent-transaction range moves the most, and moves up: normalizing PXD's and MRO's EBIT/EBITDA down from their own 2022/2023 cycle peaks toward their trailing-history median makes the deals' EV/EBITDA multiples meaningfully more expensive (as flagged qualitatively in section 2), which pushes the whole precedent-implied range up to 208.39 – 519.46 — high enough that it stops bracketing the price at all, this time because the raw range's low end no longer reaches down to Chevron's actual price. Read together with the STLD result, the pattern is that normalization corrects the specific method it's applied to in the direction the sign of that method's own cycle distortion predicts — it doesn't automatically make every football field converge on the market price, because the market price reflects information (forward estimates, buybacks, sentiment) that none of these backward-looking methods carry.

## Method note

Same standard as the STLD check: every revenue/EBIT/D&A/debt/cash figure is from an SEC 10-K (via `finmodel.edgar`), every price is a live database query against `market_data`, the two deals' exchange ratios and announcement dates are public record, and the two DCF scenarios are explicitly labelled illustrative assumptions grounded in the target's own historical margin range, not analyst consensus. Target-side deal premiums are omitted for the same reason as before: both PXD and MRO are delisted and absent from the warehouse.

Regenerate with `python scripts/football_field_cvx.py`; chart at `out/charts_football_field_cvx.html`.