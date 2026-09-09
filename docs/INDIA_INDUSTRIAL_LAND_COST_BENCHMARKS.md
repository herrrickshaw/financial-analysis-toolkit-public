# Industrial land cost benchmarks (India)

Representative industrial-plot allotment rates across the same 12 states covered in
`docs/INDIA_STATE_INVESTMENT_INCENTIVES.md`, feeding the `rate_per_acre` input of
`finmodel.sector_investment_model.industrial_land_cost`.

## Methodology note — read this before using any number below

**The central India Industrial Land Bank (IILB, indiaindustriallandbank.gov.in) does not carry a usable
price/rate field.** Its map UI now routes plot/park data through encrypted endpoints
(`AesUtil.js`/`HybridEncryption.js`/`ncb-crypto.js`), and the one visible plot-related view (a sector/state
"Net Land Listing" tree) shows area totals only, in hectares — no rupee figure appears anywhere in that UI,
its DOM, or its JS. State industrial-development-corporation (IDC) portals were the working fallback, and
each entry below is sourced individually with its own confidence level — **prices at real industrial parks
vary 10–50x by exact location within a state** (a metro-adjacent plot vs. a remote-district plot), so a
number is only meaningful with the specific park/area name attached, never as a state-level average.

Land is usually quoted per square metre or per square yard, not per acre; conversions below
(1 acre = 4,046.8564 sq.m = 4,840 sq.yard) are exact arithmetic, not a sourced figure — they're computed here
purely so every row can feed the same `rate_per_acre` input.

## Confirmed, official, dated or near-dated sources

| State | Industrial area / park | Sector character | Rate as quoted | Converted | Source |
|---|---|---|---|---|---|
| Gujarat | Naroda, Ahmedabad | general | ₹9,690/sq.m | ₹3.92 cr/acre | GIDC circular, eff. 01.09.2025 |
| Gujarat | Sanand-II (Bol), Ahmedabad | general (auto cluster) | ₹5,270/sq.m | ₹2.13 cr/acre | GIDC circular, eff. 01.09.2025 |
| Gujarat | Gandhinagar IT SEZ | IT/special | ₹6,570/sq.m | ₹2.66 cr/acre | GIDC circular, eff. 01.09.2025 |
| Gujarat | Bhat, Gandhinagar | general | ₹16,130/sq.m | ₹6.53 cr/acre | GIDC circular, eff. 01.09.2025 |
| Uttar Pradesh | Kosi Kotwan Extn-1, Mathura | general | ₹32,00,000 for 1000 sq.m (≈₹3,200/sq.m) | ₹1.30 cr/acre | UPSIDA e-auction Adv-04, 27.06.2023 |
| Uttar Pradesh | Malwan, Fatehpur (Kanpur region) | general | ₹37,04,400 for 1512 sq.m (≈₹2,450/sq.m) | ₹0.99 cr/acre | UPSIDA e-auction Adv-04, 27.06.2023 |
| Rajasthan | Chopanki, Bhiwadi | general | ₹25,000/sq.m (small plot) | ₹10.12 cr/acre | RIICO e-auction Notice 01/2025-26 |
| Rajasthan | Chopanki, Bhiwadi | general | ₹20,000/sq.m (larger corner plot) | ₹8.09 cr/acre | RIICO e-auction Notice 01/2025-26 |
| Rajasthan | Karoli Industrial Area, Auto Zone | automobile & auto components | ₹22,000/sq.m | ₹8.90 cr/acre | RIICO e-auction Notice 01/2025-26 |
| Telangana | Patancheru Ph-I | general | ₹28,600/sq.m | ₹11.57 cr/acre | TSIIC land-rate circular, 09.04.2025–31.03.2026 |
| Telangana | Hardware Park Ph-I/II | electronics/hardware | ₹12,000/sq.m | ₹4.86 cr/acre | TSIIC land-rate circular, 09.04.2025–31.03.2026 |
| Telangana | Financial District–Nanakramguda (Cyberabad) | IT (extreme high end) | ₹1,54,560/sq.m | ₹62.55 cr/acre | TSIIC land-rate circular, 09.04.2025–31.03.2026 |
| Odisha | IE Bhubaneswar / IA Chandaka / SEZ-Chandaka / Infocity, Khordha | general | ₹1.25 crore/acre | ₹1.25 cr/acre (native unit) | IDCO land-rate schedule (undated on the document itself) |
| Odisha | IE Cuttack | general | ₹75 lakh/acre | ₹0.75 cr/acre (native unit) | IDCO land-rate schedule (undated on the document itself) |
| Haryana | IMT Bawal, Rewari | automobile & auto components | ₹16,300/sq.m | ₹6.60 cr/acre | HSIIDC e-auction, tentative reserve price FY2024-25 |
| Haryana | Pace City, Gurugram | general (metro-adjacent) | ₹72,400/sq.m | ₹29.30 cr/acre | HSIIDC e-auction, tentative reserve price FY2024-25 |
| Haryana | IE Dharuhera, Rewari | general | ₹29,600/sq.m | ₹11.98 cr/acre | HSIIDC e-auction, tentative reserve price FY2024-25 |

## Official live portal, no effective date stated (treat as "as retrieved," not a dated notification)

| State | Industrial area / park | Sector character | Rate as quoted | Converted | Source |
|---|---|---|---|---|---|
| Tamil Nadu | Irungattukottai / Apparel Park, Kancheepuram | textiles/apparel (industrial rate) | ₹15,30,000/acre | ₹0.153 cr/acre (native unit) | SIPCOT transactional portal, sipcoterp.tn.gov.in/land_details |
| Tamil Nadu | Aerospace Park, Vallam Vadagal, Kancheepuram | aerospace (special) | ₹1,43,00,000/acre | ₹1.43 cr/acre (native unit) | SIPCOT transactional portal, sipcoterp.tn.gov.in/land_details |

**Flag: the Irungattukottai figure (₹0.15 cr/acre) is 5–50x lower than every other state's converted
per-acre figure above** (which run ₹0.75–₹62.5 cr/acre), despite Irungattukottai being a well-known,
metro-adjacent auto/electronics hub (Hyundai, Nissan-Renault, Foxconn) that would be expected to command a
premium, not a discount. This may reflect SIPCOT's lease-premium allotment structure differing
fundamentally from the freehold/reserve-price structures quoted elsewhere (a lease premium can legitimately
be a fraction of freehold value, with a separate ongoing ground rent), or a unit-interpretation issue on the
source page. **Treat this figure as lower-confidence despite its official-portal origin, and verify directly
against sipcoterp.tn.gov.in — including whether "Rate Per Acre" is a full sale value or a lease premium
component — before relying on it.**

## Press-sourced (not an official portal) — lower confidence

| State | Industrial area / park | Sector character | Rate as quoted | Converted | Source |
|---|---|---|---|---|---|
| Punjab | Mohali focal point | general (IT-adjacent city) | ₹39,000–42,900/sq.yard | ₹18.88–20.76 cr/acre | The Tribune, reporting a June 2025 PSIEC e-auction (psiec.punjab.gov.in itself was not reachable with an official schedule) |

## Third-party aggregator only — unverified against the primary portal

| State | Industrial area / park | Sector character | Rate as quoted | Converted | Source |
|---|---|---|---|---|---|
| Maharashtra | Taloja | chemicals-adjacent MIDC estate | ₹12,100/sq.m | ₹4.90 cr/acre | mahaindustry.com aggregator, "Updated 2026" (no precise date); NOT confirmed against midc.maharashtra.gov.in directly |
| Maharashtra | Chakan Ph I–IV | automobile & auto components | ₹5,780/sq.m | ₹2.34 cr/acre | mahaindustry.com aggregator (unverified) |
| Maharashtra | Butibori, Nagpur | general | ₹2,000/sq.m | ₹0.81 cr/acre | mahaindustry.com aggregator (unverified) |
| Maharashtra | Marol, Mumbai | general (extreme high end, metro) | ₹63,180/sq.m | ₹25.57 cr/acre | mahaindustry.com aggregator (unverified) |

## Not confirmed — no current, trustworthy figure found

- **Madhya Pradesh (MPIDC)**: `invest.mp.gov.in/land-search` and the MPIDC portal pages are functional but
  surfaced no visible rupee rate for Pithampur, Mandideep, or Dewas in this pass; an unscoped land-search
  query returned "No Land Booking Found." **No figure is reported for MP — do not substitute a plausible
  number.**
- **Karnataka (KIADB)**: `en.kiadb.in` redirects to a JS-rendered shell (`kiadb.karnataka.gov.in`) with no
  scrapable rate page found. Only farmer acquisition-compensation figures were found (e.g. ₹40 lakh/acre
  near Ballari, ₹60–75 lakh/acre near Devanahalli) — these are payouts TO land sellers, not allotment rates
  charged TO industry, and are deliberately excluded here rather than misused as a land-cost input.
- **Andhra Pradesh (APIIC)**: only historical figures found, explicitly marked stale on APIIC's own page
  (₹35 lakh/acre at Visakhapatnam SEZ, ₹16 lakh/acre at Nellore SEZ, both "valid upto 31/03/2011" — 15 years
  expired). **Not usable as a current input.**

## How this feeds the calculator

`docs/INDIA_STATE_SECTOR_INCENTIVE_MATRIX.md` uses the "Confirmed" and "official live portal" rows above as
the `rate_per_acre` input for 7 of the 12 states' worked sample calculations, explicitly uses the press- and
aggregator-sourced Punjab/Maharashtra rows with their confidence caveat carried through, and uses a clearly
labeled illustrative placeholder — never a number presented as sourced — for Madhya Pradesh, Karnataka, and
Andhra Pradesh, where no current land rate could be confirmed.
