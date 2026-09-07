# Checking the CFI football-field template against real Steel Dynamics (STLD) numbers

`finmodel.comps.football_field()` is reconciled in `tests/test_comps.py` against the CFI template's own illustrative numbers (fictional companies, fictional deals). This runs the same function on real inputs: real peer trading comps (SEC EDGAR + market_data warehouse), two real, verifiable steel-industry M&A precedents, two DCF scenarios built from STLD's own historical margin range, and STLD's real 52-week trading range — then compares the resulting football field to STLD's actual price of **$217.16** (warehouse close, 2026-07-02).

## Football field

| Method | Low | High | Current price inside range? |
|---|---|---|---|
| Trading comps | 90.30 | 434.61 | yes |
| Precedent transactions | 46.84 | 155.72 | price is above this range |
| DCF - base case (margin recovers toward FY2024 level) | 58.66 | 80.62 | price is above this range |
| DCF - blue sky (margin recovers toward FY2023 level) | 67.02 | 94.12 | price is above this range |
| 52-week range | 119.93 | 282.12 | yes |

Only Trading comps and 52-week range bracket the actual price. The trailing-multiple trading comps bracket it only because 2025 was a trough-earnings year industry-wide (the same distortion documented in `docs/VALIDATION_REAL_DATA.md` — depressed LTM EBITDA inflates EV/EBITDA), which happens to pull the range wide enough to catch the price rather than because the multiples are themselves informative. The two precedent-transaction deals and both DCF scenarios sit **entirely below** the actual price (highs of 155.72, 80.62, 94.12 vs the price of 217.16) — the honest reading is that a conservative, backward-looking model (deals priced off a *depressed* target's trailing metrics; a DCF anchored to STLD's own *depressed* FY2025 base year) undershoots what the market is actually paying. Two real, unmodelled reasons this toolkit's DCF cannot capture from EDGAR alone: STLD has been aggressively buying back stock (diluted shares fell from 235.2M in FY2018 to 148.4M in FY2025, a 37% reduction — a forward buyback pace mechanically raises per-share value in a way a single-base-year DCF does not price in), and steel-industry valuations in the 2021–2023 upcycle traded at multiples well above what trailing fundamentals alone would justify, which the market may still be partly extrapolating. This is exactly the gap a forward (FY+1/FY+2 *consensus*) comps set and a buyback-aware DCF would close — and exactly what EDGAR's trailing, as-filed data cannot supply.

## 1. Trading comps (real: SEC EDGAR fundamentals + market_data warehouse prices)

Same carbon-steel peer set and prices as `docs/VALIDATION_REAL_DATA.md` (NUE, CMC, RS, CLF, WOR); see that document for the full peer table. Statistics feeding the football field:

| Multiple | 25th | Median | 75th |
|---|---|---|---|
| EV / Revenue LTM | 0.92x | 1.45x | 1.71x |
| EV / EBITDA LTM | 15.69x | 17.14x | 19.21x |
| EV / EBIT LTM | 21.03x | 30.12x | 45.92x |

## 2. Precedent transactions (real, verifiable deals)

### Nippon Steel / United States Steel — announced 2023-12-18

Enterprise value **$15,253M** = equity value $14,045M (offer $55.00/share × 255.4M diluted shares) + net debt $1,208M, all from the target's FY2023 10-K (SEC EDGAR).

LTM revenue $18,053M, LTM EBITDA (EBIT + D&A) $1,715M, LTM EBIT $799M → **EV/Revenue 0.84x, EV/EBITDA 8.89x, EV/EBIT 19.09x**.

*Source: offer price: publicly disclosed deal terms; revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K.*

### Cleveland-Cliffs / AK Steel Holding — announced 2019-12-02

Enterprise value **$2,979M** = equity value $1,041M (offer $3.29/share × 316.6M diluted shares) + net debt $1,938M, all from the target's FY2019 10-K (SEC EDGAR).

LTM revenue $6,359M, LTM EBITDA (EBIT + D&A) $402M, LTM EBIT $209M → **EV/Revenue 0.47x, EV/EBITDA 7.41x, EV/EBIT 14.23x**.

*Source: CLF close: market_data warehouse (dividend-adjusted, likely a few % below the nominal quote); AKS revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K.*

CLF's own closing price on the AK Steel announcement date was $8.2181 (market_data warehouse; likely a dividend-adjusted figure a few percent below the nominal quote that day). Premiums to AK Steel's own undisturbed price are not shown: AK Steel is delisted and absent from the warehouse, and Yahoo Finance and Stooq both refuse historical data for a fully delisted ticker, so there is no independently verifiable price series to compute a premium against.

## 3. DCF (illustrative scenarios built from STLD's own historical range, not analyst consensus)

Discount rate 10.28% for both scenarios (`finmodel wacc examples/wacc_stld.json`); terminal growth 2.5%, perpetuity method. The low–high range is a small discount-rate (±0.5pt) × terminal-growth (2.0%/2.5%/3.0%) sensitivity grid around each scenario's central case, standing in for a banker's data table.

**DCF - base case (margin recovers toward FY2024 level)**: revenue grows 3%/yr, EBIT margin reaches 11.0% by year 5 (FY2025 was 8.1%) → implied share price **68.24** (range 58.66 – 80.62 across the sensitivity grid).

**DCF - blue sky (margin recovers toward FY2023 level)**: revenue grows 6%/yr, EBIT margin reaches 16.8% by year 5 (FY2025 was 8.1%) → implied share price **78.83** (range 67.02 – 94.12 across the sensitivity grid).

## 4. 52-week trading range (real, market_data warehouse)

$119.93 – $282.12 (2025-07-02 to 2026-07-02, 252 trading days).

## 5. Sector-tuned comparison: does cycle-normalizing the inputs change the answer?

`finmodel.sectors` was built from exactly the distortion this document flags above: STLD's own FY2025 EBIT margin (8.1%) sits well below its own trailing 8-year median (12.8%), a real trough by `finmodel cycle`'s own diagnostic (`finmodel cycle data/edgar/STLD.json --sector steel`). This section rebuilds the trading comps, precedent multiples and DCF scenarios using each company's own trailing-history median EBIT/EBITDA instead of the raw cycle-distorted LTM year, holding every other assumption (growth, D&A%, capex%, discount rate) identical, so the comparison isolates what normalization alone changes.

| Method | Raw LTM range | Sector-normalized range | Normalized brackets price? |
|---|---|---|---|
| Trading comps | 90.30 – 434.61 | 90.30 – 337.47 | yes |
| Precedent transactions | 46.84 – 155.72 | 46.84 – 185.15 | no |
| DCF - base case | 58.66 – 80.62 | 77.08 – 104.45 | no |
| DCF - blue sky | 67.02 – 94.12 | 142.90 – 192.48 | no |
| 52-week range | 119.93 – 282.12 | 119.93 – 282.12 (unchanged — real price history) | yes |

Data-driven margin targets from STLD's own trailing 8 fiscal years (`finmodel cycle`): bear 8.1%, base (trailing median) 12.8%, blue sky (trailing peak) 23.4% — versus the hand-picked 11.0%/16.8% used in the raw run above. The base case is reasonably close (+1.8%pt); the blue-sky case is not: the hand-picked 'toward FY2023' target (16.8%) significantly understated STLD's own historical best case — the true trailing peak, 23.4%, came from FY2021, which sat outside the shorter lookback I picked by hand. This is exactly the failure mode `sectors.dcf_scenarios_from_history` is meant to catch: a hand-picked scenario label ('toward last year', 'toward two years ago') implicitly assumes the cycle's extremes fall within whatever window the analyst happens to be looking at.

Normalizing does **not** change which methods bracket the price here (still Trading comps and 52-week range), even though the individual ranges move — normalizing the trading comps compresses the high end (434.61 → 337.47) because it corrects both sides of the same trade (peer AND target EBITDA rise together, since the whole steel sector shares the same 2025 trough), while normalizing the DCF and precedent ranges pushes them meaningfully higher without lifting them far enough to reach the price. Sector normalization corrected a real distortion in each individual method's own numbers, but by itself it did not close the STLD gap documented above — see `docs/FOOTBALL_FIELD_CVX.md` for a case where cycle normalization was less needed in the first place, because only one side of the trade (the precedent-deal targets) was cycle-distorted, not Chevron's own numbers.

## Method note

Everything here is either a live database query (peer prices, precedent-deal-acquirer's price, 52-week range), a public SEC filing (every revenue/EBIT/D&A/debt/cash figure), a matter of public record (the two deals' offer prices and announcement dates), or an explicitly labelled assumption I built (the two DCF scenarios' growth and margin paths, and the choice of which two precedent deals to include). Nothing here was invented and presented as fact; where a genuinely real number was unavailable (target-side premiums for delisted companies), it was omitted rather than approximated.

Regenerate with `python scripts/football_field_stld.py`; chart at `out/charts_football_field_stld.html`.