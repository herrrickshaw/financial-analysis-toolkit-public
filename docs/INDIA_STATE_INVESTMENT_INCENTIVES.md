# State-wise industrial/MSME investment incentive catalog (India)

A reconnaissance catalog of 18 states'/UTs' current industrial/MSME investment-promotion policies,
mapped onto the mechanics implemented in `finmodel.investment_incentives`
(see `docs/INVESTMENT_INCENTIVES.md`). This is a **starting point for populating that module's inputs, not
a locked reference** — read the methodology note before using any number here. The original 12 states are
below; a second research pass added Kerala, West Bengal, Bihar, Assam, Delhi (NCT), and Chandigarh (UT) —
see that section for two genuinely important findings: **Delhi and Chandigarh have no state-tier incentive
scheme at all**, and **West Bengal's entire framework was legislatively revoked in 2025** with no finalized
replacement yet.

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

## Second research pass — 6 more states/UTs

Same methodology and caveats as above (secondary compilations cross-checked across 2+ sources where
possible; every unconfirmed rate flagged rather than guessed).

### Kerala

*Kerala Industrial Policy 2023*, effective for investments from 01.04.2023, 22 priority sectors.
Source: https://industry.kerala.gov.in/images/pdf/2023/IND_POLICY_ENG.pdf (primary, scanned/unreadable) +
KSIDC/K-RIIS scheme PDFs (as accessed 2026-09).

Two overlapping capital-subsidy schemes are reported, **not clearly reconciled against each other**: (1) the
Entrepreneur Support Scheme — 15% of FCI (cap ₹30L) general, 25% (cap ₹40L) for young/women/SC-ST/NRK
entrepreneurs, +10% (cap ₹10L) priority-sector top-up; (2) the policy's own investment subsidy — Micro/
Small/Medium up to 45% (caps ₹40L/₹100L/₹200L), Large/Mega 10% (cap ₹10cr). Interest subvention: MSME term/
working-capital loans effectively at ~4% (subvention 3–6%) for up to 5 years. Net SGST reimbursement: 100%
for Large/Mega for 5 years (Priority Sectors only). K-RIIS: 100% land/building lease-purchase assistance for
women/SC-ST/PH/transgender entrepreneurs. Stamp duty %, electricity duty %, per-employee employment subsidy,
formal Large/Mega/Ultra-Mega thresholds: **not confirmed in source**.

### West Bengal

**Status is genuinely unsettled as of this research (Sept 2026) — this is the important finding, not a gap.**
Source: PRS India (Act text) https://prsindia.org/files/bills_acts/acts_states/west-bengal/2025/Act4of2025WB.pdf;
Silpasathi https://silpasathi.wb.gov.in/msme_Incentives (as accessed 2026-09).

*The Revocation of West Bengal Incentive Schemes and Obligations in the Nature of Grants and Incentives Act,
2025* nullified the state's **entire 1993-onward investment-linked incentive framework**. Secondary reporting
is contradictory on what survives: some sources claim Banglashree (MSME: capital subsidy 7.5–25% of FCI by
zone, cap ₹1–1.75cr; net SGST refund 30% for 8 years in Zone B/C) and WBIPA "remain operative"; government
statements (Aug 2026) describe a **new, not-yet-finalized** ₹5,000cr employment-linked incentive policy
replacing the investment-linked model entirely. **Do not hardcode Banglashree/WBIPA numbers as current
without re-checking whether the new policy has since been notified.** Interest subsidy, stamp duty,
electricity duty, employment subsidy, and which framework actually governs a new investment today: **not
confirmed in source**.

### Bihar

*Bihar Industrial Investment Promotion Policy 2016* (High Priority Sectors), continued/extended as the
*Bihar Industrial Investment Promotion Package 2025 (BIPPP-2025)*, approved Aug 2025, applications open to
31.03.2026. Source: nsws.gov.in policy PDF (primary, unreadable) + Dept. of Industries Bihar + Drishti IAS
(as accessed 2026-09).

Capital investment subsidy: up to 30% of approved project cost. Interest subvention: 10–12%, cap conflicts
across sources (up to ₹10cr per one source, up to ₹40cr for BIPPP-2025 per another — reconcile against
primary). Net SGST reimbursement: 80% (2025 dept. post) vs. 100%-of-project-cost cap (2016-policy secondary
summary) — **sources disagree**; one source separately cites an overall cap up to 300% of project cost over
14 years. Stamp duty/land-conversion fee: 100% reimbursement. Electricity duty: 100% reimbursement.
Employment subsidy: ₹1,000/employee/month for SC/ST and women employees, ₹500/month general. BIPPP-2025 adds
free land (10–25 acres) for ≥₹100cr/≥₹1,000cr investments. Exact tenure years for each component: **not
confirmed in source**.

### Assam

*Industrial and Investment Policy of Assam (IIPA) 2019* (amended 2023). Source: industries.assam.gov.in
policy/operational-guidelines PDF (primary, unreadable) + Cretum Advisory/SGM Consultancy summaries (as
accessed 2026-09).

Capital investment subsidy: up to 30% of P&M value (reported as Micro-focused). Interest subsidy: 3–5% on
term loans; separately 2% on working-capital loans for 5 years, capped at ₹50 lakh and 100% of P&M
investment. Net SGST reimbursement reported inconsistently ("7 years" in one source vs. "up to 15 years at
150% of FCI" in an implementation document — reconcile against primary). Stamp duty: 100% reimbursement,
subject to an FCI-linked limit not confirmed. Electricity duty exemption and employment subsidy exist only
as part of a separately-negotiated "customized incentives" package for mega projects (≥₹100cr investment,
≥200 permanent jobs) — not a standard published rate.

**North-East central overlay — a confirmed, important finding:** NEIDS 2017 (the prior central North-East
package) **expired 31.03.2022**. It was replaced, not merely lapsed: Cabinet approved the **Uttar Poorva
Transformative Industrialization Scheme (UNNATI), 2024** in March 2024 — ₹10,037cr outlay over 10 years,
covering all 8 NE states including Assam. Per unnati.dpiit.gov.in: Capital Investment Incentive 30% of P&M
(cap ₹5cr, Zone A) or 50% (cap ₹7.5cr, Zone B); Central Interest Subvention up to 5% for 7 years; GST
reimbursement 100% of net GST up to 150% of investment for 15 years; Manufacturing & Services Linked
Incentive 75% (Zone A) / 100% (Zone B) of P&M value; per-unit cap ₹250cr. **This stacks on top of Assam's own
IIPA 2019, not instead of it.** One caveat found: at least one contemporaneous report claims zero funds had
actually been disbursed under UNNATI as of that reporting — confirm current disbursement status before
assuming this overlay is functioning in practice, not just on paper.

### Delhi (NCT)

**Finding: Delhi does NOT currently have a notified, state-style industrial investment-promotion policy with
capital/interest/SGST-reimbursement mechanics.** Source: industries.delhi.gov.in draft-policy page + news
coverage (as accessed 2026-09).

A *Draft Delhi Industrial Policy 2025–2035* was released for public comment 16–30.07.2025 and, per multiple
2026 sources, **remains unnotified as of Sept 2026** — government reporting now references a further-out
"Delhi Industrial Policy 2026–2036" still in preparation. The draft's few disclosed figures are aggregate
scheme sizes (a ₹400cr venture-capital fund, a ₹50cr capital-investment reimbursement pool), not per-unit
percentages. DSIIDC's role is industrial-infrastructure development (land/estates), not subsidy disbursement
comparable to Gujarat's iNDEXTb or Kerala's KSIDC. MSME support currently visible is central-scheme-mediated
(RAMP, GeM/ONDC) rather than a Delhi-specific incentive schedule. **No confirmed state-style mechanic exists
to report — this is the honest finding, not a gap in research.**

### Chandigarh (UT)

**Finding: Chandigarh has no current industrial investment-promotion policy of its own** (no capital
subsidy, interest subsidy, or SGST-reimbursement schedule found). Source: Chandigarh Administration
Industries Dept. page + The Tribune coverage of the policy-drafting process (as accessed 2026-09).

The UT Administration began drafting a new Industrial Policy (reportedly modeled on Gujarat's), focused on
modernization/technology-upgrade of *existing* units (land is scarce, so it is not a greenfield-attraction
policy) and MSME certification/compliance support. As of the most recent reporting located (mid-2026), the
draft remains in stakeholder consultation, and — because Chandigarh is a UT administered directly by the
Centre — any finalized policy would need Central Government approval before notification, unlike a state's
own legislative process. Industrial investment in Chandigarh today is effectively governed by central MSME
schemes (e.g. PMEGP) rather than a territory-level incentive schedule. **All incentive mechanics requested:
not confirmed in source — none currently exists to confirm.**

### Cross-cutting notes from this second pass

- **West Bengal is mid-transition**: do not hardcode old-scheme numbers as current without re-checking
  whether a new policy has since been notified.
- **Assam is the one state with two additive policy layers** (state IIPA 2019 + central UNNATI 2024) — model
  these as stackable line items, not alternatives, and carry UNNATI's disbursement-reliability caveat.
- **Delhi and Chandigarh should be modeled as "no state-tier incentive" (zero/null), not populated with
  placeholder rates** — that is the accurate finding, not a data gap.
- Bihar's 2016-vs-2025(BIPPP) SGST-reimbursement figures (80% vs 100%-of-project-cost-cap) directly conflict
  between the two most authoritative-looking secondary sources found — needs primary-PDF reconciliation, same
  as the flagged MP/Karnataka conflicts from the first research pass.

## What needs primary-source follow-up before this feeds a real calculation

Automated PDF fetching failed to extract text from nearly every official state policy PDF (MP, Odisha,
Punjab, Haryana, AP, UP, Karnataka, Tamil Nadu all returned binary/corrupted content) — only the superseded
Gujarat 2016-21 HTML page parsed cleanly. Every rate above should be treated as a starting hypothesis, not a
locked calculator constant, until it is checked against the primary document (ideally via pdfplumber/PyMuPDF
rather than a simple URL fetch, since these read as scanned/image PDFs or unusually encoded text PDFs that
clearly contain the missing zone/block/tier rate tables).
