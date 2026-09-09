# State × sector × centre incentive matrix — 27-state precursor model

A worked "state × sector" matrix tying together `docs/INDIA_STATE_INVESTMENT_INCENTIVES.md` (state schemes),
`docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md` (central PLI/tax/credit schemes), and
`docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md` (land rates) into one queryable sample calculation per
state, computed by `finmodel.sector_investment_model.sample_project_matrix`
(`examples/state_sector_matrix_demo.json`, runnable via `finmodel sector-investment-model
examples/state_sector_matrix_demo.json`). This now covers 28 states/UTs (the original 12, then Kerala, West
Bengal, Bihar, Assam, Delhi (NCT), and Chandigarh (UT), then Himachal Pradesh, Uttarakhand, Jharkhand,
Chhattisgarh, Goa, Jammu & Kashmir, Ladakh, Puducherry, and Dadra & Nagar Haveli and Daman & Diu, and now
Andaman & Nicobar Islands) — **still not the full set (7 North-East states are in an active research pass;
Lakshadweep has no industrial land market to benchmark at all and remains structurally excluded here, see
below); the goal remains full coverage over time.**

## How to read these numbers — read this before quoting any figure

Every project in this matrix holds two things constant across all 28 states, purely so the states are
comparable to each other: plant & machinery ₹30 crore, building & infrastructure ₹8 crore (so "FCI" —
fixed capital investment excluding land — is ₹38 crore in every entry), 10 acres of land, and a 10% discount
rate. Only three things vary state to state: the land rate, which sector/scheme is modeled, and each
scheme's own confirmed (or unconfirmed) parameters.

One entry — Andaman & Nicobar Islands — varies a fourth thing: **land is leased, not purchased**, so its
"land rate" is a *capitalized annual rent* (via `finmodel.sector_investment_model.leasehold_land_cost`, see
below), not a per-acre purchase premium. Its capex figure is directly comparable to every other entry's
(both are present-value costs feeding the same `project_capex_stack`), but its "land rate" column can't be
read as a per-acre purchase price the way every other row's can.

Within each entry, there are two different kinds of number, and conflating them would defeat the purpose of
this catalog:

1. **The scheme's own rate/cap/tenure** — taken from `docs/INDIA_STATE_INVESTMENT_INCENTIVES.md` and
   `docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md` wherever those catalogs could confirm a number. Where a
   state's own catalog entry could not confirm a rate, where a state genuinely has NO state-tier scheme
   (Delhi, Chandigarh — confirmed findings), where a scheme exists but is **closed to new registrants**
   (Jammu & Kashmir's NCSS 2021), or where a UT's own policy is confirmed to have zero such mechanic
   (Ladakh), that state's entry reflects that honestly — an empty `incentive_components` list, not an
   invented number.
2. **The volume assumption the rate is applied to** — how much net SGST this illustrative project pays per
   year, how much interest it pays on a term loan — none of that is known for a generic 10-acre/₹38cr
   project, so a flat illustrative figure (₹6 crore/year assumed net SGST paid) is used everywhere it's
   needed. **These volume assumptions, not the scheme rates, are why the computed incentive values below
   should be read as illustrative shape, not a real project's actual entitlement.**

Each project's own `note` field (visible in both the JSON and the CLI output) records exactly which of its
numbers are confirmed-scheme-parameter vs. illustrative-assumption, and flags land-cost confidence
separately (see `docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md` for which).

**Results worth calling out rather than hiding:**

- **Tamil Nadu's `net_effective_investment` comes out negative** (-₹19.75cr against ₹39.53cr of capex) —
  what falls out of an uncapped-by-FCI 100%-SGST-reimbursement design. A scheme's *cap structure* matters
  far more than its headline rate.
- **Chhattisgarh now tops the "IRR without incentives" ranking** (15.10%), ahead of every other state,
  purely because its land is confirmed policy-subsidized to near-zero (100% premium exemption). Land cost,
  not incentive generosity, decides this ranking as often as the incentive itself does.
- **Delhi and Chandigarh remain the two worst entries on every measure** — the highest and third-highest
  land costs in the whole matrix, with zero incentive to offset either.
- **Jammu & Kashmir is a new, distinct story**: a real land rate (₹0.40cr/acre) and a nominally rich central
  scheme (NCSS 2021, ₹28,400cr) — but that scheme's registration window for new applicants closed
  30.09.2024, so no incentive is modeled. This is different in kind from Delhi/Chandigarh (never had a
  scheme) and West Bengal (scheme revoked): J&K's scheme is real and generous, just currently inaccessible
  to a hypothetical new investor.

## The 28-state matrix

| State/UT | Sector modeled | Land rate used | State scheme (confirmed parameter used) | Central scheme | Total capex (₹cr) | Incentive PV (₹cr) | Net effective investment (₹cr) | Effective subsidy % (PV basis) |
|---|---|---|---|---|---|---|---|---|
| Gujarat | Automobile & Auto Components | 2.13 cr/acre (GIDC-confirmed, Sanand-II) | Aatmanirbhar Gujarat — net SGST reimbursement, 100% rate capped at 75% of FCI over 10 yrs (confirmed) | PLI Auto & Auto Components — 18% of incremental sales | 59.33 | 42.28 | 17.04 | 71.3% |
| Uttar Pradesh | General Manufacturing / MSME | 1.30 cr/acre (UPSIDA-confirmed, may be dated) | UP IIEPP 2022 — capital subsidy 25% of FCI, capped ₹40cr (confirmed) | — | 50.95 | 9.50 | 41.45 | 18.6% |
| Rajasthan | Automobile & Auto Components | 8.90 cr/acre (RIICO-confirmed, Karoli Auto Zone) | RIPS 2024 — capital subsidy, 20% midpoint, capped ₹15cr (one source) | PLI Auto & Auto Components — 18% | 127.03 | 28.07 | 98.96 | 22.1% |
| Telangana | Electronics / Hardware Manufacturing | 4.86 cr/acre (TSIIC-confirmed, Hardware Park) | T-IDEA/T-PRIDE — 20% midpoint of FCI | PLI Large Scale Electronics — 5% | 86.56 | 13.29 | 73.28 | 15.3% |
| Odisha | General Manufacturing | 0.75 cr/acre (IDCO-confirmed, IE Cuttack) | Odisha IPR 2022 — net SGST reimbursement, 100% capped at 200% of P&M cost (confirmed) | — | 45.50 | 29.21 | 16.29 | 64.2% |
| Haryana | Automobile & Auto Components | 6.60 cr/acre (HSIIDC-confirmed, IMT Bawal) | HEEP 2020 — Block B first-phase only, 50%/5yrs (understates real value) | PLI Auto & Auto Components — 18% | 103.96 | 31.84 | 72.12 | 30.6% |
| Tamil Nadu | Textiles & Apparel | 0.15 cr/acre (SIPCOT — flagged as anomalously low) | TN Industrial Policy 2021 — 100% SGST reimbursement, 15 yrs, no overall cap confirmed | PLI Textiles — 12% flat placeholder | 39.53 | 59.28 | **-19.75** | 149.97% |
| Karnataka | General Manufacturing / MSME | 0.46 cr/acre (KIADB GIS, historical allotted-plot price) | Karnataka Industrial Policy 2025-30 — 25% of FCI, Zone 1 (confirmed) | — | 42.55 | 9.50 | 33.05 | 22.3% |
| Andhra Pradesh | Pharmaceuticals | 2.95 cr/acre (APIIC digital land bank, JN Pharma City) | AP Industrial Development Policy 4.0 — 25% of FCI, capped ₹7cr | — | 67.47 | 7.00 | 60.47 | 10.4% |
| Madhya Pradesh | Automobile & Auto Components | 1.30 cr/acre (MPIDC-confirmed, Pithampur-1&2) | MP IPP 2025 — interest subsidy, 6% midpoint, 5yrs | — | 50.97 | 0.68 | 50.28 | 1.3% |
| Maharashtra | Chemicals-adjacent / General Mfg. | 4.90 cr/acre (unverified aggregator, Taloja) | Maharashtra IPS — 100% of gross SGST, one cited zone cap (40% of FCI) | — | 86.97 | 12.82 | 74.15 | 14.7% |
| Punjab | General Manufacturing / MSME | 19.82 cr/acre (press-sourced, Mohali) | Punjab IBDP 2022 — net SGST 100%, 7yrs, capped 100% of FCI (all confirmed) | — | 236.18 | 27.16 | 209.02 | 11.5% |
| Kerala | Food Processing | 1.49 cr/acre (KINFRA-confirmed, Food Processing Park, Adoor) | Kerala Industrial Policy 2023 — Investment Subsidy, Large/Mega, 10% of FCI capped ₹10cr | — | 52.89 | 3.80 | 49.09 | 7.2% |
| West Bengal | Engineering & General Manufacturing | 0.75 cr/acre (WBIDC-confirmed, official, 2026 base price) | **None** — entire framework legislatively REVOKED 2025, no replacement finalized | — | 45.50 | 0.00 | 45.50 | 0.0% |
| Bihar | General Manufacturing / Export-Oriented (EPIP) | 2.34 cr/acre (BIADA-confirmed, EPIP Hajipur) | BIPPP 2025 — capital subsidy, up to 30% of project cost (confirmed) | — | 61.40 | 11.40 | 50.00 | 18.6% |
| Assam | General Manufacturing / Export-Oriented (EPIP) | 2.19 cr/acre (AIDC-confirmed, EPIP Amingaon) | Assam IIPA 2019 — 30% of P&M **stacked with** Central UNNATI 2024 — 30% of P&M, Zone A cap ₹5cr | UNNATI (confirmed stackable) | 59.85 | 16.40 | 43.45 | 27.4% |
| Delhi (NCT) | General Manufacturing | 42.54 cr/acre (DDA-confirmed, dated 2022 cycle) | **None** — no notified state-style policy exists | — | 463.41 | 0.00 | 463.41 | 0.0% |
| Chandigarh (UT) | General Manufacturing | 30.30 cr/acre (a circle rate, not an allotment premium) | **None** — no finalized UT policy exists | — | 340.98 | 0.00 | 340.98 | 0.0% |
| Himachal Pradesh | Pharmaceuticals | 2.02 cr/acre (HP govt-confirmed, IA Baddi) | HP Industrial Investment Policy 2019 — net SGST 50%/5yrs, capped 80% of FCI (confirmed, primary) | — | 58.20 | 11.37 | 46.83 | 19.5% |
| Uttarakhand | Automobile & Auto Components | 1.50 cr/acre (SIIDCUL-confirmed, Sitarganj Ph-II) | Uttarakhand Mega Policy 2025 — Large tier, 10% of FCI capped ₹20cr (confirmed) | — | 53.00 | 3.80 | 49.20 | 7.2% |
| Jharkhand | Automobile & Auto Components | 0.90 cr/acre (aggregator-sourced, Adityapur) | JIIPP 2021 — CPIS non-MSME, 25% of FCI capped ₹25cr (confirmed, primary gazette) | — | 47.00 | 9.50 | 37.50 | 20.2% |
| Chhattisgarh | General Manufacturing / MSME | **0.00 cr/acre** — 100% land-premium exemption (confirmed policy) | IDP 2024-30 — capital subsidy option, 35% midpoint of FCI | — | 38.00 | 13.30 | 24.70 | 35.0% |
| Goa | General Manufacturing / MSME | 0.745 cr/acre (Goa-IDC, range midpoint, no specific estate) | Capital Subsidy Scheme — 25% of FCI, capped ₹25L (MSME-scale, near-irrelevant here) | — | 45.45 | 0.25 | 45.20 | 0.6% |
| Jammu & Kashmir | General Manufacturing / MSME | 0.40 cr/acre (press-verified against official policy) | **None** — NCSS 2021's registration for new applicants CLOSED 30.09.2024 | — | 42.00 | 0.00 | 42.00 | 0.0% |
| Ladakh | General Manufacturing / MSME | 0.48 cr/acre (confirmed, primary PDF — best-sourced land rate in this matrix) | **None** — own UT policy confirmed to have zero capital/interest/GST mechanic | — | 42.80 | 0.00 | 42.80 | 0.0% |
| Puducherry (UT) | General Manufacturing / MSME | 0.405 cr/acre (PIPDIC-confirmed, cross-validated twice) | New Industrial Policy 2016 — 35% of FCI, capped ₹35L (confirmed, primary Gazette) | — | 42.05 | 0.35 | 41.70 | 0.8% |
| Dadra & Nagar Haveli and Daman & Diu (UT) | General Manufacturing / MSME | 2.0 cr/acre (**illustrative placeholder — no confirmed source**) | IPS 2022 — 25% of FCI (one of two conflicting secondary-sourced rates) | — | 58.00 | 9.50 | 48.50 | 16.4% |
| Andaman & Nicobar Islands (UT) | General Manufacturing / MSME | 8.27 cr **capitalized** (leasehold: ₹0.157cr/acre/yr base rent, Garacharama estate, 30yr lease, 50%/25% promotional discount yrs 1-15/16-25, confirmed primary) | **None** — shared central LANIDS 2018 scheme's current registration status could not be confirmed by two independent research passes; treated the same conservatively as J&K's confirmed-closed NCSS 2021 | — | 46.27 | 0.00 | 46.27 | 0.0% |
| **Total (28 states/UTs)** | | | | | **2,493.79** | **350.31** | **2,143.48** | **14.0%** |

Lakshadweep is catalogued in full in the source docs but **not** included above: it has no industrial land
market to benchmark at all — a genuine structural exclusion, not a data gap.

## Beyond this matrix's original scope — now addressed elsewhere

- **`finmodel.india_corporate_tax_regimes`** models Section 115BAB/115BAA/standard-regime tax election and
  CGTMSE's guarantee-fee effect on DSCR — see `docs/INDIA_CORPORATE_TAX_AND_CGTMSE.md`.
- **A real renewable-energy entry using IREDA's own disclosed terms** exists alongside this matrix's
  SBI/REC-style generic case — see `docs/INDIA_PROJECT_FINANCE_LENDING_TERMS.md`.

What's still open:

- **7 North-East states** (Arunachal Pradesh, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, Tripura) are in
  an active research pass as of this writing — expected to share the confirmed central UNNATI 2024 overlay.
- **Only one sector per state is modeled**, chosen from whatever the land-cost data pointed to.

Extend this matrix by adding more entries to `examples/state_sector_matrix_demo.json`'s
`sample_project_matrix` list — each entry is independent, so growing state or sector coverage doesn't
require touching the calculation code itself.
