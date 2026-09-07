# Gap analysis: financial-analysis-toolkit vs the open-source field and the EUA financial-management toolkit

Sources: GitHub search on 2026-09-06 (`gh search repos`, 15 queries — financial modeling, DCF, LBO, merger model,
comparable company analysis, financial statement analysis, ratios, three-statement, corporate finance, Excel formula
parsing — 144 unique repositories, README feature lists read for the 18 most relevant), plus the EUA–ATHENA
*Toolkit for Financial Management* (2015) for the institutional / non-profit side.

## 1. Who does what (top repositories by stars, de-duplicated)

| Repository | Stars | What it offers | Overlap with this toolkit |
|---|---|---|---|
| LongOnly/Quantitative-Notebooks | 1,394 | Teaching notebooks: quant finance, algo trading, financial modelling | Education only; no engines |
| joshuaulrich/quantmod (R) | 904 | Quant modelling framework — data, charting, technical indicators | Different domain (market data / TA) |
| FinancialModelingPrepAPI / daxm/fmpsdk / imbenrabi MCP server | 673 / 211 / 143 | Wrappers for the FMP data API | Data access, no models |
| agentii-ai/agentii-investment-intelligence | 203 | 48 LLM "skills": DCF, comps, 3-statement, LBO, SOTP → .xlsx/.pptx with citations, SEC/XBRL tools | Same model set as ours, LLM-driven, needs paid API |
| Ali-Marandi/FinAnalyzer | 108 | Bank reconciliation / period close / audit trail desktop app | Accounting controls, not valuation |
| jimlindstrom/FinModeling (Ruby) | 105 | Pulls 10-K/10-Q from EDGAR, reformulates statements, residual-income valuation, CAPM/Fama-French | EDGAR ingestion + residual income model |
| willpowerju/3-statement-ultra-for-finance | 84 | LLM skill: formula-only 3-statement build, 19 QC checks, CN/IFRS/US GAAP | Workbook QC ideas |
| tamilselvanarjun/finmodels & quantmodels | 73 / 74 | DCF, LBO, IPO, portfolio optimisation classes | Simplified engines (no template reconciliation) |
| leonarduschen/pyfinmod | 65 | NPV/IRR, FCF, WACC + DCF on FMP data | Subset |
| TimoKats/fibooks | 59 | Financial-statement objects and ratio analysis | Subset of `ratios` |
| xuelixunhua/stock_DCF | 55 | DCF notebooks from statement analysis | Subset |
| kbhujbal/AlphaAnalyst | 47 | Autonomous equity-research agent: DCF, peer comps, memo | Agent workflow |
| stockvaluation-io | 32 | Local-first MCP DCF workflow with scenarios, data-quality warnings | Reverse DCF / scenario UX |
| noahnan-max/governed-dcf-skill | 12 | FCFF/FCFE/DDM/RI/NAV/SOTP routing, WACC×g sensitivity, reverse DCF, LibreOffice recalculation, run manifests | Governance + reverse DCF |
| EmanueleSturzo/DCF-Valuation-Model | 3 | Monte-Carlo DCF (10k runs), bull/base/bear, exit multiple, implied growth, auto comps | Monte Carlo + implied growth |
| dafahentra/dcf-valuation-tool | 5 | Probabilistic DCF, global beta fetch, JSON export | Monte Carlo |
| shubhwade/telmus | 4 | Piotroski F, Altman Z, Beneish M, peer valuation, MCP server | Health scores |
| Fayepasvouri / JimCortes / Calivala LBO repos | 11 / 7 / 9 | Simple LBO models in Python + Excel round-trip | Subset of `lbo` |
| eonofrey/comparable_company_analysis | 17 | Comps with log-transformed multiples, Quandl/Intrinio data | Statistical comps |

Nothing in the field reconciles Python engines cell-for-cell to the industry templates (CFI, BIWS, Macabacus, ASM) or
transpiles arbitrary workbooks; that remains this toolkit's distinctive capability (`xlcalc`, 100% on 14 workbooks).

## 2. Feature gaps found and what was done

| Gap (who has it) | Status in this toolkit |
|---|---|
| **SEC EDGAR ingestion** (FinModeling, AlphaAnalyst, agentii) | **Added** `finmodel.edgar` — company-facts reader with tag precedence per fiscal year, derived EBIT/EBITDA/net debt, compact extracts in `data/edgar/` |
| **Health / quality scores** — Altman Z, Beneish M, Piotroski F (telmus, FinAnalyzer) | **Added** `finmodel.scores` (three Altman variants, 8-variable Beneish, 9-signal Piotroski) |
| **Comps / precedents / football field** (agentii, eonofrey, EmanueleSturzo) | **Added** `finmodel.comps`, reconciled to BIWS 107-21 / 107-27 and the CFI football-field template |
| **Reverse DCF (implied growth) and Monte-Carlo DCF** (governed-dcf, EmanueleSturzo, dafahentra, stockvaluation-io) | **Added** `dcf.implied_growth()` and `dcf.monte_carlo()` (dependency-free, seeded) |
| **Institutional cost allocation / resource allocation / income diversification** (EUA toolkit; no GitHub project covers it) | **Added** `finmodel.costing` — formula-based resource allocation with top-slice and strategic pots, two-step driver-based cost allocation with indirect-cost rates on grossed-up salary, full-economic-cost pricing, income-source HHI and diversification ranking |
| **Real-data validation and applied case studies** (AlphaAnalyst eval suite, agentii citations) | **Added** `scripts/comps_validation.py` (steel peers, warehouse prices, cross-check vs the market-pipeline ratio ledger) and `scripts/ma_case_study.py` (Microsoft/Activision, Chevron/Hess, Cisco/Splunk before-and-after) |
| **Cost of capital: CAPM, synthetic rating, bottom-up beta, WACC** (Damodaran spreadsheets; no GitHub repo does the synthetic-rating step) | **Added** `finmodel.wacc` — CAPM cost of equity, Hamada beta unlever/relever, bottom-up beta from a peer set, Damodaran-style synthetic credit rating from interest coverage, market-value-weighted WACC |
| **Residual-income / EVA valuation** (FinModeling) | **Added** `finmodel.residual_income` — clean-surplus residual income (EBO) with fading-persistence or growing terminal value, and EVA / economic-profit firm valuation |
| **Sum-of-the-parts** (agentii, governed-dcf) | **Added** `finmodel.sotp` — per-segment multiple or override value, ownership stakes, capitalised corporate costs, conglomerate discount, full equity bridge |
| **Workbook QC / hard-code scan** (3-statement-ultra's 19 QC checks, agentii's audit-xls) | **Added** `finmodel.audit` — error-value scan, hard-coded "plug" detection inside formulas and inside formula rows, R1C1-normalised inconsistent-formula detection across a row, external-link and hidden-sheet flags, optional `xlcalc.verify()` recomputation; found 112 real findings (78 hard-coded plugs, 1 very-hidden sheet) on the 15,323-formula Macabacus merger model |
| **Mid-year discounting convention** (A Simple Model's `DCF_MidYear Convention.xlsx`) | **Added** `DCFInputs.mid_year` — discounts each period's cash flow from its midpoint while leaving the terminal value at period end |
| Portfolio optimisation / efficient frontier (finmodels, pyfinmod roadmap) | Out of scope here; the market-pipeline repo already has an MPT optimiser |
| Live market-data API wrappers (FMP, yfinance) | Deliberately not bundled — the warehouse and EDGAR are used instead; adapters are two functions |
| LLM-agent packaging (agentii, 3-statement-ultra, financial-models) | Not a goal; every engine is plain Python with JSON in/out, so any agent can call it |

## 3. What the EUA toolkit adds that corporate templates do not

The EUA–ATHENA toolkit is written for universities, but its six building blocks map onto any non-profit or public body:

1. **Resource allocation model** — direct allocation, formula allocation, top-slicing, strategic pots, transparency → `costing.resource_allocation`.
2. **Budgeting and long-term financial planning** (annual plan inside a ≤5-year forecast) → `projection` engine + `charts`.
3. **Basic costing model** — activities (teaching / research / other), cost objects, cost drivers (student numbers, person-years, effective work time, space), allocation method, cost basis; Helsinki's salary add-on rate (53–55%) and indirect-cost rates (84–150%) as worked examples → `costing.allocate_costs`, `costing.full_cost_price`.
4. **Organisational structures and responsibilities** — governance, not modelling.
5. **Human-resource development** — not modelling.
6. **Income diversification strategy** — income by source (public, tuition, business & industry, private sponsors, other), stability and growth potential of each, action and resource plan → `costing.income_diversification` (shares, Herfindahl concentration, priority ranking).

## 4. Method note

Stars measure popularity, not correctness; several high-star repositories are API wrappers or course material. The
criterion used for "gap" was *a modelling capability that at least two independent projects ship and that a CFI paid
template also promises* (see `docs/PAID_TEMPLATES.md`), or a capability the EUA toolkit describes that nothing on GitHub
covers. Raw search output: `catalog/github_landscape.json`.
