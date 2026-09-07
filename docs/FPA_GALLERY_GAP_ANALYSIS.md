# FP&A template-gallery gap analysis

A different kind of survey from `docs/MORE_CFI_TEMPLATES.md` (which cross-referenced this toolkit's own
636-entry CFI/BIWS/Macabacus catalog): this one surveys the free-template galleries published by FP&A
*software vendors* — the tools finance teams reach for once a model leaves the classroom-CFI world and
becomes a recurring operating process. Two sources were given directly, plus eight more found by
following what each site itself cited or linked to as comparable free-template resources:

| Source | URL |
|---|---|
| Cube Software | https://www.cubesoftware.com/blog/free-fpa-excel-templates |
| Microsoft Excel Cloud gallery | https://excel.cloud.microsoft/create/en/financial-management-templates/ |
| Smartsheet | https://www.smartsheet.com/top-excel-financial-templates |
| Vertex42 | https://www.vertex42.com/ExcelTemplates/ |
| insightsoftware | https://insightsoftware.com/blog/11-financial-model-examples-and-templates/ |
| Vena Solutions | https://www.venasolutions.com/blog/top-5-downloaded-free-excel-templates-businesses-fpa-leaders-fpa-department-goals |
| PivotXL | https://pivotxl.com/free-excel-templates-for-accounting-finance/ |
| Wall Street Prep (free resources) | https://www.wallstreetprep.com/free-resources/ |
| Coefficient | https://coefficient.io/templates |
| SCORE.org | https://www.score.org/business-planning-financial-statements-template-gallery/ |

## The knowledge graph

The full cross-reference — which source cites which template category, and whether this toolkit already
covers it, just built it, deliberately deferred it, or ruled it out of scope — is a machine-readable graph
at [`catalog/fpa_gallery_graph.json`](../catalog/fpa_gallery_graph.json): 10 source nodes, 19 category
nodes, each category edge-linked to its citing sources and to either a `finmodel` module (`covered_by` /
`already_covered`) or a `reason` string (`deferred` / `not_applicable`). It follows the same node/edge shape
as `finmodel.catalog`'s own CFI cross-reference, scoped to this different source set instead.

## What the survey found

Stripping out categories every gallery just re-lists from the CFI/BIWS world this toolkit already covers
(3-statement models, DCF/merger/LBO/comps, loan amortization, generic what-if data tables, cost-benefit
NPV wrappers — see the graph's `already_covered` entries for the specific module each maps to), six
categories were cited by multiple independent vendor galleries, were genuinely absent from the ~30 modules
already built this session, and had a real, standard, formula-defined technique behind the template name
rather than just a fill-in-the-blank layout. All six are now built:

| Category | Cited by | Module | Real technique |
|---|---|---|---|
| Budget-vs-actual variance | Cube, Vena, PivotXL, Coefficient | `finmodel.variance_analysis.budget_vs_actual_variance` | price/rate variance + volume/efficiency variance decomposition |
| Sales mix & quantity variance | Cube, Vena, PivotXL, Coefficient | `finmodel.variance_analysis.sales_mix_and_volume_variance` | Horngren's multi-product mix/quantity/price decomposition (*Cost Accounting: A Managerial Emphasis*) |
| Horizontal & vertical statement analysis | PivotXL | `finmodel.variance_analysis.horizontal_analysis` / `.vertical_analysis` | YoY % trend analysis; common-size (% of revenue or % of total assets) analysis |
| Headcount / workforce planning | Cube, Vena | `finmodel.fpa_planning.headcount_cost_schedule` | fully-loaded cost (base × benefits load) with per-role staggered start months |
| Driver-based rolling forecast | Cube, Vena, PivotXL | `finmodel.fpa_planning.rolling_forecast` | re-anchors the forecast off the latest actual, not a static annual budget |
| Break-even / CVP analysis | SCORE.org, Smartsheet | `finmodel.breakeven` | contribution margin, break-even units/revenue, margin of safety, degree of operating leverage |

A seventh item, VC-style early-stage valuation (cited by Wall Street Prep's free-resources page, distinct
from the CFI-catalog VC/PE valuation templates already surveyed in `docs/MORE_CFI_TEMPLATES.md`), was also
built: `finmodel.cap_table.vc_method_valuation()` implements Sahlman's VC Method (Harvard Business School,
*A Method for Valuing High-Risk, Long-Term Investments*) — working backward from a target exit value and
required return (or multiple) to the ownership stake a round must carry today, adjusted for expected future
dilution, and from there to implied pre-/post-money valuation. It slots into the existing `finmodel.cap_table`
module rather than a new one, since it shares that module's cap-table vocabulary (ownership %, pre-/
post-money) and is exercised by the same `from_dict()` entry point.

## What was found but deliberately not built

Two more categories were real and distinct, but scoped out:

- ~~**Sales quota & rep-capacity planning**~~ (Cube, Vena) — **RESOLVED**, see
  `docs/DEFERRED_GAPS_REVISITED.md`: built as its own module, `finmodel.sales_capacity_planning`, rather than
  as an extension of `finmodel.cohort_analysis` after all — the unit of analysis is genuinely different (rep
  productivity ramps and quota attainment, not customer retention), even though both use a cohort-by-tenure
  structure. The "real sales-comp dataset" the original deferral asked for was unnecessary — a hand-traced
  ramp-curve example is enough to build and verify the mechanic correctly.
- ~~**WIP / percentage-of-completion contract accounting**~~ (PivotXL) — **RESOLVED**, see
  `docs/DEFERRED_GAPS_REVISITED.md`: built as `finmodel.percentage_of_completion`. The "real dataset" the
  original deferral asked for was unnecessary — the cost-to-cost method is exact and self-verifying against
  its own accounting identity (cumulative recognized revenue must equal exactly the contract price once
  costs incurred reach 100% of the total estimate).

Three more were ruled out of scope entirely, because they aren't calculations this toolkit's format can
represent:

- **Annual Operating Plan (AOP)** (PivotXL) — an orchestration of headcount + opex budget + revenue plan +
  capex into one annual process artifact, not a distinct formula; every piece it would combine is already a
  `finmodel` module.
- **Month-end close checklist** (PivotXL, Coefficient) — a process/workflow tracker, not a financial
  calculation.
- **Trial-balance-to-financial-statements automation** (PivotXL) — ERP/bookkeeping-integration territory,
  outside this toolkit's corporate-finance and FP&A modeling scope.
- **Personal-finance calculators** (Microsoft, Vertex42) — mortgage payoff, retirement, and personal-budget
  templates are consumer-finance tooling, unrelated to the corporate/FP&A scope of everything else here.

## Test coverage

`tests/test_variance_analysis.py` (7 tests) checks the variance decompositions against the real algebraic
identity that their components must sum exactly to the total variance; `tests/test_fpa_planning.py`
(5 tests) checks that a role's cost never appears before its own start month and that the rolling forecast
re-anchors off the *last* actual, not the first; `tests/test_breakeven.py` (6 tests) checks break-even
units/revenue and margin of safety against hand-computed values, plus the real property that the degree of
operating leverage is most extreme right at the break-even point and falls as volume rises above it; the
new VC-method tests in `tests/test_cap_table.py` (5 tests) check the required-multiple/ownership/valuation
chain against a hand-worked example and confirm that adding expected future dilution both raises required
ownership today and lowers the implied pre-money valuation it backs out to.
