# State × sector × centre incentive matrix — 12-state precursor model

A worked "state × sector" matrix tying together `docs/INDIA_STATE_INVESTMENT_INCENTIVES.md` (state schemes),
`docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md` (central PLI/tax/credit schemes), and
`docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md` (land rates) into one queryable sample calculation per
state, computed by `finmodel.sector_investment_model.sample_project_matrix`
(`examples/state_sector_matrix_demo.json`, runnable via `finmodel sector-investment-model
examples/state_sector_matrix_demo.json`). This covers the same 12 states as the two incentive catalogs —
**a starting slice, not the full set of Indian states; the goal is to extend this matrix to the remaining
states over time.**

## How to read these numbers — read this before quoting any figure

Every project in this matrix holds two things constant across all 12 states, purely so the states are
comparable to each other: plant & machinery ₹30 crore, building & infrastructure ₹8 crore (so "FCI" —
fixed capital investment excluding land — is ₹38 crore in every entry), 10 acres of land, and a 10% discount
rate. Only three things vary state to state: the land rate, which sector/scheme is modeled, and each
scheme's own confirmed (or unconfirmed) parameters.

Within each entry, there are two different kinds of number, and conflating them would defeat the purpose of
this catalog:

1. **The scheme's own rate/cap/tenure** — taken from `docs/INDIA_STATE_INVESTMENT_INCENTIVES.md` and
   `docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md` wherever those catalogs could confirm a number (e.g.
   Gujarat's "up to 75% of FCI over 10 years," Odisha's "100% of net SGST, capped at 200% of P&M cost,"
   Andhra Pradesh's "25% of FCI, capped ₹7 crore"). Where a state's own catalog entry could not confirm a
   rate, that state's entry here says so explicitly rather than inventing one.
2. **The volume assumption the rate is applied to** — how much net SGST this illustrative project pays per
   year, how much interest it pays on a term loan, how much its sales grow — none of that is known for a
   generic 10-acre/₹38cr project, so a flat illustrative figure (₹6 crore/year assumed net SGST paid, ₹3
   crore/year assumed interest paid, ₹100cr→₹130cr assumed sales growth for PLI) is used everywhere it's
   needed. **These volume assumptions, not the scheme rates, are why the computed incentive values below
   should be read as illustrative shape, not a real project's actual entitlement.**

Each project's own `note` field (visible in both the JSON and the CLI output) records exactly which of its
numbers are confirmed-scheme-parameter vs. illustrative-assumption, and flags land-cost confidence
separately (many states' land rates ARE genuinely sourced — see
`docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md` for which).

**One result is worth calling out rather than hiding: Tamil Nadu's `net_effective_investment` comes out
negative (-₹19.75 cr against ₹39.53 cr of capex).** This isn't a bug — it's what falls out of Tamil Nadu's
scheme being reported as "100% SGST reimbursement for 15 years" with **no overall cap tied to FCI confirmed
in the source**, unlike Gujarat (capped at 75% of FCI) or Odisha (capped at 200% of P&M). Applied to the
same illustrative ₹6 crore/year net-SGST-paid assumption for 15 years, an uncapped 100% scheme produces a
present value that exceeds this modest project's capex. That's a genuine, useful modeling insight this
matrix exists to surface — a scheme's headline rate matters far less than whether it's capped as a
percentage of the investment itself — but it also means Tamil Nadu's number here should not be read as "this
state pays you more than your capex," only as "an uncapped-by-FCI 100%-reimbursement design, at a
high-enough assumed revenue/tax-payment volume, is arithmetically unbounded relative to capex." A lower
assumed net-SGST-paid figure, or a real overall cap this research pass could not locate, would bring it back
in line with the other states.

## The 12-state matrix

| State | Sector modeled | Land rate used | State scheme (confirmed parameter used) | Central scheme | Total capex (₹cr) | Incentive PV (₹cr) | Net effective investment (₹cr) | Effective subsidy % (PV basis) |
|---|---|---|---|---|---|---|---|---|
| Gujarat | Automobile & Auto Components | 2.13 cr/acre (GIDC-confirmed, Sanand-II) | Aatmanirbhar Gujarat — net SGST reimbursement, 100% rate capped at 75% of FCI over 10 yrs (confirmed) | PLI Auto & Auto Components — 18% of incremental sales (confirmed rate) | 59.33 | 42.28 | 17.04 | 71.3% |
| Uttar Pradesh | General Manufacturing / MSME | 1.30 cr/acre (UPSIDA-confirmed, 2023 auction — may be dated) | UP IIEPP 2022 — capital subsidy 25% of FCI, capped ₹40cr (confirmed; mutually exclusive with the SGST/PLI-top-up options) | — (no confident sector-specific PLI match for this plot) | 50.95 | 9.50 | 41.45 | 18.6% |
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
| **Total (12 states)** | | | | | **997.00** | **270.63** | **726.37** | **27.1%** |

Sector assignments are matched to the specific park/land-parcel a state's own land-cost data pointed to
(e.g. Rajasthan's rate came from the "Karoli Industrial Area, **Auto Zone**"; Telangana's from the
"**Hardware Park**"; Tamil Nadu's from the "**Apparel Park**" plot within Irungattukottai; Madhya Pradesh's
from **Pithampur**, MP's largest industrial area and a well-documented auto-ancillary hub; Andhra Pradesh's
from **JN Pharma City**, a well-known pharma SEZ) — a genuine signal from the source data, not an
assumption. Where no park name pointed to a specific sector (Uttar Pradesh, Odisha, Karnataka, Punjab),
"General Manufacturing / MSME" is used deliberately rather than guessing a sector.

Every state in this matrix now carries a real, sourced land rate — the two "illustrative placeholder"
entries (Karnataka, Andhra Pradesh) and the "no confirmed source" entry (Madhya Pradesh) from the previous
round of this matrix have all been replaced following a further research pass, detailed in
`docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md`. Notably, Karnataka's real capex turned out considerably
*lower* than the earlier illustrative ₹3.0cr/acre placeholder implied (its real land rate is under half
that), which is why Karnataka now joins Gujarat and Odisha as a third **incentive-enabled** project below
(see `docs/PROJECT_BANKABILITY.md`) — a genuine finding this update surfaced, not a preserved artifact of
the placeholder it replaced.

## What this matrix does NOT yet cover

- **Only 12 of India's states/UTs.** The stated goal is full coverage; the next states to add (Kerala,
  West Bengal, Bihar, Assam/NER states with their separate central NER incentive schemes, Delhi, Chandigarh,
  Jammu & Kashmir/Ladakh which historically had special central packages) are a natural next research pass.
- **Central schemes beyond PLI are not yet wired into the matrix**, even though `docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md`
  catalogs MSME schemes (CGTMSE, PMEGP, ZED), tax incentives (80-IAC, 115BAB), and credit-guarantee schemes
  (ECLGS 5.0, Stand-Up India) — these are financing/tax mechanics rather than direct capex-offsetting
  incentives, so they don't plug into `sample_project_model`'s land+capex+incentive-PV shape the same way a
  capital subsidy or PLI payout does; representing them meaningfully (e.g. CGTMSE's effect on financing cost,
  115BAB's effect on post-tax cash flow) would need a different calculation, not just another
  `incentive_components` entry.
- **Only one sector per state is modeled**, chosen from whatever the land-cost data pointed to — most states
  have several PLI-eligible sectors active within them simultaneously (e.g. Gujarat also hosts pharma,
  chemicals, and textiles investment at scale) that a fuller matrix would model as separate rows per state.

Extend this matrix by adding more entries to `examples/state_sector_matrix_demo.json`'s
`sample_project_matrix` list — each entry is independent, so growing state or sector coverage doesn't
require touching the calculation code itself.
