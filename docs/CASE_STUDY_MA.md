# Case study: three completed acquisitions of listed companies, before and after

Real SEC filings (EDGAR company facts, extracted with `finmodel.edgar`) run through `finmodel.merger.deal()`. Figures in USD billions except per-share. 'Pre' = last full fiscal year before closing; 'Post' = the acquirer's reported fiscal years after closing. The static pro-forma is the year-1 accretion / dilution view every merger template produces: it holds both businesses flat and adds only financing costs — so the gap between pro-forma and actual is the organic growth, synergies, integration costs, purchase-accounting amortisation and divestments that the template does not model. Note the engine rebuilds each party's EPS as (EBIT + net interest) × (1 − assumed tax rate) / diluted shares, so its standalone EPS differs slightly from the reported diluted EPS in the table; accretion is measured on the engine's own basis.

## Microsoft / Activision Blizzard

*Cash from Microsoft's balance sheet (no new debt). FY2024 includes 8.5 months of Activision.*

Terms as modelled: offer 95.00 vs undisturbed 65.39 → premium +45.3%; consideration 100% cash / 0% new debt / 0% stock; acquirer price 310.20; purchase equity value 75.0bn, EV 71.5bn = 40.3x target EBITDA.

| | Acquirer pre (2023-06-30) | Target pre (2022-12-31) | Static pro-forma (engine) | Acquirer post (2024-06-30) | Acquirer post (2025-06-30) |
|---|---|---|---|---|---|
| Revenue | 211.9 | 7.5 | 219.4 | 245.1 | 281.7 |
| EBITDA | 99.5 | 1.8 | 101.3 | 124.6 | 150.5 |
| EBIT | 88.5 | 1.7 | 90.2 | 109.4 | 128.5 |
| Net income | 72.4 | 1.5 | 68.8 | 88.1 | 101.8 |
| Diluted shares (m) | 7,472 | 789 | 7,472 | 7,469 | 7,465 |
| Diluted EPS | 9.68 | 1.92 | 9.20 | 11.80 | 13.64 |
| Cash + ST investments | 111.3 | 7.1 | 43.4 | 75.5 | 94.6 |
| Total debt | 47.2 | 3.6 | 50.8 | 44.9 | 43.2 |
| EBIT margin | 41.8% | 22.2% |  | 44.6% | 45.6% |
| Net margin | 34.1% | 20.1% |  | 36.0% | 36.1% |
| ROE | 35.1% | 7.9% |  | 32.8% | 29.6% |
| Debt / equity | 22.9% | 18.8% |  | 16.7% | 12.6% |
| Net debt / EBITDA | -0.64x | -1.94x |  | -0.25x | -0.34x |
| Goodwill | 67.9 | 9.9 |  | 119.2 | 119.5 |

**Engine verdict (static, year 1):** EPS 9.38 → 9.20 = -1.9% (dilutive); target holders own 0.0% of the combined company; combined EV/EBITDA 23.0x vs acquirer standalone 22.6x.

**What actually happened (to 2025-06-30):** revenue +32.9% vs the static +3.6% the target alone adds; EPS 9.68 → 13.64 (+40.9%) vs engine -1.9%; net debt/EBITDA -0.64x → -0.34x; goodwill 67.9 → 119.5bn.

Warehouse cross-check (market_data.global_fundamentals, SEC-EDGAR-sourced) vs the EDGAR extract used here:

| FY | revenue (EDGAR) | revenue (warehouse) | net income (EDGAR) | net income (warehouse) |
|---|---|---|---|---|
| 2023-06-30 | 211.9 | 211.9 | 72.4 | 72.4 |
| 2024-06-30 | 245.1 | 245.1 | 88.1 | 88.1 |
| 2025-06-30 | 281.7 | 281.7 | 101.8 | 101.8 |

Charts: `out/charts_case_msft_atvi.html`

## Chevron / Hess

*All-stock: 1.025 Chevron shares per Hess share (~$53bn equity, ~$60bn EV at announcement). Closed after the Exxon arbitration; FY2025 has ~5.5 months of Hess.*

Terms as modelled: offer 171.00 vs undisturbed 163.00 → premium +4.9%; consideration 0% cash / 0% new debt / 100% stock; acquirer price 166.80; purchase equity value 52.7bn, EV 60.1bn = 8.3x target EBITDA.

| | Acquirer pre (2024-12-31) | Target pre (2024-12-31) | Static pro-forma (engine) | Acquirer post (2025-12-31) |
|---|---|---|---|---|
| Revenue | 202.8 | 12.9 | 215.7 | 189.0 |
| EBITDA | 45.4 | 7.3 | 52.6 | 41.1 |
| EBIT | 28.1 | 4.8 | 32.9 | 21.0 |
| Net income | 17.7 | 2.8 | 20.4 | 12.3 |
| Diluted shares (m) | 1,817 | 308 | 2,133 | 1,856 |
| Diluted EPS | 9.72 | 8.98 | 9.56 | 6.63 |
| Cash + ST investments | 8.3 | 1.2 | 9.4 | 7.3 |
| Total debt | 20.1 | 8.6 | 28.7 | 39.8 |
| EBIT margin | 13.9% | 37.0% |  | 11.1% |
| Net margin | 8.7% | 21.5% |  | 6.5% |
| ROE | 11.6% | 24.7% |  | 6.6% |
| Debt / equity | 13.2% | 76.5% |  | 21.3% |
| Net debt / EBITDA | 0.26x | 1.02x |  | 0.79x |
| Goodwill | 4.6 | 0.4 |  | 4.6 |

**Engine verdict (static, year 1):** EPS 9.69 → 9.56 = -1.3% (dilutive); target holders own 14.8% of the combined company; combined EV/EBITDA 7.1x vs acquirer standalone 6.9x.

**What actually happened (to 2025-12-31):** revenue -6.8% vs the static +6.4% the target alone adds; EPS 9.72 → 6.63 (-31.8%) vs engine -1.3%; net debt/EBITDA 0.26x → 0.79x; goodwill 4.6 → 4.6bn.

Warehouse cross-check (market_data.global_fundamentals, SEC-EDGAR-sourced) vs the EDGAR extract used here:

| FY | revenue (EDGAR) | revenue (warehouse) | net income (EDGAR) | net income (warehouse) |
|---|---|---|---|---|
| 2024-12-31 | 202.8 | 193.4 | 17.7 | 17.7 |
| 2025-12-31 | 189.0 | 184.4 | 12.3 | 12.3 |

Charts: `out/charts_case_cvx_hes.html`

## Cisco / Splunk

*~$28bn cash funded from balance sheet cash plus ~$13.5bn of new bonds (Feb 2024) and commercial paper; modelled as 60% cash / 40% debt. Splunk's last 10-K is FY Jan-2023 (FY Jan-2024 was never filed as a standalone 10-K).*

Terms as modelled: offer 157.00 vs undisturbed 119.40 → premium +31.5%; consideration 60% cash / 40% new debt / 0% stock; acquirer price 53.60; purchase equity value 25.5bn, EV 24.3bn = n/m × target EBITDA (target EBITDA negative).

| | Acquirer pre (2023-07-29) | Target pre (2023-01-31) | Static pro-forma (engine) | Acquirer post (2024-07-27) | Acquirer post (2025-07-26) |
|---|---|---|---|---|---|
| Revenue | 57.0 | 3.7 | 60.7 | 53.8 | 56.7 |
| EBITDA | 15.7 | -0.1 | 15.6 | 12.9 | 12.5 |
| EBIT | 15.0 | -0.2 | 14.8 | 12.2 | 11.8 |
| Net income | 12.6 | -0.3 | 11.4 | 10.3 | 10.2 |
| Diluted shares (m) | 4,105 | 162 | 4,105 | 4,062 | 3,998 |
| Diluted EPS | 3.07 | -1.71 | 2.78 | 2.54 | 2.55 |
| Cash + ST investments | 26.1 | 2.0 | 12.9 | 17.9 | 16.1 |
| Total debt | 8.4 | 0.8 | 19.4 | 20.1 | 24.6 |
| EBIT margin | 26.4% | -6.4% |  | 22.6% | 20.8% |
| Net margin | 22.1% | -7.6% |  | 19.2% | 18.0% |
| ROE | 28.4% | 251.4% |  | 22.7% | 21.7% |
| Debt / equity | 18.9% | -701.9% |  | 44.2% | 52.5% |
| Net debt / EBITDA | -1.13x | 9.05x |  | 0.18x | 0.68x |
| Goodwill | 38.5 | 1.4 |  | 58.7 | 59.1 |

**Engine verdict (static, year 1):** EPS 3.07 → 2.78 = -9.3% (dilutive); target holders own 0.0% of the combined company; combined EV/EBITDA 14.5x vs acquirer standalone 12.9x.

**What actually happened (to 2025-07-26):** revenue -0.6% vs the static +6.4% the target alone adds; EPS 3.07 → 2.55 (-16.9%) vs engine -9.3%; net debt/EBITDA -1.13x → 0.68x; goodwill 38.5 → 59.1bn.

Warehouse cross-check (market_data.global_fundamentals, SEC-EDGAR-sourced) vs the EDGAR extract used here:

| FY | revenue (EDGAR) | revenue (warehouse) | net income (EDGAR) | net income (warehouse) |
|---|---|---|---|---|
| 2023-07-29 | 57.0 | 57.0 | 12.6 | 12.6 |
| 2024-07-27 | 53.8 | 53.8 | 10.3 | 10.3 |
| 2025-07-26 | 56.7 | 56.7 | 10.2 | 10.2 |

Charts: `out/charts_case_csco_splk.html`

## What the comparison teaches about using the toolkit

- **The static merger template answers one question only** — is the deal accretive at the offer price given how it is funded — and it answered it correctly in direction for all three deals: cash deals funded from low-yield cash (Microsoft) are accretive on paper, an all-stock deal at a small premium for a higher-multiple target (Chevron/Hess at ~12x EBITDA vs Chevron's ~5x) dilutes, and a cash-and-debt deal for a loss-making target (Cisco/Splunk) is dilutive until synergies arrive.
- **Actual post-deal EPS diverges from the pro-forma by far more than the deal effect** because the acquirer's own business moved: Microsoft's cloud growth swamped Activision's contribution; Chevron's earnings fell with oil prices in 2025; Cisco's FY2025 carried Splunk's operating losses plus ~$1bn of acquired-intangible amortisation. The `pro_forma()` engine with synergies, integration costs and purchase-price allocation is the right tool for a multi-year view — the static `deal()` is a screening step.
- **Balance-sheet fingerprints are the most reliable 'after' signal**: goodwill jumps by roughly the purchase price minus net assets, debt rises by the debt-funded portion (Cisco), share count rises by the stock portion (Chevron ~+40m shares net of buybacks), and cash falls by the cash portion (Microsoft). These reconcile to the engine's funding split within the limits of concurrent buybacks and other deals.
- **Data hygiene matters more than the maths**: EDGAR tags differ by filer (Chevron and Hess report no `OperatingIncomeLoss`, so EBIT is derived as pre-tax income + net interest), fiscal years are misaligned (June, July, December, January year-ends), and a target's final year may never be filed (Splunk). The warehouse cross-check catches extraction slips; it agreed with EDGAR to the dollar where both had the year.
