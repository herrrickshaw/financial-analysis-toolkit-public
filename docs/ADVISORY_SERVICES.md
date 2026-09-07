# Advisory-services modules: what real CFO/VC/impact/strategy firms do, built as code

A market survey of what real, named service providers actually sell — fractional-CFO firms, impact-investing
consultancies, VC funds, and the classic strategy-consulting frameworks — turned into five new, tested
`finmodel` modules. Each module traces to a specific, cited real service, not an invented feature list.

## What was surveyed

- **[Flipcarbon](https://flipcarbon.com/fractional-cfo-service)** (Bengaluru-based fractional/virtual CFO firm,
  founded 2014): financial modeling, Annual Operating Plans, **13-week rolling cash flow forecasts**, costing/
  pricing, working-capital optimization, MIS/dashboards, M&A advisory, financial due diligence, **ESOP scheme
  design**, transfer pricing. Several of these (financial modeling, M&A advisory, due diligence) were already
  covered by this toolkit's existing `three_statement`/`comps`/`dcf`/`merger`/`scores` engines; the two genuinely
  new, distinctive deliverables — the 13-week cash flow forecast and ESOP/cap-table design — are new modules
  below.
- **[Sagana](https://sagana.com/fund-managers/)** (Swiss impact-investing advisory firm, founded 2017, $800M
  AUM advised): gender-smart/**2X** integration, climate strategy and GHG tracking, portfolio technical
  assistance, **Impact Measurement and Management (IMM)**, fund-manager capacity building. The quantifiable
  pieces (2X Criteria screening, IMP's ABC impact classification, GHG intensity) are a new module below; the
  people/capacity-building services aren't the kind of thing that becomes code.
- **VC funds generally**: the standard LP-reporting metrics (DPI/RVPI/TVPI/IRR) and GP/LP carry-waterfall
  mechanics every fund's finance function produces — a new module below.
- **McKinsey / BCG / Bain** (a market survey of MBB's own public materials and third-party strategy-framework
  references — see Sources at the bottom): M&A due diligence and valuation (already covered by this toolkit's
  comps/DCF/merger engines), plus two real, named, decades-old portfolio-classification frameworks (the **BCG
  Growth-Share Matrix** and the **GE-McKinsey Nine-Box Matrix**) and **TAM/SAM/SOM market sizing** — a new
  module below.

## The five new modules

### 1. `finmodel.cap_table` — priced-round dilution and an exit waterfall

The two mechanics that are easy to get wrong: the **option pool "shuffle"** (a pool top-up specified as a
*post-financing* percentage dilutes only existing holders, priced pre-money — solved here as a closed-form
equation, verified in tests to reproduce the new investor's exact intended ownership regardless of the pool
target) and a **non-participating preferred holder's conversion decision at exit** (take the greater of the
liquidation preference or the as-converted pro-rata share — never both, never automatically the preference).

```bash
finmodel cap-table examples/cap_table_series_ab.json
```

### 2. `finmodel.vc_fund_metrics` — LP-reporting metrics and a GP/LP carry waterfall

DPI/RVPI/TVPI (ILPA's own reporting-template definitions) plus fund- and deal-level IRR (reusing
`finmodel.fin.xirr`, the same primitive the DCF engine uses) and a European whole-fund carry waterfall (return
of capital → preferred return/hurdle → GP catch-up → residual split). Verified that once the catch-up tier
fully completes, the GP's total take is *exactly* the target carry percentage of total profit above return of
capital — the whole documented purpose of the catch-up mechanic.

```bash
finmodel vc-fund examples/vc_fund_demo.json
```

### 3. `finmodel.cash_flow_forecast` — 13-week rolling direct-method cash forecast

Flipcarbon's own named deliverable. Direct method (real cash in, real cash out, no accrual adjustments) rolled
forward week by week, with covenant-breach flagging (exactly which future week a minimum-liquidity requirement
would be breached) and a forecast-vs-actual variance report — the real, weekly treasury discipline of
recalibrating a rolling forecast rather than treating the original plan as fixed.

```bash
finmodel cash-flow-forecast examples/cash_flow_forecast_13wk.json
```

### 4. `finmodel.impact_scoring` — gender-lens and climate screening

A simplified implementation of the public **2X Criteria** (entrepreneurship/leadership/employment/consumption —
not a substitute for formal 2X Certification), the Impact Management Project's real **ABC classification**
(Act to avoid harm / Benefit stakeholders / Contribute to solutions — with an unevidenced additionality claim
correctly downgraded from C to B), and GHG Protocol-based emissions intensity (Scope 1+2 kept separate from the
much-less-precise Scope 3, not silently blended).

```bash
finmodel impact examples/impact_scoring_demo.json
```

### 5. `finmodel.strategy_frameworks` — TAM/SAM/SOM, BCG matrix, GE-McKinsey nine-box

Top-down and bottom-up market sizing; the BCG Growth-Share Matrix (relative market share vs market growth rate
→ Star/Cash Cow/Question Mark/Dog, checked at its real 1.0x/10% boundary values); the GE-McKinsey Nine-Box
(weighted multi-factor industry-attractiveness and business-strength scores, tercile-bucketed into High/Medium/
Low, placed into the three real named zones — Invest/Grow, Selective/Hold, Harvest/Divest).

```bash
finmodel strategy examples/strategy_frameworks_demo.json
```

## What wasn't built, and why

Several real MBB/CFO-firm services are either already covered elsewhere in this toolkit (M&A valuation and due
diligence — `finmodel.comps`/`dcf`/`merger`/`scores`; financial modeling and business-model advisory —
`finmodel.three_statement`/`startup_model`) or are fundamentally qualitative consulting work with no defensible
quantitative model to write (financial-process SOPs, governance-framework design, organizational/talent
strategy, McKinsey's 7S or Porter's Five Forces as pure frameworks rather than a scored output). Transfer-pricing
comparable-margin analysis is a real, buildable extension of the existing sector-comps engine but was left for a
future pass rather than rushed.

## Sources

- [Flipcarbon: Fractional CFO Service](https://flipcarbon.com/fractional-cfo-service)
- [Flipcarbon: Virtual CFO Services](https://www.flipcarbon.com/virtual-cfo-services/)
- [Sagana: Fund Managers](https://sagana.com/fund-managers/)
- [Sagana: Consulting](https://sagana.com/consulting/)
- [Umbrex: BCG Growth-Share Matrix](https://umbrex.com/resources/frameworks/strategy-frameworks/bcg-growth-share-matrix/)
- [Umbrex: GE-McKinsey Nine-Box Matrix](https://umbrex.com/resources/frameworks/strategy-frameworks/ge-mckinsey-nine-box-matrix/)
- [McKinsey & Company: M&A Strategy & Due Diligence](https://www.mckinsey.com/capabilities/m-and-a/how-we-help-clients/m-and-a-strategy-due-diligence)
- [Bain & Company: M&A Due Diligence Consulting](https://www.bain.com/consulting-services/mergers-acquisitions/corporate-due-diligence/)
