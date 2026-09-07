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
technology — a third, much lower-cyclicality sector), `python scripts/football_field_usb.py`
(`docs/FOOTBALL_FIELD_USB.md`, banking — a fourth sector where the template's own EV/EBITDA framework doesn't
apply at all, and the right fix is different multiples entirely, not just different assumptions), and
`python scripts/football_field_o.py` (`docs/FOOTBALL_FIELD_O.md`, REITs — a fifth sector where EV/EBITDA is
computable but P/E isn't the right equity multiple; also surfaces a real blind spot in `finmodel.sectors`
itself, see 8c-iii below), `python scripts/football_field_alk.py` (`docs/FOOTBALL_FIELD_ALK.md`, airlines —
a sixth sector where EV/EBITDA is directionally fine but needs a real lease adjustment (EV/EBITDAR); also finds
a real black-swan trap in `finmodel.sectors`' usual periods=8 default, see 8c-iv below), and
`python scripts/football_field_trv.py` (`docs/FOOTBALL_FIELD_TRV.md`, P&C insurance — a seventh sector where
EV/EBITDA fails for yet another reason, and where BOOK VALUE itself, not the multiple or earnings, turns out to
be the thing that's rate-exposed; see 8c-v below), and `python scripts/football_field_txn.py`
(`docs/FOOTBALL_FIELD_TXN.md`, semiconductors — an eighth sector where EV/EBIT is directionally right but GAAP
R&D expensing understates it; see 8c-vi below), and `python scripts/football_field_duk.py`
(`docs/FOOTBALL_FIELD_DUK.md`, regulated utilities — a ninth, deliberately low-cyclicality sector where the
standard EV-based framework needs no fix at all, but a thin, structurally-negative-in-places unlevered free
cash flow makes the DCF's terminal-growth assumption the whole ballgame; see 8c-vii below), and
`python scripts/football_field_abbv.py` (`docs/FOOTBALL_FIELD_ABBV.md`, pharmaceuticals — a tenth sector where
a real GAAP quirk (acquired IPR&D write-offs) distorts the margin trend until added back, and a real patent
cliff turns out not to be existential for a diversified major with a real, funded pipeline; see 8c-viii below).
§5 of each document also checks the sector-tuning in `finmodel.sectors` below.

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
revenue/EBIT tags turned out to be meaningless (see §8c-ii below); the REIT check (`docs/FOOTBALL_FIELD_O.md`)
uses `field="ffo", revenue_field="revenue"` (FFO margin) instead, since FFO — not net income — is what a REIT
is actually priced on (see §8c-iii below). The airline check (`docs/FOOTBALL_FIELD_ALK.md`, §8c-iv below) is the
one sector so far where the DEFAULT `operating_income`/`revenue` is already the right call — no override needed —
but it needed `periods=5` instead of the usual `periods=8`, because the wider window's trailing minimum is
FY2020's pandemic-collapse margin, not a usable "bear case." The insurance check (`docs/FOOTBALL_FIELD_TRV.md`,
§8c-v below) reuses banking's exact ROE override (`field="net_income", revenue_field="equity"`) — the first time
two independently-checked sectors have shared an override rather than each needing its own.

Ten sectors (`"steel"`, `"oil_gas"`, `"software"`, `"banking"`, `"reit"`, `"airline"`, `"insurance"`,
`"semiconductor"`, `"utility"`, `"pharma"`) are tuned against real multi-year data so far, each with a
`SECTOR_PROFILE` entry documenting exactly what real range justified its thresholds; every other sector falls
back to a clearly labelled `"default"` rather than a fabricated industry assumption. All ten football-field
docs' §5 rebuild part or all
of their football field
with this normalization and compare it to the raw run: at STLD it didn't close the gap (the whole peer set shares
the same trough, so
normalizing both sides of the trade moves them together); at Chevron it did change the answer (only the
precedent-deal *targets* were cycle-distorted, not Chevron itself, so correcting just that one input pushed the
precedent-implied range past the price); at Cisco the script had to add the trend guard mid-way through, because
Salesforce's peer data would otherwise have been normalized straight into a misleading number — and even Cisco's
own tight-range margin turned out to carry a real (if gentle) trend, which is not the same statistical property as
a wide cyclical range; at US Bancorp the module was pointed at ROE instead of EBIT margin entirely, and correctly
found a real, credit-cycle-driven trough in FY2020 (the COVID loan-loss reserve build) using a completely
different underlying mechanism from a commodity price cycle; at Realty Income the module was pointed at FFO
margin and correctly found *no* cycle — which turned out to be the real finding, because the actual cycle lives
entirely in the market P/FFO multiple (12.5x-18.7x with the interest-rate cycle), somewhere this fundamentals-only
module has no visibility into at all; at Alaska Air Group the module's usual `periods=8` window returned a bear
case that was literally the FY2020 pandemic collapse — not a plausible recurring low, since a company can't
sustain that margin for 5 years and still exist — and a short trend window ending right after that same crash
separately fooled `trend_diagnostics()` into flagging a "strong declining trend" that a longer, recovery-inclusive
window correctly resolved back to none; at Travelers the module was pointed at ROE (the same override as US
Bancorp) and correctly flagged a real "peak" — verified this wasn't a false positive from FY2022's AOCI-driven
book-value shrinkage alone, since the trend holds up even in 2024-2025, after book value had fully recovered.

**Try it.** `finmodel cycle data/edgar/STLD.json --sector steel`; for a bank,
`finmodel cycle data/edgar/USB.json --sector banking --field net_income --revenue-field equity`; for a REIT,
`finmodel cycle data/edgar/O.json --sector reit --field ffo --revenue-field revenue`; for an airline (note
`--periods 5`, not the default 8), `finmodel cycle data/edgar/ALK.json --sector airline --periods 5`; for an
insurer (the same ROE override as banking), `finmodel cycle data/edgar/TRV.json --sector insurance --field
net_income --revenue-field equity`.

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

## 8c-iii. REIT-appropriate valuation: P/FFO, a dividend discount model, and a real gap in the sector-tuning tool  (`docs/FOOTBALL_FIELD_O.md`)

**What it is.** The fifth football-field check (Realty Income) leads with a different negative finding from
banking's: a REIT's enterprise value *is* computable, but its most familiar equity multiple — P/E — is badly
misleading. Real estate depreciation is a large non-cash GAAP charge against an asset that, unlike a factory,
usually appreciates, so GAAP net income understates cash-generating reality by an inconsistent amount peer to
peer. Verified across six real net-lease REITs (Realty Income + NNN, W. P. Carey, Agree Realty, Essential
Properties, Four Corners) on real FY2025 SEC EDGAR data: P/E ranges 22.9x-54.3x, while P/FFO (funds from
operations = net income + real-estate D&A, the Nareit-standard non-GAAP metric analysts actually price REITs on)
sits in a much saner 13.6x-19.4x band across the SAME six companies.

- **Comps and precedents**: P/E and P/FFO — both equity-numerator multiples, reusing `finmodel.comps` exactly as
  the banking check's P/B/P/TBV/P/E did (no new engine code). FFO here is a proxy (net income + D&A): Nareit's
  official definition also excludes gains/losses on real-estate sales, and AFFO (which further backs out
  straight-line rent and recurring capex) has no standardized XBRL tag across filers at all — a real
  data-availability ceiling, not something this toolkit patches around.
- **DCF-equivalent**: a two-stage dividend discount model (Gordon growth), since REITs must distribute ≥90% of
  taxable income as dividends — the dividend stream is the natural cash-flow-to-equity proxy here, more directly
  than for a non-REIT. Growth scenarios come from Realty Income's own real dividend-per-share history: an
  11-year CAGR of ~3.55%/yr (blue sky) versus a decelerating trailing-3-year CAGR of ~2.77%/yr (bear case), real
  and driven by the ~4x share-count dilution from stock-funded M&A (the VEREIT and Spirit Realty deals below).
- **Net debt isn't needed** for either multiple (both are equity-numerator), which turned out to matter: verified
  that `finmodel.edgar`'s debt tags return `None` for the target and 2 of 5 peers in FY2025 — Realty Income's own
  aggregate `LongTermDebt` tag stopped being populated after FY2016, replaced by disaggregated
  `SecuredDebt`/`UnsecuredDebt`/`NotesPayable` tags that are additive components, not fallback alternatives, so
  summing them needs a different `TAGS` design than this module's first-tag-wins tuples. This is real
  filer-by-filer variation, not a sector-wide gap: the other 3 of 5 peers still report a populated `debt_total`.

**A real gap this check found in `finmodel.sectors` itself, not in the target company.** Pointing
`cycle_diagnostics()` at FFO margin (`field="ffo", revenue_field="revenue"`) correctly reports "near normal" with
a weak/no trend for Realty Income over FY2018-2025 — the fundamental really was that stable. But Realty Income's
real year-end P/FFO trading multiple swung 12.5x-18.7x over the exact same window, compressing hardest exactly
when the Fed hiked rates. `cycle_diagnostics()` isn't wrong here; it simply has no way to see this, because it
only ever looks at a company's own EDGAR fundamentals history, never its market price or trading multiple — and
for a REIT, the real cycle lives almost entirely in the multiple, driven by the risk-free rate, not in anything
the fundamentals show. Worth remembering on any sector: a "near normal" fundamentals reading is not the same
claim as "nothing cyclical is happening to the valuation."

**Learn it.** Nareit's FFO/AFFO white paper and definitions; Damodaran's "valuing real estate/REITs" material;
Investopedia's *Funds From Operations* and *Dividend Discount Model* entries.

**Try it.** `python scripts/football_field_o.py` — both real precedent deals (Realty Income/VEREIT, Realty
Income/Spirit Realty) priced below the peer P/FFO trading range, and `finmodel cycle data/edgar/O.json --sector
reit --field ffo --revenue-field revenue` to see the "near normal" reading for yourself.

## 8c-iv. Airline-appropriate valuation: EV/EBITDAR, and a black-swan trap in the sector-tuning tool  (`docs/FOOTBALL_FIELD_ALK.md`)

**What it is.** The sixth football-field check (Alaska Air Group) is different in kind from the banking and REIT
checks: EV/EBITDA isn't meaningless for an airline, and net income isn't systematically distorted the way it is
for a REIT — the gap is narrower and more familiar to credit analysts. An airline that owns its fleet shows that
cost as debt + depreciation, both already inside EV/EBITDA; one that leases it shows an operating expense that
reduces EBITDA with, pre-ASC-842, nothing added to EV to compensate. ASC 842 (FY2019+) put the real operating
lease liability on the balance sheet; `finmodel.edgar` now extracts it (`operating_lease_liability_current`/
`_noncurrent`, `operating_lease_cost`). Verified real, FY2025: EV/EBITDAR (EBITDA + operating lease cost; EV +
the real lease liability) compresses the multiple 1-22% across 4 of 5 peers — largest for JetBlue, whose thin
EBITDA makes the add-back matter proportionally the most.

A real, quoted piece of history ties this to the old convention directly: Alaska's 2016 acquisition of Virgin
America (pre-ASC-842) had its own press release state the "aggregate transaction value" was "inclusive of...
capitalized aircraft operating leases" — backing that figure out against Virgin America's own real disclosed
rent expense gives an implied capitalization multiple of ~7x, landing almost exactly on the classic "7-8x annual
rent" rule of thumb credit analysts used before operating leases were required on the balance sheet.

A real filer-level data gap, not smoothed over: Southwest's own XBRL filing doesn't disaggregate operating lease
cost from finance/short-term/variable lease cost — its aggregate `LeaseCost` tag is dominated (~84%) by variable
lease cost (airport/gate fees ASC 842 expenses as incurred, with no matching capitalized liability), so folding
it into an EBITDAR add-back would badly overstate Southwest's multiple relative to peers with a clean tag.
`finmodel.edgar` keeps `operating_lease_cost`/`total_lease_cost`/`variable_lease_cost` as three separate fields
for exactly this reason, rather than silently falling back from one to another.

**A real second data-quality trap found and fixed while building this check**: some filers (again, Alaska)
report real total capex split across asset-class-specific tags (`PaymentsForFlightEquipment` for aircraft,
`PaymentsToAcquireOtherPropertyPlantAndEquipment` for everything else) that are ADDITIVE, not alternatives for
the same figure — using flight-equipment capex alone understated Alaska's real FY2024 capex by ~26%. Fixed the
same way `debt_total` already handles the REIT check's analogous debt-tag fragmentation: sum the components when
the primary aggregate tag is absent, rather than picking one and calling it done.

**A real methodological trap in `finmodel.sectors` itself, not in the target company**: `dcf_scenarios_from_
history()`'s usual `periods=8` default returns a bear_margin of -49.8% for Alaska — literally FY2020's pandemic
collapse, not a plausible recurring bear case (a company sustaining that margin for 5 years would be bankrupt,
not bearish). `periods=5` (the post-recovery years only) gives a real, usable 0.7%/3.8%/11.1% bear/base/blue-sky
instead. A second, related trap: `trend_diagnostics()` on a 5-year window ending right after the crash
(`as_of='2020-12-31'`) fires a "strong declining trend" (r=-0.80) — a real result, but a misleading one, since it
reflects one catastrophic data point dragging a short window's correlation, not a genuine multi-year structural
decline the way Salesforce's software-check trend was. The SAME company's 8-year window ending FY2025 (which
includes the recovery) correctly resolves this back to "weak/none" (r=0.11). A correlation coefficient cannot,
by construction, distinguish "gradual structural decline" from "stable, then one cliff" — both can show a strong
|r| over a short-enough window ending right after the discontinuity.

**Learn it.** Moody's/S&P airline and retail credit-analysis methodology on EV/EBITDAR and rent capitalization;
ASC 842 (Topic 842, Leases) transition guidance; Investopedia's *EBITDAR* entry.

**Try it.** `python scripts/football_field_alk.py` — both real precedent deals (Alaska/Virgin America,
Alaska/Hawaiian Holdings) are all-cash, simpler to verify than the exchange-ratio deals in the banking/REIT
checks, and `finmodel cycle data/edgar/ALK.json --sector airline --periods 5` to see the COVID-year exclusion
matter for yourself.

## 8c-v. Insurance-appropriate valuation: book value is what's rate-exposed, not the multiple or earnings  (`docs/FOOTBALL_FIELD_TRV.md`)

**What it is.** The seventh football-field check (Travelers) shares banking's conclusion (EBITDA doesn't apply,
use P/B/P/TBV/P/E) but for a genuinely different reason, and its headline finding is new, not a repeat of any
prior check. Real evidence EV/EBITDA breaks for a P&C insurer: Chubb reports no `da`/`ebitda` tag at all, and
W. R. Berkley's own `da` value is genuinely NEGATIVE (real, FY2025) because `finmodel.edgar`'s preferred D&A tag
(`DepreciationAmortizationAndAccretionNet`) bundles in bond-portfolio premium/discount accretion for a filer
with a large investment book — a different root cause from a bank's revenue-tag mismatch, same fix.

The real, sector-defining finding: verified across five real P&C peers (Travelers, Chubb, Allstate, Progressive,
Cincinnati Financial) that EVERY ONE showed a real book-value-per-share DECLINE in FY2022 (-9% to -23%) during
that year's historic bond-market selloff — even though three of five stayed solidly net-income-positive. This is
mechanistically new: a REIT's operating fundamental stayed flat while its trading MULTIPLE moved with rates; a
bank's credit losses hit book value AND earnings together. An insurer's available-for-sale bond portfolio marks
to fair value through OCI (equity), not net income, under GAAP — book value and earnings can genuinely decouple
in a way they structurally cannot for a bank's amortized-cost loan book.

**A real, connected trap for this sector's ROE override** (`field="net_income", revenue_field="equity"` — the
same one banking established, the first time two checked sectors have shared an override): Travelers' own
measured ROE actually ROSE in FY2022, purely because the book-value denominator shrank from the same AOCI hit,
not because performance improved. Checked, not assumed, that the module's broader "strong improving trend" flag
on TRV's real ROE isn't just this artifact: 2024-2025's ROE — the highest in the whole series — comes after book
value had already recovered well past its pre-2022 peak, so the underlying trend is real, sustained profitability
improvement (a harder P&C pricing market, higher rates flowing through to investment income), the same kind of
genuine secular trend the software check's guard exists to protect (there, Salesforce's margin expansion; here,
Travelers' ROE expansion — same guard, opposite-looking but equally real trend, different sector entirely).

**A real, unrelated bonus finding surfaced while building this check**: W. R. Berkley's own
`WeightedAverageNumberOfDilutedSharesOutstanding` was filed at roughly 1/1000th its real scale for FY2017-2022 —
a real, persistent XBRL filer error, verified directly against SEC's live API. `finmodel.edgar`'s "latest filing
wins" logic only self-heals a bad figure while that period still appears as a comparative column in some later
10-K; FY2023's identical error WAS corrected this way, but FY2017-2022 have since aged out of every subsequent
filing's comparative window and remain wrong in SEC's own live data today — a reason to sanity-check per-share
figures against neighboring years rather than trust a single filed value at face value.

Real precedents, both simpler than exchange-ratio deals: AIG/Validus Holdings (2018, all-cash $68.00/share —
Validus's FY2017 net income was genuinely negative, a real catastrophe-loss year from Hurricanes Harvey/Irma/
Maria, so its P/E is correctly NM) and Berkshire Hathaway/Alleghany Corporation (2022, all-cash $848.02/share).
DCF-equivalent: residual income (`finmodel.residual_income`), the exact same generic tool the banking check
validated, now confirmed on a second, independent financial-services sector.

**Learn it.** GAAP ASC 320/326 (available-for-sale securities, OCI treatment); Damodaran's "valuing financial
service firms" chapter; Investopedia's *Book Value* and *Combined Ratio* entries.

**Try it.** `python scripts/football_field_trv.py` — both real precedent deals priced at 1.5x+ tangible book
value, the opposite of the banking check's precedents (which priced near or below it); and `finmodel cycle
data/edgar/TRV.json --sector insurance --field net_income --revenue-field equity` to see the real "peak" flag on
a genuinely improving trend.

## 8c-vi. R&D capitalization: EV/EBIT understates an R&D-intensive company  (`finmodel.rd_capitalization`, `docs/FOOTBALL_FIELD_TXN.md`)

**What it is.** The eighth football-field check (Texas Instruments) is the second sector (after airlines) where
the default `operating_income`/`revenue` fields are already correct — the gap isn't which fields to use, it's
that GAAP expenses R&D immediately even though it creates a multi-year economic asset (chip designs) the same
way capex does. `finmodel.rd_capitalization` (new) capitalizes each historical year's R&D as its own vintage,
straight-line-amortized over an assumed useful life (5 years for semiconductors) — `amortization_schedule()`
reconciles exactly to CFI's real `RD-Capitalization.xlsx` single-vintage template, then `capitalize_rd()`
generalizes it to Damodaran's cross-sectional method (every vintage amortizing simultaneously; the current
year's own spend hasn't amortized at all yet).

Real, verified uplift across five of six real peers with growing R&D budgets (TXN +6.1% to SWKS +43.0%);
ON Semiconductor is the real counter-example (its own R&D spend has declined since FY2021, so capitalizing it
LOWERS adjusted EBIT). The same adjustment compresses both real 2019 all-cash precedent deals (NVIDIA/Mellanox,
Infineon/Cypress) from ~60x raw EV/EBIT to ~38-40x once each target's own real R&D history is capitalized — and
recovers Microchip's raw multiple from `NM` (>=100x) entirely, a real bonus of the adjustment beyond simple
compression. Also: TXN's own real capex/revenue (25.7%, a disclosed capacity-expansion supercycle) needed the
same flat-vs-normalized DCF fix the airline check's fleet-renewal capex needed.

**Learn it.** Damodaran's R&D-capitalization research and "Value of Growth" material; CFI's `RD-Capitalization`
template; Investopedia's *Capitalized Cost* entry.

**Try it.** `python scripts/football_field_txn.py`, and `finmodel cycle data/edgar/TXN.json --sector
semiconductor` to see the real "silicon cycle" (pandemic chip-shortage peak, FY2022) without any field override.

## 8c-vii. Regulated utilities: thin free cash flow makes the terminal-growth assumption everything  (`docs/FOOTBALL_FIELD_DUK.md`)

**What it is.** The ninth football-field check (Duke Energy) is the deliberate low-cyclicality bookend to the
eight prior sectors, and the third (after airlines and semiconductors) where the default `operating_income`/
`revenue` fields are already correct — but here that's the LEAST interesting part. A regulated utility's real
capex ran 39.6%-45.7% of revenue every single year FY2019-2025 (persistently ~1.8-2.1x real D&A, not a
temporary supercycle the way TXN's was), leaving unlevered free cash flow negative in 2 of those 7 years and
never exceeding ~$1.3B against $87B of debt — not distress, but the entire rate-of-return regulatory mechanism
working as designed: a utility earns its allowed ROE on a rate base that only grows if it keeps building it.

With near-term cash flow this thin, terminal value ends up carrying the large majority of enterprise value —
verified directly: a generic 2.5% terminal growth rate (a perfectly normal assumption for a mature industrial)
produces a NEGATIVE implied equity value for a real, solvent, investment-grade company, because it silently
assumes DUK's own real, disclosed $103B 2026-2030 capital plan (5%-7% guided long-run EPS growth, 9.6% rate-base
growth) stops mattering the instant the 5-year forecast window ends. The fix: anchor terminal growth to the
company's own real guidance, moderated safely below WACC (since a Gordon-growth perpetuity is mathematically
undefined once growth reaches the discount rate) — kept alongside the naive case, not silently replacing it,
since the failure mode itself is the lesson.

Two further real, verified findings: `finmodel.wacc.synthetic_rating()`'s coverage-based table maps DUK's real
thin interest coverage (2.37x) to a synthetic junk rating, while DUK's actual rating is investment-grade
(BBB/Baa2) — regulated utilities are allowed structurally low coverage because rate-of-return regulation makes
debt-service recovery through rates close to guaranteed, the same low-coverage signal the airline check saw on
a genuinely distressed company, with the opposite real-world meaning here. And peer Xcel Energy's real ROE held
a tight band for seven straight years before a real FY2025 drop caused by a disclosed forward equity offering
funding its own capital plan — a real dilution mechanism distinct from every other sector's cyclicality driver.

**Learn it.** Regulated-utility rate-base/allowed-ROE mechanics (any utility-sector equity research primer);
Gordon-growth perpetuity mechanics and why g must stay below the discount rate; Damodaran's synthetic-rating
methodology and its assumptions about unregulated issuers.

**Try it.** `python scripts/football_field_duk.py`, and `finmodel cycle data/edgar/DUK.json --sector utility`
to see the real secular margin-improvement trend (rate-base growth, not a cyclical peak) without any field
override.

## 8c-viii. Pharmaceuticals: a real GAAP quirk distorts the trend, and a real patent cliff isn't always fatal  (`docs/FOOTBALL_FIELD_ABBV.md`)

**What it is.** The tenth football-field check (AbbVie) is a fourth sector (after airlines, semiconductors and
utilities) where the default `operating_income`/`revenue` field needs no OVERRIDE — but it's the first sector
where the field needs a real ADJUSTMENT before its year-to-year history can be trusted at all, a third distinct
pattern alongside "wrong field entirely" (banking/REIT/insurance) and "right field, nothing to fix" (airlines/
semiconductors/utilities). The cause: AbbVie's own GAAP-mandated (ASC 730-10-25-2c) acquired-in-process-R&D
write-offs — expensed immediately when acquired via an asset acquisition with no alternative future use — ran
real, verified $0.7B-$5.0B/year FY2020-2025, with FY2025's real $5.0B charge (from the 2024-closed ImmunoGen and
Cerevel Therapeutics deals) alone compressing reported operating margin by 8.2 percentage points. On the raw
field, `trend_diagnostics()` shows a misleadingly negative-leaning correlation (r=-0.33) driven by that single
FY2024 charge-year trough; on the field with the charge added back it resolves to a genuinely weak trend
(r=-0.09) — meaning the GENERIC `dcf_scenarios_from_history()` trailing min/median/max is the right tool here,
unlike DUK/TRV/CSCO's real secular trends, provided the input is fixed first. This is mechanically different
from the semiconductor check's R&D capitalization: that module amortizes a real multi-year asset (organic R&D)
that GAAP expenses too early; an acquired-IPR&D write-off is a real one-time acquisition cost GAAP correctly
expenses all at once — normalizing it means adding it back like a restructuring charge, not capitalizing it.

The real, sector-defining finding is separate: AbbVie's own genuine Humira patent cliff (US exclusivity lost
2023; real global Humira revenue $21.2B FY2022 → $8.99B FY2024, AbbVie's own disclosed figures) never dragged
AbbVie's total revenue down more than 6.4% in any single year and fully recovered within two, because its own
real, disclosed Skyrizi+Rinvoq replacement franchise grew from roughly $16B to $25.9B in a single year (2027
guidance raised to a combined $31B) — a real, generalizable lesson that a naive "patent cliff sinks the company"
DCF assumption is right for a single-product biotech (the real Pfizer/Seagen precedent here is a genuinely
pre-profitability biotech with negative EBIT AND EBITDA, making EV/Revenue the only usable multiple for that
$42B deal) and wrong for a diversified major pharma with a real, funded pipeline.

Two further real findings surfaced while building this check: a genuine `finmodel.edgar` extraction gap
(AbbVie's and Merck's own "da" tag resolved all the way down to plain PP&E `Depreciation`, silently dropping
real, material `AmortizationOfIntangibleAssets` — now a real additive fix, summed in only when the picked tag
was the narrow one, to avoid double-counting for filers that already report a combined tag), and an unrelated
real `market_data` warehouse bug (ABBV specifically carries duplicate, unpurged OHLC batches — an older,
unadjusted load never removed after a newer, dividend-adjusted reload — the same class of bug this repo's own
recent OHLC-cache fix addressed elsewhere, now found in a second table and fixed here by de-duplicating on the
latest `batch_id` per date).

**Learn it.** ASC 730 (in-process R&D) and its asset-acquisition-vs-business-combination distinction; real
pharma patent-cliff case studies (Humira/AbbVie is one of the most publicly documented); Damodaran's material on
distinguishing a real accounting distortion from a real business trend before applying any cycle normalization.

**Try it.** `python scripts/football_field_abbv.py`, and `finmodel cycle data/edgar/ABBV.json --sector pharma`
to see the raw field's misleading correlation (compare against the adjusted field computed in the script).

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

## 8g. New-business / startup model  (`finmodel.startup_model`, `docs/STARTUP_MODEL.md`)

The mirror image of §8c's real-company checks: instead of validating this toolkit against a real filer,
`finmodel startup <inputs.json>` generates a HYPOTHETICAL new business's financials from a handful of high-level
assumptions (a revenue ramp, a margin trajectory, funding rounds) — then checks the plan against the REAL peer
data those real-company checks already collected, rather than a fabricated "typical startup" benchmark.

No new modeling engine: `build_three_statement()` translates the assumptions into `finmodel.three_statement`
(the same CFI-workbook-reconciled linked 3-statement engine from §1), and `dcf_from_projection()` translates the
resulting forecast into `finmodel.dcf` (the same engine from §2, EBIT = EBT + interest add-back). The one new
piece, `benchmark_against_sector()`, reads `data/edgar/<ticker>.json` for whichever of the seven validated
sectors (steel, oil & gas, software, banking, REITs, airlines, insurance) is the closest real-world comparison,
and reports where the plan's assumed exit-year margin sits relative to those real companies' own most recent
fiscal year — it raises rather than fabricating a benchmark for a sector without real peer data on disk.

A real bug worth knowing about if you extend this: giving the seed year "free" starting PP&E (an asset with no
matching capex/financing entry) balances the two balance-sheet totals but breaks the cash-flow waterfall, since
the model's `equity_issued` field is implicitly a CASH raise. The fix — model any starting PP&E as a same-day
equipment purchase (day-0 capex funded by day-0 equity) rather than a free opening balance — is a genuine, if
narrow, three-statement-modeling lesson: a non-cash contribution needs its own capex/financing entries, not just
a balance-sheet plug.

**Try it.** `finmodel startup examples/startup_saas.json` — a fully-illustrative SaaS example (see
`docs/STARTUP_MODEL.md`), benchmarked against the real software peers from §8c-i/`docs/FOOTBALL_FIELD_CSCO.md`.
`--benchmark-sector airline` on the same file shows what an assumption OUTSIDE a real sector's actual range
looks like, using a deliberately poor real-world comparison.

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
