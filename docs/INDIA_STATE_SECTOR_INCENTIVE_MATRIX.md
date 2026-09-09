# State × sector × centre incentive matrix — 18-state precursor model

A worked "state × sector" matrix tying together `docs/INDIA_STATE_INVESTMENT_INCENTIVES.md` (state schemes),
`docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md` (central PLI/tax/credit schemes), and
`docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md` (land rates) into one queryable sample calculation per
state, computed by `finmodel.sector_investment_model.sample_project_matrix`
(`examples/state_sector_matrix_demo.json`, runnable via `finmodel sector-investment-model
examples/state_sector_matrix_demo.json`). This now covers 18 states/UTs (the original 12, plus Kerala, West
Bengal, Bihar, Assam, Delhi (NCT), and Chandigarh (UT) from a second research pass) — **still not the full
set of Indian states/UTs; the goal remains full coverage over time.**

## How to read these numbers — read this before quoting any figure

Every project in this matrix holds two things constant across all 18 states, purely so the states are
comparable to each other: plant & machinery ₹30 crore, building & infrastructure ₹8 crore (so "FCI" —
fixed capital investment excluding land — is ₹38 crore in every entry), 10 acres of land, and a 10% discount
rate. Only three things vary state to state: the land rate, which sector/scheme is modeled, and each
scheme's own confirmed (or unconfirmed) parameters.

Within each entry, there are two different kinds of number, and conflating them would defeat the purpose of
this catalog:

1. **The scheme's own rate/cap/tenure** — taken from `docs/INDIA_STATE_INVESTMENT_INCENTIVES.md` and
   `docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md` wherever those catalogs could confirm a number. Where a
   state's own catalog entry could not confirm a rate, or where a state genuinely has NO state-tier scheme
   (Delhi, Chandigarh — a confirmed finding, not a gap) or its scheme is mid-revocation (West Bengal), that
   state's entry here reflects that honestly — an empty `incentive_components` list, not an invented number.
2. **The volume assumption the rate is applied to** — how much net SGST this illustrative project pays per
   year, how much interest it pays on a term loan, how much its sales grow — none of that is known for a
   generic 10-acre/₹38cr project, so a flat illustrative figure (₹6 crore/year assumed net SGST paid, ₹3
   crore/year assumed interest paid, ₹100cr→₹130cr assumed sales growth for PLI) is used everywhere it's
   needed. **These volume assumptions, not the scheme rates, are why the computed incentive values below
   should be read as illustrative shape, not a real project's actual entitlement.**

Each project's own `note` field (visible in both the JSON and the CLI output) records exactly which of its
numbers are confirmed-scheme-parameter vs. illustrative-assumption, and flags land-cost confidence
separately (see `docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md` for which).

**Two results are worth calling out rather than hiding:**

- **Tamil Nadu's `net_effective_investment` comes out negative** (-₹19.75cr against ₹39.53cr of capex).
  This isn't a bug — it's what falls out of Tamil Nadu's scheme being reported as "100% SGST reimbursement
  for 15 years" with **no overall cap tied to FCI confirmed in the source**, unlike Gujarat (capped at 75%
  of FCI) or Odisha (capped at 200% of P&M). A scheme's *cap structure* matters far more than its headline
  rate — the genuine modeling insight this matrix exists to surface.
- **Delhi and Chandigarh are the two worst entries in the entire 18-state matrix, on both dimensions at
  once.** Delhi's land rate (₹42.54cr/acre, Mangolpuri) is the highest of all 18 states/UTs here, reflecting
  real urban land scarcity; Chandigarh's (₹30.30cr/acre) is the third-highest. Neither has a state-tier
  incentive to offset that cost — the confirmed finding that neither UT currently runs an investment-linked
  incentive scheme at all. The result: both post deeply negative IRR (-24.05% and -20.84% respectively) with
  zero incentive present value, the only two entries in the matrix with `nominal_total` incentive of exactly
  0 alongside West Bengal (whose own framework is mid-revocation, not absent by design — see below).

## The 18-state matrix

| State/UT | Sector modeled | Land rate used | State scheme (confirmed parameter used) | Central scheme | Total capex (₹cr) | Incentive PV (₹cr) | Net effective investment (₹cr) | Effective subsidy % (PV basis) |
|---|---|---|---|---|---|---|---|---|
| Gujarat | Automobile & Auto Components | 2.13 cr/acre (GIDC-confirmed, Sanand-II) | Aatmanirbhar Gujarat — net SGST reimbursement, 100% rate capped at 75% of FCI over 10 yrs (confirmed) | PLI Auto & Auto Components — 18% of incremental sales (confirmed rate) | 59.33 | 42.28 | 17.04 | 71.3% |
| Uttar Pradesh | General Manufacturing / MSME | 1.30 cr/acre (UPSIDA-confirmed, 2023 auction — may be dated) | UP IIEPP 2022 — capital subsidy 25% of FCI, capped ₹40cr (confirmed; mutually exclusive with the SGST/PLI-top-up options) | — | 50.95 | 9.50 | 41.45 | 18.6% |
| Rajasthan | Automobile & Auto Components | 8.90 cr/acre (RIICO-confirmed, Karoli Auto Zone) | RIPS 2024 — capital subsidy, 20% of FCI (13–28% range, midpoint used), capped ₹15cr (one source; reconcile against primary PDF) | PLI Auto & Auto Components — 18% of incremental sales (confirmed rate) | 127.03 | 28.07 | 98.96 | 22.1% |
| Telangana | Electronics / Hardware Manufacturing | 4.86 cr/acre (TSIIC-confirmed, Hardware Park) | T-IDEA/T-PRIDE — investment subsidy, 20% of FCI (15–25% range, midpoint used; cap not confirmed) | PLI Large Scale Electronics — 5% of incremental sales (4–6% range, midpoint used) | 86.56 | 13.29 | 73.28 | 15.3% |
| Odisha | General Manufacturing | 0.75 cr/acre (IDCO-confirmed, IE Cuttack) | Odisha IPR 2022 — net SGST reimbursement, 100% rate capped at 200% of P&M cost (both confirmed; 7-yr tenure assumed) | — | 45.50 | 29.21 | 16.29 | 64.2% |
| Haryana | Automobile & Auto Components | 6.60 cr/acre (HSIIDC-confirmed, IMT Bawal) | HEEP 2020 — Block B first-phase only: 50% of net SGST for 5 yrs (confirmed for that block; the real scheme's further 25%-for-3-yrs phase is omitted, so this UNDERSTATES Haryana's actual value) | PLI Auto & Auto Components — 18% of incremental sales (confirmed rate) | 103.96 | 31.84 | 72.12 | 30.6% |
| Tamil Nadu | Textiles & Apparel | 0.15 cr/acre (SIPCOT live portal — flagged as anomalously low, verify before use) | TN Industrial Policy 2021 — 100% SGST reimbursement for 15 yrs (confirmed; no overall FCI-based cap confirmed — see the callout above) | PLI Textiles — 12% flat placeholder (real scheme tapers 15%→11%, not confirmed at primary-source level) | 39.53 | 59.28 | **-19.75** | 149.97% |
| Karnataka | General Manufacturing / MSME | 0.46 cr/acre (KIADB GIS-confirmed, Sira Industrial Area — a historical *allotted*-plot price, ₹91L÷2 acres, not a quoted per-acre rate) | Karnataka Industrial Policy 2025-30 — Investment Promotion Subsidy, 25% of FCI in Zone 1 (confirmed rate; cap not confirmed) | — | 42.55 | 9.50 | 33.05 | 22.3% |
| Andhra Pradesh | Pharmaceuticals | 2.95 cr/acre (APIIC digital land bank API-confirmed, JN Pharma City Parawada — dated, official, with a proceeding reference) | AP Industrial Development Policy 4.0 — capital subsidy, 25% of FCI, capped ₹7cr (medium tier; both confirmed) | — | 67.47 | 7.00 | 60.47 | 10.4% |
| Madhya Pradesh | Automobile & Auto Components | 1.30 cr/acre (MPIDC Land Availability Report-confirmed, Pithampur-1&2) | MP IPP 2025 — interest subsidy, 6% for 5 yrs (5–7% range, midpoint used; annual cap not confirmed) | — | 50.97 | 0.68 | 50.28 | 1.3% |
| Maharashtra | Chemicals-adjacent / General Mfg. | 4.90 cr/acre (**unverified — third-party aggregator, Taloja**) | Maharashtra IPS — 100% of gross SGST reimbursed (confirmed rate), overall cap taken from one cited zone example (40% of FCI, may not generalize) | — | 86.97 | 12.82 | 74.15 | 14.7% |
| Punjab | General Manufacturing / MSME | 19.82 cr/acre (**press-sourced, not an official PSIEC schedule** — Mohali) | Punjab IBDP 2022 — net SGST reimbursement, 100% rate for 7 yrs capped at 100% of FCI (all confirmed) | — | 236.18 | 27.16 | 209.02 | 11.5% |
| Kerala | Food Processing | 1.49 cr/acre (KINFRA Land Bank-confirmed, Food Processing Industrial Park, Adoor) | Kerala Industrial Policy 2023 — Investment Subsidy, Large/Mega tier, 10% of FCI, capped ₹10cr (confirmed rate; a second, MSME-scale scheme also exists, unreconciled against this one — see the state catalog) | — | 52.89 | 3.80 | 49.09 | 7.2% |
| West Bengal | Engineering & General Manufacturing | 0.75 cr/acre (WBIDC-confirmed, official, 2026 tentative base price, Vidyasagar Industrial Park) | **None modeled** — West Bengal's entire investment-linked incentive framework was legislatively REVOKED in 2025; a replacement (employment-linked) policy is not yet finalized | — | 45.50 | 0.00 | 45.50 | 0.0% |
| Bihar | General Manufacturing / Export-Oriented (EPIP) | 2.34 cr/acre (BIADA-confirmed, official live portal, EPIP Hajipur) | BIPPP 2025 — capital subsidy, up to 30% of approved project cost (confirmed rate; SGST reimbursement rate conflicts across sources, not modeled) | — | 61.40 | 11.40 | 50.00 | 18.6% |
| Assam | General Manufacturing / Export-Oriented (EPIP) | 2.19 cr/acre (AIDC-confirmed, official, dated EOI, EPIP Amingaon — a minimum bid-floor rate) | Assam IIPA 2019 — capital subsidy 30% of P&M (confirmed rate) **stacked with** Central UNNATI 2024 — Capital Investment Incentive 30% of P&M, Zone A cap ₹5cr (confirmed; the successor to the expired NEIDS 2017 — the one confirmed stackable central+state combination in this matrix) | UNNATI (North-East specific, itself central) | 59.85 | 16.40 | 43.45 | 27.4% |
| Delhi (NCT) | General Manufacturing | 42.54 cr/acre (DDA-confirmed, but a 2022 e-auction cycle; DSIIDC's own portal was unreachable) | **None** — Delhi has no notified, state-style industrial investment-promotion policy as of this research (a confirmed finding) | — | 463.41 | 0.00 | 463.41 | 0.0% |
| Chandigarh (UT) | General Manufacturing | 30.30 cr/acre (a Collector/circle rate, not an actual allotment premium — weakest land-cost confidence in this matrix) | **None** — Chandigarh (a UT administered directly by the Centre) has no finalized industrial investment-promotion policy of its own | — | 340.98 | 0.00 | 340.98 | 0.0% |
| **Total (18 states/UTs)** | | | | | **2,021.03** | **302.23** | **1,718.80** | **15.0%** |

Sector assignments are matched to the specific park/land-parcel a state's own land-cost data pointed to
(e.g. Rajasthan's rate came from the "Karoli Industrial Area, **Auto Zone**"; Telangana's from the
"**Hardware Park**"; Madhya Pradesh's from **Pithampur**; Andhra Pradesh's from **JN Pharma City**; Bihar's
and Assam's from their respective **EPIP** — Export Promotion Industrial Park — plots) — a genuine signal
from the source data, not an assumption. Where no park name pointed to a specific sector, "General
Manufacturing / MSME" is used deliberately rather than guessing.

## Beyond this matrix's original scope — now addressed elsewhere

Two of the three gaps flagged in the prior round of this matrix are now built, in their own modules rather
than forced into this matrix's land+capex+incentive-PV shape:

- **`finmodel.india_corporate_tax_regimes`** models Section 115BAB/115BAA/standard-regime tax election
  (a real, exact, 3.88-percentage-point IRR effect on Gujarat's own project) and CGTMSE's guarantee-fee
  effect on DSCR — see `docs/INDIA_CORPORATE_TAX_AND_CGTMSE.md`.
- **A real renewable-energy entry using IREDA's own disclosed terms** (`examples/dscr_matrix_ireda_demo.json`)
  now exists alongside this matrix's SBI/REC-style generic case — see `docs/INDIA_PROJECT_FINANCE_LENDING_TERMS.md`.

What's still open:

- **6 more states/UTs added, but still not the full set.** Jammu & Kashmir/Ladakh (which historically had a
  special central package), the remaining North-East states beyond Assam, and Goa are natural next
  additions.
- **Only one sector per state is modeled**, chosen from whatever the land-cost data pointed to — most states
  have several PLI-eligible sectors active within them simultaneously that a fuller matrix would model as
  separate rows per state.

Extend this matrix by adding more entries to `examples/state_sector_matrix_demo.json`'s
`sample_project_matrix` list — each entry is independent, so growing state or sector coverage doesn't
require touching the calculation code itself.
