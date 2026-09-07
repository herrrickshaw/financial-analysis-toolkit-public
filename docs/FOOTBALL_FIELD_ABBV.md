# Tenth real-company check: a real patent cliff, offset by a real pipeline — and two real data-plumbing bugs found along the way

Same real-data method as the nine prior checks, applied to AbbVie (ABBV). Like airlines/semiconductors/utilities, the standard EV-based comps framework needs no override here — the real story is a genuine patent cliff that didn't sink the company, plus a real GAAP accounting quirk for acquisitive pharma and two real bugs (one in `finmodel.edgar`, one in the `market_data` warehouse) found while building this check.

## Football field

| Method | Low | High | Current price inside range? |
|---|---|---|---|
| Trading comps | 41.33 | 256.36 | price is above this range |
| Precedent transactions | 379.12 | 595.93 | price is below this range |
| DCF - base (6%/yr growth, trailing-8yr median adjusted margin) | 197.21 | 411.33 | yes |
| DCF - blue sky (9%/yr growth, trailing-8yr max adjusted margin) | 281.44 | 581.91 | price is below this range |
| 52-week range | 179.29 | 259.22 | yes |

DCF - base (6%/yr growth, trailing-8yr median adjusted margin) and 52-week range bracket the actual price.
Ranges the price sits **above**: Trading comps (high 256.36).
Ranges the price sits **below**: Precedent transactions (low 379.12), DCF - blue sky (9%/yr growth, trailing-8yr max adjusted margin) (low 281.44).

## 1. Trading comps (EV/Revenue, EV/EBITDA, EV/EBIT, P/E — the standard framework, no override needed)

Peers: Pfizer, Merck, Bristol-Myers Squibb, Eli Lilly — real large-cap US pharmaceutical companies.

| Ticker | Price | EV/Revenue | EV/EBITDA | EV/EBIT | P/E |
|---|---|---|---|---|---|
| PFE | 24.27 | 3.23x | 12.51x | 21.10x | 17.85x |
| MRK | 128.10 | 5.47x | 12.74x | 16.12x | 17.59x |
| BMY | 57.33 | 3.14x | 10.35x | 14.25x | 16.57x |
| LLY | 1206.04 | 17.18x | 39.12x | 42.06x | 52.55x |

| Multiple | 25th | Median | 75th |
|---|---|---|---|
| EV / Revenue | 3.21x | 4.35x | 8.40x |
| EV / EBITDA | 11.97x | 12.62x | 19.34x |
| EV / EBIT | 15.65x | 18.61x | 26.34x |
| P / E | 17.34x | 17.72x | 26.52x |

## 2. Precedent transactions (real, verifiable, all-cash 2022-2023 biotech mergers — a deliberate profitability contrast)

### Pfizer / Seagen — announced 2023-03-13

All-cash: **$229.00**/target share. Equity value $42,291M (184.7M target diluted shares) + net debt $-320M = enterprise value **$41,971M**, target fundamentals from its FY2022 10-K (SEC EDGAR).

**EV/Revenue 21.39x, EV/EBITDA NM, EV/EBIT NM** (target net income -$610M).

### Amgen / Horizon Therapeutics — announced 2022-12-12

All-cash: **$116.50**/target share. Equity value $27,457M (235.7M target diluted shares) + net debt $991M = enterprise value **$28,448M**, target fundamentals from its FY2021 10-K (SEC EDGAR).

**EV/Revenue 8.82x, EV/EBITDA 31.72x, EV/EBIT 52.38x** (target net income $534M).

Seagen's real FY2022 operating income (-$613M) AND EBITDA (-$566M) are both genuinely negative — a still-scaling, pre-profitability oncology biotech, not a data error — so EV/EBIT and EV/EBITDA are correctly NM for that $42B real deal; EV/Revenue (~21x) is the only usable multiple. Horizon Therapeutics, by contrast, was solidly profitable (17% operating margin) at the time of its own real $27B deal — the full multiple set applies there. A single 'pharma M&A multiple' doesn't exist; it depends entirely on whether the target has reached profitability yet.

## 3. The real, sector-defining finding: a genuine patent cliff, offset by a genuine pipeline

Real, publicly disclosed AbbVie figures (its own earnings releases — product revenue isn't tagged in standard EDGAR XBRL the way consolidated revenue is):

| | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Humira (global) | $21.2B | $14.4B | $9.0B | — |
| Skyrizi + Rinvoq (combined) | — | — | $16.0B | $25.9B |
| AbbVie total revenue | $58.1B | $54.3B | $56.3B | $61.2B |

Humira lost US patent exclusivity in 2023 and its real global revenue collapsed by more than half in two years — a genuine, severe patent cliff, exactly the risk pharma equity research spends years modeling. But AbbVie's TOTAL revenue never fell by more than 6.4% in any single year and fully recovered within two — because its own real, disclosed Skyrizi+Rinvoq replacement franchise (management's own stated decade-long strategy) grew from roughly $16B to $25.9B in a single year, with 2027 guidance raised to a combined $31B. The real lesson for pharma DCF/comps work: a naive 'assume the flagship product's patent cliff sinks the company' assumption is right for a single-product biotech (Seagen, above, has no such offset to fall back on) and WRONG for a diversified major pharma with a real, funded pipeline — the two require genuinely different treatment, not the same haircut applied uniformly.

## 4. A real GAAP quirk this toolkit's own PPA/impairment modules are built for: acquired IPR&D write-offs

| FY | Acquired IPR&D write-off | % of revenue | Reported margin | IPR&D-adjusted margin |
|---|---|---|---|---|
| 2020 | $1,376M | 3.0% | 24.8% | 27.8% |
| 2021 | $1,124M | 2.0% | 31.9% | 33.9% |
| 2022 | $697M | 1.2% | 31.2% | 32.4% |
| 2023 | $778M | 1.4% | 23.5% | 24.9% |
| 2024 | $2,757M | 4.9% | 16.2% | 21.1% |
| 2025 | $5,016M | 8.2% | 24.6% | 32.8% |

Real, GAAP-mandated (ASC 730-10-25-2c): in-process R&D acquired via an asset acquisition with no alternative future use is expensed immediately, not capitalized. AbbVie's own real FY2025 charge ($5.0B, from its 2024-closed ImmunoGen and Cerevel Therapeutics acquisitions) alone compresses reported operating margin by 8.2 percentage points versus the adjusted figure — a real, lumpy, ACQUISITION-driven distortion, mechanically different from the semiconductor check's capitalization of ORGANIC R&D spend (`finmodel.rd_capitalization`): that module amortizes a real multi-year asset GAAP expenses too early; this charge is a real one-time cost that GAAP correctly expenses all at once, and normalizing it means adding it BACK for comps purposes (like a restructuring charge), not amortizing it forward. This is the exact real automation topic `finmodel.ppa_valuation` and `finmodel.impairment_testing` (built from this toolkit's own Big 4 market survey, docs/BIG4_AUTOMATION.md) exist for — the acquired assets behind these write-offs are the same category of intangible a real ASC 805 purchase price allocation values.

## 5. A real, verified EDGAR extraction gap this check found and fixed: `finmodel.edgar`'s "da" tag

AbbVie's own `da` figure resolved all the way down to the narrow `Depreciation` tag (PP&E only, $762M for FY2025) because none of `finmodel.edgar`'s combined D&A tags were ever populated for this filer — silently dropping AbbVie's real, separately-tagged `AmortizationOfIntangibleAssets` ($7,377M for FY2025, ~10x the PP&E depreciation alone, and real given AbbVie's ~$63B Allergan acquisition alone). Merck shows the exact same real gap (`AmortizationOfIntangibleAssets` = $2.8B for FY2025, invisible to the old extraction). Now fixed as a real additive component in `finmodel.edgar` — summed into `da` only when the tag actually picked was the narrow `Depreciation` one, since a combined tag (when a filer does report one, like Pfizer/BMS/Eli Lilly) already includes intangible amortization by its own XBRL definition and summing unconditionally would double-count it.

## 6. A real, unrelated data-hygiene bug found while pulling live prices

The `market_data` warehouse carries TWO rows per trading day for ABBV specifically — 250 of the last 260 trading days, verified — an older, unadjusted OHLC batch (`batch_id` 4, loaded 2026-07-17) never purged after a newer, dividend-adjusted reload (`batch_id` 7, loaded one day later). Every peer ticker in this check (PFE/MRK/BMY/LLY) is clean. This is the exact same class of bug this repo's own recent 'stop the OHLC cache serving stale frames' fix addressed elsewhere, now found in a second table — fixed here by de-duplicating on the latest `batch_id` per date (`DISTINCT ON` in both the `prices()` and `week52()` queries above) rather than trusting a plain date-equality lookup.

## 7. DCF (unlevered, margin scenarios from ABBV's own IPR&D-adjusted history)

Discount rate 7.33% (`finmodel wacc examples/wacc_abbv.json`). Once the acquired-IPR&D noise is removed, `trend_diagnostics()` on the adjusted margin shows a genuinely weak trend (see §8), so — unlike the DUK/TRV/CSCO checks — the GENERIC `dcf_scenarios_from_history()` trailing min/median/max is appropriate here rather than needing a trend-guard override.

**DCF - bear (2%/yr growth, trailing-8yr min adjusted margin)** -> implied share price **168.44** (range 122.94 - 261.88).
**DCF - base (6%/yr growth, trailing-8yr median adjusted margin)** -> implied share price **267.30** (range 197.21 - 411.33).
**DCF - blue sky (9%/yr growth, trailing-8yr max adjusted margin)** -> implied share price **379.77** (range 281.44 - 581.91).

## 8. Why the generic scenario tool is appropriate here (unlike DUK/TRV/CSCO)

`finmodel cycle data/edgar/ABBV.json --sector pharma` on the RAW field shows a misleadingly negative-leaning correlation driven by the FY2024 IPR&D-charge trough; the ADJUSTED field (removing the acquired-IPR&D noise) resolves it to a genuinely weak trend instead:

- Raw (unadjusted): `trend_strength` **weak/none** (r=-0.33, none).
- IPR&D-adjusted: `trend_strength` **weak/none** (r=-0.09, none).

Neither is a real, actionable secular trend the way Cisco's, Travelers' or Duke Energy's were — the real lesson here isn't 'apply a trend guard,' it's 'fix the input before checking for a trend at all,' since the raw series' apparent decline is a real accounting artifact, not a real business one.

## 9. 52-week trading range (real, market_data warehouse, de-duplicated by batch)

$179.29 - $259.22 (2025-07-17 to 2026-07-17, 252 trading days).

## Method note

Every revenue/EBIT/D&A/debt/cash figure is from an SEC 10-K (via `finmodel.edgar`); every price is a live database query against `market_data`; both deals' per-share cash prices and announcement dates come from the acquirer's own 8-K press releases (public record); Humira/Skyrizi/Rinvoq product revenue figures are from AbbVie's own public earnings releases (not derivable from standard EDGAR XBRL tags). Both real precedent targets are delisted, so target-side deal premiums are omitted for the same reason as every prior check's precedents.

Regenerate with `python scripts/football_field_abbv.py`; chart at `out/charts_football_field_abbv.html`.