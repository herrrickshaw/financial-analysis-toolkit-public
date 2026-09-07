# Literature survey: banking, retail credit, and FX-desk calculations

`docs/LEARNING_GUIDE.md` covers this toolkit's corporate-finance and valuation engines (3-statement, DCF,
LBO, merger, comps) with their books and open-university sources. It has no coverage at all of the banking,
retail-credit, deposit, project-finance, real-estate, tax-provision, or FX modules built across this
session's later rounds — a real gap, since those modules draw on an entirely different literature (bank
regulatory economics, consumer-credit law, actuarial science, international finance) rather than investment-
banking valuation. This survey closes that gap: what real books, standards, and papers exist for each
banking-related module this toolkit implements, and — mirroring the format of every other survey doc this
session has written (`docs/MORE_CFI_TEMPLATES.md`, `docs/FPA_GALLERY_GAP_ANALYSIS.md`,
`docs/OPERATING_FINANCE_TOOLS.md`, `docs/RETAIL_BANKING_TOOLS.md`) — what real technique each book/standard
actually teaches versus what this toolkit currently implements from it.

---

## 1. Bank operating economics: NII, NIM, capital adequacy  (`finmodel.bank_model`)

**What it is.** A bank's core operating model isn't revenue-minus-cost like a normal company — its "revenue"
is net interest income (interest earned on assets minus interest paid on liabilities), its principal risk
cost is loan-loss provisioning, and its solvency is measured against risk-weighted regulatory capital ratios
rather than a debt/EBITDA multiple.

| Source | Author(s) | What it teaches |
|---|---|---|
| *Bank Management & Financial Services* | Peter S. Rose, Sylvia C. Hudgins (McGraw-Hill) | The standard bank-management textbook: NII/NIM mechanics, asset-liability management, the loan-loss provisioning cycle, liquidity management |
| *Financial Institutions Management: A Risk Management Approach* | Anthony Saunders, Marcia Millon Cornett (McGraw-Hill) | A risk-based lens on the same operating economics: interest-rate risk (duration gap, repricing gap), credit risk, and capital regulation together |
| *Basel III: A Global Regulatory Framework for More Resilient Banks and Banking Systems* | Basel Committee on Banking Supervision (BIS, 2010/11, rev. 2017) | The primary source for CET1/Tier 1/Total Capital ratios and the leverage ratio — the actual numerator/denominator definitions `finmodel.bank_model` implements |
| RBI Master Circular on Basel III Capital Regulations | Reserve Bank of India | India-specific capital-adequacy implementation (relevant alongside the IRAC norms in §10 below) |

**Implemented here.** NII/NIM computation, a CECL-style provision-for-credit-losses walk, and CET1/Tier 1/
leverage ratio checks against the real US Prompt Corrective Action thresholds. **Not implemented**:
duration-gap / repricing-gap interest-rate-risk analysis (a real, distinct ALM discipline — a plausible
future module if there's a real bank balance sheet to reconcile it against).

## 2. Project finance: DSCR sizing, sculpting, LLCR  (`finmodel.project_finance`)

| Source | Author(s) | What it teaches |
|---|---|---|
| *Principles of Project Finance* | E.R. Yescombe (Academic Press) | THE standard project-finance textbook: DSCR-based debt sizing, cash-flow sculpting to a target cover ratio, LLCR, and lender security packages |
| *Project Finance in Theory and Practice* | Stefano Gatti (Academic Press) | A quantitative companion — the same mechanics with worked numerical models |
| Wall Street Prep / Breaking Into Wall Street project-finance courses | — | Practitioner-level walk-throughs of the same DSCR/LLCR mechanics in Excel (already catalogued as sources `wsp`/`biws`) |

**Implemented here** (see also `docs/MORE_CFI_TEMPLATES.md` and `docs/DUE_DILIGENCE_TOOLS.md`): DSCR-based
debt sizing and sculpting, LLCR, cap-rate/NOI valuation, level-annuity and interest-only/bullet debt
structures, balloon coverage, and a debt-structure comparison tool.

## 3. Real-estate development pro formas  (`finmodel.real_estate_development`)

| Source | Author(s) | What it teaches |
|---|---|---|
| *Commercial Real Estate Analysis and Investments* | David Geltner, Norman Miller, Piet Eichholtz, Jim Clayton (OnCourse Learning) | THE standard commercial real-estate finance textbook — development pro formas, yield on cost, the development-spread underwriting convention |
| *Real Estate Finance and Investments* | William Brueggeman, Jeffrey Fisher (McGraw-Hill) | An equally standard alternative covering the same ground-up development mechanics |
| *Real Estate Finance and Investments: Risks and Opportunities* | Peter Linneman (Linneman Associates) | A practitioner-oriented treatment, particularly of construction-loan structuring and interest capitalization |

**Implemented here.** Total development cost, a capitalized-interest construction-loan draw schedule, yield
on cost, development spread, and unlevered development IRR (`docs/OPERATING_FINANCE_TOOLS.md`).

## 4. Actuarial loss reserving  (`finmodel.loss_reserving`)

| Source | Author(s) | What it teaches |
|---|---|---|
| *Estimating Unpaid Claims Using Basic Techniques* | Jacqueline Friedland (Casualty Actuarial Society, freely available exam study note) | The chain-ladder method exactly as implemented here — age-to-age factors, cumulative development factors, IBNR |
| *Loss Models: From Data to Decisions* | Stuart Klugman, Harry Panjer, Gordon Willmot (Wiley) | The broader actuarial-statistics textbook behind loss reserving and ratemaking |
| Mack, T. (1993), "Distribution-free calculation of the standard error of chain ladder reserve estimates," *ASTIN Bulletin* | Thomas Mack | The classic academic paper establishing chain-ladder's statistical properties (used to size confidence intervals around the point estimate this module produces) |

**Implemented here.** Chain-ladder age-to-age/cumulative development factors and IBNR (`docs/OPERATING_FINANCE_TOOLS.md`).
**Not implemented**: Bornhuetter-Ferguson (blends chain-ladder with an a-priori loss ratio, useful for thin
recent-year data — flagged as a real future extension in that doc), and Mack's own standard-error formula
(would need a real multi-year dataset with known outcomes to validate against rather than a synthetic
example).

## 5. Corporate income-tax provision  (`finmodel.tax_provision`)

| Source | What it teaches |
|---|---|
| FASB ASC 740, *Income Taxes* | The US GAAP source for deferred tax assets/liabilities and the valuation-allowance "more likely than not" realizability test |
| IAS 12, *Income Taxes* (IFRS) | The international equivalent of ASC 740 |
| IRC Section 172, as amended by the Tax Cuts and Jobs Act of 2017 | The statutory source for the post-2017 80%-of-taxable-income NOL cap and the pre-2018 20-year-expiration/100%-offset legacy rule this module tracks as two separate baskets |
| Big 4 accounting-for-income-taxes handbooks (e.g. KPMG's *Handbook: Accounting for Income Taxes*, Deloitte's *Roadmap to Accounting for Income Taxes*) | Detailed worked interpretive guidance on applying ASC 740 in practice, including the rate-reconciliation table format this module reproduces |

**Implemented here.** Deferred tax position, valuation allowance, the two-basket NOL carryforward schedule,
effective-rate reconciliation, and a deferred-tax rollforward (`docs/OPERATING_FINANCE_TOOLS.md`).

## 6. Working-capital financing  (`finmodel.working_capital_financing`)

| Source | Author(s) | What it teaches |
|---|---|---|
| *Principles of Corporate Finance* | Richard Brealey, Stewart Myers, Franklin Allen (McGraw-Hill) | The classic "cost of not taking a trade discount" formula this module implements exactly, plus the broader working-capital-management chapter |
| *Corporate Finance* | Jonathan Berk, Peter DeMarzo (Pearson) | An equally standard alternative covering factoring and asset-based-lending economics |

**Implemented here.** Invoice-factoring cost, early-payment-discount APR, asset-based-lending borrowing-base
availability (`docs/OPERATING_FINANCE_TOOLS.md`).

## 7. Retail loans: EMI, amortization, prepayment  (`finmodel.retail_loans`)

| Source | What it teaches |
|---|---|
| Reserve Bank of India, *Master Direction — Interest Rate on Advances* | The regulatory mandate for reducing-balance EMI disclosure this module's amortization schedule implements |
| Indian Institute of Banking & Finance (IIBF) *Retail Banking* macmillan textbook (the standard JAIIB/CAIIB certification curriculum for Indian bank officers) | Retail-lending product mechanics including prepayment options and FOIR-based eligibility underwriting |
| Frank Fabozzi (ed.), *The Handbook of Mortgage-Backed Securities* (Oxford University Press) | The mortgage-amortization mathematics underlying any reducing-balance loan, at the more quantitative end (also the source this toolkit's `finmodel.cmo` cites for PSA prepayment modeling) |

**Implemented here.** EMI, amortization schedule, prepayment (reduce-tenure/reduce-EMI), floating-rate
reset, foreclosure payoff, FOIR loan eligibility (`docs/RETAIL_BANKING_TOOLS.md`).

## 8. Retail deposits: FD, RD, TDS  (`finmodel.retail_deposits`)

| Source | What it teaches |
|---|---|
| Reserve Bank of India, *Master Direction — Interest Rate on Deposits* | The compounding-basis requirement this module's FD/RD maturity calculations implement |
| Income Tax Act, 1961, Section 194A (Government of India) | The statutory TDS-withholding rule on bank interest — the real "full amount, not just the excess" behavior this module's test suite specifically checks |
| IIBF *Retail Banking* / *Banking Regulations and Business Laws* (JAIIB/CAIIB curriculum) | Deposit-product mechanics including premature-closure rate conventions |

**Implemented here.** FD maturity, RD maturity (simulated per-installment compounding), premature RD
closure, Section 194A TDS (`docs/RETAIL_BANKING_TOOLS.md`).

## 9. Revolving credit: cash credit/overdraft, credit cards  (`finmodel.revolving_credit`)

| Source | What it teaches |
|---|---|
| US Credit CARD Act of 2009 (Public Law 111-24) | The statutory source for the minimum-payment warning disclosure every US credit-card statement must print — the real "minimum-payment trap" this module simulates |
| *Consumer Credit and the American Economy* | Thomas Durkin, Gregory Elliehausen, Michael Staten, Todd Zywicki (Oxford University Press) — the standard academic treatment of consumer revolving credit, including average-daily-balance billing |
| Consumer Financial Protection Bureau (CFPB) reports on credit-card minimum payments | Real, published regulator research quantifying how much minimum-payment-only behavior costs consumers, corroborating this module's simulated result |
| RBI guidance on cash credit/overdraft facilities (part of the same Master Direction — Interest Rate on Advances as §7) | The daily-outstanding-balance interest convention for Indian CC/OD accounts |

**Implemented here.** Daily-balance interest (shared mechanic for CC/OD accounts and credit-card billing
cycles) and the credit-card minimum-payment schedule, including a real negative-amortization case.

## 10. NPA classification and provisioning (India's IRAC norms)  (`finmodel.npa_classification`)

| Source | What it teaches |
|---|---|
| RBI Master Circular on *Prudential Norms on Income Recognition, Asset Classification and Provisioning Pertaining to Advances* | The primary source for this module's entire classification ladder (Standard/SMA-0/1/2/Sub-standard/Doubtful-1/2/3/Loss) and the secured/unsecured provisioning-rate table |
| RBI, *Prudential Framework for Resolution of Stressed Assets* (2019) | The source of the SMA-0/1/2 early-warning sub-categories this module implements alongside the older Standard/NPA split |
| Basel Committee, *Guidelines: Prudential Treatment of Problem Assets* (BIS, 2017) | The international NPL-definition standard RBI's own framework is harmonized against, useful context for comparing India's norms to a global bank's |

**Implemented here.** DPD/NPA-age-based classification and secured/unsecured provisioning
(`finmodel.npa_classification`). Rates are illustrative of the published circular as a worked example — RBI
amends specific segment rates periodically, so a live provisioning calculation should be checked against the
current circular, exactly as this toolkit's own module docstring notes.

## 11. FX carry trade and interest rate parity  (`finmodel.carry_trade`)

| Source | Author(s) | What it teaches |
|---|---|---|
| *Options, Futures, and Other Derivatives* | John Hull (Pearson) | Covered interest rate parity's no-arbitrage derivation exactly as this module implements it |
| *International Financial Management* | Cheol Eun, Bruce Resnick (McGraw-Hill) | Uncovered interest rate parity and the carry trade as a direct bet against it |
| Fama, E. (1984), "Forward and Spot Exchange Rates," *Journal of Monetary Economics* | Eugene Fama | The seminal paper documenting the "forward premium puzzle" — that forward rates are, empirically, poor predictors of future spot rates, which is precisely why carry trades have historically been profitable on average despite CIP holding as a no-arbitrage identity |
| Burnside, C., Eichenbaum, M., Rebelo, S. (2007-2011 NBER working-paper series), "Carry Trade and Momentum in Currency Markets" | Burnside, Eichenbaum, Rebelo | Modern empirical evidence on carry-trade returns and crash risk |
| Menkhoff, L., Sarno, L., Schmeling, M., Schrimpf, A. (2012), "Carry Trades and Global Foreign Exchange Volatility," *Journal of Finance* | Menkhoff et al. | Links carry-trade returns to a global volatility risk factor — the modern academic explanation for why the forward premium puzzle persists |

**Implemented here.** Covered interest rate parity's forward rate, the unhedged carry trade's real cash
flow, and break-even depreciation — with this toolkit's own test suite confirming the textbook result that
break-even depreciation equals exactly the CIP forward premium (`docs/RETAIL_BANKING_TOOLS.md`).

---

## What this survey did NOT find a defensible source to build from

- **Duration-gap / repricing-gap interest-rate-risk analysis** (bank ALM) — real and well-documented (Rose &
  Hudgins, Saunders & Cornett both cover it), but needs a full bank balance sheet with maturity/repricing
  buckets to reconcile a real implementation against, which none of this session's worked examples provide.
- **Mack's chain-ladder standard-error formula** — the natural statistical companion to the chain-ladder
  point estimate already built, deferred for the same reason: no real multi-year triangle with a known
  eventual outcome to validate the confidence interval against.
- **Bornhuetter-Ferguson reserving** — flagged in `docs/OPERATING_FINANCE_TOOLS.md` as a direct, well-scoped
  extension of `finmodel.loss_reserving` once there's a real a-priori loss ratio to reconcile it against.
