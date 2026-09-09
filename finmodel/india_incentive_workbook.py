"""Investment Promotion Agency (IPA) Support workbook: consolidates this toolkit's India investment-incentive
research -- state schemes, central schemes, land-cost benchmarks, and the worked 27-state matrix -- into a
single, multi-sheet Excel workbook, playing the same role for an investor that a state or central IPA
(Invest India, Invest MP, Invest Karnataka, APIIC, and their counterparts) already plays one state/scheme at
a time: the same facts as `docs/INDIA_STATE_INVESTMENT_INCENTIVES.md`,
`docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md`, `docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md`, and
`docs/INDIA_STATE_SECTOR_INCENTIVE_MATRIX.md`, but consolidated across states and the centre in one
spreadsheet a non-technical reader can filter and sort directly, rather than reading four markdown files or
visiting a dozen separate IPA portals.

Two different kinds of sheet, and they're built two different ways:

  * The MATRIX sheet's numbers are computed LIVE, at build time, from the same example JSON files and the
    same `finmodel.sector_investment_model` / `finmodel.project_bankability` modules used everywhere else in
    this toolkit -- never re-typed into this file -- so they can never silently drift from what
    `finmodel sector-investment-model` / `finmodel project-bankability` themselves would print.
  * The state-scheme, central-scheme, and land-cost sheets are a structured TRANSCRIPTION of their source
    markdown docs' own tables. Those docs, with their full citation URLs and every "not confirmed in
    source" flag, remain the authoritative narrative; this workbook is an index into the same facts for
    filtering/sorting, not a new, independently-sourced dataset. A `Confidence` column on every row (and a
    `Source` column citing exactly where each row came from) carries the same honesty discipline into the
    spreadsheet -- no row here asserts a number more confidently than its source document does.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .excel import write_record_tables
from . import sector_investment_model as SIM
from . import project_bankability as PB
from . import india_corporate_tax_regimes as TAX

_EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

STATE_INCENTIVES_HEADERS = ["State", "Policy (Name, Year)", "Primary Mechanic", "Rate", "Cap", "Tenure (yrs)",
                           "Other Incentives", "Confidence", "Source"]
STATE_INCENTIVES_ROWS = [
    ["Madhya Pradesh", "Industrial Promotion Policy (IPP) 2025 (24.02.2025)",
     "Net-SGST-style reimbursement (\"Investment Promotion Assistance\")", "Not confirmed in source", "Rs200cr per applicant",
     "7-10 (varies by size)", "Interest subsidy 5-7% for 5yrs (general/textile split unclear); 70% local-employment condition",
     "Low", "invest.mp.gov.in IPP_2025_Policy.pdf (unreadable); secondary summaries"],
    ["Gujarat", "Aatmanirbhar Gujarat Scheme for Assistance to Industries 2022 (Oct 2022)",
     "Net SGST reimbursement (MSME)", "Up to 75% of FCI", "75% of FCI", 10,
     "Large/Mega: interest subsidy up to 12% of FCI; capital subsidy up to Rs35L (micro); electricity duty exemption 5yrs",
     "Medium", "cmogujarat.gov.in circular PDF; ic.gujarat.gov.in"],
    ["Maharashtra", "New industrial policy, notified 31.12.2025 (to 30.12.2030)",
     "Industrial Promotion Subsidy (IPS) = 100% of gross SGST paid", "100% of gross SGST", "40% of FCI (one cited zone example, Group B)",
     "Not confirmed", "Interest subsidy up to 5% p.a.; stamp duty exemption; EPF reimbursement", "Low",
     "maitri.maharashtra.gov.in (GR text not independently fetched)"],
    ["Tamil Nadu", "Tamil Nadu Industrial Policy 2021 (eff. 01.01.2021)", "100% SGST reimbursement",
     "100% of SGST payable", "Not confirmed (no overall FCI-based cap found)", 15,
     "Flexible Capital Subsidy up to 35-40% of Eligible Fixed Assets by district category", "Medium",
     "indembassybern.gov.in PDF (fetch failed, cert error); secondary summary"],
    ["Uttar Pradesh", "UP Industrial Investment & Employment Promotion Policy 2022 (Nov 2022)",
     "Mutually-exclusive choice: capital subsidy / net-SGST reimbursement / PLI top-up", "25% of FCI (capital-subsidy option)",
     "Rs40cr (Madhyanchal/Paschimanchal) / Rs45cr (Bundelkhand/Poorvanchal)", "Not confirmed",
     "SGST-option and PLI-top-up-option rates not confirmed", "Medium", "invest.up.gov.in PDF (unreadable)"],
    ["Rajasthan", "Rajasthan Investment Promotion Scheme (RIPS) 2024 (Oct 2023, to 31.03.2029)",
     "Capital subsidy", "13-28% of EFCI (20% used as midpoint)", "~Rs15cr (one source; conflicts with % scaling)", 10,
     "SGST reimbursement up to 75%/10yrs; interest subsidy +0.5-2%; stamp duty up to 75% exemption; +5% for SC/ST/women FPOs",
     "Medium", "rising.rajasthan.gov.in / istart.rajasthan.gov.in PDF"],
    ["Karnataka", "Karnataka Industrial Policy 2025-30", "Investment Promotion Subsidy (or turnover-linked PLI, mutually exclusive)",
     "25% of FCI (Zone 1; 10% lower zones)", "Not confirmed", "Not confirmed",
     "Turnover-linked alternative 1.0-2.5% of net sales; interest subsidy up to 6%, cap Rs50L loan", "Medium",
     "investkarnataka.co.in policy PDF"],
    ["Telangana", "TS-iPASS / T-IDEA / T-PRIDE", "Investment subsidy (MSME)", "15-25% of FCI", "Not confirmed", "Not confirmed",
     "Interest subsidy 3-9%/3-5yrs; power-cost reimbursement Rs1-2/unit/5yrs; SGST reimbursement 5-10yrs; stamp duty refund 100% (backward districts)",
     "Low (no single dated source doc)", "TS-iPASS portal / telangana.gov.in"],
    ["Andhra Pradesh", "AP Industrial Development Policy 4.0 (2024-29)", "Capital subsidy", "25% of FCI",
     "Rs25L (micro) / Rs1.5cr (small) / Rs7cr (medium)", 5,
     "Enhanced 35% (cap Rs7cr) for women/BC/SC/ST/PwD; SGST reimbursement 100%/5yrs, annual cap 5% of turnover",
     "Medium-High", "apindustries.gov.in PDF (extraction failed; figures corroborated across secondary sources)"],
    ["Odisha", "Industrial Policy Resolution (IPR) 2022", "Capital investment subsidy on P&M",
     "30% (Thrust) / 20% (Priority)", "Not confirmed", "Not confirmed",
     "Electricity duty exemption 100%/10yrs(Thrust)/7yrs(Priority); power tariff reimbursement Rs2/unit; stamp duty 100% exemption; net SGST 100% capped 200% of P&M cost",
     "Medium-High", "investodisha.gov.in"],
    ["Haryana", "Haryana Enterprises and Employment Policy (HEEP) 2020 (29.12.2020)", "Net SGST reimbursement (block-based)",
     "30-100% of net SGST paid (Block B example: 50%/5yrs+25%/3yrs)", "100% of FCI", "5-10 (by block/unit size)",
     "Interest subsidy, EPF/ESI reimbursement, electricity/stamp duty concessions (exact %/caps not confirmed)", "Medium",
     "investharyana.in (labeled \"Draft\", extraction failed)"],
    ["Punjab", "Punjab Industrial and Business Development Policy (IBDP) 2022 (17.10.2022-16.10.2027)",
     "Net SGST reimbursement", "100% of net SGST", "100% of FCI", 7,
     "Stamp duty 100% exemption; capital subsidy exists (base % not confirmed); extra incentive up to 125% of FCI for thrust sectors",
     "Medium", "punjabinfotech.in PDF"],
    ["Kerala", "Kerala Industrial Policy 2023 (eff. 01.04.2023)",
     "Two overlapping capital-subsidy schemes, not reconciled: Entrepreneur Support Scheme (MSME-scale) and the policy's own Investment Subsidy (Large/Mega)",
     "ESS 15-25% of FCI (MSME); Investment Subsidy 10% of FCI (Large/Mega)", "ESS cap Rs30-40L; Investment Subsidy cap Rs10cr (Large/Mega)",
     "Not confirmed", "Interest subvention (effective ~4% for MSME loans, 5yrs); net SGST 100%/5yrs (Large/Mega, Priority Sectors only); K-RIIS 100% land/building lease-purchase assistance for women/SC-ST/PH/transgender",
     "Medium", "industry.kerala.gov.in policy PDF (unreadable); KSIDC/K-RIIS scheme PDFs"],
    ["West Bengal", "REVOKED 2025 -- no confirmed current state-linked capital/interest/SGST scheme",
     "None currently confirmed", "N/A", "N/A", "N/A",
     "The entire investment-linked incentive framework (Banglashree/WBIPA) was legislatively REVOKED by Act 4 of 2025; a proposed employment-linked replacement (~Rs5,000cr) was not yet finalized as of this research (Aug 2026) -- an active policy transition, not a stable baseline",
     "Low (transition in progress)", "PRS India (Act 4 of 2025 text); silpasathi.wb.gov.in"],
    ["Bihar", "Bihar Industrial Investment Promotion Package (BIPPP) 2025 (approved Aug 2025, applications to 31.03.2026)",
     "Capital investment subsidy", "Up to 30% of approved project cost", "Not explicitly capped for this component", "Not confirmed",
     "Interest subvention 10-12% (cap conflicts: Rs10cr vs Rs40cr across sources); net SGST reimbursement 80% vs 100%-of-cost-cap (sources disagree); stamp duty/electricity duty 100% reimbursement; employment subsidy Rs1,000/mo (SC/ST/women) or Rs500/mo (general); free land (10-25 acres) for >=Rs100cr/>=Rs1,000cr investments",
     "Medium (SGST rate conflicts across sources)", "Dept. of Industries Bihar; Drishti IAS; nsws.gov.in policy PDF (unreadable)"],
    ["Assam", "Industrial and Investment Policy of Assam (IIPA) 2019 (amended 2023) + central UNNATI 2024 overlay",
     "State: capital subsidy on P&M. Central: UNNATI Capital Investment Incentive (stacks on top of the state scheme)",
     "State 30% of P&M (Micro-focused); Central (UNNATI) 30% (Zone A) / 50% (Zone B) of P&M",
     "State: not confirmed; Central (UNNATI): Rs5cr (Zone A) / Rs7.5cr (Zone B), per-unit cap Rs250cr",
     "Central (UNNATI): 10 years (scheme outlay period)",
     "State interest subsidy 3-5% on term loans; UNNATI GST reimbursement 100% up to 150% of investment for 15yrs; UNNATI Manufacturing & Services Linked Incentive 75-100% of P&M value. NEIDS 2017 (UNNATI's predecessor) expired 31.03.2022. UNNATI's real-world disbursement track record is separately reported as unverified/possibly nil as of this research",
     "Medium (UNNATI rates confirmed via DPIIT portal; disbursement reliability unverified)", "industries.assam.gov.in; unnati.dpiit.gov.in"],
    ["Delhi (NCT)", "NO notified state-style industrial investment-promotion policy",
     "None currently exists", "N/A", "N/A", "N/A",
     "A Draft Delhi Industrial Policy 2025-2035 remains UNNOTIFIED as of Sept 2026 (a further-out 2026-2036 draft is now referenced instead); DSIIDC's role is industrial-infrastructure development, not subsidy disbursement; MSME support visible is central-scheme-mediated (RAMP, GeM/ONDC) rather than a Delhi-specific mechanic -- this is the honest finding, not a research gap",
     "High confidence that NO scheme currently exists", "industries.delhi.gov.in draft policy page; news coverage"],
    ["Chandigarh (UT)", "NO current industrial investment-promotion policy",
     "None currently exists", "N/A", "N/A", "N/A",
     "UT Administration is drafting a new Industrial Policy (reportedly modeled on Gujarat's, focused on modernization of EXISTING units, not greenfield attraction -- land is scarce); still in stakeholder consultation as of mid-2026; any finalized policy needs Central Government approval since Chandigarh is Centrally administered; industrial investment today is effectively governed by central MSME schemes (e.g. PMEGP) only",
     "High confidence that NO scheme currently exists", "Chandigarh Administration Industries Dept.; The Tribune coverage"],
    ["Himachal Pradesh", "HP Industrial Investment Policy 2019 (repeatedly extended, now to 12.10.2026 pending a replacement)",
     "Net SGST reimbursement (confirmed, primary gazette)", "50/80/90% (A/B/C, MSME) or 50/70/80% (Large)", "80% of FCI",
     "7 (MSME) / 5 (Large)",
     "Land-premium concessions 25-70% by category; interest subvention 3-5%, cap Rs2-20L p.a.; stamp duty exemption 50-90%; electricity duty concession 1-7%/5yrs; employment subsidy Rs1,000/mo/employee beyond 50, 10yrs; central hill-state package: 58% of central tax, 01.07.2017-31.03.2027 (not the old 100% excise exemption)",
     "High (primary gazette PDF fully read)", "emerginghimachal.hp.gov.in policy PDF"],
    ["Uttarakhand", "Uttarakhand Mega Industrial & Investment Policy-2025 (~5yr validity from Oct 2025)",
     "Capital subsidy by scale tier", "Large 10% / Ultra Large 12% / Mega 15% / Ultra-Mega 20% of FCI",
     "Rs20cr/Rs60cr/Rs150cr/Rs400cr by tier", "8/10/12/15 years by tier",
     "Hill-district top-up +1-2% FCI; stamp duty reimbursement 50% cap Rs50L; superseded the MSME Policy 2015/2023 for this tier; same central hill-state 58%-of-tax package as HP",
     "Medium (large-tier policy; MSME-tier 2023 update not independently verified)", "doiuk.org; siidcul.com"],
    ["Jharkhand", "Jharkhand Industrial and Investment Promotion Policy (JIIPP) 2021 (Gazette 09.07.2021)",
     "Comprehensive Project Investment Subsidy (CPIS), confirmed primary gazette", "25% of FCI (MSME and non-MSME)",
     "Rs1-10cr (MSME by tier); Rs25cr (non-MSME)", "N/A (one-time)",
     "Interest subsidy 5% p.a./5yrs, cap Rs15L-3cr; net SGST 100%/5-9yrs (75%/12yrs Ultra-Mega), capped 100% of FCI; stamp duty 100% (direct-purchase only); electricity duty 100% for captive power only; stackable Anchor/Early-Bird/SC-ST-Women-PwD +5% top-ups",
     "High (primary gazette PDF fully read)", "industries.jharkhand.gov.in; nsws.gov.in gazette PDF"],
    ["Chhattisgarh", "Chhattisgarh Industrial Development Policy (IDP) 2024-30 (launched 14.11.2024)",
     "Choice (not stackable): net SGST reimbursement OR FCI capital subsidy", "SGST 100%/10yrs cap 150% of FCI; OR capital subsidy 30-45% of FCI",
     "150% of FCI (SGST option)", "10 (SGST option)",
     "Interest subsidy 40-70% of interest rate by category, 5-11yrs (exact tiers not confirmed); land in CSIDC/DoI areas is 100% premium-exempt with nominal Rs1/acre/year lease -- the single biggest finding of this entry",
     "Medium (policy PDF resisted extraction)", "industries.cg.gov.in; csidc.in"],
    ["Goa", "Goa Industrial Growth and Investment Promotion Policy 2022 (notified 13.10.2022) + Capital Subsidy Scheme",
     "Capital Subsidy Scheme (tracing to a 2017-era scheme)", "25% of FCI", "Rs25 lakh (MSME-scale, irrelevant above a few crore)",
     "Not confirmed",
     "Interest subsidy exists (~5yrs/20 quarters) but rate unfetchable (expired TLS cert); net SGST reported 75%/7yrs cap 100% of FCI, sector scope unconfirmed; green-practice water/energy-audit reimbursement 25%",
     "Low-Medium", "ditc.goa.gov.in"],
    ["Jammu & Kashmir", "New Central Sector Scheme (NCSS) 2021 -- registration for NEW applicants CLOSED 30.09.2024",
     "Capital Investment Incentive (confirmed, but inaccessible to new investors today)", "30% (Zone A) / 50% (Zone B) of P&M",
     "Rs5cr (Zone A) / Rs7.5cr (Zone B)", "N/A (registration closed)",
     "Capital Interest Subvention 6%/7yrs on loans to Rs500cr; GST-linked incentive 100% of gross GST/10yrs capped 300% of investment; Working Capital Interest Subvention 5%/5yrs cap Rs1cr. Rs28,400cr total outlay, running through 2037 for ALREADY-APPROVED units only -- a genuinely new investment cannot register today",
     "High (mechanics); the closure date is the critical caveat", "jkindustriescommerce.nic.in; jknis.dpiit.gov.in"],
    ["Ladakh", "Ladakh Sustainable Industrial Policy 2022-27 -- confirmed to have NO capital/interest/GST mechanic",
     "None (own UT policy keyword-searched directly, zero matches)", "N/A", "N/A", "N/A",
     "Stamp duty 100% reimbursement; DPR-preparation subsidy 50% cap Rs50,000; transport/export freight subsidies; green-energy/quality-certification reimbursements. A separate central scheme (Rs3,500cr since FY2023-24) exists but its exact %/caps could not be confirmed -- distinct from, and much thinner than, J&K's NCSS",
     "High (primary policy PDF fully read)", "industries.ladakh.gov.in policy PDF"],
    ["Puducherry (UT)", "New Industrial Policy 2016 / Gazette G.O. Ms. No. 2 & 4/Ind.&Com./A6/2017 (eff. 01.04.2017)",
     "Capital Investment Subsidy (confirmed directly from primary Gazette text)", "Micro/Small 40%; Medium/Large 35%; Women/SC/ST 45%",
     "Rs40L / Rs35L / Rs75L respectively", "N/A (one-time)",
     "Interest subsidy 25% of annual interest, cap Rs5L/yr, 5yrs (Puducherry/Karaikal) or 7yrs (Mahe/Yanam); stamp duty 100% reimbursement (separately confirmed via a dated 2025 notification); 60%-local-employment condition on all incentives; SGST reimbursement reported only by secondary source (100%/75%/50% by MSME/Medium/Large tier), not independently verified against primary text",
     "High (primary Gazette text read directly) -- the strongest-sourced state/UT incentive entry in this catalog",
     "industry.py.gov.in Gazette PDF"],
    ["Dadra & Nagar Haveli and Daman & Diu (UT)", "Investment Promotion Scheme (IPS) 2022 (eff. 20.05.2022-19.05.2027)",
     "Capital subsidy -- two sources CONFLICT, not reconciled", "15% of GFCI (one source) OR 25% of investment (another source)",
     "Rs15-35L by MSME tier (first source only)", "N/A (one-time)",
     "Thrust-sector enhanced subsidy 20% cap Rs50L; interest subsidy 50-70% by sector, 5yrs, cap Rs30-60L/yr; stamp duty 50%(MSME)/25%(large)/100%(thrust-sector complexes); employment incentive Rs3L per 20 local persons recruited (per-batch, not per-employee); GST/SGST reimbursement and electricity duty concession both asserted to exist but no numeric figure found for either",
     "Medium (primary gazette PDF resisted extraction; all figures secondary)", "swp.dddgov.in gazette PDF (unreadable)"],
    ["Andaman & Nicobar Islands and Lakshadweep (UTs)", "Lakshadweep and Andaman & Nicobar Islands Industrial Development Scheme (LANIDS) 2018 -- a shared CENTRAL scheme, status unclear",
     "7 components incl. Capital Investment Incentive (confirmed structure; current registration status genuinely unclear)", "30% of P&M",
     "Rs5cr; overall ceiling Rs200cr/unit", "5 (most components)",
     "Interest Incentive 3%/5yrs on working capital; Comprehensive Insurance Incentive 100% premium/5yrs; GST reimbursement 58% CGST+29% IGST/5yrs; income-tax reimbursement (% not confirmed); transport and EPF employment incentives. Registration ran 2018-2020, extended once to 2023; no confirmed successor (unlike NEIDS->UNNATI); two independent research passes could not confirm whether it is open, extended again, or closed as of Sept 2026. Lakshadweep ALSO runs its own separate 25% Capital Investment Subsidy Scheme (CISS), confirmed via an official FY2023-24 notice and the national myScheme portal",
     "Medium (scheme structure confirmed; current status unclear)", "as.and.nic.in/lanids; lakshadweep.gov.in"],
]

CENTRAL_INCENTIVES_HEADERS = ["Scheme", "Category", "Outlay / Cap", "Mechanic / Rate", "Tenure", "Confidence", "Source"]
CENTRAL_INCENTIVES_ROWS = [
    ["Large Scale Electronics Manufacturing", "PLI", "Rs40,995cr", "4-6% of incremental sales over base year FY2019-20",
     "5yrs from 01.08.2020", "High", "PIB (pib.gov.in/newsite/PrintRelease.aspx?relid=200572)"],
    ["Pharmaceuticals", "PLI", "Rs15,000cr", "10-20% of incremental sales, by product category", "FY2022-23 to FY2027-28",
     "High", "PIB PRID 2197944"],
    ["Bulk Drugs (KSMs/DIs/APIs)", "PLI", "Rs6,940cr", "20% (fermentation-based) / 10% (chemical-synthesis) of incremental sales, first 4yrs; taper rate for yrs 5-6 not confirmed",
     "FY2022-23 to FY2028-29", "Medium", "PIB PRID 2081491"],
    ["Telecom & Networking Products", "PLI", "Rs12,195cr",
     "4-7% of net incremental sales over FY2019-20; MSMEs 7%->4%, non-MSME champions 6%->4%", "FY2021-22 to FY2025-26",
     "High", "PIB PRID 1763872"],
    ["Textiles (MMF fabric/apparel + Technical Textiles)", "PLI", "Rs10,683cr",
     "Reported 15% Year1 tapering to 11% by Year5 -- NOT confirmed at primary-source level", "5yrs from notification 24.09.2021",
     "Low", "PIB PRID 1753118"],
    ["Food Processing Industries (PLISFPI)", "PLI", "Rs10,900cr",
     "Performance-linked on incremental sales, exact % slabs not confirmed; separate 50% overseas branding/marketing reimbursement, capped at lower of 3% of sales or Rs50cr/yr",
     "FY2021-22 to FY2026-27", "Low", "PIB PRID 2081393"],
    ["White Goods (ACs & LED Lights)", "PLI", "Rs6,238cr", "4-6% of incremental sales, reducing over 5yrs post 1-yr gestation",
     "FY2021-22 to FY2028-29", "Medium", "PIB PRID 1710116"],
    ["Automobile & Auto Components", "PLI", "Rs25,938cr", "Up to 18% of determined sales value of AAT products, requires >=50% DVA",
     "5yrs", "Medium", "PIB PRID 1806077, 2040737"],
    ["Specialty Steel", "PLI", "Rs6,322cr", "4-12% across 5 product categories (highest: CRGO electrical steel)",
     "Max 5yrs, first payout FY2023-24", "High", "PIB PRID 1737722, FAQ 1738126"],
    ["Advanced Chemistry Cell (ACC) Battery Storage", "PLI", "Rs18,100cr",
     "Rate scales with cell performance, exact formula not confirmed; mandatory investment Rs225cr/GWh within 2yrs",
     "Gestation 2023-2024, incentive 2025-2029", "Low", "PIB PRID 2224542"],
    ["Solar PV (High Efficiency Modules)", "PLI", "Rs24,000cr (enhanced from Rs4,500cr)",
     "Paid for 5yrs post-commissioning; exact %/GW rate not confirmed", "5yrs post-commissioning", "Low", "PIB PRID 1861127"],
    ["Drones & Drone Components", "PLI", "Rs120cr over 3 FYs", "Flat 20% of VALUE ADDITION (not sales) per year; min 40% value addition required",
     "3yrs from FY2021-22", "High", "PIB PRID 1779782, 1755452"],
    ["IT Hardware (PLI 2.0)", "PLI", "Rs17,000cr (vs original Rs7,325cr)",
     "1-4% of net incremental sales over FY2019-20; exact tiering not independently confirmed", "6yrs from approval 17.05.2023",
     "Low", "Secondary press (Business Standard); primary PIB not directly retrieved"],
    ["Medical Devices", "PLI", "Rs3,420cr", "Flat 5% of incremental sales, across 4 target segments",
     "FY2022-23 to FY2026-27", "High", "PIB PRID 2085344"],
    ["CGTMSE (Credit Guarantee Fund Trust for MSEs)", "MSME Credit Guarantee",
     "Guarantee cover 75-85%; max covered loan Rs10cr (Rs20cr for DPIIT startups/exporters)",
     "Annual guarantee fee 0.37%-1.20% p.a.", "Ongoing", "Medium (caps/fee schedule from bank/advisory sources, not directly a PIB release)",
     "PIB PRID 1986183"],
    ["PMEGP (Prime Minister's Employment Generation Programme)", "MSME Subsidy",
     "Project cost cap Rs50L (mfg) / Rs20L (services)", "15% urban/25% rural (general); 25% urban/35% rural (special category)",
     "Ongoing", "High", "PIB PRID 1795121"],
    ["CLCSS (Credit Linked Capital Subsidy Scheme)", "MSME Capital Subsidy", "Historically cap Rs15L",
     "Historically 15% of institutional finance; DISCONTINUED after 31.03.2017, no confirmed successor",
     "Inactive", "Low (discontinuation date not PIB-confirmed)", "dcmsme.gov.in FAQ; secondary trade press"],
    ["ZED (Zero Defect Zero Effect) Certification", "MSME Subsidy", "Handholding support up to Rs5L/MSME",
     "80% (micro) / 60% (small) / 50% (medium) of cert cost; +10%/+5% top-ups", "Ongoing", "High", "PIB PRID 1821003"],
    ["Section 80-IAC (Startup tax holiday)", "Tax", "Turnover must not exceed Rs100cr in any FY",
     "100% profit deduction for any 3 consecutive years out of first 10", "Incorporated 01.04.2016-31.03.2030",
     "High", "PIB PRID 2128860"],
    ["Section 115BAB (15% concessional rate, new manufacturing)", "Tax", "N/A",
     "15% base rate (~17.16% effective with surcharge+cess), irrevocable election",
     "Must commence production by 31.03.2024; no further extension found", "Medium", "incometaxindia.gov.in"],
    ["Section 32(1)(iia) (Additional depreciation)", "Tax", "N/A",
     "20% additional depreciation (10% if used <180 days/yr); NOT available under 115BAA/115BAB",
     "Ongoing (old regime only)", "High", "incometaxindia.gov.in"],
    ["Section 10AA (SEZ tax holiday)", "SEZ", "N/A", "100% export-profit exemption 5yrs, 50% next 5yrs, 50% of ploughed-back profit final 5yrs",
     "NEW units after 31.03.2020 NOT eligible", "Low (sunset date not PIB/Parliament-confirmed)", "Secondary tax-law commentary (Lexology, TaxGuru)"],
    ["EOU (Export Oriented Units)", "SEZ/EOU", "N/A", "Sec 10B income-tax holiday withdrawn; duty-free imports + GST refund remain",
     "Ongoing", "Low", "Secondary (ClearTax, TaxGuru)"],
    ["ECLGS (original, COVID-era 1.0-4.0)", "Credit Guarantee", "Rs3,68,108.04cr disbursed (final tally)",
     "Guarantee-backed emergency credit lines", "CLOSED 31.03.2023 (disbursement to 30.06.2023)", "High", "PIB PRID 1811580"],
    ["ECLGS 5.0 (2026, \"West Asia Crisis\")", "Credit Guarantee", "Rs2,55,000cr ceiling (incl. Rs5,000cr for airlines)",
     "100% cover (MSME) / 90% (non-MSME, airlines); nil guarantee fee; up to 20% of Q4FY26 peak WC, cap Rs100cr/borrower",
     "Cabinet approval 05.05.2026", "High", "PIB PRID 2258114, 2281936"],
    ["Stand-Up India", "Credit Guarantee", "Rs10L-Rs100L composite loan (Rs1cr figure unconfirmed, sources conflict)",
     "Mandates >=1 SC/ST borrower + >=1 woman borrower per bank branch", "Ongoing", "Medium", "standupmitra.in"],
]

LAND_COST_HEADERS = ["State", "Industrial Area / Park", "Sector Character", "Rate (as quoted)", "Converted (Rs cr/acre)",
                    "Confidence Tier", "Source"]
LAND_COST_ROWS = [
    ["Gujarat", "Naroda, Ahmedabad", "General", "Rs9,690/sq.m", 3.92, "Confirmed, official, dated", "GIDC circular, eff. 01.09.2025"],
    ["Gujarat", "Sanand-II (Bol), Ahmedabad", "General (auto cluster)", "Rs5,270/sq.m", 2.13, "Confirmed, official, dated", "GIDC circular, eff. 01.09.2025"],
    ["Gujarat", "Gandhinagar IT SEZ", "IT / special", "Rs6,570/sq.m", 2.66, "Confirmed, official, dated", "GIDC circular, eff. 01.09.2025"],
    ["Gujarat", "Bhat, Gandhinagar", "General", "Rs16,130/sq.m", 6.53, "Confirmed, official, dated", "GIDC circular, eff. 01.09.2025"],
    ["Uttar Pradesh", "Kosi Kotwan Extn-1, Mathura", "General", "~Rs3,200/sq.m", 1.30, "Confirmed, official, dated (2023 auction, may be stale)", "UPSIDA e-auction Adv-04, 27.06.2023"],
    ["Uttar Pradesh", "Malwan, Fatehpur (Kanpur region)", "General", "~Rs2,450/sq.m", 0.99, "Confirmed, official, dated (2023 auction, may be stale)", "UPSIDA e-auction Adv-04, 27.06.2023"],
    ["Rajasthan", "Chopanki, Bhiwadi (small plot)", "General", "Rs25,000/sq.m", 10.12, "Confirmed, official, dated", "RIICO e-auction Notice 01/2025-26"],
    ["Rajasthan", "Chopanki, Bhiwadi (larger corner plot)", "General", "Rs20,000/sq.m", 8.09, "Confirmed, official, dated", "RIICO e-auction Notice 01/2025-26"],
    ["Rajasthan", "Karoli Industrial Area, Auto Zone", "Automobile & auto components", "Rs22,000/sq.m", 8.90, "Confirmed, official, dated", "RIICO e-auction Notice 01/2025-26"],
    ["Telangana", "Patancheru Ph-I", "General", "Rs28,600/sq.m", 11.57, "Confirmed, official, dated", "TSIIC land-rate circular, 09.04.2025-31.03.2026"],
    ["Telangana", "Hardware Park Ph-I/II", "Electronics / hardware", "Rs12,000/sq.m", 4.86, "Confirmed, official, dated", "TSIIC land-rate circular, 09.04.2025-31.03.2026"],
    ["Telangana", "Financial District-Nanakramguda (Cyberabad)", "IT (extreme high end)", "Rs1,54,560/sq.m", 62.55, "Confirmed, official, dated", "TSIIC land-rate circular, 09.04.2025-31.03.2026"],
    ["Odisha", "IE Bhubaneswar / IA Chandaka / SEZ-Chandaka / Infocity, Khordha", "General", "Rs1.25cr/acre", 1.25, "Confirmed, official (undated document)", "IDCO land-rate schedule"],
    ["Odisha", "IE Cuttack", "General", "Rs75 lakh/acre", 0.75, "Confirmed, official (undated document)", "IDCO land-rate schedule"],
    ["Haryana", "IMT Bawal, Rewari", "Automobile & auto components", "Rs16,300/sq.m", 6.60, "Confirmed, official, dated", "HSIIDC e-auction, tentative reserve price FY2024-25"],
    ["Haryana", "Pace City, Gurugram", "General (metro-adjacent)", "Rs72,400/sq.m", 29.30, "Confirmed, official, dated", "HSIIDC e-auction, tentative reserve price FY2024-25"],
    ["Haryana", "IE Dharuhera, Rewari", "General", "Rs29,600/sq.m", 11.98, "Confirmed, official, dated", "HSIIDC e-auction, tentative reserve price FY2024-25"],
    ["Tamil Nadu", "Irungattukottai / Apparel Park, Kancheepuram", "Textiles / apparel", "Rs15,30,000/acre", 0.153,
     "Official live portal, no date (flagged anomalously low)", "SIPCOT transactional portal, sipcoterp.tn.gov.in/land_details"],
    ["Tamil Nadu", "Aerospace Park, Vallam Vadagal, Kancheepuram", "Aerospace (special)", "Rs1,43,00,000/acre", 1.43,
     "Official live portal, no date", "SIPCOT transactional portal, sipcoterp.tn.gov.in/land_details"],
    ["Punjab", "Mohali focal point", "General (IT-adjacent city)", "Rs39,000-42,900/sq.yard", 19.82,
     "Press-sourced, not an official portal", "The Tribune, reporting a June 2025 PSIEC e-auction"],
    ["Maharashtra", "Taloja", "Chemicals-adjacent MIDC estate", "Rs12,100/sq.m", 4.90, "Third-party aggregator, unverified", "mahaindustry.com, \"Updated 2026\""],
    ["Maharashtra", "Chakan Ph I-IV", "Automobile & auto components", "Rs5,780/sq.m", 2.34, "Third-party aggregator, unverified", "mahaindustry.com"],
    ["Maharashtra", "Butibori, Nagpur", "General", "Rs2,000/sq.m", 0.81, "Third-party aggregator, unverified", "mahaindustry.com"],
    ["Maharashtra", "Marol, Mumbai", "General (extreme high end, metro)", "Rs63,180/sq.m", 25.57, "Third-party aggregator, unverified", "mahaindustry.com"],
    ["Madhya Pradesh", "Pithampur-1 & 2, Dhar district", "Automobile & auto-components hub (MP's largest industrial area)",
     "Rs2,204/sq.m land + Rs1,000/sq.m development", 1.30, "Confirmed, official", "MPIDC Land Availability Report; LBA portal Charges Details tab"],
    ["Madhya Pradesh", "Mandideep, Raisen district", "General", "Rs2,907/sq.m land + Rs580/sq.m development", 1.41,
     "Confirmed, official", "MPIDC Land Availability Report; LBA portal"],
    ["Madhya Pradesh", "Dewas Sector 2 & 3", "General", "Rs1,785/sq.m land + Rs670/sq.m development", 0.99,
     "Confirmed, official", "MPIDC Land Availability Report; LBA portal"],
    ["Andhra Pradesh", "JN Pharma City, Parawada (Anakapalli district)", "Pharmaceuticals", "Rs7,283/sq.m", 2.95,
     "Confirmed, official, dated (eff. 01.04.2026-31.03.2027)", "APIIC digital land bank API, digital.apiic.in/landbankapi"],
    ["Andhra Pradesh", "IP-BP SEZ, Ongole (Prakasam district)", "General / SEZ", "Rs1,255/sq.m", 0.51,
     "Confirmed, official, dated", "APIIC digital land bank API"],
    ["Karnataka", "Sira Industrial Area, Tumakuru, Plot 108", "General (2-acre plot, historical allotment)",
     "Rs91,00,000 total (derived: Rs45.5L/acre)", 0.455, "Confirmed via official API, but a historical allotted-plot price",
     "KIADB GIS portal, \"Search Data -> By Land Bank\""],
    ["Kerala", "KINFRA Food Processing Industrial Park, Adoor, Pathanamthitta", "Food processing", "Rs148.85 lakh/acre (developed)",
     1.489, "Confirmed, official, live portal (no single effective date; page flags lease premium under revision)", "kinfra.org/investor-zone Land Bank table"],
    ["West Bengal", "Vidyasagar Industrial Park, Kharagpur, Paschim Medinipur", "Engineering / multi-product", "Rs75.02 lakh/acre (freehold)",
     0.750, "Confirmed, official, dated (\"Tentative Base Price for the Year 2026\")", "wbidc.com/wbidc-land/availability-of-land-modules"],
    ["Bihar", "EPIP, Hajipur, Vaishali", "Export-oriented (EPIP)", "Rs537.10/sq.ft", 2.340,
     "Confirmed, official, live portal", "biada1.bihar.gov.in Vacant Plot Details"],
    ["Assam", "EPIP Amingaon, Kamrup", "Export-oriented (EPIP)", "Rs5,400/sq.m", 2.185,
     "Confirmed, official, dated (EOI ECF No.353649/114, 05.09.2024) -- a minimum bid-floor rate, actual allotment may be higher",
     "aidcltd.assam.gov.in EOI PDF"],
    ["Delhi (NCT)", "Mangolpuri Industrial Area, Ph-I & II", "General (extreme high-cost urban location)", "Rs1,05,120/sq.m", 42.541,
     "Confirmed, official, but dated (2022 e-auction cycle) -- DSIIDC's own portal was unreachable in this research pass",
     "dda.gov.in e-auction reserve-price schedule (Annexure-I)"],
    ["Chandigarh (UT)", "Industrial Area, Phase III", "General", "Rs62,600/sq.yard", 30.298,
     "Weakest confidence in this catalog: a Collector/circle rate (stamp-duty valuation floor, eff. 01.04.2025), NOT a Housing Board/Estate Office allotment or auction premium -- the actual allotment portal could not be reached",
     "The Tribune, reporting UT collector-rate notification"],
    ["Himachal Pradesh", "IA Baddi, Solan", "General (well-known pharma/FMCG hub)", "Rs5,000/sq.m", 2.023,
     "Confirmed, official, dated (eff. 01.04.2019 cycle; may be stale, no newer cycle located)", "emerginghimachal.hp.gov.in premium circular"],
    ["Himachal Pradesh", "IA Parwanoo, Solan", "General", "Rs8,784/sq.m", 3.555,
     "Confirmed, official, dated (same cycle)", "emerginghimachal.hp.gov.in premium circular"],
    ["Uttarakhand", "Integrated Industrial Estate, Sitarganj Phase-II", "General (auto/FMCG belt)", "Rs3,700/sq.m", 1.497,
     "Confirmed, official live portal, no effective date", "siidcul.com"],
    ["Jharkhand", "Adityapur, Saraikela-Kharsawan", "Automobile & auto components", "Rs90 lakh/acre (30-yr lease)", 0.90,
     "Third-party aggregator (EMC indicative rate doc), dated ~July 2022, not a primary JIADA notification",
     "secondary compilation citing emcpms.gov.in"],
    ["Chhattisgarh", "Any CSIDC/Directorate of Industries industrial area", "General", "100% land-premium exemption, nominal Rs1/acre/year lease", 0.0,
     "Confirmed, official (IDP 2024-30) -- genuinely near-zero, not an illustrative placeholder", "industries.cg.gov.in; csidc.in"],
    ["Goa", "Goa-IDC estates (unspecified; range across the portfolio)", "General", "Rs1,020-2,680/sq.m", 0.745,
     "Confirmed, official, dated (eff. 01.04.2021; a ~10% hike was under consideration as of Feb 2026, not yet approved) -- this is the RANGE MIDPOINT, not a specific named estate's rate",
     "goa.gov.in GIDC plot-rate circular"],
    ["Jammu & Kashmir", "Zone A (J&K Industrial Land Allotment Policy 2021-30)", "General", "Rs5.0 lakh/Kanal (99-yr lease)", 0.40,
     "Confirmed via press coverage citing the official policy; primary policy PDF not independently re-extracted",
     "Deccan Herald + jkindustriescommerce.nic.in"],
    ["Ladakh", "Urban industrial estates, largest plot tier (>20 Kanal)", "General", "Rs6.0 lakh/Kanal (one-time premium)", 0.48,
     "Confirmed, official, primary PDF fully read -- best-sourced land entry in this whole catalog", "industries.ladakh.gov.in policy PDF"],
    ["Puducherry (UT)", "Mettupalayam Industrial Estate", "General (167 acres, PIPDIC's largest)", "Rs1,000/sq.m (99-yr lease premium)", 0.405,
     "Confirmed, official -- cross-validated by two independent research passes", "pipdic.com/pipdic.in"],
    ["Dadra & Nagar Haveli and Daman & Diu (UT)", "Any DIC/DPDDC industrial estate", "General", "Not confirmed", 2.0,
     "ILLUSTRATIVE PLACEHOLDER -- no official rate found despite an active industrial base; the one likely-relevant document (a vacant-plot list) resisted extraction",
     "dnh.gov.in vacant-plot-list PDF (unreadable)"],
]


def _matrix_and_bankability_rows() -> Dict[str, Any]:
    with open(_EXAMPLES / "state_sector_matrix_demo.json") as f:
        matrix_payload = json.load(f)
    matrix = SIM.from_dict(matrix_payload)["sample_project_matrix"]

    with open(_EXAMPLES / "project_bankability_demo.json") as f:
        bankability_payload = json.load(f)
    bankability = PB.from_dict(bankability_payload)["rank_projects"]
    irr_by_state = {p["state"]: p for p in bankability["projects"]}

    with open(_EXAMPLES / "dscr_matrix_demo.json") as f:
        dscr_payload = json.load(f)
    dscr = PB.from_dict(dscr_payload)["dscr_matrix"]
    dscr_by_state = {r["state"]: r for r in dscr}

    headers = ["State", "Sector", "Land Rate (Rs cr/acre)", "Total Capex (Rs cr)", "Incentive PV (Rs cr)",
              "Net Effective Investment (Rs cr)", "Effective Subsidy % (PV basis)", "IRR without Incentives",
              "IRR with Incentives", "DSCR (SBI/REC-style, 70% leverage)", "DSCR Compliant (>=1.20x)"]
    rows: List[List[Any]] = []
    for p in matrix["projects"]:
        state = p["state"]
        irr_row = irr_by_state.get(state, {})
        dscr_row = dscr_by_state.get(state, {})
        rows.append([
            state, p["sector"], round(p["land"]["rate_per_acre"], 4), round(p["capex"]["total_capex"], 2),
            round(p["incentives"]["total_present_value"], 2), round(p["net_effective_investment"], 2),
            round(p["effective_subsidy_pct_pv_basis"], 4),
            round(irr_row.get("irr_without_incentives", 0.0), 4), round(irr_row.get("irr_with_incentives", 0.0), 4),
            round(dscr_row.get("dscr", 0.0), 3), "Yes" if dscr_row.get("compliant") else "No",
        ])
    rows.append(["TOTAL (27 states)", "", "", round(matrix["total_capex_across_projects"], 2),
                round(matrix["total_incentive_present_value_across_projects"], 2),
                round(matrix["total_capex_across_projects"] - matrix["total_incentive_present_value_across_projects"], 2),
                "", "", "", "", ""])
    return {"headers": headers, "rows": rows}


def _tax_regime_rows() -> Dict[str, Any]:
    with open(_EXAMPLES / "india_corporate_tax_regimes_demo.json") as f:
        payload = json.load(f)
    result = TAX.from_dict(payload)["tax_regime_comparison"]
    headers = ["Regime", "Base Rate", "Surcharge Rate", "Cess Rate", "Effective Rate", "Post-tax Cash Flow (Rs cr)",
              "IRR (post-tax)", "Best Regime?"]
    rows = []
    for name, r in result["regimes"].items():
        rows.append([name, r["base_rate"], r["surcharge_rate"], r["cess_rate"], round(r["effective_rate"], 4),
                    round(r["post_tax_annual_cash_flow"], 3), round(r["irr_post_tax"], 4),
                    "Yes" if name == result["best_regime"] else "No"])
    return {"headers": headers, "rows": rows}


def _financing_effects_rows() -> Dict[str, Any]:
    with open(_EXAMPLES / "india_corporate_tax_regimes_demo.json") as f:
        cgtmse_payload = json.load(f)
    cgtmse = TAX.from_dict(cgtmse_payload)["cgtmse_adjusted_dscr"]

    with open(_EXAMPLES / "dscr_matrix_ireda_demo.json") as f:
        ireda_payload = json.load(f)
    ireda = PB.from_dict(ireda_payload)["dscr_matrix"]

    headers = ["Example", "Lender / Scheme", "Loan (Rs cr)", "Rate", "Tenure (yrs)", "Annual Cash Flow (Rs cr)",
              "DSCR", "Min DSCR Required", "Compliant?", "Note"]
    rows = [
        ["MSME term loan (Rajasthan-style illustrative)", "CGTMSE-covered, no fee", "5.0", "10.5%", "7",
         "1.27", round(cgtmse["dscr_without_fee_for_comparison"], 3), 1.2,
         "Yes" if cgtmse["dscr_without_fee_for_comparison"] >= 1.2 else "No",
         "Debt service alone, before the CGTMSE guarantee fee"],
        ["MSME term loan (same loan, with CGTMSE fee)", "CGTMSE (0.75% p.a. guarantee fee)", "5.0", "10.5%", "7",
         "1.27", round(cgtmse["dscr_with_cgtmse_fee"], 3), 1.2, "Yes" if cgtmse["compliant"] else "No",
         "The fee's real, small cost tips this boundary case into breach"],
    ]
    for r in ireda:
        rows.append([f"{r['sector']}, {r['state']}", r["lender"], round(0.75 * 38.0, 2), "8.65%", "15",
                    round(0.20 * 38.0, 2), round(r["dscr"], 3), r["min_dscr_required"],
                    "Yes" if r["compliant"] else "No", "IREDA's own disclosed Grade I rate/DSCR floor, not the generic SBI/REC case"])
    return {"headers": headers, "rows": rows}


WORKBOOK_TITLE = "Investment Promotion Agency (IPA) Support"

README_LINES = [
    f"{WORKBOOK_TITLE} -- India Investment Incentive & Bankability Workbook, generated by finmodel (financial-analysis-toolkit)",
    "",
    "The role this workbook fills is the one a state or central Investment Promotion Agency (IPA) itself plays",
    "for an investor -- Invest India, Invest MP, Invest Karnataka, APIIC, and their counterparts each publish",
    "and explain their own state's/sector's incentives one at a time; this workbook consolidates that same kind",
    "of information -- which schemes apply, at what rate, with what land cost, and what that means for a",
    "project's actual bankability -- across states and the centre in one place, filterable and sortable.",
    "",
    "Sheets:",
    "  State Incentives    -- 27 states/UTs' industrial/MSME investment-promotion schemes",
    "  Central Incentives  -- PLI (14 sectors), MSME, tax, SEZ/EOU, and credit-guarantee schemes",
    "  Land Cost Benchmarks-- sourced industrial land allotment rates across the same 27 states/UTs (plus 2 catalogued but excluded, see below)",
    "  27-State Matrix     -- a worked sample project per state/UT: land+capex netted against incentives (PV basis),",
    "                         IRR with/without incentives, and a DSCR covenant check -- computed LIVE from the",
    "                         toolkit's own modules and example files at the time this workbook was built, never re-typed",
    "  Tax Regime Comparison-- Section 115BAB vs 115BAA vs the standard regime, post-tax IRR, computed LIVE",
    "  Financing Effects   -- CGTMSE's guarantee-fee effect on DSCR, and a renewable-energy DSCR check using",
    "                         IREDA's own disclosed rate/covenant instead of the generic SBI/REC case, computed LIVE",
    "",
    "EVERY row on the State/Central/Land sheets carries its own Confidence and Source column. A 'Not confirmed'",
    "or 'Low' confidence entry means the underlying research could not verify that number against a primary",
    "source -- treat it as a starting hypothesis, not a locked constant, and check the Source column before",
    "relying on it. The full narrative detail and every citation URL live in this repository's docs/ folder:",
    "  docs/INDIA_STATE_INVESTMENT_INCENTIVES.md",
    "  docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md",
    "  docs/INDIA_INDUSTRIAL_LAND_COST_BENCHMARKS.md",
    "  docs/INDIA_STATE_SECTOR_INCENTIVE_MATRIX.md",
    "  docs/PROJECT_BANKABILITY.md",
    "  docs/INDIA_PROJECT_FINANCE_LENDING_TERMS.md",
    "  docs/INDIA_CORPORATE_TAX_AND_CGTMSE.md",
    "",
    "This is a precursor/sample calculation tool, not investment advice -- every matrix figure depends on the",
    "illustrative assumptions documented alongside it (a held-constant capex stack, a flat assumed operating",
    "cash flow, an illustrative discount/hurdle rate); change those assumptions and the numbers will change.",
]


def build_workbook(path: str) -> str:
    sheets = {
        "State Incentives": {"headers": STATE_INCENTIVES_HEADERS, "rows": STATE_INCENTIVES_ROWS},
        "Central Incentives": {"headers": CENTRAL_INCENTIVES_HEADERS, "rows": CENTRAL_INCENTIVES_ROWS},
        "Land Cost Benchmarks": {"headers": LAND_COST_HEADERS, "rows": LAND_COST_ROWS},
        "27-State Matrix": _matrix_and_bankability_rows(),
        "Tax Regime Comparison": _tax_regime_rows(),
        "Financing Effects": _financing_effects_rows(),
    }
    return str(write_record_tables(path, sheets, readme_lines=README_LINES, workbook_title=WORKBOOK_TITLE))
