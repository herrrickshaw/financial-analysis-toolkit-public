# Glossary of financial terms, with GAAP vs IFRS evaluation notes

176 terms. Sources: CFI Financial Analysis Glossary (111 terms) and Modeling Fundamentals Glossary, the PwC *Basic understanding of a company's financial statements* deck, the CFI Accounting e-book and fact sheet, plus authored valuation / LBO / M&A / modelling terms with formulas and pointers into this toolkit. Search from the CLI: `finmodel glossary <term>`.

## How the three statements link (PwC deck, CFI fact sheet)

```
Opening balance sheet ──► Income statement ──► Cash flow statement ──► Closing balance sheet
Assets (cash, inventory,   Revenue − cost of sales    Operating profit + D&A         Assets = Liabilities + Equity
  receivables, PP&E,        = gross profit             − ΔInventory − ΔReceivables    (closing cash = opening cash
  intangibles)              − SG&A ± other = EBIT      + ΔPayables = operating CF      + change in cash)
Liabilities (payables,     − interest = EBT           − interest paid − tax paid
  short/long-term debt)    − tax = net income         − capex − dividends ± equity ± debt = change in cash
Equity                      − dividends = Δ retained earnings
```

## GAAP vs IFRS: what differs and how to evaluate it

| Topic | US GAAP | IFRS | How to evaluate / adjust |
|---|---|---|---|
| Framework style | Rules-based, detailed industry guidance (FASB ASC) | Principles-based (IASB), more judgement and disclosure | Expect more policy choices under IFRS; read the accounting-policies note first. |
| Balance sheet order | Current to non-current, liquidity order | Usually non-current first; liquidity order permitted | Re-order before common-sizing. |
| Inventory | LIFO allowed; lower of cost or NRV/market; no reversal of write-downs | LIFO prohibited (IAS 2); lower of cost and NRV; reversals allowed | Restate LIFO to FIFO using the LIFO reserve; DIO and gross margin otherwise not comparable. |
| PP&E measurement | Historical cost only | Cost or revaluation model (IAS 16) | Revalued assets inflate equity and depreciation; adjust P/B and ROE. |
| Component depreciation | Permitted, rarely used | Required when components have different lives | Depreciation profiles differ; use EBITDA or cash capex for comparisons. |
| Development costs | Expensed (except certain software) | Capitalised when IAS 38 criteria are met | IFRS EBITDA and capex are higher; add back capitalised development to compare R&D intensity. |
| Impairment of long-lived assets | Two-step (undiscounted recoverability, then fair value); no reversals | One-step to recoverable amount; reversals allowed (not goodwill) | IFRS earnings can bounce back after reversals; normalise. |
| Goodwill | Impairment only; optional qualitative screen; reporting-unit level; private-company amortisation election | Impairment only at CGU level; annual test | Neither amortises; impairments are non-cash — exclude from EBITDA. |
| Leases | ASC 842: operating leases keep straight-line lease cost in opex | IFRS 16: all leases on balance sheet as depreciation + interest | IFRS EBITDA, CFO and net debt are higher; use EBITDAR or add lease liabilities to EV for both. |
| Cash flow classification | Interest paid/received and dividends received = operating; dividends paid = financing | Policy choice: interest paid operating or financing; dividends received operating or investing | Normalise interest into a single bucket before computing FCF. |
| Extraordinary items | Category eliminated (2015) | Prohibited | Treat both under 'non-recurring' and normalise. |
| Deferred taxes | DTAs in full with valuation allowance; current/non-current split historically, now non-current | Recognised when probable; always non-current (IAS 12) | Effective tax rate reconciliation is the check. |
| Financial instruments | CECL (lifetime expected losses at inception) for credit losses | IFRS 9 three-stage expected-credit-loss model | Provisioning timing differs; matters for banks and receivables-heavy models. |
| Convertible debt | Generally a single liability (ASU 2020-06) | Split into liability and equity components (IAS 32) | Interest expense and diluted EPS differ. |
| Revenue recognition | ASC 606 five-step model | IFRS 15 five-step model (converged) | Largely comparable; watch collectability threshold and licence renewals. |
| Business combinations | ASC 805; NCI at full fair value | IFRS 3; NCI at fair value or proportionate share | Goodwill differs by the NCI choice under IFRS. |
| Share-based payment | ASC 718; graded vesting may use straight-line | IFRS 2; graded vesting requires accelerated attribution | Front-loaded expense under IFRS. |
| Interim reporting | Integral view (annual costs spread) | Discrete view (each period stands alone) | Quarterly margins are smoother under US GAAP. |
| Presentation of expenses | By function | By nature or by function | Rebuild COGS vs opex lines when a by-nature IFRS statement is compared with US peers. |

## Terms A–Z

### Assets

- **Accounts Receivable** *(also: receivables, debtors)* — Amounts due to an organization for goods delivered or services rendered. Selling to customers on credit will generate accounts receivable for a business.
- **Amortisation** — Allocation of the cost of intangible assets (or capitalised financing fees, debt discounts) over time. **Formula:** `Cost / useful life`. **GAAP vs IFRS:** IAS 38 allows capitalisation of development costs meeting six criteria; US GAAP expenses R&D except software (ASC 985-20 / 350-40). Amortising vs indefinite-lived intangibles is similar in both. **Toolkit:** `lbo fee amortisation; merger intangible amortisation`.
- **Amortization** — The gradual reduction of a financial amount over time.
- **Assets** — Resources owned and employed by an organization which confer future economic benefits.
- **Current Assets** — Current assets are all assets other than fixed assets. They are either cash or assets expected to be converted into cash or consumed in the business during the year. Current assets include items such as cash, accounts receivable and inventory.
- **Depreciation** *(also: amortization)* — Systematic allocation of the cost of tangible fixed assets over their useful lives (straight-line, declining balance, units of production). **Formula:** `Straight-line = (cost − salvage) / life`. **GAAP vs IFRS:** IFRS (IAS 16) requires component depreciation and allows the revaluation model; US GAAP uses historical cost only and component depreciation is permitted but rare. Impairment reversals are allowed under IFRS (IAS 36), prohibited under US GAAP. **Evaluate:** Depreciation waves per capex vintage in the LBO; % of opening PP&E in the CFI models. **Toolkit:** `three_statement PPE schedule; lbo depreciation_detail; xlcalc SLN/SYD`.
- **Fixed Assets** — Assets intended for use on a continuing basis in an organization’s activities (normally defined as assets an organization intends to keep for more than one year). There are three categories of fixed assets: intangible, tangible and investments.
- **Goodwill** — Excess of purchase price over the fair value of identifiable net assets acquired; not amortised, tested for impairment. **Formula:** `Purchase equity value − FV of net identifiable assets (after write-ups and deferred taxes)`. **GAAP vs IFRS:** Both prohibit amortisation and require impairment testing; IFRS (IAS 36) tests at the cash-generating unit with a one-step recoverable-amount test, US GAAP (ASC 350) at the reporting unit with an optional qualitative screen and a one-step quantitative test. Neither allows reversal of goodwill impairment. US private companies may elect amortisation. **Evaluate:** Compare goodwill to equity; a large impairment signals an overpaid deal. **Toolkit:** `merger.pro_forma purchase_price_allocation; lbo closing balance sheet`.
- **Impairment** — Write-down of an asset's carrying amount to its recoverable amount when it can no longer be supported. **GAAP vs IFRS:** IFRS: one-step test against recoverable amount (higher of value in use and fair value less costs of disposal), reversals permitted except goodwill. US GAAP: two-step for long-lived assets (undiscounted recoverability screen, then fair value), no reversals. **Evaluate:** Treat as non-cash; adjust EBITDA and normalise earnings.
- **Intangible Fixed Assets** — Intangible fixed assets have no ‘physical’ presence. Examples include patents, goodwill, trademarks and brand names.
- **Inventory** — Inventory normally refers to items held for resale and may include raw materials, work in progress and finished goods.
- **Inventory valuation** — Cost flow assumption for inventory: FIFO, weighted average or LIFO. **Formula:** `COGS = opening + purchases − closing`. **GAAP vs IFRS:** LIFO is allowed under US GAAP and prohibited by IFRS (IAS 2); IFRS measures at lower of cost and net realisable value with reversals allowed, US GAAP at lower of cost and NRV (non-LIFO) or market (LIFO) with no reversals. **Evaluate:** Add the LIFO reserve to inventory and subtract its change from COGS to restate a LIFO filer to FIFO.
- **Investing Activities** — Deals or transactions involving sale or purchase of equipment, plant, properties, securities, or other assets.
- **Net Book Value** — Net book value typically refers to property plant and equipment (PP&E). The net book value of PP&E is calculated by taking the total gross cost of PP&E and deducting total accumulated depreciation / amortization.
- **Net working capital (NWC)** — Operating current assets less operating current liabilities (typically receivables + inventory + prepaids − payables − accruals), excluding cash and debt. **Formula:** `AR + inventory + prepaids − AP − accrued expenses`. **GAAP vs IFRS:** Inventory: LIFO permitted under US GAAP, prohibited under IFRS (IAS 2); write-downs to NRV can be reversed under IFRS, not under US GAAP. **Evaluate:** Model with days assumptions; an increase in NWC consumes cash. **Toolkit:** `three_statement schedules; projection working_capital; ratios.efficiency`.
- **Revenue** *(also: sales, sales revenue, turnover)* — Revenue includes both cash sales and credit sales of goods and services, but does not include the sale of fixed assets.
- **Tangible Fixed Assets** *(also: capital assets)* — Tangible fixed assets are fixed assets that have physical presence and include things like land, buildings, machinery, equipment, computers and so on.

### Debt & liabilities

- **Accounts Payable** *(also: payables, creditors)* — Amounts owed by an organization to others for goods or services received. Buying from suppliers on credit will generate accounts payable.
- **Cash sweep** — Mandatory prepayment of debt with excess cash flow above a minimum cash balance, applied to tranches in order of seniority. **Formula:** `Sweep = min(excess cash × sweep %, tranche balance)`. **Evaluate:** Accelerates deleveraging; creates a circular reference with interest in Excel (iterate or use average-balance toggles). **Toolkit:** `lbo.Tranche.sweep_pct (iterative solver)`.
- **Creditors** — See accounts payable.
- **Current Liabilities** — An organization’s liabilities due within one year. Current liabilities include items such as short term loans, any element of long term loans due within one year, and accounts payable.
- **Debt Financing** — Raising money for a business through loans or by issuing bonds.
- **Debtors** — See accounts receivable.
- **Deferred tax liability (DTL)** — Tax payable in future periods because book profit is recognised before taxable profit (e.g. accelerated tax depreciation, asset write-ups in an acquisition). **Formula:** `New DTL in a deal = (PP&E + intangible write-ups) × tax rate`. **GAAP vs IFRS:** Both use the balance-sheet liability method; IFRS (IAS 12) classifies all deferred taxes as non-current and requires 'probable' recognition of deferred tax assets, US GAAP recognises DTAs in full with a valuation allowance. **Toolkit:** `merger.PPA / pro_forma`.
- **Leases (IFRS 16 / ASC 842)** — Right-of-use asset and lease liability recognised for most leases. **Formula:** `Liability = PV of lease payments`. **GAAP vs IFRS:** IFRS 16 has a single lessee model (all leases financing-type: depreciation + interest). ASC 842 keeps operating leases with a single straight-line lease cost in operating expenses. Effect: IFRS EBITDA, operating cash flow and debt are all higher than for an identical US GAAP company. **Evaluate:** Add lease liabilities to net debt and use EBITDAR, or de-capitalise, before comparing.
- **Liabilities** — Money owed, or other financial obligations to other organizations Liabilities and individuals.
- **Mezzanine / subordinated debt** — Debt ranking below senior loans, priced with higher coupons, often PIK-able, and frequently carrying equity warrants. **Evaluate:** Lender IRR = interest + principal + warrant equity at exit. **Toolkit:** `lbo.Tranche.warrant_equity_pct; returns[tranche]`.
- **Net Assets** — Total assets less total liabilities.
- **Net debt** — Total debt less cash and cash equivalents. **Formula:** `Debt − cash`. **Evaluate:** Net debt / EBITDA is the standard leverage multiple; covenants usually cap it. **Toolkit:** `lbo debt schedule; ratios.leverage`.
- **Operating Profit** *(also: earnings before interest and income taxes (EBIT), profit)* — before interest and income taxes (PBIT) Sales revenues less all operating expenses. Operating profit is calculated before financing costs and taxes. It is often referred to as EBIT.
- **Paid-in-kind (PIK) interest** — Interest accrued to the principal instead of paid in cash, common on mezzanine/subordinated debt. **Formula:** `PIK accrual = opening balance × rate × PIK share`. **GAAP vs IFRS:** Deductibility of PIK interest for tax differs by jurisdiction; both GAAP and IFRS accrue it as interest expense. **Evaluate:** Non-cash: add back in cash flow; the balance compounds. **Toolkit:** `lbo.Tranche.pik_pct`.
- **Revolver (revolving credit facility)** — Committed line of credit drawn when cash falls below the minimum balance and repaid from surplus cash. **Formula:** `Draw = max(0, prior balance − cash available)`. **Evaluate:** Interest on the revolver is circular with cash; the ASM template leaves it out, this toolkit can iterate it. **Toolkit:** `lbo.LBOInputs.revolver_interest`.
- **Tax Expense** — The tax liability that companies, and individuals, are required to pay by law.

### Equity & capital

- **Book value vs market value** — Book value is the accounting carrying amount (historical cost less depreciation); market value is what the asset or equity trades for. **Formula:** `P/B = market cap / book equity`. **GAAP vs IFRS:** IFRS permits revaluation of PP&E, intangibles (active market) and investment property to fair value; US GAAP does not — IFRS book values can sit closer to market. **Toolkit:** `CFI 'BV vs MV of Equity' template`.
- **Capital** — See capital employed.
- **Capital Asset** — Assets such as property, plant and equipment employed to generate income.
- **Capital Employed** *(also: capital)* — Capital employed represents the funds provided to an organization in the form of equity or debt.
- **Capital In Excess Of Par Value** — See contributed surplus.
- **Capital Stock** *(also: stock, shares, share capital)* — There are two types of stock - common stock and preferred stock. Most shares tend to be common stock and generally carry one vote each and carry an equal right to a proportionate share of dividends. Capital stock is not a liability in the sense of other sources of funds (e.g. bank loans) since it is not generally paid back to shareholders unless the company is wound up.
- **Common Shares** — See common stock.
- **Common Stock** *(also: common shares, ordinary shares)* — Most shares tend to be common stock carrying one vote each and with an equal right to a proportionate share of dividends. Common stock dividends tend to rise as profits grow. This is in contrast to preferred stock where the dividend tends to be fixed.
- **Contributed Surplus** *(also: share premium, capital in excess of par value)* — Most stock is originally issued with a nominal/par value attached to it (e.g. 1 share in ABC Inc. has a nominal value of $1.00). However, if shareholders buy shares from the company for more than the nominal value (e.g. $1.50) the excess is called the contributed surplus. **Formula:** `Most stock is originally issued with a nominal/par value attached to it (e`.
- **Debt** — Capital used to finance an organization that is subject to payment of interest over the life of the loan, at the end of which the loan is normally repaid.
- **Dividends** — A share of a company’s net profits distributed by the company to a class of its stockholders.
- **Equity** *(also: shareholders’ equity, shareholders’ funds)* — Total assets less total liabilities. Also called shareholders’ equity, net worth or book value.
- **Equity Financing** — The money acquired from the business owners themselves or from other investors.
- **Loan Capital** — See debt.
- **Ordinary Shares** — See common stock.
- **Preferred Stock** *(also: preference shares)* — Preferred stock has preferential rights over common stock to both dividends and also to assets in the event that a company is wound up (i.e. preferred stock holders are paid out before common stock holders). Typically preferred stock dividends are fixed (e.g. 6 percent preferred stock) and do not increase with rising profits.
- **Property, Plant And Equipment (Pp&E)** — Non-current fixed or capital assets such as buildings, computers, land, and vehicles.
- **Reserves** — Reserves are part of shareholders’ equity. Reserves are subdivided into revenue reserves (e.g. retained earnings), which are available to be distributed to the shareholders by way of dividends, and capital reserves (e.g. contributed surplus), which for various reasons are not distributable as dividends.
- **Share Capital** — See capital stock.
- **Share Premium** — See contributed surplus.
- **Shareholders’ Equity** — See equity.
- **Shares** — See capital stock.
- **Stock** — See capital stock.
- **Treasury stock method** — Counts options and warrants in diluted shares net of shares repurchasable with the exercise proceeds. **Formula:** `Net new shares = options − (options × strike / price)`. **Toolkit:** `CFI Treasury Stock Method Calculator`.

### Financial statements

- **Accrual accounting** — Revenue is recognised when earned and expenses when incurred (matched to the revenue they generate), regardless of when cash moves. **GAAP vs IFRS:** Both frameworks are accrual-based; differences are in specific recognition rules (leases, development costs, impairment). **Evaluate:** Large gaps between net income and operating cash flow signal aggressive accruals.
- **Audit** — The process of examination and verification of a firm’s books of account, transaction records, and other relevant documents including financial models.
- **Cash Flow Statement** — The cash flow statement is a ‘summarized bank statement’ that shows an organization’s sources of cash during the financial year and the ways in which the cash has been used during that period (e.g. investments, fixed asset purchases, etc.).
- **Current vs non-current** — Current assets/liabilities are expected to convert to cash or be settled within one year (or the operating cycle); everything else is non-current. **Evaluate:** Current ratio and quick ratio measure the cover of current liabilities by current assets. **Toolkit:** `ratios.liquidity`.
- **DCF** — Discounted cash flow analysis. A financial evaluation method that takes the “time value of money” into account.
- **Extraordinary and non-recurring items** — One-off gains or losses outside normal operations. **GAAP vs IFRS:** IFRS prohibits the 'extraordinary' label; US GAAP eliminated it in 2015 (ASU 2015-01). Both require separate disclosure of unusual items. **Evaluate:** Normalise EBIT/EBITDA by removing them before applying multiples. **Toolkit:** `merger 'Adjusted EPS' logic`.
- **Income Statement** *(also: profit and loss account, P&L statement, statement of)* — earnings The income statement is an organization’s ‘financial history book’ and summarizes the revenue, expenses and operating profit for the financial year. It also shows the tax charged against profit, how much of the profit for the year has been paid out in dividends and how much has been retained in the business.
- **Net Earnings** *(also: net income, retained profit for the year, retained earnings)* — for the year The profits retained by an organization after all expenses including interest expenses, taxes and dividends. The retained profits / earnings for a given year are reinvested in the business (hopefully making the organization grow, and increasing the value of its shares) and are added to ‘retained earnings’ in the balance sheet (which represent all retained profits accumulated over an organization’s entire life to date which have been reinvested in the business).
- **Non-Current Assets** — Assets that are not expected to be converted into cash within 12 months of the balance sheet date.
- **Retained Earnings (Balance Sheet)** *(also: P&L reserve, Retained earnings reserve)* — Retained earnings in the balance sheet represent all retained profits accumulated over an organization’s entire life to date which have been reinvested in the business. As the retained earnings ultimately belong to shareholders, they are included as part of shareholders’ equity.
- **Retained Earnings (Income Statement)** — See net earnings.
- **Revenue recognition (IFRS 15 / ASC 606)** — Five-step model: identify the contract, performance obligations, transaction price, allocation, and recognise when control transfers. **GAAP vs IFRS:** Converged standards; remaining differences are in collectability thresholds, licence renewals and some cost capitalisation. **Evaluate:** Check deferred revenue and contract assets when revenue growth outpaces cash.
- **Statement Of Earnings** — See income statement.

### General

- **COGS** — Cost of goods sold.
- **Direct Costs** — Direct costs are those that are directly attributable to the product or service provided by the organization. They are included in cost of goods sold.
- **Forecast** — The projection or estimate of future sales, revenue, earnings, or costs.
- **Gross Profit** — Sales revenue less cost of sales.
- **Net Income** — See net earnings.
- **Operating Revenues** — The net sales revenue accumulated by a firm.
- **Research And Development Expenses** — These expenses are directly attributable to researching and developing new or improved products or systems.
- **Sales** — See revenue.

### Modelling technique

- **Absolute reference** — When copied across multiple cells, the cells they refer to never changes.
- **Circular reference** — A formula chain that refers back to itself, e.g. interest → net income → cash → revolver → interest; Excel needs iterative calculation. **Evaluate:** Prefer opening-balance interest or a switch; this toolkit iterates to a fixed point. **Toolkit:** `xlcalc.XlModel.recalc (iterative), lbo revolver loop`.
- **Circular References** — Circular references occur when a formula includes a reference to the cell in which the formula appears.
- **Data tables** — Used to test one or two variables for sensitivity analysis.
- **Financial Model** — A mathematical model describing the interrelationships among various financial variables. Typically financial models are broken down into inputs, processing, and outputs.
- **Football field** — Chart of valuation ranges by method (DCF, comps, precedents, LBO) against the current price. **Evaluate:** The standard one-page valuation summary. **Toolkit:** `charts.range_bars; CFI Football Field Chart template`.
- **Goal seek** — Used to test which assumptions are needed to satisfy the desired output.
- **Inputs** — Financial model assumptions that are used to drive model outputs.
- **Model Structure** — The framework around which a financial model is built.
- **Name cells** — By naming a cell, you use the name reference rather than the cell reference.
- **Nested IF statements** — A complicated formula with multiple IF statements within each other.
- **Output** — Financial model calculations that are driven by one or more inputs.
- **Processing** — The translation of financial model inputs or assumptions into financial model outputs.
- **Relative reference** — When copied across multiple cells, they change based on the relative position of rows and columns.
- **Scenario analysis** — Running the model under alternative coherent input sets (base / upside / downside) selected by a switch (CHOOSE / INDEX). **Evaluate:** Keep scenario inputs in one block; drive with a single selector cell. **Toolkit:** `lbo.sensitivity scenarios; three_statement list-valued assumptions`.
- **Scenario manager** — Used to test for different scenarios that may happen in the future, usually base, worst and best.
- **Scenario planning** — Tests the model’s robustness against possible future changes.
- **Sensitivity analysis** — Tests the final value against changes in one (or more) variables.
- **Sensitivity analysis / data table** — Recomputing an output over a grid of one or two inputs (Excel Data Table); a heatmap is the natural visual. **Evaluate:** Use for WACC × g (DCF), scenario × exit multiple (LBO), premium × % stock (merger). **Toolkit:** `dcf.sensitivity, lbo.sensitivity, merger.deal_sensitivity, charts.heatmap`.
- **Solver** — Used to minimize or maximize the output under a certain set of assumptions.
- **Test data** — Inputting specific test data to stress test and sanity test your model. www.corporatefinanceinstitute.com
- **Tracing dependents** — www.corporatefinanceinstitute.com Shows the cells that use the selected cell in its calculations.
- **Tracing precedents** — Shows the cells that are used in the calculation of the selected cell.
- **VLOOKUP functions** — One of the lookup and reference functions, is used to find things in a table or a range by row.
- **Waterfall chart** — Bridge from a starting value through positive and negative steps to an ending value (cash bridge, EV → equity bridge, returns attribution, PPA). **Toolkit:** `charts.waterfall; CFI Waterfall Chart template`.
- **YEARFRAC (stub period)** — Fraction of a year between two dates; Excel's default basis 0 is US 30/360, used to scale a partial first forecast period in a DCF. **Formula:** `days360(d1, d2) / 360`. **Evaluate:** The CFI DCF stub 31-Dec-2017 → 30-Jun-2018 is exactly 0.5. **Toolkit:** `fin.yearfrac, dcf.period_dates`.

### Ratios & metrics

- **Accounts Payable Days Ratio** — Accounts payable / COGS x 365. Average number of days a firm takes to pay for items purchased. **Formula:** `Accounts payable / COGS x 365`.
- **Accounts Payable Turnover** — Cost of sales / Accounts payable (either the ending balance or average balance). This ratio measures how effective management is in paying its suppliers. **Formula:** `Cost of sales / Accounts payable (either the ending balance or average balance)`.
- **Accounts Receivable Days Ratio** — Accounts receivable / Sales x 365. Average number of days a firm takes to collect payments on goods sold. **Formula:** `Accounts receivable / Sales x 365`.
- **Accounts Receivable Turnover** — Sales / Accounts receivable (either the ending balance, or average balance). This ratio measures how effective the company’s credit policies are. **Formula:** `Sales / Accounts receivable (either the ending balance, or average balance)`.
- **Acid Test** — See quick ratio.
- **Administration Cost Ratio** — Administration costs / Sales. This margin shows the general overhead cost for each dollar of sales. **Formula:** `Administration costs / Sales`.
- **Asset Turnover Ratio** — Sales / Total assets. This ratio shows how effective the company is in generating sales from its assets. **Formula:** `Sales / Total assets`.
- **Average Balance** — (Opening balance - Closing balance) / 2. This balance can be used to calculate efficiency / turnover ratios instead of using a closing balance.
- **Balance Sheet** — The balance sheet is a ‘snapshot’ of an organization’s assets and liabilities on a particular date. The balance sheet shows the sources of funds provided to an organization (called the capital employed and normally either equity or debt) and how those funds have been used by the organization to invest in fixed assets (assets the organization intends to keep for more than one year) and working capital (money tied up in the day to day operations of the business).
- **Common-size analysis** — Every income-statement line as % of revenue and every balance-sheet line as % of total assets, to compare companies of different sizes or across time. **Evaluate:** First step of any peer comparison. **Toolkit:** `CFI Common Size Analysis template`.
- **Coverage Ratios** — Ratios that analyze a company’s liquidity or its ability to “cover” its financial debt obligations. An example of a coverage ratio is EBITDA / Interest expense.
- **Current Ratio** — Current assets / current liabilities. This ratio measures short term liquidity, whether or not a company will have the ability to cover its obligations in the short term. **Formula:** `Current assets / current liabilities`.
- **Days inventory outstanding (DIO)** — Average days inventory is held. **Formula:** `Inventory / COGS × 365`. **GAAP vs IFRS:** LIFO (US GAAP only) lowers inventory and raises COGS in inflation, distorting DIO versus IFRS peers; use the LIFO reserve to restate. **Toolkit:** `ratios.efficiency.inventory_days`.
- **Days payable outstanding (DPO)** — Average days taken to pay suppliers. **Formula:** `Accounts payable / COGS × 365`. **Evaluate:** Cash conversion cycle = DSO + DIO − DPO. **Toolkit:** `ratios.efficiency.payables_days, working_capital_funding_gap_days`.
- **Days sales outstanding (DSO)** — Average days to collect receivables. **Formula:** `Accounts receivable / Revenue × 365`. **Evaluate:** Rising DSO with flat revenue flags collection problems or channel stuffing. **Toolkit:** `ratios.efficiency.receivable_days`.
- **DuPont analysis** — Decomposes return on equity into margin, asset turnover and leverage. **Formula:** `ROE = (NI / revenue) × (revenue / assets) × (assets / equity)`. **Evaluate:** Separates operating performance from financial gearing. **Toolkit:** `ratios.profitability + efficiency + leverage`.
- **Earnings per share (EPS)** — Net income attributable to common shareholders divided by weighted-average shares; diluted EPS adds in-the-money options, warrants and convertibles (treasury stock method). **Formula:** `NI / weighted average shares`. **GAAP vs IFRS:** IAS 33 and ASC 260 are largely converged; minor differences in contracts settleable in cash or shares and in year-to-date diluted share calculations. **Toolkit:** `merger.deal['combined']['eps']; CFI Treasury Stock Method calculator`.
- **EBIT** — Earnings before interest and taxes (operating income). **Formula:** `Revenue − COGS − operating expenses (incl. D&A)`. **Evaluate:** Base for NOPAT = EBIT × (1 − t) and unlevered FCF. **Toolkit:** `dcf.ebit`.
- **EBIT Margin** — EBIT / Sales. **Formula:** `EBIT / Sales`.
- **EBITDA** — Earnings before interest, taxes, depreciation and amortisation: operating profit plus non-cash D&A, a proxy for operating cash generation used in leverage multiples and enterprise-value multiples. **Formula:** `EBIT + D&A`. **GAAP vs IFRS:** IFRS 16 puts all leases on balance sheet so lease costs become depreciation + interest and EBITDA rises; under US GAAP operating leases keep a straight-line lease expense inside EBITDA. Add back lease expense (EBITDAR) or capitalise consistently before comparing. **Evaluate:** Never compare EBITDA multiples across IFRS and US GAAP lessees without a lease adjustment. **Toolkit:** `three_statement, lbo (tranche sizing = multiple × EBITDA), dcf terminal multiple`.
- **Financial Covenants** — The promises made by the borrowing firm in a loan agreement to adhere to certain limits in the firm’s operations.
- **Financial Statements** — Statements, in financial terms, of the financial position of an entity at a given date, or of the results of its operations for a given period. The statements are normally prepared in one of a number of standard formats. Most commonly, when people refer to financial statements, they mean the income statement, the balance sheet, the cash flow statement and the related notes to the accounts.
- **Fixed charge coverage ratio** — Coverage of interest plus lease/rent and scheduled principal by EBITDA (or EBIT) plus fixed charges. **Formula:** `(EBITDA + fixed charges) / (fixed charges + interest)`. **Evaluate:** Common LBO covenant. **Toolkit:** `CFI Fixed Charge Coverage template; BIWS FCCR example`.
- **Gross Margin** — Gross profit / Sales revenue. Gross margin shows how much was spent producing the good or service that was sold for every dollar of sales revenue. **Formula:** `Gross profit / Sales revenue`.
- **Interest Bearing Current Liabilities (Ibcl’s)** — These are liabilities that bear interest, normally short term borrowings. They are excluded from some ratios in order to factor in the cost of financing.
- **Interest Cover Ratio** — EBITDA / Interest expense. This solvency ratio shows how much income is available to service debt costs. **Formula:** `EBITDA / Interest expense`.
- **Interest coverage** — Ability to service interest from operating profit. **Formula:** `EBIT / interest expense (or EBITDA / cash interest)`. **GAAP vs IFRS:** Lease reclassification under IFRS 16 raises EBIT and interest simultaneously — recompute on a like-for-like basis. **Evaluate:** Damodaran maps coverage to a synthetic rating and default spread. **Toolkit:** `ratios.coverage; Damodaran ratings.xls`.
- **Inventory Days Ratio** — Inventories / COGS x 365. Average number of days goods remain in inventory before being sold. **Formula:** `Inventories / COGS x 365`.
- **Inventory Turnover Ratio** — Sales / Inventory (either the ending balance, or average inventory balance). This ratio illustrates how a company manages its inventory. **Formula:** `Sales / Inventory (either the ending balance, or average inventory balance)`.
- **Labour Cost Ratio** — Direct labour / Sales. Cost of goods sold is made up of labour, materials, and direct costs. This margin shows the proportion of labour that goes to make up each dollar of sales. **Formula:** `Direct labour / Sales`.
- **Land And Buildings Ratio** — Sales / Land and buildings. The sales generated from land and buildings is measured by this ratio. **Formula:** `Sales / Land and buildings`.
- **Leverage Ratios** — Ratios that analyze a company’s solvency or the level of its debt financing relative to its equity financing. An example of a leverage ratio is Total debt / Total shareholders’ equity.
- **Material Cost Ratio** — Materials / Sales. Cost of goods sold is made up of labour, materials, and direct costs. This margin shows the proportion of materials that goes to make up each dollar of sales. **Formula:** `Materials / Sales`.
- **MOIC (multiple of invested capital)** — Total cash returned divided by cash invested, ignoring timing. **Formula:** `Σ distributions / Σ contributions`. **Evaluate:** Read together with IRR: a 2x over 3 years is ~26% IRR, over 7 years ~10%. **Toolkit:** `lbo returns['moic']`.
- **Net Asset Ratio** — Sales / Net assets. This ratio takes into account the financing of assets, and measures management’s efficiency in relation to the use of assets. **Formula:** `Sales / Net assets`.
- **Net Profit Margin** — Net income / Sales. This margin shows how much is earned for every dollar of sales revenue. **Formula:** `Net income / Sales`.
- **Operating Activities** *(also: earnings before interest and income taxes (EBIT), profit)* — before interest and income taxes (PBIT) Cash inflows and outflows relating to a company’s operations. Examples includes receiving payments from customers, paying salaries, etc.
- **Operating Assets** — Assets acquired for or used throughout the operations of the business (such as cash, inventory, prepaid expenses, equipment).
- **Operating Cost Ratio** — Operating costs / Sales. This margin shows the operating expenses as a percentage of sales. This does not include cost of goods sold (as is the case with the operating profit margin), so is an indication of the efficiency of the operation. **Formula:** `Operating costs / Sales`.
- **Operating Profit Margin** — Otherwise known as the EBIT margin. Operating income / Sales. This performance ratio shows the cost of running the operation for each dollar of sales.
- **Personnel Cost Ratio** — Personnel costs / Sales. The personnel costs used in this ratio could be research and development specific, or general overhead personnel costs, or total personnel depending upon the type of organization. This margin is useful in monitoring the amount spent on wages, salaries, and related expenses for each dollar of sales. **Formula:** `Personnel costs / Sales`.
- **Plant And Machinery Turnover Ratio** — Sales / Plant and Machinery. This ratio measures the efficiency of the company’s operating assets. **Formula:** `Sales / Plant and Machinery`.
- **Property, Plant And Equipment (Pp&E) Turnover Ratio** — Sales / Property, Plant & Equipment. This ratio measures the sales a company is able to generate from capital assets. **Formula:** `Sales / Property, Plant & Equipment`.
- **Quick Ratio** — Current assets - Inventory / Current liabilities. This ratio provides a more prudent measure of short-term liquidity recognizing the inventory can not always be readily converted into cash. **Formula:** `Current assets - Inventory / Current liabilities`.
- **Research And Development Cost Ratio** — Research and development costs / Sales. This margin shows how much the company invests in developing the next generation of products or services for each dollar of sales. **Formula:** `Research and development costs / Sales`.
- **Return on invested capital (ROIC)** — After-tax operating profit relative to the capital invested in operations. **Formula:** `NOPAT / (net debt + equity − excess cash)`. **Evaluate:** Value is created when ROIC exceeds WACC (Koller); in an LBO the BIWS sweep model tracks ROIC yearly. **Toolkit:** `CFI ROIC Template; Damodaran returncalculator.xls`.
- **Selling Cost Ratio** — Selling costs / Sales. This margin shows how much it costs to sell each dollar of sales. **Formula:** `Selling costs / Sales`.
- **SG&A (Selling, General, And Administration)** — Operational expenses that include direct and indirect selling expenses and all general and administrative expenses. Rent, heat, lights are all examples of general expenses.
- **Stock Repurchases** — When a corporation buys back its own shares in the open market.
- **Tax Ratio** — Tax / Sales. This efficiency ratio shows how well management is managing tax. **Formula:** `Tax / Sales`.
- **Turnover** — See revenue.
- **Turnover Ratio** — Ratios that measure an assets’ activity or efficiency in generating revenues or cash. Total assets / Sales.
- **Work Overhead Ratio** — Direct overhead / Sales. Cost of goods sold is made up of labour, materials, and direct costs. This margin shows the proportion of direct overhead that goes to make up each dollar of sales. **Formula:** `Direct overhead / Sales`.
- **Working Capital** — Working capital is normally defined as money tied up in the day to day operations of an organization. It is approximately equal to current assets less current liabilities. However, many analysts will define working capital more explicitly as inventory and accounts receivable less accounts payable (and exclude other current assets / liabilities such as cash and non-trade receivables and payables).

### Valuation

- **Accretion / dilution** — Change in the acquirer's EPS caused by a deal: positive (accretive) when the combined EPS exceeds standalone EPS. **Formula:** `Combined EPS − standalone EPS; % = that / standalone EPS`. **Evaluate:** Rule of thumb: all-stock deals are accretive when the target's P/E is below the acquirer's; cash deals when the target's earnings yield exceeds the after-tax cost of cash/debt. **Toolkit:** `merger.deal, merger.pro_forma, deal_sensitivity`.
- **CAPM** — Capital asset pricing model: expected return on equity equals the risk-free rate plus beta times the equity risk premium. **Formula:** `k_e = r_f + β × (E[r_m] − r_f)`. **Evaluate:** Unlever peer betas and relever at the target capital structure. **Toolkit:** `Damodaran levbeta.xls; CFI Beta Calculator, CAPM Formula`.
- **Enterprise value (EV)** — Value of the operating business to all capital providers: market equity value plus debt, preferred and non-controlling interests, minus cash. **Formula:** `Equity value + debt + preferred + NCI − cash`. **GAAP vs IFRS:** Under IFRS 16 lease liabilities are debt-like for every lessee; under US GAAP operating-lease liabilities are also recognised (ASC 842) but presented separately — decide consistently whether to include them in EV. **Evaluate:** Pair EV with unlevered metrics (EBITDA, EBIT, revenue) only. **Toolkit:** `dcf market block; merger.Company.enterprise_value`.
- **Equity value** — Value attributable to shareholders: EV + cash − debt, or price × diluted shares. **Formula:** `EV − net debt − preferred − NCI`. **Evaluate:** Pair with levered metrics (net income, book equity). **Toolkit:** `dcf.equity_value, merger deal`.
- **Exchange ratio** — Number of acquirer shares issued per target share in a stock deal. **Formula:** `Offer price per target share / acquirer share price`. **Evaluate:** Fixed vs floating exchange ratios shift price risk between the parties. **Toolkit:** `merger.deal['exchange_ratio']`.
- **Exit multiple** — EV/EBITDA multiple assumed at sale; usually set equal to (or below) the entry multiple to avoid banking on multiple expansion. **Formula:** `Exit EV = multiple × exit-year EBITDA`. **Evaluate:** Sensitise IRR to exit multiple × operating scenario (the data table). **Toolkit:** `lbo.sensitivity`.
- **Free cash flow to equity (FCFE)** — Cash available to shareholders after debt service: net income + D&A − capex − ΔNWC + net borrowing. **Formula:** `NI + D&A − capex − ΔNWC + net debt issued`. **Evaluate:** Discount at the cost of equity; used for financials and highly levered firms. **Toolkit:** `Damodaran fcfe templates in catalog`.
- **Internal rate of return (IRR) / XIRR** — Discount rate at which NPV is zero; XIRR uses dated flows. **Formula:** `Σ CF_t / (1 + IRR)^t = 0`. **Evaluate:** Needs at least one sign change; compare with WACC (projects) or the sponsor hurdle (LBO). **Toolkit:** `fin.irr, fin.xirr; lbo returns`.
- **Leveraged buyout (LBO)** — Acquisition funded mostly with debt secured on the target's cash flows; the sponsor's return comes from EBITDA growth, multiple expansion and debt paydown. **Formula:** `Sponsor IRR from −equity at entry … +equity value at exit`. **Evaluate:** Attribute returns to the three levers; check leverage (debt/EBITDA) and coverage covenants each year. **Toolkit:** `finmodel.lbo`.
- **Net present value (NPV) / XNPV** — Sum of cash flows discounted to today; XNPV discounts by actual dates (days/365) rather than whole periods. **Formula:** `NPV = Σ CF_t / (1 + r)^t; XNPV = Σ CF_i / (1 + r)^((d_i − d_0)/365)`. **Evaluate:** Excel NPV discounts the first flow one full period — put the time-0 flow outside NPV(). **Toolkit:** `fin.npv, fin.xnpv`.
- **Precedent transactions** — Multiples paid in past M&A deals for similar companies, including control premia. **Formula:** `Implied EV = precedent multiple × target metric`. **Evaluate:** Usually higher than trading comps because of the premium; check deal timing and cycle. **Toolkit:** `BIWS precedent-transactions files`.
- **Purchase price allocation (PPA)** — Allocating the purchase price to acquired assets and liabilities at fair value (PP&E and intangibles write-ups, new deferred tax liability), with the residual as goodwill. **Formula:** `Goodwill = price − book value + old goodwill − write-ups − DTL written down + new DTL`. **GAAP vs IFRS:** IFRS 3 and ASC 805 are largely converged; differences remain on NCI measurement (IFRS allows proportionate share; US GAAP requires full fair value) and contingent liabilities. **Evaluate:** Write-ups create extra D&A that depresses reported EPS; show 'adjusted' EPS excluding it. **Toolkit:** `merger.pro_forma`.
- **Sources and uses** — Funding table for a transaction: where the money comes from (equity, each debt tranche, cash on hand) and what it pays for (equity purchase, debt refinanced, fees). **Formula:** `Total sources = total uses`. **Evaluate:** Fees are capitalised (financing) or expensed (transaction) and flow through the closing balance sheet. **Toolkit:** `lbo.run['sources'/'uses'], merger.pro_forma`.
- **Synergies** — Incremental value from combining businesses: cost synergies (overhead, procurement) and revenue synergies (cross-selling, pricing), phased in by a realisation schedule and offset by integration costs. **Formula:** `Value of synergies = PV of after-tax synergy cash flows − integration costs`. **Evaluate:** Cost synergies are credited more than revenue synergies; pre-tax break-even synergies = dilution ÷ (1 − t) × shares. **Toolkit:** `merger.pro_forma; Damodaran synergyvaluation.xls`.
- **Terminal value** — Value of cash flows beyond the explicit forecast, by perpetuity growth (Gordon) or an exit multiple. **Formula:** `TV = FCF_n × (1 + g) / (WACC − g); or multiple × EBITDA_n`. **Evaluate:** Cross-check the implied exit multiple of the perpetuity method and the implied growth of the multiple method. **Toolkit:** `dcf.terminal_value (average/perpetuity/multiple)`.
- **Trading comparables (comps)** — Valuation from multiples of similar listed companies (EV/EBITDA, EV/revenue, P/E), applied to the target's metrics. **Formula:** `Implied EV = peer median multiple × target metric`. **GAAP vs IFRS:** Use consistent accounting (lease, LIFO, development-cost adjustments) across the peer set. **Evaluate:** Report the 25th–75th percentile range in the football field. **Toolkit:** `BIWS comps files in catalog; charts.range_bars`.
- **Unlevered free cash flow (UFCF)** — Cash available to all capital providers before financing: NOPAT plus D&A less capex and the increase in net working capital. **Formula:** `EBIT × (1 − t) + D&A − capex − ΔNWC`. **GAAP vs IFRS:** Lease classification (IFRS 16 vs ASC 842) and capitalised development costs (IAS 38 allows capitalisation of development spend; US GAAP expenses most R&D) shift items between opex and capex — FCF should be similar but EBITDA and capex lines are not comparable. **Evaluate:** Discount at WACC; reconcile to CFO − capex. **Toolkit:** `dcf.run['ufcf']`.
- **Weighted average cost of capital (WACC)** — Blended after-tax return required by debt and equity investors, used to discount unlevered cash flows. **Formula:** `E/(D+E) × k_e + D/(D+E) × k_d × (1 − t)`. **Evaluate:** k_e from CAPM: r_f + β × ERP (+ country / size premia); k_d from yield or synthetic rating. **Toolkit:** `dcf.discount_rate; Damodaran wacccalc.xls; CFI WACC Calculator`.

## Sources

- PwC, Basic understanding of a company's financial statements (Sept 2020) — downloads/refs/pwc-basic-understanding-of-a-companys-financials.pdf
- CFI Financial Analysis Glossary, Financial Modeling Fundamentals Glossary, Accounting e-book, Accounting fact sheet — downloads/cfi/ (member dashboard)
- CFI MEI Guide preview (docs.mypilotstore.com) — could not be retrieved: Cloudflare bot challenge blocks both curl and the browser session
- Authored: core modelling / valuation terms and the GAAP vs IFRS evaluation table (standards: IAS 1/2/12/16/32/33/36/38, IFRS 3/9/15/16; ASC 260/350/606/718/805/842, ASU 2015-01, ASU 2020-06)