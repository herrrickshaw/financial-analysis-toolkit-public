# Learning guide: what each tool does, and where to learn it properly

Each section summarises one engine in this toolkit (the method, the formulas the code actually
runs, the judgement calls that matter), then points to **books** and **open university material**
that teach it, and to the **public templates** in `catalog/` that implement it in Excel.
All course links were checked live on 2026-09-06.

---

## 0. The reading stack (in the order practitioners recommend)

| Book | Author(s) | Edition | Use it for |
|---|---|---|---|
| *Financial Modeling and Valuation: A Practical Guide to Investment Banking and Private Equity* | Paul Pignataro | 2nd ed. (Wiley, 2022) | Build the 3-statement model line by line; the closest book to the CFI case study |
| *Investment Banking: Valuation, LBOs, M&A, and IPOs* | Joshua Rosenbaum, Joshua Pearl | 3rd ed. (Wiley, 2020/2022 with model templates) | Comps, precedents, DCF, LBO, merger and IPO models the way banks build them |
| *Valuation: Measuring and Managing the Value of Companies* | Tim Koller, Marc Goedhart, David Wessels (McKinsey) | 8th ed. (Wiley, 2025) | Value drivers (ROIC, growth), continuing value, enterprise DCF vs economic profit |
| *Investment Valuation* / *Damodaran on Valuation* / *The Little Book of Valuation* / *Narrative and Numbers* | Aswath Damodaran | 3rd ed. 2012 / 2nd ed. 2006 / 2011 / 2017 | DCF inputs (cost of capital, growth, terminal value), relative valuation, real options |
| *Applied Corporate Finance* | Aswath Damodaran | 4th ed. (Wiley, 2014) | WACC, capital structure, dividend policy, project analysis |
| *Financial Statement Analysis and Security Valuation* | Stephen Penman | 5th ed. (McGraw-Hill, 2013) | Accounting-based valuation, reformulated statements, ratio decomposition |
| *Financial Modeling* | Simon Benninga | 4th ed. (MIT Press, 2014) | Excel implementation: pro-forma models, cost of capital, options, Monte Carlo |
| *Building Financial Models* | John Tjia | 3rd ed. (McGraw-Hill, 2018) | Model architecture, balancing the balance sheet, circularity, error checks |
| *Principles of Financial Modelling* | Michael Rees | Wiley, 2018 | Design principles, sensitivity, scenario and risk modelling |
| *Corporate Finance* | Berk & DeMarzo / Brealey, Myers & Allen | 5th ed. 2019 / 14th ed. 2022 | The underlying theory; either is the standard MBA text |
| CFA Program Curriculum — Level I FSA, Level II Equity (FCFF/FCFE, residual income, multiples) | CFA Institute | current | Rigorous definitions of every ratio and DCF variant |

**Free college-level textbooks**
- OpenStax *Principles of Finance* (Rice University, CC-BY): https://openstax.org/details/books/principles-finance — TVM, statements, ratios, capital budgeting, cost of capital.
- Saylor Academy BUS202 *Principles of Finance* (full course, free): https://learn.saylor.org/course/view.php?id=1252
- *Introduction to Financial Analysis* (Open Textbook Library): https://open.umn.edu/opentextbooks/textbooks/1221

**Open university courses**
- NYU Stern, Damodaran — MBA *Valuation* class: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/equity.html ; lecture notes index: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/eqlect.htm ; Spring-2025 syllabus: https://pages.stern.nyu.edu/~adamodar/pdfiles/eqnotes/eqsyllspr25.pdf ; lecture packet 1: https://pages.stern.nyu.edu/~adamodar/pdfiles/eqnotes/packet1a.pdf ; topic notes: `basics.pdf`, `dcfinput.pdf`, `fcff.pdf`, `fcfe.pdf`, `ddm.pdf`, `pe.pdf`, `eva.pdf`, `option.pdf` under https://pages.stern.nyu.edu/~adamodar/pdfiles/
- NYU Stern, Damodaran — *Corporate Finance* class: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/corpfin.html ; lecture notes index: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/cflect.htm ; Spring-2025 syllabus: https://pages.stern.nyu.edu/~adamodar/pdfiles/cfovhds/cfsyllspr25.pdf ; packet 1: https://pages.stern.nyu.edu/~adamodar/pdfiles/cfovhds/cfpacket1.pdf ; YouTube playlist linked from the page
- NYU Stern, Damodaran — Executive valuation class: https://pages.stern.nyu.edu/~adamodar/New_Home_Page/execvaln.html
- MIT OCW 15.401 *Finance Theory I* (video + slides): https://ocw.mit.edu/courses/15-401-finance-theory-i-fall-2008/
- MIT OCW 15.402 *Finance Theory II* (corporate finance, capital structure, valuation cases): https://ocw.mit.edu/courses/15-402-finance-theory-ii-spring-2003/
- MIT OCW 15.414 *Financial Management*: https://ocw.mit.edu/courses/15-414-financial-management-summer-2003/
- MIT OCW 15.535 *Business Analysis Using Financial Statements* (ratios, DCF foundations, earnings quality): https://ocw.mit.edu/courses/15-535-business-analysis-using-financial-statements-spring-2003/
- MIT OCW 15.501 *Introduction to Financial and Managerial Accounting*: https://ocw.mit.edu/courses/15-501-introduction-to-financial-and-managerial-accounting-spring-2004/
- MIT OCW 15.433 *Investments*: https://ocw.mit.edu/courses/15-433-investments-spring-2003/
- Open Yale ECON 252 *Financial Markets* (Shiller): https://oyc.yale.edu/economics/econ-252

**Practitioner knowledge bases (free tutorials with Excel files)**
- Breaking Into Wall Street KB: https://breakingintowallstreet.com/kb/ (direct S3 spreadsheet links; catalogued as source `biws`)
- Macabacus Learn: https://macabacus.com/learn (free demo models catalogued as source `macabacus`)
- Wall Street Prep knowledge: https://www.wallstreetprep.com/knowledge/financial-modeling/ (files behind an email form)
- A Simple Model: https://www.asimplemodel.com (source `asimplemodel`)

---

## 1. Three-statement model  (`finmodel.three_statement`)

**What it is.** One integrated workbook where the income statement, balance sheet and cash-flow
statement are linked so that a change in any assumption flows through all three and the balance
sheet still balances. It is the base layer under every DCF, LBO and merger model.

**How the engine works (CFI structure).**
- Revenue_t = Revenue_{t-1} × (1 + g); COGS and salaries as % of revenue; rent as an amount.
- D&A_t = opening PP&E × rate; PP&E_close = open + capex − D&A.
- Interest_t = average(debt_open, debt_close) × rate; debt_close = open + issuance.
- AR = revenue × days/365; inventory and AP = COGS × days/365; ΔNWC = NWC_t − NWC_{t-1}.
- Net earnings = (gross profit − expenses) × (1 − tax rate); retained earnings roll forward.
- Cash_t = cash_{t-1} + (NI + D&A − ΔNWC) − capex + debt issued + equity issued, and the check
  `Total L&E − Total assets = 0` proves the links.

**Judgement calls.** Days-based working capital vs % of revenue; whether interest uses average
or opening debt (average creates circularity in Excel, not here); which historical years to
average for the forecast ratios; a revolver / cash sweep if cash can go negative (not in CFI's version).

**Learn it.** Pignataro ch. 1–8 (build), Tjia ch. 4–11 (architecture and balancing), Rosenbaum & Pearl
ch. 3 (financial projections inside a DCF), Damodaran corporate-finance packet 1 (statements as inputs),
MIT 15.501 (accounting foundations), MIT 15.535 (reading statements for valuation), OpenStax ch. 5–6.

**Templates.** `asimplemodel/IFS_Simple Three Statement Model.xlsx`, `…/IFS_PPE Schedule.xlsx`,
`macabacus/operating-model.xlsx`, `exinfm/statmnts.xls`, `exinfm/Financial Projections Model v6.8.4.xls`.

---

## 2. Discounted cash flow  (`finmodel.dcf`)

**What it is.** Enterprise value = present value of unlevered free cash flows + present value of a
terminal value; equity value = EV + cash − debt; per-share value vs market price gives the upside.

**How the engine works (CFI structure).**
- UFCF = EBIT × (1 − t) + D&A − capex − ΔNWC.
- Stub period: first flow is scaled by `YEARFRAC(transaction date, first FYE)` (Excel basis 0, US 30/360).
- Terminal value: perpetuity `UFCF_n × (1+g)/(r−g)` and exit multiple `EV/EBITDA × EBITDA_n`; CFI averages them.
- EV = `XNPV(r, [0, UFCF_1·yf_1 … UFCF_n·yf_n, TV], dates)`; IRR from `XIRR` on (−market EV, flows, TV).
- Sensitivity grid over discount rate × growth (`dcf.sensitivity`).

**Judgement calls.** WACC inputs (see §5); g must be below the long-run nominal growth of the economy;
mid-year convention (`DCFInputs.mid_year = True` discounts each period's cash flow from its midpoint,
leaving the terminal value at period end — matches `asimplemodel/DCF_MidYear Convention.xlsx`) vs
end-of-period; reconciling the two terminal methods — the implied exit multiple of the perpetuity TV is
the sanity check; treatment of leases, options, minority interests and non-operating assets in the bridge.

**Reverse DCF and Monte Carlo.** `dcf.implied_growth(inp)` bisects for the perpetual growth rate that
reproduces the current price under the perpetuity terminal method — "what does the market believe?" instead
of "what do I believe?" (stockvaluation-io, governed-dcf-skill). `dcf.monte_carlo(inp, runs=2000)` redraws
discount rate, growth, and EBIT/capex scale factors from normal distributions and reports the distribution
of equity value per share, including the probability the model value exceeds the current price
(EmanueleSturzo's and dafahentra's Monte-Carlo DCFs).

**Learn it.** Damodaran `basics.pdf`, `dcfinput.pdf`, `fcff.pdf`; *Investment Valuation* ch. 12–15;
Koller ch. 8–12 (enterprise DCF, continuing value); Rosenbaum & Pearl ch. 3; Pignataro ch. 9–10;
MIT 15.401 lectures on capital budgeting and equities; MIT 15.402 valuation cases; OpenStax ch. 16–17.

**Templates.** `damodaran/fcffsimpleginzu.xlsx` (the full ginzu), `damodaran/fcffginzu.xlsx`,
`damodaran/fcff2st.xls`, `fcff3st.xls`, `fcffgen.xls`; `asimplemodel/DCF_Discounted Cash Flow Model.xlsx`
and `DCF_MidYear Convention.xlsx`; `exinfm/LBO_DCF_Model.xls`; BIWS DCF case files (see `catalog/catalog.md`).

---

## 3. Bottom-up projection  (`finmodel.projection`)

**What it is.** An FP&A-style operating model: revenue built from units × price per product,
payroll from headcount × hours × wage, opex by category, then rolled into the three statements and a
ratio dashboard. This is the "budget and forecast" model rather than the valuation model.

**How the engine works (CFI structure).** Monthly base year (NETWORKDAYS drives hours), annual
forecast years with growth rates per product / employee type / expense line; bonus pool = 10% of
positive EBIT; taxes only on positive EBT; AR/inventory/AP by days, prepaid and accrued by growth;
PP&E and debt schedules as in §1; 20+ ratios per year.

**Judgement calls.** Driver choice (units vs price vs mix), seasonality, headcount timing, whether
wage expense is gross or net pay (the CFI sheet books net pay — see README), capex as % of revenue vs
a plan, and the four template corrections listed in the README.

**Learn it.** Benninga part I (pro-forma models), Rees ch. 2–6, Tjia; CFI *FP&A Fundamentals* and the
free *Financial Modeling Guidelines* PDF on your dashboard; Saylor BUS202 units on pro-forma statements
and forecasting; MIT 15.414 lecture notes on financial planning.

**Templates.** `exinfm/Financial_model_1.xls`, `exinfm/CashModel1.4.xls` (not downloaded, on the exinfm page),
`macabacus/operating-model.xlsx`, `exinfm/Box IPO Financial Model.xls` (a real-company operating model).

---

## 4. Ratio analysis  (`finmodel.ratios`)

**What it is.** Profitability (margins, ROA, ROE), efficiency (turnover and days: DSO, DIO, DPO,
working-capital funding gap), liquidity (current, quick), leverage (D/E, liabilities/equity,
assets/equity), coverage (EBIT/interest).

**Judgement calls.** Average vs closing balances in turnover ratios; which "debt" (gross, net,
including leases); DuPont decomposition (ROE = margin × turnover × leverage) is the standard extension;
compare against sector benchmarks (Damodaran's industry averages, updated each January).

**Learn it.** Penman ch. 9–12 (reformulation and ratio analysis), MIT 15.535 classes 1–8, CFA Level I
*Financial Statement Analysis* readings, OpenStax ch. 6, CFI *Financial Ratios Definitive Guide* (free download on your dashboard).

**Templates.** `exinfm/Ratio_Tree.xls`, `damodaran/returncalculator.xls`, Damodaran industry datasets
(`betas.xls`, `wacc.xls`).

---

## 5. Cost of capital (inputs to the DCF)  (`finmodel.wacc`)

**What it is.** WACC = E/(D+E) × k_e + D/(D+E) × k_d × (1 − t); k_e from CAPM = r_f + β × ERP (+ size and country
risk); β from regression or bottom-up (unlever each peer at its own D/E and tax rate, average, relever at the
target's D/E); k_d from a supplied pre-tax cost of debt or, for a company without traded debt, a synthetic rating
derived from interest coverage (Damodaran's large-firm / small-firm coverage bands and default spreads).

**Learn it.** Damodaran *Applied Corporate Finance* ch. 4, corporate-finance packet 1; `dcfinput.pdf`;
Koller ch. 15; MIT 15.401 CAPM lectures; OpenStax ch. 15–17; Investopedia *WACC*.

**Templates.** `damodaran/wacccalc.xls`, `ratings.xls` (synthetic rating), `levbeta.xls`, `risk.xls`,
`implprem.xls` (implied ERP), `ctryprem.xlsx` (country premia), `exinfm/betawacc.xls`. Free CFI dashboard
items: *WACC Calculator*, *Beta Calculator*, *Cost of Debt*, *CAPM Formula*, *Market Risk Premium*.

**Try it.** `finmodel wacc examples/wacc_stld.json` — CAPM cost of equity, a synthetic AAA/A+/… rating from
EBIT/interest coverage, and the market-value-weighted WACC, feeding `dcf.DCFInputs.discount_rate` directly.

---

## 6. Leveraged buyout  (`finmodel.lbo`)

**What it is.** Buy a company with mostly debt, run the operating model for 5–7 years, pay debt down
from free cash flow, exit at a multiple, and solve for the sponsor's IRR / MOIC. Core mechanics:
sources & uses, purchase-price allocation and goodwill, tranched debt schedule with cash sweep,
PIK interest, management rollover, returns attribution.

**How the engine works.** Tranches sized as EBITDA multiples (or amounts) with rate, scheduled amortisation, PIK share, sweep share and warrant equity; closing balance sheet with goodwill = seller proceeds − book equity, fees capitalised, transaction expenses through retained earnings; depreciation waves per capex vintage; revolver against a minimum cash balance; exit at a multiple; XIRR on dated flows for the sponsor and each lender; scenario × exit-multiple table. Reconciled to the A Simple Model workbook.

**Learn it.** Rosenbaum & Pearl ch. 4–5, Pignataro part III, BIWS "Simple LBO model" tutorial
(https://breakingintowallstreet.com/kb/leveraged-buyouts-and-lbo-models/simple-lbo-model-excel/),
Macabacus LBO tutorials (https://macabacus.com/learn), Damodaran `lboval.xls` for the valuation view.

**Templates.** `macabacus/lbo-model-long-form.xlsx` and `lbo-model-short-form.xlsx`,
`asimplemodel/LBO_Simple LBO Scenarios and Data Tables.xlsx`, `LBO II Common_Preferred.xlsx`,
`exinfm/LBO Model Template.xls`, `damodaran/lboval.xls`.

---

## 7. Merger / M&A model  (`finmodel.merger`)

**What it is.** Combine acquirer and target statements, fund the deal (cash / debt / stock),
adjust for purchase accounting (asset write-ups, goodwill, new D&A), synergies and transaction fees,
then test accretion / dilution of EPS and the pro-forma leverage.

**How the engine works.** Deal level: purchase equity = target market cap × (1 + premium); funding split cash / debt / stock; combined NI = (EBT_A + EBT_B − cash × foregone rate − debt × cost of debt + synergies − fees) × (1 − t); new shares = stock consideration ÷ acquirer price; accretion = combined EPS − standalone EPS. Multi-year: PPA (write-ups, new DTL, goodwill), synergies with realisation, integration costs, new-debt interest and amortisation, adjusted EPS. Reconciled to the BIWS workbook.

**Learn it.** Rosenbaum & Pearl ch. 6–7, Damodaran `synergyvaluation.xls` and *The Value of Synergy* paper,
BIWS merger-model tutorial (https://breakingintowallstreet.com/kb/ma-and-merger-models/merger-model/),
Koller ch. 31 (mergers and acquisitions).

**Templates.** `macabacus/merger-model.xlsx`, `exinfm/Combination Template.xls`, `damodaran/synergyvaluation.xls`,
`damodaran/controlvalue.xls`.

---

## 8. Comparable companies and precedent transactions  (`finmodel.comps`)

**What it is.** Relative valuation: pick peers, spread their equity value (price × diluted shares) and enterprise
value (equity + debt + preferred + NCI − cash), compute EV/Revenue, EV/EBITDA, EV/EBIT and P/E for LTM and forward
years (negative or ≥100x multiples are "NM"), take max / 75th / median / 25th / min (Excel-inclusive quartiles), apply
the range to the target's metrics, bridge implied EV to equity (cash, NOLs, investments add; debt, preferred, NCI,
pensions, leases subtract) and divide by diluted shares; precedents do the same with deal EV, LTM metrics and the
offer premium over the 1-day / 1-week / 1-month undisturbed price; the football field lays the low–high ranges of every
method beside DCF and the 52-week range. Reconciled cell-for-cell to BIWS 107-21 (Steel Dynamics), BIWS 107-27 (Jazz
precedents) and the CFI *Comps, Precedents, Football Field* template (`tests/test_comps.py`).

**Learn it.** Rosenbaum & Pearl ch. 1–2, Damodaran `pe.pdf` and *Investment Valuation* ch. 17–20, Investopedia
*Comparable Company Analysis* and *Precedent Transaction Analysis*, Wall Street Prep's trading-comps and
precedent-transactions lessons, Macabacus valuation pages (`catalog/analysis_intent.json` holds the links).

**Templates.** `exinfm/Comparable Companies (NON-FDS).xls`, `damodaran/eqmult.xls`, `firmmult.xls`, BIWS
`107-21-Comparable-Company-Analysis.xlsx` and `107-27-*-Precedent-Transactions.xlsx`, CFI *Comparable Company
Analysis*, *Valuation Model – Comps, Precedents, Football Field*, *Pharmaceuticals / Retail Industry Comps*.

**Try it.** `finmodel comps examples/comps_stld.json`; `finmodel charts comps …`; on real filings:
`python scripts/comps_validation.py` (see `docs/VALIDATION_REAL_DATA.md`). To see the *full* CFI football-field
template — comps + precedents + DCF + 52-week range together — checked against a real company's actual price,
`python scripts/football_field_stld.py` (`docs/FOOTBALL_FIELD_STLD.md`, steel),
`python scripts/football_field_cvx.py` (`docs/FOOTBALL_FIELD_CVX.md`, oil & gas — a different sector, a genuinely
different result), `python scripts/football_field_csco.py` (`docs/FOOTBALL_FIELD_CSCO.md`, enterprise
technology — a third, much lower-cyclicality sector), and `python scripts/football_field_usb.py`
(`docs/FOOTBALL_FIELD_USB.md`, banking — a fourth sector where the template's own EV/EBITDA framework doesn't
apply at all, and the right fix is different multiples entirely, not just different assumptions). §5 of each
document also checks the sector-tuning in `finmodel.sectors` below.

---

## 8a. Health and quality scores  (`finmodel.scores`)

Altman Z (1968 public, 1983 private Z′ and non-manufacturing Z″), Beneish M (8 variables, −1.78 threshold) and
Piotroski F (9 signals) from two fiscal years of statements — the screens every open-source fundamental
screener ships and the CFI *Financial Analysis* templates approximate with ratio dashboards. Learn it from the
original papers (Altman 1968 / 2000 update, Beneish 1999, Piotroski 2000) and Investopedia's entries.
`finmodel scores examples/scores_stld.json`.

## 8b. Institutional costing and resource allocation  (`finmodel.costing`)

From the EUA–ATHENA *Toolkit for Financial Management*: formula-based resource allocation with top-slicing and
strategic pots, two-step driver-based cost allocation (students, person-years, effective work time, m²) with
indirect-cost rates on grossed-up salary (Helsinki: 53–55% add-on, 84–150% indirect rates), full-economic-cost
pricing of a project, and an income-diversification scan (shares, Herfindahl index, priority ranking).
`finmodel costing examples/costing_university.json`.

## 8c. Real statements from SEC EDGAR  (`finmodel.edgar`)

`edgar.fetch(cik, user_agent)` + `edgar.annual()` turn the public company-facts API into annual rows (tag precedence
per fiscal year, latest filing wins, EBIT derived from pre-tax + net interest when a filer omits it). This is what
feeds `scripts/ma_case_study.py` — Microsoft/Activision, Chevron/Hess, Cisco/Splunk before and after — and the comps
validation. Read `docs/CASE_STUDY_MA.md` for what a static merger model can and cannot tell you.

## 8c-i. Sector-aware cycle tuning  (`finmodel.sectors`)

**What it is.** `docs/FOOTBALL_FIELD_STLD.md` and `docs/FOOTBALL_FIELD_CVX.md` both found the same problem from
opposite directions: a single trailing fiscal year's EBITDA can sit anywhere in a company's own multi-year earnings
cycle, and a trading-comps or precedent-transaction multiple built on it is silently too rich (a cycle trough —
steel's 2025) or too cheap (a cycle peak — the oil & gas precedent targets' pre-deal years) depending on where that
year happens to fall. `finmodel.sectors` formalizes the fix directly from that finding, using a company's own
`finmodel.edgar` history rather than an industry-wide assumption:

- `cycle_diagnostics(history, sector=...)` — compares the latest fiscal year's margin to its own trailing multi-year
  median and flags trough / peak / near-normal. Regression-tested against the real committed data: it correctly
  flags STLD's FY2025 as a trough, Pioneer Natural Resources' FY2022 as a peak, and Cisco's FY2026 as near normal —
  the exact readings the football-field docs found by hand.
- `dcf_scenarios_from_history(history)` — data-driven bear/base/blue-sky EBIT-margin targets (trailing minimum /
  median / maximum) instead of a hand-picked "toward last year's level" assumption, which the STLD check found
  had materially understated the true historical peak margin by picking too short a lookback.
- `normalized_comps_metrics(history, sector=...)` — a metrics dict with through-cycle-normalized EBITDA/EBIT ready
  to feed `finmodel.comps.Peer`/`Target`, leaving revenue and net income at the latest year.
- `trend_diagnostics(history)` — the guard the enterprise-tech check (`docs/FOOTBALL_FIELD_CSCO.md`) added: it
  distinguishes a genuine secular trend (Salesforce's margin moving ~2%→20% over 8 years as it shifted from
  growth-at-all-costs to profitability — real, deliberate, not something that will mean-revert) from noisy or
  mean-reverting cyclicality, using the correlation between margin and time. `cycle_diagnostics()` calls it
  automatically and appends a CAUTION to its flag when the trend is strong, because trailing-median normalization
  is the wrong tool for a company on a real secular trend — it would misread a sustainable, improved margin as a
  misleading cyclical peak and understate its multiple.
- `sector_beta(sector)` — an illustrative, Damodaran-style unlevered beta by sector, a starting point when a
  company-specific beta isn't available.

Every function above takes `field`/`revenue_field` parameters (default `"operating_income"`/`"revenue"`, an EBIT
margin) that can be pointed at any other ratio — the banking check (`docs/FOOTBALL_FIELD_USB.md`) uses
`field="net_income", revenue_field="equity"` to get ROE cyclicality instead, because a bank's standard
revenue/EBIT tags turned out to be meaningless (see §8c-ii below): the same module, a different ratio.

Four sectors (`"steel"`, `"oil_gas"`, `"software"`, `"banking"`) are tuned against real multi-year data so far, each
with a `SECTOR_PROFILE` entry documenting exactly what real range justified its thresholds; every other sector
falls back to a clearly labelled `"default"` rather than a fabricated industry assumption. All four football-field
docs' §5 rebuild part or all of their football field with this normalization and compare it to the raw run: at
STLD it didn't close the gap (the whole peer set shares the same trough, so normalizing both sides of the trade
moves them together); at Chevron it did change the answer (only the precedent-deal *targets* were cycle-distorted,
not Chevron itself, so correcting just that one input pushed the precedent-implied range past the price); at Cisco
the script had to add the trend guard mid-way through, because Salesforce's peer data would otherwise have been
normalized straight into a misleading number — and even Cisco's own tight-range margin turned out to carry a real
(if gentle) trend, which is not the same statistical property as a wide cyclical range; at US Bancorp the module
was pointed at ROE instead of EBIT margin entirely, and correctly found a real, credit-cycle-driven trough in
FY2020 (the COVID loan-loss reserve build) using a completely different underlying mechanism from a commodity
price cycle.

**Try it.** `finmodel cycle data/edgar/STLD.json --sector steel`; for a bank,
`finmodel cycle data/edgar/USB.json --sector banking --field net_income --revenue-field equity`.

## 8c-ii. Bank-appropriate valuation: P/B, P/TBV and residual income  (`docs/FOOTBALL_FIELD_USB.md`)

**What it is.** The fourth football-field check (US Bancorp) leads with a negative finding, not a positive one:
`finmodel.edgar`'s revenue/operating-income extraction is built for an industrial income statement and gives
nonsense for a real bank filer — SunTrust's own FY2018 10-K shows "operating income" ($4,638M) *exceeding*
"revenue" ($3,226M), because a bank's core economics (net interest income = interest income − interest expense,
plus fee income) don't map onto a cost-of-goods-sold structure at all. "Enterprise value" fares no better: a
bank's balance-sheet "debt" is overwhelmingly customer deposits funding the loan book, not financing debt, so
`equity + debt − cash` is not a meaningful number.

The fix isn't a new engine — it's choosing the right multiples and the right DCF-equivalent, both of which
`finmodel.comps` and `finmodel.residual_income` already support generically:

- **Comps and precedents**: P/B, P/TBV, P/E — all equity-numerator multiples (`("equity", "book_value")` etc. in
  `finmodel.comps`'s multiples mapping), no EV, no EBITDA. Tangible book value = equity − goodwill − intangibles.
- **DCF-equivalent**: residual income (net income − cost of equity × book value), the textbook-correct approach
  for a bank, using `finmodel.residual_income` with the cost of equity (not the full debt-weighted WACC — see
  `finmodel wacc examples/wacc_usb.json`, which passes `debt=0` for exactly this reason).

**Learn it.** CFA Level II bank-valuation readings; Damodaran's "valuing financial service firms" chapter
(*Investment Valuation*); Investopedia's *Price-to-Book Ratio* and *Residual Income* entries.

**Try it.** `python scripts/football_field_usb.py` — real precedent deals (BB&T/SunTrust, Huntington/TCF) both
priced near or below tangible book value, the opposite of the control-premium-heavy tech and steel precedents.

## 8d. Residual income and EVA valuation  (`finmodel.residual_income`)

**What it is.** Two ways to value equity or a firm from accounting numbers instead of cash-flow projections,
useful when free cash flow is negative or lumpy but earnings and book value are stable:

- **Residual income (Edwards–Bell–Ohlson)**: RI_t = NI_t − k_e × B_{t−1}; equity value = B_0 + Σ PV(RI_t) +
  PV(terminal RI). Clean-surplus accounting rolls book value forward (B_t = B_{t−1} + NI_t − dividends_t), so
  most of the value shows up immediately as B_0 and RI captures only the *excess* over the cost of equity —
  a useful cross-check against a DCF, since the two agree exactly under consistent assumptions.
- **EVA / economic profit**: EVA_t = NOPAT_t − WACC × invested capital_{t−1}; firm value = capital_0 +
  Σ PV(EVA_t) + PV(terminal EVA); equity = firm value − net debt. The firm-level analogue of residual income.

Terminal value is either a fading-persistence factor (ω, common for cyclical earnings — RI shrinks toward zero
rather than growing forever) or a Gordon-style growing perpetuity.

**Learn it.** CFA Level II residual-income and EVA readings; Penman *Financial Statement Analysis* ch. 5, 14–15;
jimlindstrom/FinModeling's residual-operating-income model (Ruby, reformulates EDGAR statements the same way);
Investopedia *Residual Income Valuation* and *Economic Value Added*.

**Try it.** `finmodel residual-income examples/residual_income_stld.json` — Steel Dynamics book value and a
4-year net-income projection, discounted at cost of equity from `finmodel wacc`.

## 8e. Sum-of-the-parts  (`finmodel.sotp`)

Value a multi-segment or holding company by valuing each piece on its own terms — a multiple on its own metric,
or an override value (a quoted market cap for a listed subsidiary, a DCF, a net-asset value) — weighted by
economic ownership, then subtract capitalised unallocated corporate costs, apply an optional conglomerate
discount, and bridge enterprise value to equity value per share. Mirrors the SOTP tabs in agentii and
governed-dcf-skill and Damodaran's "valuing a multi-business company" method (*Investment Valuation* ch. 24).

**Try it.** `finmodel sotp examples/sotp_conglomerate.json` — an industrial segment on EV/EBITDA, a
financial-services segment on a book-value multiple, and a 55%-owned listed subsidiary at its quoted market cap.

## 8f. Workbook audit  (`finmodel.audit`)

The quality checks a model-review checklist runs before trusting a workbook (CFI's modelling guidelines,
3-statement-ultra's 19 QC checks, agentii's audit-xls skill): cached error values (#REF!, #DIV/0!, …),
hard-coded numbers inside formulas ("plugs" — a constant other than 0/1/−1/100/12/365/…), a typed number
sitting inside an otherwise-formula row, a formula whose R1C1-normalised pattern breaks from its row's
dominant pattern, external workbook links, and hidden/very-hidden sheets. `--recompute` adds a full
`xlcalc.verify()` pass. Run on the 15,323-formula Macabacus merger model, it found 112 findings — 78 hard-coded
plugs and one `very Hidden` `__FDSCACHE__` sheet — while the recompute check still reported a 100% match rate,
which is the point: a workbook can recalculate perfectly and still be full of undocumented assumptions.

`finmodel audit path/to/workbook.xlsx --recompute --markdown-out out/audit.md`.

---

## 9. Capital budgeting (NPV / IRR / payback) and options

Project appraisal is the same maths as the DCF applied to one project: `finmodel.fin.npv/irr/xnpv/xirr/pmt`.
Learn it from OpenStax ch. 16, MIT 15.401 capital-budgeting lectures, Damodaran corporate-finance packet 2,
Brealey–Myers ch. 5–10. Templates: `damodaran/capbudg.xls`, `exinfm/npv_irr.xls`, `damodaran/apv.xls`.
Option pricing (Black–Scholes, binomial, real options): Damodaran `option.pdf`, templates `optst.xls`,
`optlt.xls`, `warrant.xls`, `expand.xls`, `delay.xls`, `abandon.xls`, `natres.xls`.

---

## 10. Where the industry-standard titles on the CFI paid tier are covered elsewhere

`catalog/alternatives.md` (generated by `finmodel catalog alternatives`) maps every one of the 127
paid-only CFI titles — LBO Model, M&A Model, Trading/Transaction Comps, Bank & FIG model, REIT model,
SaaS model, Debt Capacity, Scenario & Sensitivity, Dividend Discount Model, FCFF vs FCFE, … — to the
closest public files from Damodaran, A Simple Model, Macabacus, BIWS and exinfm, using model-type tags.
