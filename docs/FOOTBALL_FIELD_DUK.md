# Ninth real-company check: regulated utilities are the low-cyclicality bookend — and the standard framework mostly just works

Same real-data method as the eight prior checks, applied to Duke Energy (DUK). Unlike banking, REITs, insurance and (partially) semiconductors, the STANDARD EV-based comps framework (EV/Revenue, EV/EBITDA, EV/EBIT, P/E) needs no override here — the interesting findings are elsewhere: a real secular margin trend, a persistently thin unlevered free cash flow that's a feature not a bug, a real credit-rating mismatch, and a real equity-dilution mechanism at a peer.

## Football field

| Method | Low | High | Current price inside range? |
|---|---|---|---|
| Trading comps | 109.26 | 188.79 | yes |
| Precedent transactions | -21.88 | 83.04 | price is above this range |
| DCF - base (terminal growth anchored to DUK's own real 5-7% EPS guidance) | -17.49 | 67.38 | price is above this range |
| DCF - blue sky (top of DUK's own real guidance range, FY2025 actual margin sustained) | 39.86 | 196.17 | yes |
| 52-week range | 112.07 | 132.32 | yes |

Trading comps, DCF - blue sky (top of DUK's own real guidance range, FY2025 actual margin sustained) and 52-week range bracket the actual price.
Ranges the price sits **above**: Precedent transactions (high 83.04), DCF - base (terminal growth anchored to DUK's own real 5-7% EPS guidance) (high 67.38).

## 1. Trading comps (EV/Revenue, EV/EBITDA, EV/EBIT, P/E — the standard framework, no override needed)

Peers: Southern Company, American Electric Power, Dominion Energy, Exelon, Xcel Energy — real large-cap US regulated electric/gas utilities.

| Ticker | Price | EV/Revenue | EV/EBITDA | EV/EBIT | P/E |
|---|---|---|---|---|---|
| SO | 97.08 | 5.83x | 12.95x | 23.66x | 24.80x |
| AEP | 137.46 | 5.53x | 14.00x | 22.75x | 19.99x |
| D | 68.94 | 6.36x | 15.45x | 23.80x | 19.67x |
| EXC | 47.45 | 3.99x | 11.01x | 18.81x | 17.35x |
| XEL | 81.27 | 5.41x | 14.31x | 30.75x | 23.72x |

| Multiple | 25th | Median | 75th |
|---|---|---|---|
| EV / Revenue | 5.41x | 5.53x | 5.83x |
| EV / EBITDA | 12.95x | 14.00x | 14.31x |
| EV / EBIT | 22.75x | 23.66x | 23.80x |
| P / E | 19.67x | 19.99x | 23.72x |

## 2. Precedent transactions (real, verifiable, all-cash regulated-utility mergers)

### Exelon / Pepco Holdings — announced 2014-04-30

All-cash: **$27.25**/target share. Equity value $6,704M (246.0M target diluted shares) + net debt $4,433M = enterprise value **$11,136M**, target fundamentals from its FY2013 10-K (SEC EDGAR).

**EV/Revenue 2.39x, EV/EBITDA 9.76x, EV/EBIT 16.67x, P/E NM** (target net income -$212M).

### Southern Company / AGL Resources — announced 2015-08-24

All-cash: **$66.00**/target share. Equity value $7,867M (119.2M target diluted shares) + net debt $3,675M = enterprise value **$11,542M**, target fundamentals from its FY2014 10-K (SEC EDGAR).

**EV/Revenue 2.14x, EV/EBITDA 7.83x, EV/EBIT 10.54x, P/E 16.32x** (target net income $482M).

Pepco Holdings' real FY2013 net loss isn't a data error — confirmed against SEC's live XBRL data (`EarningsPerShareDiluted` = -$0.86 for that year) — and `comps.multiple()`'s NM-cap logic correctly reports its P/E as NM rather than a nonsensical negative multiple, the same real pattern the steel, airline and insurance checks' precedents hit.

A real, smaller finding visible in the football field itself: the EV/Revenue precedent bracket's low end implies a NEGATIVE equity value for DUK (see the table below), while EV/EBITDA and EV/EBIT from the same two deals don't have this problem. The cause is real, not a data error: both 2014-2015 targets were meaningfully less levered per dollar of revenue than Duke Energy is today (Pepco Holdings' net debt was 0.95x its own revenue, AGL Resources' 0.68x, versus DUK's real 2.74x) — EV/Revenue implicitly assumes similar leverage-per-revenue-dollar across targets, which breaks down for a much larger, more heavily-levered multi-state holding company; EV/EBITDA and EV/EBIT scale with capital intensity rather than raw revenue and don't inherit the same problem.

## 3. The real, sector-defining finding: elevated capex is the steady state, not a peak to fade

| FY | Capex/Revenue | D&A/Revenue | Unlevered FCF (before NWC, $M) |
|---|---|---|---|
| 2019 | 45.7% | 21.3% | -960 |
| 2020 | 42.6% | 23.6% | 990 |
| 2021 | 39.7% | 23.1% | 1,079 |
| 2022 | 39.6% | 20.4% | 46 |
| 2023 | 44.0% | 21.2% | -100 |
| 2024 | 40.9% | 21.4% | 1,165 |
| 2025 | 44.2% | 24.3% | 1,336 |

Real capex ran 39.6%-45.7% of revenue every single year FY2019-2025 — a persistent ~1.8-2.1x real D&A — and unlevered free cash flow (before working capital) was **negative** in 2 of those 7 years, never exceeding roughly $1.3B against $87B of debt and a ~$100B market cap. This isn't distress: it's the entire regulated-return mechanism working as designed — a utility earns its allowed ROE on a rate base that only grows if it keeps building it, so capex staying elevated forever (not fading back toward D&A the way the semiconductor check's temporary supercycle did) is the real, correct assumption for a utility DCF. The practical consequence, verified in the DCF below: with near-term UFCF this thin, terminal value carries the large majority of enterprise value — functionally, a 'standard' unlevered DCF ends up shaped like a perpetuity-dominated dividend discount model without actually needing to swap engines the way banking/REITs/insurance did.

## 4. DCF (unlevered, capex held at DUK's own real FY2025 ratio — not tapered) — and why the terminal growth rate matters more here than anywhere else this toolkit has checked

Discount rate 6.19% (`finmodel wacc examples/wacc_duk.json`) — itself the LOWEST WACC of any sector this toolkit has profiled, a direct consequence of DUK's low 0.35 unlevered beta and heavy tax-advantaged debt weighting. Margin scenarios use DUK's own real recent levels — FY2025 actual margin 27.2%, trailing-3yr average 26.1%, trailing-8yr median 23.4% — not a blind trailing-median reversion, since §5 below confirms DUK's real margin trend is a genuine, sustained improvement, not a cyclical extreme to revert away from.

With UFCF this thin (§3), terminal value dominates enterprise value so completely that the perpetuity growth assumption, not the 5-year forecast, drives the whole result — verified by actually running both a generic and a real-guidance-anchored assumption side by side:

**DCF - bear (generic 2.5% terminal growth, revert to trailing 8yr median margin)** (perpetual growth 2.5%, margin target 23.4%, revenue growth 3.0%/yr) -> implied share price **-88.88** (range -92.06 - -84.09); terminal value is 75% of enterprise value.
**DCF - base (terminal growth anchored to DUK's own real 5-7% EPS guidance)** (perpetual growth 4.5%, margin target 26.1%, revenue growth 6.0%/yr) -> implied share price **21.76** (range -17.49 - 67.38); terminal value is 92% of enterprise value.
**DCF - blue sky (top of DUK's own real guidance range, FY2025 actual margin sustained)** (perpetual growth 5.0%, margin target 27.2%, revenue growth 7.0%/yr) -> implied share price **131.34** (range 39.86 - 196.17); terminal value is 95% of enterprise value.

The bear case's generic 2.5% terminal growth rate — this toolkit's usual default, and a perfectly ordinary assumption for a mature industrial — produces a NEGATIVE implied equity value here. That is not a sign DUK is worth less than zero; it's a tell that 2.5% silently assumes DUK's real, currently-disclosed $103B 2026-2030 capital plan (which DUK itself guides to 5%-7% long-run EPS growth off a 9.6% rate-base growth rate) stops mattering the instant the 5-year forecast window ends. The base and blue-sky cases instead anchor terminal growth to DUK's own real guidance (4.5% and 5.0% respectively — moderated below the low end of that 5%-7% range specifically to stay safely under the 6.19% discount rate, since a Gordon-growth perpetuity is mathematically undefined once growth reaches it), producing positive, far more defensible values. No prior sector check in this series has been this sensitive to the terminal growth assumption — a direct, real consequence of pairing thin UFCF with a low WACC, both of which are structural to how a regulated utility is financed.


## 5. A real callback on a third, independent sector: the trend guard from software/insurance, on regulated rate-base growth

`finmodel cycle data/edgar/DUK.json --sector utility` — the default field (operating_income/revenue) needs no override here, unlike banking/REIT/insurance:

FY2025 margin 27.2% vs trailing-8yr median 23.4% (+15.9%) -> **peak — trailing multiples built on this year likely UNDERstate the true multiple**. `trend_diagnostics()` fires **strong** (r=0.75, improving) — the same guard `docs/FOOTBALL_FIELD_CSCO.md` (software) and `docs/FOOTBALL_FIELD_TRV.md` (insurance) established, now confirmed on a THIRD, independent sector: DUK's real margin genuinely improved (23.4% -> 27.2%, FY2019-2025) because its real rate base has been growing (the capex table in §3), not because of a cyclical peak a trailing-median would be right to fade.

## 6. A real, verified caveat for `finmodel.wacc.synthetic_rating()` on regulated entities

DUK's real FY2025 interest coverage (EBIT $8,626M / interest expense $3,634M = 2.37x) maps to a synthetic **'BB+'** rating on Damodaran's large-firm coverage table — sub-investment-grade. DUK's REAL rating, as of 2026-02, is investment-grade: **BBB** (S&P) / **Baa2** (Moody's), both stable outlook. The coverage table was built for unregulated industrials; a regulated utility is ALLOWED to run structurally thin coverage because rate-of-return regulation makes debt-service recovery through rates close to guaranteed — the same low-coverage SIGNAL the airline check saw on a genuinely distressed ALK, with the opposite real-world meaning here. Always sanity-check a coverage-based synthetic rating against the filer's actual published rating before using it for a regulated entity.

## 7. A real, independent finding at a peer: Xcel Energy's ROE dilution from funding its capital plan

`finmodel cycle data/edgar/XEL.json --sector utility --field net_income --revenue-field equity` — XEL's own ROE held a tight 10.1%-10.4% band FY2018-2024 before dropping to 8.5% in FY2025 (-15.9% vs the trailing-8yr median). `trend_diagnostics()` fires **strong** (r=-0.70, declining) — but the real cause isn't earnings deterioration: Xcel Energy closed a real ~$1.18B forward common-stock offering in November 2024 (18,320,610 shares at $65.50) and disclosed a further $4.3B equity distribution program funding its multi-year capital plan, mechanically diluting ROE in the issuance year before the new equity has earned a full year's return — a real, utility-specific mechanism distinct from every other sector's cyclicality driver this module has been tuned against (commodity price, credit losses, rate-sensitivity, demand shock, catastrophe losses, the silicon cycle).

## 8. 52-week trading range (real, market_data warehouse)

$112.07 - $132.32 (2025-07-02 to 2026-07-02, 252 trading days).

## Method note

Every revenue/EBIT/D&A/debt/cash figure is from an SEC 10-K (via `finmodel.edgar`); every price is a live database query against `market_data`; both deals' per-share cash prices and announcement dates come from the acquirer's own 8-K press releases (public record). Both real precedent targets are delisted (though the same CIKs still file as wholly-owned subsidiaries with public debt outstanding, which is how their historical fundamentals were pulled), so target-side deal premiums are omitted for the same reason as the banking, REIT, airline and insurance checks' precedents.

Regenerate with `python scripts/football_field_duk.py`; chart at `out/charts_football_field_duk.html`.