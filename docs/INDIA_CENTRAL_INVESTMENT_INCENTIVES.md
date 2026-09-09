# Central government investment/business incentive catalog (India)

A reconnaissance catalog of Government of India investment and business incentive schemes, mapped onto the
mechanics implemented in `finmodel.investment_incentives` (see `docs/INVESTMENT_INCENTIVES.md`), prioritizing
PIB (Press Information Bureau) press releases and Parliament (Lok Sabha/Rajya Sabha) records as the primary
source of numeric parameters. As with the state catalog (`docs/INDIA_STATE_INVESTMENT_INCENTIVES.md`), every
number here is either sourced to a specific PIB URL or explicitly flagged "not confirmed in source" —
**this is a starting point for populating the calculator's inputs, not a locked reference.**

## 1. Production Linked Incentive (PLI) schemes

**Overall**: 14 approved sectors, combined outlay ₹1.97 lakh crore. As of 31 Dec 2025: 836 applications
approved, ₹2.16 lakh crore cumulative investment, ₹28,748 crore disbursed.
Source: PIB https://www.pib.gov.in/PressReleasePage.aspx?PRID=2246085 and
https://www.pib.gov.in/PressReleasePage.aspx?PRID=2107825.

The PLI mechanic is modeled by `incremental_metric_linked_incentive` — a percentage of the *increase* in
sales/turnover over a base year, not a percentage of investment.

| Sector | Outlay | Incentive mechanic | Tenure | Source |
|---|---|---|---|---|
| Large Scale Electronics Manufacturing | ~₹40,995 cr | 4–6% of incremental sales over base year FY2019-20 | 5 years from 1.8.2020 | PIB PRID (via pib.gov.in/newsite/PrintRelease.aspx?relid=200572) |
| Pharmaceuticals | ₹15,000 cr | 10–20% of incremental sales, rate depends on product category (biopharma/complex generics/patented) | FY2022-23 to FY2027-28 | PIB PRID 2197944 |
| Bulk Drugs (KSMs/DIs/APIs) | ₹6,940 cr | 20% (fermentation-based) or 10% (chemical-synthesis) of incremental sales, first 4 years, tapering thereafter (taper rate **not confirmed**) | FY2022-23 to FY2028-29 | PIB PRID 2081491 |
| Telecom & Networking Products | ₹12,195 cr | 4–7% of net incremental sales over base year FY2019-20; MSMEs (min. incremental investment ₹10 cr) get 7% tapering to 4%; "champions" (min. ₹100 cr) get 6% tapering to 4% | FY2021-22 to FY2025-26 | PIB PRID 1763872 |
| Textiles (MMF fabric/apparel + Technical Textiles) | ₹10,683 cr | reported as 15% Year 1 tapering ~1%/yr to 11% by Year 5, conditional on ≥25% annual turnover growth — **tapering schedule not confirmed at primary-source level, verify at pli.texmin.gov.in** | 5 years from notification 24.9.2021 | PIB PRID 1753118 |
| Food Processing (PLISFPI) | ₹10,900 cr | performance-linked on incremental sales; exact % slabs by category **not confirmed in source**. Separate: 50% reimbursement of overseas branding/marketing spend, capped at lower of 3% of annual food-product sales or ₹50 cr/year | FY2021-22 to FY2026-27 | PIB PRID 2081393 |
| White Goods (ACs & LED Lights) | ₹6,238 cr | 4–6% of incremental sales, reducing over 5 years following a 1-year gestation period | FY2021-22 to FY2028-29 | PIB PRID 1710116 |
| Automobile & Auto Components | ₹25,938 cr | up to 18% of determined sales value of Advanced Automotive Technology products, requires ≥50% Domestic Value Addition; two sub-schemes ("Champion OEM", "Component Champion") | 5 years | PIB PRID 1806077, 2040737 |
| Specialty Steel | ₹6,322 cr | 3 slabs, 4% (lowest) to 12% (highest, CRGO electrical steel), across 5 product categories | max 5 years, first payout FY2023-24 | PIB PRID 1737722, FAQ 1738126 |
| Advanced Chemistry Cell (ACC) Battery Storage | ₹18,100 cr | incentive rate scales with cell performance ("technology agnostic"; exact %/formula **not confirmed**); mandatory investment ₹225 cr/GWh within 2 years; Domestic Value Addition min 25% rising to 60% within 5 years | gestation 1.1.2023–31.12.2024, incentive period 1.1.2025–31.12.2029 | PIB PRID 2224542 |
| Solar PV (High Efficiency Modules) | enhanced to ₹24,000 cr (from original ₹4,500 cr) | paid for 5 years post-commissioning based on manufacture/sale of high-efficiency modules; exact %/GW rate **not confirmed**, check MNRE guidelines | 5 years post-commissioning | PIB PRID 1861127 |
| Drones & Drone Components | ₹120 cr over 3 FYs from 2021-22 | flat 20% of VALUE ADDITION (not sales) per year; min value addition required 40% of net sales; MSME/startup eligibility floor ₹2 cr (drones) / ₹50 lakh (components) annual sales; per-beneficiary cap 25% of total annual outlay | 3 years | PIB PRID 1779782, 1755452 |
| IT Hardware (PLI 2.0) | ₹17,000 cr (vs. original PLI 1.0's ₹7,325 cr) | 1–4% of net incremental sales over base year FY2019-20 (exact tiering by investment/employment target **not independently confirmed** — sourced via secondary press summary, not a directly retrieved PIB release; verify at meity.gov.in) | 6 years from approval 17.5.2023 | secondary (Business Standard); primary PIB not directly retrieved |
| Medical Devices | ₹3,420 cr | flat 5% of incremental sales, across 4 target segments. As of Dec 2025: 28 applicants approved, ₹157.15 cr disbursed to 7 | FY2022-23 to FY2026-27 | PIB PRID 2085344 |

## 2. MSME support schemes

**CGTMSE (Credit Guarantee Fund Trust for Micro and Small Enterprises)**: guarantee cover generally 75% of
sanctioned loan, up to 85% for eligible micro enterprises and priority categories (women, SC/ST, North
East). Max guarantee-covered loan reported at ₹10 crore for eligible MSMEs, ₹20 crore for DPIIT-recognised
startups/exporters under the Credit Guarantee Scheme for Startups (CGSS). Annual Guarantee Fee: 0.37% p.a.
(loans up to ₹10 lakh) up to 1.20% p.a. (₹5–10 crore band), reported effective April 2025. Cumulative to
30.11.2023: 79,53,694 guarantees, ₹5,33,587 crore.
Source: PIB https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=1986183.
**The ₹10cr/₹20cr caps and the April-2025 fee schedule came from bank/advisory sources, not a directly
retrieved PIB release — verify against cgtmse.in circulars before hard-coding.**

**PMEGP (Prime Minister's Employment Generation Programme)**, implemented by KVIC: subsidy 15% (urban) /
25% (rural) of project cost for the general category; 25% (urban) / 35% (rural) for the special category
(SC/ST/OBC/minorities/women/ex-servicemen/PwD/NER/Hill & Border areas). Beneficiary contribution: 10%
(general) / 5% (special). Project cost caps: ₹50 lakh (manufacturing), ₹20 lakh (services).
Source: PIB https://www.pib.gov.in/PressReleasePage.aspx?PRID=1795121 (exact release date not captured).

**CLCSS (Credit Linked Capital Subsidy Scheme)**: historically a 15% capital subsidy on institutional
finance up to ₹1 crore for eligible plant/machinery, capped at ₹15 lakh. **Finding: CLCSS was discontinued
and stopped accepting applications after 31 March 2017.** As of late 2025, MSME trade bodies were pressing
for its revival; no official successor scheme with confirmed replacement parameters was found.
**Treat CLCSS as NOT currently active — do not encode it as a live scheme without further confirmation.**
Source: dcmsme.gov.in FAQ (https://www.dcmsme.gov.in/schemes/faqs.pdf) and secondary trade-press coverage;
**no PIB primary source located for the discontinuation date — recommend a Lok Sabha/Rajya Sabha unstarred
question search ("CLCSS discontinued") via sansad.in.**

**ZED (Zero Defect Zero Effect) Certification**: subsidy on certification cost — Micro 80%, Small 60%,
Medium 50%; +10% additional for women/SC/ST-owned MSMEs or units in NER/Himalayan/LWE/Island/aspirational
districts; +5% additional for SFURTI/MSE-CDP cluster participants. Handholding/consultancy support up to ₹5
lakh per MSME. Joining reward: ₹10,000 per MSME on taking the ZED Pledge.
Source: PIB https://www.pib.gov.in/PressReleasePage.aspx?PRID=1821003.

## 3. Tax incentives

**Section 80-IAC — startup tax holiday**: 100% profit deduction for any 3 consecutive assessment years out
of the first 10 years from incorporation. Eligibility: Private Limited Company or LLP incorporated on/after
1.4.2016 and on/before 31.3.2030 (window repeatedly extended, most recently via Finance Act 2025); annual
turnover must not exceed ₹100 crore in any FY; requires DPIIT recognition AND a Certificate of Eligible
Business from the Inter-Ministerial Board.
Source: PIB https://www.pib.gov.in/PressReleasePage.aspx?PRID=2128860; statutory text at
incometaxindia.gov.in.

**Section 115BAB — 15% concessional rate for new manufacturing companies**: 15% base corporate tax rate
(~17.16% effective with surcharge+cess) for domestic companies incorporated on/after 1.10.2019, engaged
solely in manufacturing/production. Sunset: must commence manufacturing/production on or before 31.3.2024
(original deadline 31.3.2023, extended by one year via Finance Bill 2022). **No further extension beyond
31.3.2024 was found — treat as the current confirmed status but verify directly at incometaxindia.gov.in**,
since this is finance-critical. The election is irrevocable, and companies under 115BAB forgo most other
deductions/exemptions, including additional depreciation under Sec 32(1)(iia).
Source: incometaxindia.gov.in statutory text; secondary tax-advisory commentary (BDO) on the extension
history.

**Accelerated/additional depreciation — Section 32(1)(iia)**: 20% additional depreciation on the actual
cost of new plant/machinery (excluding ships, aircraft, certain intangibles) acquired and installed by a
manufacturing/power-generation/transmission taxpayer after 31.3.2005; reduced to 10% if the asset is used
for fewer than 180 days in the year of acquisition (remaining 10% claimed the following year). **Available
only under the old tax regime — NOT available to companies electing the concessional regimes under Sections
115BAA or 115BAB**, a critical interaction to encode if this module ever models depreciation-linked
incentives alongside 115BAB.
Source: incometaxindia.gov.in (general statutory reference, not a single dated release).

## 4. SEZ / EOU benefits

**Section 10AA — SEZ tax holiday**: 100% exemption on export profits for the first 5 years, 50% for the
next 5 years, then 50% of ploughed-back export profit for a final 5 years (15-year total window).
**Sunset for NEW units: any SEZ unit that commenced operations after 31 March 2020 cannot claim Section
10AA at all**; units that began on or before that date continue for the remainder of their original 15-year
window.
Source: secondary tax-law commentary (Lexology, TaxGuru) citing the SEZ Act sunset clause. **No direct PIB
or Parliament Q&A citation was retrieved for this exact sunset date — recommend confirming via a
sansad.in unstarred-question search or the SEZ Act amendment notification before treating as final.**

**EOU (Export Oriented Units) — current benefits**: the former income-tax holiday under Section 10B has
been fully withdrawn (exact withdrawal date not located). Remaining benefits: duty-free import of raw
materials/capital goods (basic customs duty exemption; exemption from additional customs duties under
Customs Tariff Act sections 3(1)/3(3)/3(5)), and GST refund/reimbursement on domestic procurement. Under
GST, EOUs are otherwise treated like any regular GST-registered supplier — no special GST rate remains.
Source: secondary tax-advisory summaries (ClearTax, TaxGuru); **no PIB primary source retrieved — verify
against cbic.gov.in / dgft.gov.in EOU scheme documents.**

## 5. Credit guarantee / collateral-free lending schemes

**Emergency Credit Line Guarantee Scheme (ECLGS)** — two distinct schemes share this name:
- *Original COVID-era ECLGS (1.0–4.0)*: closed. Sanctions were valid only up to 31.3.2023 (disbursement
  window extended to 30.6.2023) or until ₹5 lakh crore in guarantees was reached, whichever came first.
  Final tally: ~1,19,52,715 guarantees totaling ₹3,68,108.04 crore.
  Source: PIB https://pib.gov.in/PressReleasePage.aspx?PRID=1811580.
- *"ECLGS 5.0" (2026)*: a separate, newly-approved scheme (Cabinet approval 5 May 2026) targeted at
  businesses affected by the "West Asia Crisis," not a continuation of the COVID scheme. Guarantee coverage:
  100% for MSMEs, 90% for non-MSMEs and the airline sector; nil guarantee fee. Total additional credit
  ceiling ₹2,55,000 crore (including ₹5,000 crore ring-fenced for airlines). Additional credit available: up
  to 20% of peak working-capital utilisation during Q4 FY26, capped at ₹100 crore per borrower, measured
  against outstanding standard credit as of 31.3.2026. As of 20.8.2026: 6,73,979 guarantees issued totaling
  ₹2,50,024 crore (~98% of ceiling).
  Source: PIB https://www.pib.gov.in/PressReleasePage.aspx?PRID=2258114 and
  https://www.pib.gov.in/PressReleasePage.aspx?PRID=2281936.
  **This is a distinct, very recent (2026) scheme — do not confuse it with the original pandemic ECLGS.**

**Stand-Up India**: composite loan (term loan + working capital) between ₹10 lakh and ₹100 lakh (some
sources say up to ₹1 crore — sources conflict; the scheme's own portal states ₹10 lakh–₹100 lakh, treat the
₹1 crore figure as unconfirmed). Mandates at least one SC/ST borrower and at least one woman borrower per
bank branch (all scheduled commercial banks), for greenfield enterprises in manufacturing, services,
agri-allied, or trading; applicant must be 18+.
Source: standupmitra.in (official portal); **no PIB release with exact numeric confirmation was retrieved —
verify the ₹100 lakh vs ₹1 crore upper limit directly at standupmitra.in or via a Parliament Q&A.**

## Gaps needing primary-source follow-up before any number here is hard-coded

1. PLI Textiles' exact 15%→11% tapering schedule (unconfirmed at primary-source level).
2. PLISFPI (Food Processing) exact incentive % slabs by product category (not found).
3. PLI ACC Battery and Solar PV exact incentive-rate formulas (need MNRE/Heavy Industries guideline PDFs).
4. IT Hardware PLI 2.0 exact incentive tiering (only found via secondary press summary).
5. CGTMSE's ₹10cr/₹20cr caps and April-2025 fee schedule (sourced from bank/advisory pages, not PIB directly).
6. CLCSS's 2017 discontinuation date and current non-active status (no PIB primary source found — this
   materially affects whether the calculator should offer this scheme at all).
7. Section 10AA sunset date (31.3.2020) and Section 10B EOU withdrawal date (sourced from tax-advisory
   sites, not PIB/Parliament directly).
8. Stand-Up India's upper loan limit (₹100 lakh vs ₹1 crore — sources disagree).
9. Section 115BAB — confirm no extension exists beyond 31.3.2024 (finance-critical; warrants a direct
   incometaxindia.gov.in check).

Where a "not confirmed in source" flag appears above, the calculator should not assume a number — either a
follow-up primary-source fetch (PIB search, a sansad.in Parliament Q&A search, or the ministry's own
scheme-guideline PDF) or explicit user confirmation is needed first.
