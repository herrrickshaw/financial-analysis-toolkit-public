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

## Third research pass — 5 hill/central states + 6 Union Territories

Same methodology as above. Two states (Himachal Pradesh, Jharkhand) were exceptions where the primary
gazette/notification PDF was fully read via image extraction, giving genuinely primary-sourced numbers
rather than secondary paraphrase — flagged explicitly below.

### Himachal Pradesh

*Himachal Pradesh Industrial Investment Policy 2019* (notified 16.08.2019; primary PDF fully read).
Source: emerginghimachal.hp.gov.in policy PDF, as accessed 2026-09.

**Currency flag**: this policy's sunset has been repeatedly extended (most recently to 12.10.2026) because a
promised replacement policy remains unfinalized — a milder version of West Bengal's "framework in limbo"
finding. State divided into Category A (developed) / B (developing) / C (tribal/backward). No blanket
capital-subsidy %; instead land-premium concessions (MSME 50/60/70% by category; Large 25/45/65%). Interest
subvention: MSME 3% capped ₹2–6L p.a. for 3 years; Large 3% capped ₹10–20L p.a.; SC/ST/women/disabled 5%
capped ₹3–7L p.a. for 5 years. **Net SGST reimbursement (confirmed, primary): MSME 50/80/90% (A/B/C) for 7
years, capped 80% of FCI; Large 50/70/80% for 5 years, same cap.** Stamp duty exemption 50/70/90% (A/B/C,
MSME). Electricity duty concession 1–7% by consumer category, 5 years. Employment subsidy ₹1,000/month per
additional employee beyond 50, for 10 years. **Central hill-state package**: the pre-GST 100% central excise
exemption was rescinded post-GST, replaced by 58%-of-central-tax budgetary support, 01.07.2017–31.03.2027
(confirmed) — not the old 100% exemption, and it expires in ~18 months from this research date.

### Uttarakhand

Layered, not one document. *MSME Policy 2015 (amended 2019)* governed until 31.03.2023, then **superseded**
by the *Uttarakhand MSME Policy 2023* (06.09.2023) — secondary-sourced, not independently verified against a
primary PDF. Separately, the *Uttarakhand Mega Industrial & Investment Policy-2025* (~5-yr validity from Oct
2025) sets Large-scale capital subsidy: 10% of FCI cap ₹20cr/8yrs; Ultra Large 12% cap ₹60cr/10yrs; Mega 15%
cap ₹150cr/12yrs; Ultra-Mega 20% cap ₹400cr/15yrs — with a **hill-district top-up** of +2% FCI (Category-A
districts) or +1% (Category-B). Stamp duty reimbursement 50%, cap ₹50L/unit for this tier (interest
subsidy/SGST/electricity duty not stated for this specific tier — not confirmed in source). Same central
hill-state 58%-budgetary-support package as HP applies (01.07.2017–31.03.2027).

### Jharkhand

*Jharkhand Industrial and Investment Promotion Policy (JIIPP) 2021*, Gazette Notification No.
06/U.Ni./Vividh(Au.Ni.)-07/2021-552, dated 09.07.2021 (**primary gazette PDF fully read**).

**Comprehensive Project Investment Subsidy (CPIS), confirmed primary**: MSME 25% of FCI, cap
₹1cr(Micro)/₹5cr(Small)/₹10cr(Medium); Non-MSME 25% of FCI, cap ₹25cr. Interest subsidy 5% p.a. for 5 years
from Date of Production, capped ₹15L–₹3cr by tier. Net SGST reimbursement 100% for 5 years (MSME) / 7 years
(Large) / 9 years (Mega) or 75% for 12 years (Ultra-Mega), all capped 100% of FCI. Stamp duty 100%
reimbursement (direct-purchase transactions only, JIADA/park lessees excluded from this specific benefit).
Electricity duty 100% reimbursement, but **only for captive power plants**, 5 years — no blanket grid
electricity-duty exemption found. Stackable top-ups: Anchor-unit +5%, Early-Bird +5%, SC/ST/Women/PwD +5%
(amended 20.12.2023). Sector character (mineral-heavy, as expected): the policy frames its Mining/Steel/
Cement/Automobile focus around raw-material/supply-chain access (coal linkages via JSMDC), not a distinct
fiscal top-up for those sectors specifically — separate named sector policies (Textile/Apparel, Automobile,
Pharma, ESDM — each 2016) carry their own richer, sector-specific fiscal tables instead.

### Chhattisgarh

*Chhattisgarh Industrial Development Policy (IDP) 2024-30*, launched 14.11.2024. Source PDF located but
resisted extraction (scanned); figures below are secondary-compilation, cross-checked across 2+ sources.

Investor makes a **choice, not a stack**: (a) net SGST reimbursement, 100% for 10 years, capped 150% of FCI;
or (b) FCI capital subsidy, 30–45% by District Group and Thrust-Sector status. Interest subsidy 40–70% of
the interest rate by MSME category/district group, 5–11 years (exact tier table not confirmed). **The
single most important finding for this state**: land allotted in Directorate of Industries/CSIDC industrial
areas now carries **100% exemption of land premium**, with a **nominal ₹1/acre/year lease** (maintenance
charges still apply) — effectively free land under the current policy cycle, a bigger land-cost signal than
any per-acre market rate. Stamp duty exemption %, electricity duty exemption %, employment subsidy: not
confirmed in source.

### Goa

*Goa Industrial Growth and Investment Promotion Policy 2022* (notified 13.10.2022) reads as a strategic
framework (ease-of-doing-business, thrust sectors: ecotourism, food processing, education/R&D) rather than a
self-contained rate schedule; the actual fiscal mechanics live in continuing companion schemes. **Capital
Subsidy Scheme**: 25% of FCI, capped **₹25 lakh** (a figure tracing to the 2017-era scheme, still cited as
Goa's flagship incentive) — an MSME-scale cap, effectively irrelevant at any investment size above a few
crore. Interest subsidy exists (benefit period ~5 years/20 quarters from commencement) but its rate could
not be fetched (expired TLS certificate on the relevant subdomain). Net SGST reimbursement reported as 75%
for 7 years, capped 100% of FCI — sector scope (universal vs. thrust-sector-only) not confirmed. Stamp duty,
electricity duty, employment subsidy: not confirmed in source.

### Jammu & Kashmir

**NIDS 2017 (the original J&K central package) is confirmed lapsed** (ran 15.06.2017–31.03.2021, no further
extension). Its successor, the **New Central Sector Scheme (NCSS) 2021** — ₹28,400cr outlay, running through
2037 — is real and richly documented (Capital Investment Incentive 30% of P&M cap ₹5cr Zone A / 50% cap
₹7.5cr Zone B; Capital Interest Subvention 6% for 7 years on loans up to ₹500cr; GST-linked incentive 100%
of gross GST for 10 years capped 300% of investment; Working Capital Interest Subvention 5% for 5 years
capped ₹1cr) — **but its registration window for NEW applicants closed 30.09.2024.** An August 2025 Apex
Committee decision released ~₹5,630cr in accrued savings to register previously-waitlisted backlog
applicants — this draws down existing outlay for a backlog, **not a reopened window for fresh applicants**.
**A genuinely new investment today cannot access NCSS 2021 registration** — a third, distinct flavor of
"no incentive available in practice" alongside Delhi/Chandigarh (never had one) and West Bengal (revoked):
J&K had a rich one that is now closed to new entrants, with disputed implementation even for approved units
(one industry association alleges ~₹20,000cr of the outlay is concentrated in 18 large units, with
GST-linked incentives "pending" despite compliance). A separate *J&K Industrial Policy 2021-30* is listed in
DPIIT's policy compendium but its primary PDF is a scanned image; not confirmed whether it adds any
UT-funded incentive beyond referencing NCSS.

### Ladakh

Ladakh runs its **own, separate, and much thinner** central scheme from J&K's — the *Central Sector Scheme
for Industrial Development of UT Ladakh*, started FY2023-24, ₹3,500cr outlay (vs. J&K's ₹28,400cr) — modest
uptake so far (1,006 units, ₹122.71cr cumulative investment). Component names mirror J&K's (Capital
Investment Incentive, Capital Interest Subvention, GST-Linked Incentive, Working Capital Interest
Subvention) but **exact %/cap figures specific to Ladakh could not be confirmed** — do not assume they match
J&K's 30/50%/6% figures without primary verification. Separately, the UT's own *Ladakh Sustainable
Industrial Policy 2022-27* was directly read via its primary PDF (a rare, genuinely machine-readable find),
and its own Chapter 6 ("Incentives") was keyword-searched for "interest subvention," "capital investment
incentive," "net GST," "working capital," "income tax": **zero matches**. **Ladakh's own UT policy has no
capital-subsidy-on-investment, interest-subvention, or GST-linked mechanic at all** — only stamp duty 100%
reimbursement, a DPR-preparation subsidy, transport/export freight subsidies, and green-energy/quality-
certification reimbursements. Structurally much thinner than J&K's, even though a central scheme nominally
exists — a genuinely different shape from the J&K entry above, not a smaller version of the same thing.

### Puducherry (UT)

**Confirmed via primary Gazette text (highest confidence of any state/UT entry in this catalog)**: Gazette
of Puducherry, Part II, G.O. Ms. No. 2 and No. 4/Ind.&Com./A6/2017, both dated 02.05.2017, implementing the
*New Industrial Policy 2016*, effective 01.04.2017 — still the operative framework as of this research (no
successor policy found notified). **Capital Investment Subsidy**: Micro/Small 40% (cap ₹40L); Medium/Large
35% (cap ₹35L — a low cap for the "large" tier, flagged by a second, independent research pass as worth
reconciling, though it is what the primary text states); Women/SC/ST 45% (cap ₹75L). **Interest Subsidy**:
25% of annual interest, capped ₹5L/annum, for 5 years (Puducherry/Karaikal) or 7 years (Mahe/Yanam). **Stamp
duty: 100% reimbursement** on land/building transactions (separately confirmed via a dated 2025 notification).
A 60%-local-employment condition applies to all incentives under the scheme. SGST/VAT reimbursement is
reported only by a secondary source (100% for MSME, 75% Medium, 50% Large — its adjacent capital/interest
figures matched the primary text exactly, raising some confidence, but the SGST figure itself is not
independently verified against a primary G.O.). Puducherry is a real, populated exception to the
Delhi/Chandigarh "UTs have nothing" pattern, consistent with its distinct administrative history (former
French territory, PIPDIC industrial-estate corporation since 1974).

### Dadra & Nagar Haveli and Daman & Diu (UT)

*Investment Promotion Scheme (IPS) 2022*, effective 20.05.2022–19.05.2027, continuing the *IPS-2015*
framework — confirmed real and active (a genuine, if secondary-sourced, industrial hub, as expected). Primary
gazette PDF located but resisted extraction; figures below are secondary-compilation. **Capital subsidy:
sources disagree** — one compilation reports 15% of Gross Fixed Capital Investment (cap ₹15–35L by MSME
tier), another reports 25% of investment for new MSMEs — **not reconciled, verify against the primary gazette
before use.** Thrust-sector enhanced subsidy 20% (cap ₹50L) for Furniture/Marble/IT-ITeS/EV/Toys/Medical/
AYUSH. Interest subsidy 50–70% by sector, 5-year tenure, caps ₹30–60L/year. Stamp duty reimbursement 50%
(MSME) / 25% (large) / 100% (thrust-sector industrial complexes). Employment incentive: one-time ₹3 lakh per
20 local persons recruited (a per-batch, not per-employee, incentive). GST/SGST reimbursement and electricity
duty concession are both asserted to exist by secondary sources but **no numeric figure was found anywhere
for either** — not confirmed in source.

### Andaman & Nicobar Islands and Lakshadweep (UTs)

**Both territories are covered by a shared CENTRAL scheme — not zero, unlike the Delhi/Chandigarh finding —
but that scheme's current status is genuinely unclear.** The *Lakshadweep and Andaman & Nicobar Islands
Industrial Development Scheme (LANIDS), 2018*, administered by the Ministry of Home Affairs, offers seven
components: Capital Investment Incentive (30% of P&M, cap ₹5cr), Interest Incentive (3% on working capital,
5 years), Comprehensive Insurance Incentive (100% premium reimbursement, 5 years), GST reimbursement (58% of
CGST + 29% of IGST paid, 5 years), income-tax reimbursement (% not confirmed), transport incentive, and an
EPF employment incentive — overall capped at total P&M investment, ceiling ₹200cr/unit. **Registration ran
01.04.2018–31.03.2020, was extended once to 31.03.2023; no confirmed successor scheme exists (unlike
NEIDS→UNNATI for the North-East) and no source confirms whether it is still open, extended again, or fully
closed as of this research (Sept 2026) — two independent research passes reached the same "genuinely
unclear, likely closed to new registrants" conclusion.** A separate, lapsed (2012-2017) UT-administered
capital subsidy for A&N Islands was also found — explicitly historical, not current.

**Lakshadweep additionally runs its own, separate UT-level scheme** — the *25% Capital Investment Subsidy
Scheme (CISS)*, confirmed via an official notice for the FY2023-24 application round (25.01–12.02.2024) and
listed on the national myScheme portal — scope limited to Micro & Small entrepreneurial units, cap amount
not confirmed. This is a genuine exception to the "small UTs have nothing" expectation, corroborated
independently by two separate research passes.

### Cross-cutting notes from this third pass

- **Structural land-cost complication (important for the matrix)**: A&N Islands' land rate is confirmed as
  **annual lease rent per sq.m**, not a one-time purchase/lease premium like every other row in
  `docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md` — it cannot be dropped into the same `rate_per_acre`
  one-time-cost field without misrepresenting an annual obligation as a capital cost. Lakshadweep has no
  industrial land market to benchmark at all (a genuine finding tied to its unusually restrictive
  land-ownership regime, not a research gap). Both are catalogued here and in the land-cost doc but excluded
  from the quantitative 12→27-state matrix for this reason.
- **Chhattisgarh's near-zero land cost and Kerala's/Goa's/Puducherry's MSME-scale subsidy caps** (all far too
  small to matter at the ₹38cr FCI scale used throughout this matrix) are recurring, genuine findings, not
  isolated flukes — several state schemes are simply not designed with large-scale investment in mind.
- **J&K is the first entry showing a scheme that is generous on paper but closed to new registrants** — a
  third distinct "no incentive available in practice" story, alongside Delhi/Chandigarh (never existed) and
  West Bengal (revoked, no replacement yet).

## What needs primary-source follow-up before this feeds a real calculation

Automated PDF fetching failed to extract text from nearly every official state policy PDF (MP, Odisha,
Punjab, Haryana, AP, UP, Karnataka, Tamil Nadu all returned binary/corrupted content) — only the superseded
Gujarat 2016-21 HTML page parsed cleanly. Every rate above should be treated as a starting hypothesis, not a
locked calculator constant, until it is checked against the primary document (ideally via pdfplumber/PyMuPDF
rather than a simple URL fetch, since these read as scanned/image PDFs or unusually encoded text PDFs that
clearly contain the missing zone/block/tier rate tables).
