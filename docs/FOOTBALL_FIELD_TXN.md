# Eighth real-company check: R&D capitalization, and a sixth distinct sector cycle

Same real-data method as the seven prior checks, applied to Texas Instruments (TXN). Unlike banking, REITs or insurance, EV/EBIT is directionally the right multiple here — the gap is that GAAP expenses R&D immediately, understating value for an R&D-intensive business the same way ignoring a lease understated an airline's.

## Why raw EV/EBIT understates value for an R&D-heavy company (real evidence)

`finmodel.rd_capitalization` (new this check) capitalizes each year's R&D spend as its own vintage, straight-line-amortized over 5 years — reconciled exactly to CFI's real `RD-Capitalization.xlsx` single-vintage template (`tests/test_rd_capitalization.py`), then generalized to Damodaran's cross-sectional method for a rolling multi-year history. Verified real, FY2025 SEC EDGAR data across six real peers:

| Ticker | Reported EBIT | Adjusted EBIT | Uplift | R&D asset added to EV |
|---|---|---|---|---|
| TXN | $6,023M | $6,391M | +6.1% | $5,747M |
| ADI | $2,932M | $3,259M | +11.1% | $4,892M |
| MCHP | $490M | $571M | +16.5% | $3,177M |
| NXPI | $3,047M | $3,292M | +8.0% | $6,935M |
| ON | $84M | $50M | -40.4% | $1,791M |
| SWKS | $500M | $715M | +43.0% | $2,009M |

Five of six real companies show a positive uplift — reported EBIT understates true operating profitability because R&D has been growing (older, smaller vintages amortize less than the current year's larger spend gets added back). ON Semiconductor is the real counter-example: its own R&D spend has been flat-to-declining since FY2021 (real, matches the sector's FY2023-2025 demand downturn — see the cyclicality section below), so the same adjustment LOWERS its adjusted EBIT — proof this isn't a one-directional fudge, and a reminder that the adjustment's PERCENTAGE swing is amplified whenever reported EBIT is already thin, independent of anything unusual about the R&D itself.

**A real, narrower tag-fallback fix found while pulling this data**: ON Semiconductor's own R&D tag is `ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost`, not the plain `ResearchAndDevelopmentExpense` `finmodel.edgar` otherwise expects — now a same-field fallback (a true alternative, not an additive-component trap like the REIT/airline tag issues, since it nets out lumpy acquisition-accounting IPR&D write-offs that are less comparable across peers anyway). See `finmodel.sectors.SECTOR_PROFILES['semiconductor']` for the same findings encoded into the toolkit.

## Football field

| Method | Low | High | Current price inside range? |
|---|---|---|---|
| Trading comps (EV/EBIT, raw) | 130.91 | 287.46 | price is above this range |
| Trading comps (EV/AdjEBIT, R&D-capitalized) | 141.92 | 465.45 | yes |
| Precedent transactions | 247.99 | 376.45 | yes |
| DCF - naive (flat capex at the current supercycle rate) | 38.76 | 66.33 | price is above this range |
| DCF - base case (capex normalizing to pre-supercycle rate) | 70.61 | 117.07 | price is above this range |
| DCF - blue sky (2022 chip-shortage peak margin, capex normalizing) | 97.16 | 159.80 | price is above this range |
| 52-week range | 151.57 | 332.28 | yes |

Trading comps (EV/AdjEBIT, R&D-capitalized), Precedent transactions and 52-week range bracket the actual price.
Ranges the price sits **above**: Trading comps (EV/EBIT, raw) (high 287.46), DCF - naive (flat capex at the current supercycle rate) (high 66.33), DCF - base case (capex normalizing to pre-supercycle rate) (high 117.07), DCF - blue sky (2022 chip-shortage peak margin, capex normalizing) (high 159.80).

## 1. Trading comps (real: SEC EDGAR fundamentals + market_data warehouse prices)

Peers: Analog Devices, Microchip, NXP Semiconductors, ON Semiconductor, Skyworks — real analog/mixed-signal semiconductor companies, the closest real comparison set to Texas Instruments.

| Multiple | 25th | Median | 75th |
|---|---|---|---|
| EV/EBIT (raw, n=3 of 5) | 21.64x | 25.07x | 45.37x |
| EV/AdjEBIT (R&D-capitalized, n=4 of 5) | 22.87x | 42.95x | 69.09x |

Two of five peers (Microchip, ON Semiconductor) are `NM` (>=100x) on raw EV/EBIT — reported EBIT is thin enough relative to enterprise value that the multiple isn't meaningful at all, per `comps.multiple()`'s existing NM cap. A real, additional benefit of the R&D adjustment shows up here: capitalizing Microchip's own real, growing R&D history raises its adjusted EBIT enough to pull its multiple back under the NM cap entirely (94.6x, now real usable information) — R&D capitalization doesn't just compress an already-computable multiple, it can recover one that raw GAAP EBIT had made meaningless. ON's multiple stays NM either way (its own R&D adjustment goes the other direction — see below).

## 2. Precedent transactions (real, verifiable, all-cash 2019 semiconductor mergers)

### NVIDIA / Mellanox Technologies — announced 2019-03-11

All-cash: **$125.00**/target share. Enterprise value (raw) **$6,774M**, target EBIT $112M, R&D asset $989M, target fundamentals from its FY2018 10-K (SEC EDGAR).

**EV/EBIT (raw) 60.44x, EV/AdjEBIT (R&D-capitalized) 37.21x**.

### Infineon / Cypress Semiconductor — announced 2019-06-03

All-cash: **$23.85**/target share. Enterprise value (raw) **$9,527M**, target EBIT $164M, R&D asset $1,005M, target fundamentals from its FY2018 10-K (SEC EDGAR).

**EV/EBIT (raw) 57.94x, EV/AdjEBIT (R&D-capitalized) 40.45x**.

## 3. DCF — a real, disclosed capex supercycle needs the same fix as the airline check's fleet renewal

Cost of capital 9.33% (`finmodel wacc examples/wacc_txn.json`; TXN's real ~11x interest coverage maps to a AAA synthetic rating — a real, strong balance sheet, not a stress-tested assumption). Growth/margin scenarios use `finmodel.sectors.dcf_scenarios_from_history()`'s real trailing median/peak — no periods override needed here, unlike the airline check's COVID contamination.

TXN's real FY2025 capex/revenue is 25.7% — up from a real 4.5%-7.2% in FY2018-2020, driven by a real, publicly-disclosed multi-billion-dollar capacity-expansion program TXN's own guidance describes as a temporary buildout, not the new steady state (real capex/revenue: 13.4% FY2021, 14.0% FY2022, 28.9% FY2023, 30.8% FY2024, 25.7% FY2025 — a real peak already past and now easing). Holding the peak-cycle 25.7% ratio flat for a 5-year DCF (the naive scenario below) is the exact same mistake the airline check's flat fleet-renewal capex assumption made before being fixed; tapering it toward TXN's own pre-supercycle ~13% level materially changes the answer.

**DCF - naive (flat capex at the current supercycle rate)** (EBIT margin target 41.3%, year-5 capex 26% of revenue) → implied share price **$49.30** (range 38.76 – 66.33).
**DCF - base case (capex normalizing to pre-supercycle rate)** (EBIT margin target 41.3%, year-5 capex 13% of revenue) → implied share price **$88.36** (range 70.61 – 117.07).
**DCF - blue sky (2022 chip-shortage peak margin, capex normalizing)** (EBIT margin target 50.6%, year-5 capex 13% of revenue) → implied share price **$121.08** (range 97.16 – 159.80).

## 4. 52-week trading range (real, market_data warehouse)

$151.57 – $332.28 (2025-07-02 to 2026-07-02, 252 trading days).

## 5. Cyclicality: a sixth distinct real mechanism

`finmodel cycle data/edgar/TXN.json --sector semiconductor` — FY2025 EBIT margin 34.1% vs trailing-8yr median 41.3% (-17.5%) → **near normal**.

TXN's real EBIT margin swung 30.3% (FY2014) to a pandemic-chip-shortage peak of 50.6% (FY2022) back to 34.1% (FY2025) — the real "silicon cycle" bullwhip effect: a shortage triggers over-ordering across the supply chain, which becomes an inventory glut once demand normalizes. A sixth distinct mechanism from every sector checked so far — not a commodity price (steel/oil & gas), credit losses (banking), the risk-free rate (REITs), a demand shock (airlines) or catastrophe losses (insurance).

## Method note

Every EBIT / R&D / debt figure is from an SEC 10-K (via `finmodel.edgar`); every price is a live database query against `market_data`; both deals' per-share cash prices and announcement dates come from the target's own 8-K filings (public record). Both real precedent targets are delisted and absent from the warehouse, so target-side deal premiums are omitted for the same reason as the banking, REIT, airline and insurance checks' precedents.

Regenerate with `python scripts/football_field_txn.py`; chart at `out/charts_football_field_txn.html`.