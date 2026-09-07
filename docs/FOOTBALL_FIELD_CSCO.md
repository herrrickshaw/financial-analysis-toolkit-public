# Third real-company check: the CFI football-field template against Cisco (CSCO)

Same method as `docs/FOOTBALL_FIELD_STLD.md` (steel) and `docs/FOOTBALL_FIELD_CVX.md` (oil & gas), applied to a third, structurally different sector: enterprise technology / software, expected — and, per `finmodel.sectors`, confirmed — to show far lower earnings cyclicality than either commodity sector. Real peer trading comps, two real all-cash precedent deals, two DCF scenarios grounded in Cisco's own margin history, and Cisco's real 52-week range — compared to Cisco's actual price of **$112.36** (warehouse close, 2026-07-02).

## Football field

| Method | Low | High | Current price inside range? |
|---|---|---|---|
| Trading comps | 59.14 | 117.59 | yes |
| Precedent transactions | 107.79 | 228.87 | yes |
| DCF - base case (margin near recent 3yr average) | 42.80 | 57.89 | price is above this range |
| DCF - blue sky (margin recovers toward FY2020-22 level) | 57.00 | 77.58 | price is above this range |
| 52-week range | 65.10 | 130.00 | yes |

Trading comps, Precedent transactions and 52-week range bracket the actual price.
Ranges the price sits **above**: DCF - base case (margin near recent 3yr average) (high 57.89), DCF - blue sky (margin recovers toward FY2020-22 level) (high 77.58).

## 1. Trading comps (real: SEC EDGAR fundamentals + market_data warehouse prices)

Peers: Microsoft, Oracle, IBM, Adobe, Salesforce — latest-fiscal-year fundamentals, 2026-07-02 closing prices.

| Ticker | Price | EV/Revenue | EV/EBITDA | EV/EBIT | P/E |
|---|---|---|---|---|---|
| MSFT | 389.13 | 8.63x | 15.11x | 18.45x | 21.68x |
| ORCL | 139.97 | 7.51x | 17.93x | 24.56x | 23.87x |
| IBM | 286.68 | 4.73x | 23.00x | 27.52x | 25.67x |
| ADBE | 220.55 | 3.95x | 9.85x | 10.77x | 13.21x |
| CRM | 166.32 | 3.95x | 17.19x | 19.67x | 21.32x |

| Multiple | 25th | Median | 75th |
|---|---|---|---|
| EV / Revenue LTM | 3.95x | 4.73x | 7.51x |
| EV / EBITDA LTM | 15.11x | 17.19x | 17.93x |
| EV / EBIT LTM | 18.45x | 19.67x | 24.56x |

Note the absolute level of these multiples versus the earlier checks: even the *25th percentile* EV/EBITDA here exceeds the *75th percentile* for steel or oil & gas — enterprise software commands structurally richer multiples because of higher margins, recurring revenue and lower reinvestment needs, not because these five companies are in the same cyclical position steel or oil & gas producers were.

## 2. Precedent transactions (real, verifiable, all-cash deals)

### Broadcom / VMware — announced 2022-05-26

All-cash: offer **$142.50**/share. Enterprise value **$69,248M** = equity value $60,191M (422.4M target diluted shares) + net debt $9,057M, target fundamentals from its FY2022 10-K (SEC EDGAR).

LTM revenue $12,851M, LTM EBITDA $3,497M, LTM EBIT $2,387M → **EV/Revenue 5.39x, EV/EBITDA 19.80x, EV/EBIT 29.01x**.

*Source: offer price: publicly disclosed deal terms (all-cash); VMware revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K.* *Note: VMware's debt includes ~$11.5bn raised for a special dividend ahead of the deal, not organic leverage.*

### IBM / Red Hat — announced 2018-10-28

All-cash: offer **$190.00**/share. Enterprise value **$33,350M** = equity value $35,074M (184.6M target diluted shares) + net debt $-1,724M, target fundamentals from its FY2018 10-K (SEC EDGAR).

LTM revenue $2,920M, LTM EBITDA $573M, LTM EBIT $476M → **EV/Revenue 11.42x, EV/EBITDA 58.22x, EV/EBIT 70.10x**.

*Source: offer price: publicly disclosed deal terms (all-cash); Red Hat revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K.*

Unlike the steel and oil & gas precedents, both deals here are simple all-cash offers, so no acquirer share price or exchange ratio was needed to compute the offer value. Both multiples are far richer than the steel or oil & gas precedents (Red Hat alone traded at ~58x EBITDA) — again a real structural sector difference, not a cyclical distortion.

## 3. DCF (illustrative scenarios built from Cisco's own historical range, not analyst consensus)

Discount rate 8.68% for both scenarios (`finmodel wacc examples/wacc_csco.json`); terminal growth 2.5%, perpetuity method. Cisco's own EBIT margin ranged 20.8%-27.6% over FY2020-2026 — far tighter than steel's 8.1%-23.4% or Chevron's -7.1% to +20.4%, consistent with the 'low cyclicality' `finmodel.sectors` classification. The low-high range is a small discount-rate (±0.5pt) x terminal-growth (2.0%/2.5%/3.0%) sensitivity grid.

**DCF - base case (margin near recent 3yr average)**: revenue grows 3%/yr, EBIT margin reaches 23.0% by year 5 (FY2026 was 24.3%) → implied share price **49.14** (range 42.80 – 57.89 across the sensitivity grid).

**DCF - blue sky (margin recovers toward FY2020-22 level)**: revenue grows 6%/yr, EBIT margin reaches 27.0% by year 5 (FY2026 was 24.3%) → implied share price **65.64** (range 57.00 – 77.58 across the sensitivity grid).

## 4. 52-week trading range (real, market_data warehouse)

$65.10 – $130.00 (2025-07-02 to 2026-07-02, 252 trading days).

## 5. Sector-tuned comparison, with a trend-detection guard this time

The same `finmodel.sectors` treatment as the first two checks, but this one adds a step the earlier scripts didn't need: before normalizing each peer's EBIT/EBITDA to a trailing-history median, this script runs `trend_diagnostics()` on it first. A commodity producer's margin history is mean-reverting, so a trailing median is a sensible baseline; several software peers here are on genuine secular trends where it is not.

| Peer | Trend | Direction | Correlation | Normalized this peer? |
|---|---|---|---|---|
| MSFT | strong | improving | 0.95 | no — trend guard skipped it |
| ORCL | moderate | declining | -0.51 | yes |
| IBM | weak/none | none | 0.08 | yes |
| ADBE | moderate | improving | 0.46 | yes |
| CRM | strong | improving | 0.86 | no — trend guard skipped it |

Cisco's own margin also shows a real trend (strong, declining, r=-0.75) despite its tight absolute range — tight range and 'no trend' are different properties (`SECTOR_PROFILES['software']`'s note says so explicitly). This script normalizes Cisco's own metrics anyway, on the judgement that a single gentle drift with a partial recent reversal is a materially different situation from Salesforce's clean, large, one-directional ramp — but a stricter guard could reasonably skip Cisco too; this is a judgement call the tool surfaces rather than hides, not one it resolves for you.

**What normalizing Salesforce anyway would have done, for comparison**: its own trailing-median EBITDA is $1,580M against a real LTM EBITDA of $9,531M — normalizing would have replaced Salesforce's genuine, sustainable, current profitability with a stale average from its intentionally-unprofitable growth years, understating its multiple's denominator and making Salesforce look far more expensive than it now is. This script's trend guard kept Salesforce at its raw LTM figure specifically to avoid that error.

| Method | Raw LTM range | Sector-normalized (trend-guarded) range | Normalized brackets price? |
|---|---|---|---|
| Trading comps | 59.14 – 117.59 | 52.52 – 117.59 | yes |
| Precedent transactions | 107.79 – 228.87 | 100.36 – 155.68 | yes |
| DCF - base case | 42.80 – 57.89 | 47.54 – 64.46 | no |
| DCF - blue sky | 57.00 – 77.58 | 58.23 – 79.29 | no |
| 52-week range | 65.10 – 130.00 | 65.10 – 130.00 (unchanged — real price history) | yes |

Data-driven margin targets from Cisco's own trailing 8 fiscal years (`finmodel cycle`): bear 20.8%, base (trailing median) 25.8%, blue sky (trailing peak) 27.6% — close to the hand-picked 23.0%/27.0% used in the raw run above, since Cisco's tight range leaves little room for a hand-picked guess to be far off.

Normalizing does not change which methods bracket the price here (still Trading comps, Precedent transactions and 52-week range) — consistent with a low-cyclicality sector where there was little real distortion to correct in the first place.

## Method note

Same standard as the first two checks: every revenue/EBIT/D&A/debt/cash figure is from an SEC 10-K (via `finmodel.edgar`), every price is a live database query against `market_data`, the two deals' offer prices and announcement dates are public record, and the two DCF scenarios are explicitly labelled illustrative assumptions grounded in Cisco's own historical margin range, not analyst consensus. Target-side deal premiums are omitted for the same reason as before: both VMware and Red Hat are delisted and absent from the warehouse.

Regenerate with `python scripts/football_field_csco.py`; chart at `out/charts_football_field_csco.html`.