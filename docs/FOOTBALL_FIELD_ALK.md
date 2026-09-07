# Sixth real-company check: airlines need EV/EBITDAR, and a black-swan year trips up this toolkit's own sector tuning

Same real-data method as the five prior checks, applied to Alaska Air Group (ALK). Unlike banking or REITs, EV/EBITDA isn't meaningless here — it's just missing a real, material adjustment that credit analysts have made for airlines and retailers for decades.

## Why EV/EBITDA needs a lease adjustment for an airline (real evidence)

An airline that owns its fleet shows that cost as debt + depreciation (both already inside EV/EBITDA). One that leases its fleet shows it as an operating expense that reduces EBITDA, with — pre-ASC-842 — nothing added to EV to compensate. ASC 842 (FY2019+) fixed half of this by putting the operating lease liability ON the balance sheet with a real, disclosed present value; `finmodel.edgar` now extracts it (`operating_lease_liability_current/noncurrent`, `operating_lease_cost`). Verified on real FY2025 SEC EDGAR data across five real peers:

| Ticker | EV/EBITDA (raw) | EV/EBITDAR (lease-adjusted) | Compression |
|---|---|---|---|
| LUV | 14.94x | N/A | n/a |
| DAL | 8.44x | 8.21x | 2.7% |
| UAL | 7.72x | 7.62x | 1.3% |
| AAL | 9.67x | 7.90x | 18.3% |
| JBLU | 27.24x | 21.27x | 21.9% |

**A real filer-level data gap, not papered over**: Southwest's own XBRL doesn't disaggregate operating lease cost from finance/short-term/variable lease cost — its aggregate `LeaseCost` tag (reported, not estimated) is $2,529M for FY2025, of which $2,130M is `VariableLeaseCost` (airport/gate fees ASC 842 expenses as incurred, with NO matching capitalized liability). Treating that whole aggregate as "operating lease cost" would badly overstate Southwest's EBITDAR add-back relative to peers who report the clean, disaggregated tag — so `finmodel.edgar` keeps `operating_lease_cost`, `total_lease_cost` and `variable_lease_cost` as three separate fields rather than silently falling back from one to another, and this check reports Southwest's EV/EBITDAR as unavailable rather than guessing. See `finmodel.sectors.SECTOR_PROFILES['airline']` for the same finding encoded directly into the toolkit.

## Football field

| Method | Low | High | Current price inside range? |
|---|---|---|---|
| Trading comps (EV/EBITDA, raw) | 38.21 | 97.79 | yes |
| Trading comps (EV/EBITDAR, lease-adjusted) | 39.67 | 81.58 | yes |
| Precedent transactions | 55.09 | 57.62 | price is below this range |
| DCF - naive (periods=8, COVID-contaminated bear case) | -621.47 | -492.84 | price is above this range |
| DCF - sector-normalized (periods=5, trailing median) | -1.24 | 8.62 | price is above this range |
| DCF - sector-normalized (periods=5, trailing peak) | 73.93 | 104.93 | price is below this range |
| 52-week range | 34.19 | 63.86 | yes |

Trading comps (EV/EBITDA, raw), Trading comps (EV/EBITDAR, lease-adjusted) and 52-week range bracket the actual price.
Ranges the price sits **above**: DCF - naive (periods=8, COVID-contaminated bear case) (high -492.84), DCF - sector-normalized (periods=5, trailing median) (high 8.62).
Ranges the price sits **below**: Precedent transactions (low 55.09), DCF - sector-normalized (periods=5, trailing peak) (low 73.93).

## 1. Trading comps (real: SEC EDGAR fundamentals + market_data warehouse prices)

Peers: Southwest, Delta, United, American, JetBlue — the other five large US network/low-cost carriers.

| Multiple | 25th | Median | 75th |
|---|---|---|---|
| EV/EBITDA (raw) | 8.44x | 9.67x | 14.94x |
| EV/EBITDAR (lease-adjusted, n=4 of 5) | 7.83x | 8.06x | 11.48x |

## 2. Precedent transactions (real, verifiable, all-cash airline mergers, both Alaska as acquirer)

### Alaska Air Group / Virgin America — announced 2016-04-04

All-cash: **$57.00**/target share. Equity value **$2,535M** (44.5M target diluted shares), target EBITDA $196M, lease adjustment: estimated (7x disclosed rent expense, pre-ASC-842 convention), target fundamentals from its FY2015 10-K (SEC EDGAR).

**EV/EBITDA 11.78x, EV/EBITDAR 9.17x**.

### Alaska Air Group / Hawaiian Holdings — announced 2023-12-03

All-cash: **$18.00**/target share. Equity value **$929M** (51.6M target diluted shares), target EBITDA -$160M, lease adjustment: real (ASC 842 disclosed), target fundamentals from its FY2023 10-K (SEC EDGAR).

**EV/EBITDA NM, EV/EBITDAR NM**.

**A real, quoted confirmation of the old rule-of-thumb convention**: Alaska/Virgin America's own 2016 press release states the "aggregate transaction value" of approximately $4.0 billion is "inclusive of existing indebtedness and CAPITALIZED AIRCRAFT OPERATING LEASES" — three years before ASC 842 made that capitalization mandatory. Backing out the implied capitalized-lease amount from that $4.0B figure against Virgin America's own real FY2015 rent expense ($235.3M, via the pre-ASC-842 `pre_842_rent_expense` tag) gives an implied capitalization multiple of **~7.0x** — independently backed into from real disclosed numbers here, not assumed, and landing almost exactly on the classic "7-8x annual rent" credit-analyst rule of thumb this check's `lease_adjustment()` helper uses as its own pre-ASC-842 estimate.

## 3. DCF — a real methodological trap in this toolkit's own sector tuning

Cost of capital 10.47% (`finmodel wacc examples/wacc_alk.json`; ALK's real FY2025 interest coverage is thin enough — EBIT $303M vs interest expense $272M — to map to a distressed synthetic credit rating and a correspondingly high cost of debt; this is real, not a stress-tested assumption). `finmodel.sectors.dcf_scenarios_from_history()`'s usual `periods=8` default returns a bear_margin of **-49.8%** — literally FY2020's pandemic-collapse EBIT margin, not a plausible recurring bear case for a 5-year forward projection (a company sustaining that margin for 5 straight years would be bankrupt, not bearish). `periods=5` (the trailing FY2021-2025 recovery years, which excludes FY2020 entirely) gives a real, usable 0.7%/3.8%/11.1% bear/base/blue-sky instead.

**DCF - naive (periods=8, COVID-contaminated bear case)** (EBIT margin target -49.8%) → implied share price **$-549.11** (range -621.47 – -492.84).
**DCF - sector-normalized (periods=5, trailing median)** (EBIT margin target 3.8%) → implied share price **$3.08** (range -1.24 – 8.62).
**DCF - sector-normalized (periods=5, trailing peak)** (EBIT margin target 11.1%) → implied share price **$87.50** (range 73.93 – 104.93).

A deeply negative implied share price (the naive scenario above) isn't a literal fair-value estimate — real equity floors at $0 — it's this check's DCF math correctly reporting that a 5-year pandemic-level EBIT margin would consume far more cash in committed fleet capex than the business generates, an honest signal that the input assumption itself is unusable, not a valuation to report at face value.

## 4. 52-week trading range (real, market_data warehouse)

$34.19 – $63.86 (2025-07-02 to 2026-07-02, 252 trading days).

## 5. A second real trap: correlation-based trend detection can't tell a structural decline from a one-off cliff

`trend_diagnostics()` on ALK's own EBIT margin history, 5-year window ending right after the COVID crash (`as_of='2020-12-31'`): correlation r=-0.80, flagged **strong** — a real result. But the SAME company's 8-year window ending FY2025 (which includes the recovery) resolves this back to **weak/none** (r=0.11). A correlation coefficient cannot, by construction, distinguish "gradual multi-year structural decline" (Salesforce's real margin-expansion trend in the software check, in the opposite direction) from "stable, then one catastrophic data point" — both can produce a strong |r| over a short-enough window ending right after the discontinuity. Worth remembering before trusting a trend flag near any real shock, not just this one.

## Method note

Every EBITDA / lease / debt figure is from an SEC 10-K (via `finmodel.edgar`); every price is a live database query against `market_data`; both deals' per-share cash prices and announcement dates come from Alaska Air Group's or Virgin America's own 8-K press releases (public record). Both real precedent targets are delisted and absent from the warehouse, so target-side deal premiums are omitted for the same reason as the banking and REIT checks' precedents.

Regenerate with `python scripts/football_field_alk.py`; chart at `out/charts_football_field_alk.html`.