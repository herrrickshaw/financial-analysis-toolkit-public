# Professor and course survey: cross-referencing real syllabi against this toolkit

Every prior survey this session cross-referenced a template gallery or a literature list against the
toolkit's own coverage. This one instead starts from real, named **professors and their real, currently
(or recently) taught courses** at business schools across North America, Europe, and Asia, checked live via
web search on 2026-09-07, to find topics a genuine graduate finance/banking curriculum covers that this
toolkit still doesn't. It complements, rather than repeats, `docs/LEARNING_GUIDE.md` (corporate-finance
valuation reading list) and `docs/BANKING_LITERATURE_SURVEY.md` (books/regulatory sources behind the banking
modules) — this survey's unit of analysis is the *course*, not the book.

## What was found

| Professor | Institution | Course | Topics it covers |
|---|---|---|---|
| Bruce Tuckman | NYU Stern | Fixed Income Securities (Fall) | Fixed-income market overview, then the analytic tools for pricing, hedging and investing — duration, convexity, term-structure modeling. Tuckman is also the author of the standard textbook *Fixed Income Securities: Tools for Today's Markets* |
| Johannes Stroebel / D. Sam Chandan | NYU Stern | Real Estate specialization (MBA) | Economics of real-estate development and investment, financing of projects, leasing and appraisal, real-estate-linked financial instrument pricing/valuation, primary and secondary market structure, legal/tax/regulatory environment |
| P C Narayan | IIM Bangalore | Banking and Financial Markets: A Risk Management Perspective (IIMBx MOOC) | Bank risk types, asset securitization (RMBS and credit-card securitization specifically named), credit derivatives, interest-rate risk, regulatory capital frameworks |
| Christopher M. O'Daniel | Ohio State (Fisher College) | BUSFIN 4265, Financial Institutions | Bank balance-sheet management, interest-rate risk (repricing gap), regulatory capital, the standard undergraduate/MBA "financial institutions" curriculum |
| (HEC Paris Finance faculty, Financial Engineering cluster) | HEC Paris | Master in International Finance — Financial Engineering electives | Energy markets, stochastic processes, FX derivatives trading, origination of structured products |
| (Faculty across Wisconsin, UT Austin, UIUC, Columbia) | Multiple (ratemaking/reserving actuarial programs) | P&C actuarial ratemaking & reserving courses | Loss triangles, loss development, on-level premium, IBNR estimation, frequency/severity modeling, credibility methods — the same syllabus `finmodel.loss_reserving`'s chain-ladder implementation already covers |

This list is intentionally a sample, not exhaustive — the point of the exercise is the cross-reference
below, not cataloguing every finance professor globally.

## Cross-referencing against this toolkit's coverage

| Course topic | Covered here? | Module |
|---|---|---|
| Real-estate development pro forma, financing, appraisal | Yes | `finmodel.real_estate_development`, `finmodel.project_finance.cap_rate_valuation` |
| P&C ratemaking, loss reserving, IBNR | Yes | `finmodel.loss_reserving`, `finmodel.insurance_pricing` |
| Bank regulatory capital (Basel ratios) | Yes (US CET1/Tier1/leverage) | `finmodel.bank_model` |
| India-specific NPA classification/provisioning | Yes | `finmodel.npa_classification` |
| FX derivatives / interest rate parity | Yes | `finmodel.carry_trade` |
| **Bond duration, convexity, DV01** | **No — a real gap.** Tuckman's own course is built entirely around these tools, and this toolkit already touches bonds (`finmodel.convertible_bonds`, `finmodel.cmo`) without ever computing them | **Built this round: `finmodel.fixed_income_risk`** |
| **Credit risk: PD/LGD/EAD, Basel IRB risk-weighted assets** | **No — a real gap.** Named explicitly in P C Narayan's course and every credit-risk curriculum (TU Delft, GARP FRM Part II), and distinct from this toolkit's existing India-specific (`finmodel.npa_classification`) or US-CECL-style (`finmodel.bank_model`) provisioning | **Built this round: `finmodel.credit_risk`** |
| **Bank interest-rate risk: repricing gap, NII sensitivity** | **No — a real gap**, and one this toolkit's OWN `docs/BANKING_LITERATURE_SURVEY.md` had already flagged as deferred ("needs a full bank balance sheet... to reconcile against") — re-examined here and built anyway, since a standalone bucketed-gap input (which every course teaches the technique on) is enough to compute it correctly without needing a specific real bank's full balance sheet | **Built this round: `finmodel.interest_rate_risk`** |
| Asset securitization: RMBS and credit-card master-trust structures | Partially — `finmodel.cmo` covers RMBS-style sequential-pay tranching; the credit-card master-trust mechanic (named explicitly in P C Narayan's course) | **RESOLVED — `finmodel.credit_card_abs`, see `docs/DEFERRED_GAPS_REVISITED.md`** |
| FX derivatives trading / structured-product origination (HEC Paris) | Partially — `finmodel.options` covers vanilla option pricing; exotic FX structured products are a real, much larger scope | **Deferred — see below** |

## What was built this round

- **`finmodel.credit_risk`** — expected loss (PD x LGD x EAD) and the real Basel II/III Foundation IRB
  formula for corporate exposures, including its own inverse-normal-CDF helper (Acklam's rational
  approximation, verified against published exact quantiles) and verified against Basel's own well-known
  published corporate risk-weight reference point (PD=1%, LGD=45%, 2.5-year maturity floor -> a ~92.3% risk
  weight — this toolkit's own test suite reproduces that figure to within 1 percentage point).
- **`finmodel.interest_rate_risk`** — the repricing-gap model and first-order NII sensitivity to a rate
  shock, the exact technique named in Ohio State's Financial Institutions syllabus and Saunders & Cornett's
  textbook, closing a gap this toolkit had explicitly flagged as deferred in an earlier survey.
- **`finmodel.fixed_income_risk`** — bond price, Macaulay/modified duration, DV01, and convexity, verified
  against the classic textbook reference bond (a 2-year, 10%-coupon, annual-pay bond priced at par has a
  Macaulay duration of ~1.91 years) and against the exact identity that a zero-coupon bond's duration equals
  its own maturity.

## What was deliberately left out

- ~~**Credit-card / master-trust securitization**~~ — **RESOLVED**, see `docs/DEFERRED_GAPS_REVISITED.md`:
  built as `finmodel.credit_card_abs` (excess spread, the real 3-month-average early-amortization trigger
  every master-trust prospectus defines, and the revolving-vs-amortization cash-flow mechanic under both
  pass-through and controlled-amortization methods). The "own careful, separately-verified formula set" the
  original deferral worried about turned out to be entirely hand-verifiable without needing a real trust's
  historical data.
- **FX structured-product origination / exotic derivatives** (HEC Paris' Financial Engineering cluster) —
  `finmodel.options` already covers vanilla Black-Scholes pricing and the Greeks; barrier options, Asian
  options, and other exotics are each their own real pricing model with no single unifying formula to build
  in one pass, better done individually against a specific real product term sheet.
- **A full professor/course "knowledge graph" artifact** (matching the JSON-graph pattern used in
  `catalog/fpa_gallery_graph.json`) — considered, but the professor/course list above is short enough (six
  rows) that a graph structure would add indirection without adding clarity; the direct cross-reference table
  serves the same purpose more legibly at this scale.

## Test coverage

`tests/test_credit_risk.py` (7 tests) checks the inverse-normal-CDF helper against published exact
quantiles, checks the Basel IRB formula against its own published reference risk weight, and checks that
risk weight rises monotonically with PD over the normal working range. `tests/test_interest_rate_risk.py`
(4 tests) checks the repricing-gap arithmetic by hand and checks the real directional property that an
asset-sensitive bank's NII rises with rates while a liability-sensitive bank's NII falls.
`tests/test_fixed_income_risk.py` (4 tests) checks the classic 2-year par-bond reference point, the real
property that a longer-maturity bond has strictly higher duration, and the exact zero-coupon-bond duration
identity.

## Sources

- [MBA in Finance Syllabus 2026: Subjects & Specialisations](https://www.zelleducation.com/blog/mba-in-finance-syllabus/)
- [Course Syllabus: Financial Institutions, BUSFIN 4265, Ohio State (Fisher College)](https://s3.us-east-2.amazonaws.com/files.fisher.osu.edu/public/syllabi/BUSFIN%204265%20Financial%20Institutions%20-%20Syllabus%20-%20SP%202026%20BUSFIN%204265_C%20ODaniel.pdf)
- [NYU Stern fixed-income course listing (Bruce Tuckman)](https://web-apps-shib.stern.nyu.edu/syllabi/static/syllabusfiles/FINC-UB.26_001_F2026.pdf)
- [NYU Stern MBA Real Estate specialization](https://www.stern.nyu.edu/portal-partners/academic-affairs-advising/specializations/real-estate)
- [Johannes Stroebel (Wikipedia)](https://en.wikipedia.org/wiki/Johannes_Stroebel)
- [IIMBx: Banking and Financial Markets — A Risk Management Perspective](https://iimbx.iimb.ac.in/catalog/banking-and-financial-markets-a-risk-management-perspective/)
- [HEC Paris Master in International Finance — course content](https://www.hec.edu/en/masters-programs/msc-international-finance/course-content)
- [University of Wisconsin-Madison Actuarial Science course catalog](https://guide.wisc.edu/courses/act_sci/)
- [UT Austin Actuarial Course Descriptions](https://sites.utexas.edu/actuarial-sciences/actuarial-course-descriptions/)
- [TU Delft: Advanced Credit Risk Management](https://learningforlife.tudelft.nl/advanced-credit-risk-management/)
