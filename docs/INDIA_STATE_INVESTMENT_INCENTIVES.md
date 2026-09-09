# State-wise industrial/MSME investment incentive catalog (India)

A reconnaissance catalog of 12 major states' current industrial/MSME investment-promotion policies,
mapped onto the mechanics implemented in `finmodel.investment_incentives`
(see `docs/INVESTMENT_INCENTIVES.md`). This is a **starting point for populating that module's inputs, not
a locked reference** — read the methodology note before using any number here.

## Methodology note — read this before using any number below

For nearly every state, the official policy PDF is either a scanned/image PDF or uses an encoding that
defeated automated text extraction. The numbers below therefore come from secondary compilations (law-firm
and consultancy summaries — KIP Financial, TeamLease RegTech, Grant Thornton, EY, PwC, Mondaq) that
explicitly cite the named official policy, cross-checked across two or more independent sources where
possible. **Treat every number as "reported by secondary sources citing the official policy, not
independently verified against primary PDF text"** unless a line says otherwise. Internal disagreements
between sources and outright gaps are flagged explicitly as "not confirmed in source" rather than filled in
with a plausible-sounding guess — a fabricated number is worse than a missing one in a calculator real users
may rely on. Before hardcoding any rate from this file into a calculation, verify it against the linked
primary PDF/portal, ideally with a proper PDF-text-extraction pass (pdfplumber/PyMuPDF) rather than a simple
web fetch, since several of these documents contain exactly the zone/tier rate tables this catalog is
missing.

Two states below (Karnataka, Maharashtra) have two live-looking policy vintages in circulation — confirm
which one governs a given investment's date before using either set of numbers.

## Madhya Pradesh

*Industrial Promotion Policy (IPP) 2025*, notified 24 Feb 2025.
Source: https://invest.mp.gov.in/wp-content/uploads/2025/02/IPP_2025_Policy.pdf (primary; unreadable by
automated extraction — as accessed 2026-09).

"Investment Promotion Assistance" (a net-SGST-style reimbursement, structurally the mechanic modeled by
`net_tax_reimbursement_schedule`) for 7–10 years depending on investment size — exact % not confirmed in
source. Interest subsidy 5–7% for 5 years (general) or specifically 5% for 5 years for textile units —
sources disagree on which applies generally. Total benefits capped at ₹200 crore per applicant over 7 years
with a 70% local-employment condition. A 50% capital subsidy (cap ₹5–10 cr) exists only for
waste-management/ETP infrastructure, not as a general FCI subsidy. Stamp duty/electricity duty exemption %,
per-employee employment subsidy, and women/SC-ST top-ups: **not confirmed in source**.

## Gujarat

*Aatmanirbhar Gujarat Scheme for Assistance to Industries 2022* (current; supersedes the 2016-21 scheme),
effective Oct 2022.
Source: https://cmogujarat.gov.in/sites/default/files/2024-09/aatmanirbhar-gujarat-schemes-2022-assistance-industries.pdf
and https://ic.gujarat.gov.in (as accessed 2026-09).

MSMEs: net SGST reimbursement up to 75% of FCI over 10 years; capital subsidy up to ₹35 lakh (micro);
interest subsidy up to ₹35 lakh/annum for up to 7 years. Large industries: interest subsidy up to 12% (cap
language ambiguous across sources — reported as "12% of FCI" in one), net SGST reimbursement up to 75% of
FCI over 10 years. Mega industries (>₹2,500 cr investment, >2,500 jobs, thrust sectors): interest subsidy up
to 12% of FCI. Electricity duty exemption for 5 years. Exact annual SGST caps, stamp-duty %, per-employee
employment subsidy, women/SC-ST top-ups: **not confirmed in source**.

## Maharashtra

New industrial policy notified 31 Dec 2025 (replacing PSI-2019), valid to 30 Dec 2030 — likely the
*Maharashtra Industries, Investment & Services Policy 2025 (MIISP 2025)*.
Source: https://maitri.maharashtra.gov.in/policies/ (portal link only; the GR text itself was not
independently fetched — as accessed 2026-09; **GR name/number not confirmed**).

Flagship mechanic — Industrial Promotion Subsidy (IPS) = 100% of gross SGST paid on eligible in-state sales,
with total entitlement capped as a percentage of FCI that varies by zone (example cited: Group B, ₹5 cr
investment → 40% of FCI cap). Also reported: interest subsidy up to 5% p.a. on term loans, stamp duty
exemption, EPF reimbursement for employment-intensive units, power-tariff subsidy. Exact tenure years and
the full zone-by-zone cap table, plus women/SC-ST top-ups: **not confirmed in source**.

## Tamil Nadu

*Tamil Nadu Industrial Policy 2021*, eligible from 1 Jan 2021.
Source: https://www.indembassybern.gov.in/docs/1617966871Tamil_Nadu_Industrial_Policy_2021.pdf (primary
fetch failed — cert error; content below via secondary search summary, as accessed 2026-09).

SGST: 100% reimbursement of SGST payable on final products sold/manufactured/registered in-state, for 15
years. Capital subsidy: up to 25% disbursed over up to 15 years (varies by location/category); a "Flexible
Capital Subsidy" up to 35–40% of Eligible Fixed Assets by district category (A/B/C), disbursed over 2.5x the
investment period. The package also lists, without a confirmed %: Training Subsidy, Electricity Tax
Incentive, Land Cost Incentive, Stamp Duty Incentive, Interest Subvention, Green Industry Incentive, SGST
Refund on Capital Goods. Exact interest-subvention rate, per-employee employment subsidy, women/SC-ST
top-up: **not confirmed in source**.

## Uttar Pradesh

*UP Industrial Investment & Employment Promotion Policy 2022*, launched Nov 2022.
Source: https://invest.up.gov.in/wp-content/uploads/2023/02/Uttar_Pradesh_Industrial_Investment_Employment_Promotion_Policy_2022-en.pdf
(fetch returned unreadable binary — as accessed 2026-09).

Structurally distinct from most other states: the investor makes a one-time **mutually-exclusive choice**
among (a) capital subsidy, (b) net SGST reimbursement, or (c) a top-up on Central PLI incentives — these do
NOT stack. Capital subsidy option: 25% of eligible FCI (excludes land), capped at ₹40 crore in
Madhyanchal/Paschimanchal, ₹45 crore in Bundelkhand/Poorvanchal (Gautam Buddh Nagar & Ghaziabad may have a
different/lower cap — not confirmed). Investment tiers (Large/Mega/Super Mega/Ultra Mega) exist but their
breakpoints are **not confirmed in source**. SGST-option %/tenure, interest subsidy, stamp duty %,
electricity duty %, employment subsidy, women/SC-ST top-up: **not confirmed in source**.

## Rajasthan

*Rajasthan Investment Promotion Scheme (RIPS) 2024*, launched Oct 2023, valid to 31 Mar 2029.
Source: https://rising.rajasthan.gov.in/storage/app/public/files/pdf/rips-2024.pdf and
https://istart.rajasthan.gov.in/public/Policies/2024/rips-2024.pdf (portal links located, not
text-extracted — as accessed 2026-09).

Capital subsidy: 13–28% of Eligible Fixed Capital Investment (EFCI), disbursed in annual installments over
10 years (one source cites a cap of up to ₹15 crore, which conflicts with the "up to 28%" scaling —
reconcile against the primary PDF). SGST reimbursement: up to 75% of SGST paid, for 10 years from commercial
production. Interest subsidy: an additional 0.5–2% on term loans for eligible MSMEs. Stamp duty: up to 75%
exemption/reimbursement (category-dependent). Special top-ups: +5% additional capital subsidy for
SC/ST/women-owned FPOs or units in Tribal Sub-Plan areas; women-led startups get 100% SGST reimbursement for
2 years; the first 3 mega/ultra-mega sunrise-sector projects get +25% extra incentive. General MSME size
breakpoints apply (Micro ≤₹1 cr investment/≤₹5 cr turnover; Small ≤₹10 cr/≤₹50 cr; Medium ≤₹50 cr/≤₹250 cr);
Large/Mega/Ultra-Mega breakpoints specific to RIPS: **not confirmed in source**.

## Karnataka

*Karnataka Industrial Policy 2025-30* (supersedes the 2020-25 policy), announced 2025.
Source: https://investkarnataka.co.in/wp-content/uploads/2025/02/IndustrialPolicy2025_PrintPagesSingle_.pdf
(located, not text-extracted — as accessed 2026-09).

Reported mechanics: an Investment Promotion Subsidy of up to 25% (Zone 1) down to 10% (lower zones) of FCI,
OR the investor may instead choose a turnover-linked incentive of up to 2.5%–1.0% of net sales
(zone-dependent) — a mutually-exclusive choice similar to UP's structure; some units may reach up to 35% of
FCI subject to caps/approval. Interest subsidy: up to 6% on term loans, capped at a loan amount of ₹50 lakh.
The zone system differentiates Zone 1/2 (more backward) from Zone 3 (developed), but the exact per-zone rate
table is **not confirmed in source**. For comparison, the prior 2020-25 policy offered an MSME investment
promotion subsidy of 30%/25%/15% of Value of Fixed Assets in Zone-1/2/3 and a 10% interest subsidy on
tech-upgradation loans for 5 years — confirm which policy vintage governs a given investment before using
either set of numbers. SGST reimbursement %, stamp duty %, electricity duty %, employment subsidy, and
women/SC-ST top-up under the 2025-30 policy: **not confirmed in source**.

## Telangana

Operates under *TS-iPASS* (single-window) with the T-IDEA/T-PRIDE incentive schedule for MSMEs.
Source: TS-iPASS portal / telangana.gov.in (policy PDF not independently retrieved — as accessed 2026-09;
recommend re-confirming the exact policy name/year directly against the portal, since the numbers below
are ranges compiled from secondary sources without one clearly dated source document).

Reported: investment subsidy 15–25% of FCI for MSMEs, with SC/ST-owned, women-owned, and backward-district
units receiving a higher rate (exact enhanced % not confirmed). Interest subsidy 3–9% on term loans for 3–5
years. Power-cost reimbursement ₹1–2/unit for 5 years. SGST reimbursement for 5–10 years (% not confirmed).
Stamp duty refund 100% for MSMEs in backward districts (rate for non-backward districts not confirmed).

## Andhra Pradesh

*AP Industrial Development Policy 4.0 (2024-29)* and the companion *AP MSME and Entrepreneurship
Development Policy 4.0 (2024-2029)*.
Source: https://www.apindustries.gov.in/APIndus/Data/policies/AP%20Industrial%20Development%20Policy%20(4.0)%202024-29.pdf
(primary located, extraction failed — as accessed 2026-09).

Capital subsidy: 25% of FCI, capped at ₹25 lakh (micro), ₹1.5 crore (small), ₹7 crore (medium). Enhanced
subsidy for women/BC/SC/ST/differently-abled entrepreneurs: up to 35% of FCI, capped at ₹7 crore. An "Early
Bird" incentive gives the first 200 projects securing a Consent for Operation within 18 months a 30%
investment subsidy; PLI-aligned value-added manufacturing projects (Sub-Large/Large/Mega/Ultra-Mega) get a
40% subsidy. SGST reimbursement: 100% for Micro/Small/Medium for 5 years, annual cap of 5% of annual
turnover. Policy term: 5 years. Interest subsidy %, stamp duty %, electricity duty %, per-employee
employment subsidy: **not confirmed in source**.

## Odisha

*Industrial Policy Resolution (IPR) 2022*.
Source: https://investodisha.gov.in/industrial-policy-resolution-2022 and
https://investodisha.gov.in/download/Amendment_of_Industrial_Policy_Resolution_2022.pdf (primary located,
extraction failed — as accessed 2026-09).

Capital investment subsidy on plant & machinery: 30% (Thrust sector) / 20% (Priority sector), disbursed in
phases. Electricity duty exemption: 100% for 10 years (Thrust) / 7 years (Priority). Power tariff
reimbursement: ₹2.00/unit for 10 years (Thrust) / 7 years (Priority). Stamp duty and land-conversion charges:
100% exemption. Net SGST reimbursement: 100%, overall capped at 200% of the cost of plant & machinery
(tenure years not confirmed — this is the exact "cumulative overall cap" shape modeled by
`net_tax_reimbursement_schedule`). Interest subsidy, employment-generation subsidy amount, women/SC-ST
top-up %: **not confirmed in source** — the portal states an employment subsidy scheme exists operationally
but no rate was retrievable.

## Haryana

*Haryana Enterprises and Employment Policy (HEEP) 2020*, notified 29 Dec 2020.
Source: https://investharyana.in/content/pdfs/Draft%20EPP%202020.pdf (primary located but labeled "Draft"
and extraction failed — as accessed 2026-09; **confirm a final notified version exists before use**).

The state is divided into Blocks A/B/C/D by development level, with more backward blocks getting higher
incentives. Net SGST reimbursement ("Investment Subsidy in lieu of Net SGST"): 30–100% of net SGST paid,
tenure 5–10 years depending on block and unit size; one cited example is Block B = 50% of net SGST for the
first 5 years + 25% for the next 3 years, capped at 100% of FCI. The package also includes interest subsidy,
EPF/ESI reimbursement, and electricity duty/stamp duty concessions, but the exact %/caps for each are
**not confirmed in source**, as are the per-employee employment subsidy and women/SC-ST top-ups.

## Punjab

*Punjab Industrial and Business Development Policy (IBDP) 2022*, effective 17 Oct 2022 – 16 Oct 2027.
Source: https://punjabinfotech.in/assets/pdf/Industrial_Policy_2022.pdf (primary located, extraction failed
— as accessed 2026-09).

Net SGST reimbursement: 100% for 7 years from commercial production, capped at 100% of FCI — uniform
statewide, with no regional/zone classification. Stamp duty: 100% exemption/reimbursement on purchase/lease
of land and building. A capital subsidy exists per clause 16.19 of IBDP-2022, but its base % is
**not confirmed in source**; an "extra" incentive up to 125% of FCI is reported for thrust sectors (Agri &
Food Processing, Textiles, Pharma, IT, Electronics, Renewable Energy) — the base rate this extra builds on
is also **not confirmed**. Interest subsidy, electricity duty exemption %, per-employee employment subsidy,
women/SC-ST top-up: **not confirmed in source**.

## What needs primary-source follow-up before this feeds a real calculation

Automated PDF fetching failed to extract text from nearly every official state policy PDF (MP, Odisha,
Punjab, Haryana, AP, UP, Karnataka, Tamil Nadu all returned binary/corrupted content) — only the superseded
Gujarat 2016-21 HTML page parsed cleanly. Every rate above should be treated as a starting hypothesis, not a
locked calculator constant, until it is checked against the primary document (ideally via pdfplumber/PyMuPDF
rather than a simple URL fetch, since these read as scanned/image PDFs or unusually encoded text PDFs that
clearly contain the missing zone/block/tier rate tables).
