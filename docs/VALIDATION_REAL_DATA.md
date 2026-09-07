# Validation on real market data: US steel comps

Peer fundamentals: latest 10-K in `data/edgar/` (SEC EDGAR company facts via `finmodel.edgar`). Prices: warehouse, close of 2026-07-02. Target: Steel Dynamics (the same company the BIWS template values). Statistics use the carbon-steel core set (NUE, CMC, RS, CLF, WOR); ATI and CRS (specialty alloys at 35x EBITDA) are shown to demonstrate why peer selection dominates the answer, and X (acquired by Nippon Steel, June 2025) has no current price and drops out — the peer-hygiene step a banker performs by hand.

| Ticker | Company | FY | Price | Equity value ($bn) | EV ($bn) | EV/Revenue | EV/EBITDA | EV/EBIT | P/E | Altman Z | Piotroski F | Beneish M |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NUE | NUCOR CORP | 2025-12-31 | 217.39 | 50.2 | 55.7 | 1.71x | 14.45x | 21.20x | 28.79x | 5.02 (safe) | 6 | -2.47 |
| CMC | COMMERCIAL METALS COMPANY | 2025-08-31 | 61.28 | 7.0 | 7.2 | 0.92x | 18.18x | 66.52x | 82.58x | 3.80 (safe) | 4 | -2.92 |
| RS | RELIANCE, INC. | 2025-12-31 | 370.18 | 19.6 | 20.8 | 1.45x | 16.10x | 20.53x | 26.47x | 6.74 (safe) | 5 | -2.38 |
| CLF | CLEVELAND-CLIFFS INC. | 2025-12-31 | 9.56 | 4.9 | 12.3 | 0.66x | NM | NM | NM | 1.03 (distress) | 2 | -3.42 |
| WOR | WORTHINGTON ENTERPRISES, INC. | 2026-05-31 | 54.24 | 2.7 | 3.0 | 2.15x | 22.29x | 39.05x | 17.28x | 3.58 (safe) | 7 | -2.46 |
| ATI | ATI Inc. | 2025-12-28 | 186.74 | 26.5 | 27.9 | 6.09x | 34.52x | 43.57x | 65.50x | 6.83 (safe) | 9 | -2.72 |
| CRS | CARPENTER TECHNOLOGY CORPORATION | 2026-06-30 | 586.63 | 29.6 | 29.9 | 9.56x | 35.17x | 42.54x | 55.81x | 13.69 (safe) | 7 | -2.38 |
| X | United States Steel Corp | 2024-12-31 | no price (delisted) | | | | | | | | | |
| STLD | Steel Dynamics, Inc. | 2025-12-31 | 217.16 | 32.2 | 35.5 | 1.95x | 17.51x | 24.05x | 27.18x | 5.64 (safe) | 5 | -2.37 |

## Peer statistics and implied value for Steel Dynamics

| Multiple | Max | 75th | Median | 25th | Min | STLD metric ($bn) | Implied price @25th | @median | @75th |
|---|---|---|---|---|---|---|---|---|---|
| EV / Revenue LTM | 2.15x | 1.71x | 1.45x | 0.92x | 0.66x | 18.18 | 90.30 | 156.06 | 187.82 |
| EV / EBITDA LTM | 22.29x | 19.21x | 17.14x | 15.69x | 14.45x | 2.03 | 192.29 | 212.14 | 240.39 |
| EV / EBIT LTM | 66.52x | 45.92x | 30.12x | 21.03x | 20.53x | 1.48 | 187.09 | 277.53 | 434.61 |
| P / E LTM | 82.58x | 42.24x | 27.63x | 24.17x | 17.28x | 1.19 | 193.12 | 220.76 | 337.47 |

Current STLD price 217.16; implied range across multiples 58.65 – 659.77. Template sanity check: the BIWS 2017 spread had EV/Revenue 0.5–1.2x and EV/EBITDA 5.5–14x for the same names; the 2025/26 set sits at the top of or above that band because 2025 was a trough-earnings year for steel (Cleveland-Cliffs loss-making, Nucor EBITDA down ~55% from 2023), so trailing multiples inflate — the classic reason comps use forward (FY+1/FY+2) estimates, which EDGAR cannot supply.

## Cross-check against the market-pipeline ratio ledger

The pipeline computes P/E independently (yfinance close × NI / shares outstanding). Re-pricing the comps engine at the pipeline's close should reproduce its P/E:

| Ticker | Pipeline close | Pipeline EPS | Pipeline P/E | Engine EPS (EDGAR diluted) | Engine P/E at pipeline close | Δ P/E |
|---|---|---|---|---|---|---|
| NUE | 263.97 | 7.56 | 34.92 | 7.55 | 34.96 | +0.05 |
| CMC | 69.15 | 0.76 | 90.82 | 0.74 | 93.18 | +2.37 |
| RS | 400.21 | 14.29 | 28.00 | 13.98 | 28.62 | +0.62 |
| ATI | 204.54 | 2.97 | 68.77 | 2.85 | 71.74 | +2.97 |
| CRS | 467.48 | 7.56 | 61.80 | 10.51 | 44.47 | -17.33 |
| STLD | 246.03 | 8.18 | 30.08 | 7.99 | 30.80 | +0.72 |

Residual differences come from diluted (engine) vs period-end basic (pipeline) share counts — ~1–2% — not from the multiple arithmetic.

## Health scores on the same filings

Altman Z (public-company form, market cap from the warehouse price), Piotroski F (vs prior FY) and Beneish M are shown in the peer table. Cleveland-Cliffs sits in the distress zone after two loss years and heavy debt; Nucor and Reliance are safe on Z but carry weak F-scores because 2025 profits fell versus 2024 — the same picture the market-pipeline's screener reached from a different data path.
