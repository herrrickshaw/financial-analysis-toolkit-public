"""Knowledge base for the paid-only CFI template titles: what each does, public analogues, literature, and
how much of it this toolkit already implements.

Inputs: catalog/catalog.json (titles), catalog/paid_templates_raw.json (scraped CFI resource-page description and
section headings), catalog/alternatives.json (tag-matched public files), plus authored category descriptions,
literature pointers and toolkit coverage.  Output: catalog/paid_templates.json + docs/PAID_TEMPLATES.md and the
`finmodel catalog paid [--title ...]` command.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from .catalog import CATALOG_DIR

# category -> (what these templates do, literature, toolkit coverage, coverage level)
CATEGORIES: Dict[str, Dict[str, Any]] = {
    "3-statement / operating model": {
        "match": r"3-statement|three statement|operating budget|forecasting template|monthly cash flow|fp&a|rollforward|advanced all in one|operational modeling|financial projection|audit and balance|intro to 3-statement|consolidation|amzn financial model|tmt financial model|ecommerce|saas model|mining model|robo-advisor|etf allocator|individual equity allocation|budgeting and forecasting",
        "does": "Links income statement, balance sheet and cash flow with supporting schedules (working capital, PP&E, debt) so any assumption flows through all three; sector versions (SaaS, e-commerce, TMT, mining, consolidation) swap in industry revenue drivers.",
        "literature": "Pignataro ch. 1–8; Tjia ch. 4–11; Benninga part I; CFI Financial Modeling Guidelines PDF (downloaded); MIT OCW 15.535; Saylor BUS202 pro-forma units",
        "toolkit": "finmodel.three_statement (reconciled to the free CFI case study), finmodel.projection (bottom-up monthly base year), xlcalc transpiler for any downloaded operating model",
        "coverage": "full"},
    "DCF / intrinsic valuation": {
        "match": r"\bdcf\b|dividend discount|business valuation|fcff vs fcfe|intrinsic|valuation model|financial institution dividend|introduction to bank valuation",
        "does": "Projects unlevered (FCFF) or levered (FCFE / dividend) cash flows, discounts them at WACC or cost of equity, adds a terminal value and bridges enterprise value to a per-share value with sensitivity tables.",
        "literature": "Damodaran Investment Valuation ch. 12–15 and `fcff.pdf`, `fcfe.pdf`, `ddm.pdf`; Koller ch. 8–12; Rosenbaum & Pearl ch. 3; CFA Level II residual income / EBO readings",
        "toolkit": "finmodel.dcf (stub period, XNPV, mid-year convention, perpetuity + exit multiple TV, sensitivity, reverse DCF via implied_growth, Monte Carlo via monte_carlo), finmodel.residual_income (residual income / EBO and EVA), finmodel.charts dcf template; Damodaran ginzu spreadsheets in downloads/damodaran",
        "coverage": "full"},
    "LBO": {
        "match": r"\blbo\b|leveraged buyout|debt capacity",
        "does": "Funds an acquisition with tranches of debt sized off EBITDA, projects cash flow to service and sweep debt, exits at a multiple and solves for sponsor IRR / MOIC with scenario and exit-multiple tables.",
        "literature": "Rosenbaum & Pearl ch. 4–5; Pignataro part III; BIWS Simple LBO / cash-sweep / PIK tutorials (downloads/biws); Macabacus long- and short-form LBO (downloads/macabacus)",
        "toolkit": "finmodel.lbo (reconciled to A Simple Model; sweep, PIK, revolver, warrants, returns attribution), charts lbo template",
        "coverage": "full"},
    "M&A / merger": {
        "match": r"m&a|merger|purchase price allocation|business combinations|intro to mergers|accretion|consolidation model|restructuring",
        "does": "Combines acquirer and target, funds the deal with cash / debt / stock, allocates the purchase price (write-ups, goodwill, deferred taxes), layers synergies and integration costs and tests EPS accretion / dilution and pro-forma leverage.",
        "literature": "Rosenbaum & Pearl ch. 6–7; Koller ch. 31; Damodaran synergy paper and `synergyvaluation.xls`; BIWS merger-model tutorial",
        "toolkit": "finmodel.merger (deal-level reconciled to BIWS; multi-year pro forma with PPA), charts merger template; Macabacus merger-model.xlsx verified 100% by xlcalc",
        "coverage": "full"},
    "Comparable companies / precedent transactions": {
        "match": r"comps|comparable|trading comps|transaction comps|benchmarking|energy industry|detailed comps",
        "does": "Spreads peer multiples (EV/EBITDA, EV/revenue, P/E) and precedent deal multiples, computes quartile ranges and applies them to the target; sector versions add industry KPIs.",
        "literature": "Rosenbaum & Pearl ch. 1–2; Damodaran `pe.pdf` and Investment Valuation ch. 17–20; BIWS comps and precedent files (downloads/biws); Investopedia CCA and precedent-transaction-analysis entries",
        "toolkit": "finmodel.comps (trading comps, precedents, implied valuation, football field — reconciled to BIWS 107-21/107-27 and the CFI football-field template), charts comps template",
        "coverage": "full"},
    "Ratios & financial analysis": {
        "match": r"ratio|turnover|days sales|days inventory|leverage|coverage|return on|ebt example|trend analysis|financial analysis fundamentals|normalizing|degree of leverage|working capital cycle|calculating net interest|risk weighted|bank ratio|bank of america|bank financial analysis|insurance company",
        "does": "Computes and interprets liquidity, efficiency, leverage, coverage and return ratios, common-size and trend analysis; bank / insurance versions use regulatory metrics (net interest income, risk-weighted assets, combined ratio).",
        "literature": "Penman ch. 9–12; CFA Level I FSA; CFI Financial Ratios Definitive Guide (downloaded PDF); MIT OCW 15.535; Altman (1968/2000), Beneish (1999), Piotroski (2000)",
        "toolkit": "finmodel.ratios (CFI ratio sheet), finmodel.scores (Altman Z, Beneish M, Piotroski F health/quality scores), glossary formulas; bank-specific regulatory ratios not implemented",
        "coverage": "partial"},
    "Cost of capital & capital structure": {
        "match": r"wacc|cost of capital|capital structure|corporate finance fundamentals|efficient frontier|market risk fundamentals|interest rate parity",
        "does": "Estimates cost of equity (CAPM), cost of debt and WACC, tests capital-structure choices and financing decisions.",
        "literature": "Damodaran Applied Corporate Finance ch. 4; corporate-finance packet 1 (`cfpacket1.pdf`); Koller ch. 15; MIT 15.401 CAPM lectures; Damodaran synthetic-rating methodology",
        "toolkit": "finmodel.wacc (CAPM cost of equity, Hamada beta levering/unlevering, bottom-up beta from peers, Damodaran-style synthetic credit rating from interest coverage, market-value-weighted WACC), dcf.discount_rate input + sensitivity; Damodaran `wacccalc.xls`, `capstru.xlsx`, `levbeta.xls` downloaded; free CFI WACC / Beta / CAPM calculators downloaded; efficient frontier and interest rate parity not implemented",
        "coverage": "partial"},
    "Real estate & project models": {
        "match": r"real estate|reit|cap rate|solar|renewable|project",
        "does": "Cash-flow models for property or infrastructure assets: NOI, cap rates, debt service coverage, construction and ramp-up, levered IRR.",
        "literature": "BIWS real-estate modelling KB (downloads/biws REPE files); Damodaran `reval.xls`; Yescombe, Principles of Project Finance",
        "toolkit": "fin (NPV/IRR/XIRR/PMT) and lbo tranche mechanics reusable; no dedicated real-estate engine",
        "coverage": "partial"},
    "Excel / charting / dashboards": {
        "match": r"excel|dashboard|goal seek|solver|chart|pitchbook|pitch deck|scenario & sensitivity|sensitivity analysis model",
        "does": "Spreadsheet technique: advanced formulas, scenario and sensitivity tables, dashboards and presentation output.",
        "literature": "Benninga; Rees, Principles of Financial Modelling; CFI Excel e-book (paid) — free CFI Excel Fundamentals files downloaded",
        "toolkit": "xlcalc (formula engine), dcf/lbo/merger sensitivity grids, charts module (data → chart template)",
        "coverage": "full"},
    "Options, trading & derivatives": {
        "match": r"option|trading strateg|put call|algorithmic|nvda|cmo|collateralized",
        "does": "Payoff diagrams, option strategies, put-call parity, algorithmic signals and structured-product cash-flow models.",
        "literature": "Damodaran `option.pdf` and real-option spreadsheets (downloaded); Hull, Options, Futures and Other Derivatives",
        "toolkit": "xlcalc supports NORMSDIST etc.; free CFI Black-Scholes calculator downloaded; ~/put_call_parity subsystem in market-pipeline",
        "coverage": "partial"},
    "Accounting topics": {
        "match": r"accounting for|depreciation-methods|leases|inventory|diluted shares|cash to accrual|lease",
        "does": "Worked accounting examples: lease capitalisation, inventory methods, depreciation methods, diluted EPS, equity-method investments.",
        "literature": "CFI Accounting e-book (downloaded); Penman; docs/GLOSSARY.md GAAP-vs-IFRS table",
        "toolkit": "glossary GAAP-vs-IFRS notes; xlcalc SLN/SYD; merger PPA/DTL logic",
        "coverage": "partial"},
    "Soft skills & career": {
        "match": r"diagnostic|questionnaire|feedback|appraisal|coaching|relationships|hybrid team|business decisions|nda|confidential information memorandum|investment banking manual|pitch",
        "does": "Non-modelling material: assessments, checklists and document templates.",
        "literature": "—", "toolkit": "not applicable", "coverage": "n/a"},
}


_STOP = {"template", "model", "the", "and", "of", "a", "for", "to", "complete", "example", "analysis", "excel", "financial"}


def _relevant(title: str, url: str) -> bool:
    """Keep a scraped page only when its slug shares a meaningful word with the title."""
    words = set(re.findall(r"[a-z0-9]+", title.lower())) - _STOP
    slug = set(url.rstrip("/").rsplit("/", 1)[-1].split("-"))
    hits = words & slug
    return bool(hits) and (len(hits) >= 2 or len(words) <= 2 or any(len(w) > 4 for w in hits))


def categorise(title: str) -> str:
    t = title.lower()
    for name, spec in CATEGORIES.items():
        if re.search(spec["match"], t):
            return name
    return "Other"


def build(catalog_dir: Path = CATALOG_DIR) -> Dict[str, Any]:
    cat = json.loads((catalog_dir / "catalog.json").read_text())
    raw = json.loads((catalog_dir / "paid_templates_raw.json").read_text()) if (catalog_dir / "paid_templates_raw.json").exists() else {}
    alts = {i["cfi_title"]: i for i in json.loads((catalog_dir / "alternatives.json").read_text())["items"]} if (catalog_dir / "alternatives.json").exists() else {}
    items = []
    for e in cat["entries"]:
        if e["source"] != "cfi" or e["access"] != "cfi-paid":
            continue
        c = categorise(e["title"]); spec = CATEGORIES.get(c, {})
        r = dict(raw.get(e["title"], {}))
        if r.get("url") and not _relevant(e["title"], r["url"]):
            r = {}                                   # generic search fallback, not this template's page
        desc = (r.get("description") or "").strip()
        items.append({"title": e["title"], "category": c, "cfi_page": r.get("url"), "cfi_description": desc,
                      "cfi_sections": r.get("headings", [])[:8], "what_it_does": spec.get("does", ""),
                      "analogues": [{"source": a["source"], "title": a["title"], "url": a["url"]} for a in alts.get(e["title"], {}).get("alternatives", [])[:5]],
                      "literature": spec.get("literature", ""), "toolkit": spec.get("toolkit", ""), "coverage": spec.get("coverage", "none")})
    summary = {"paid_titles": len(items), "with_cfi_page": sum(1 for i in items if i["cfi_page"]), "with_analogues": sum(1 for i in items if i["analogues"]),
               "coverage": {k: sum(1 for i in items if i["coverage"] == k) for k in ("full", "partial", "n/a", "none")},
               "by_category": {k: sum(1 for i in items if i["category"] == k) for k in list(CATEGORIES) + ["Other"]}}
    out = {"generated": cat["generated"], "summary": summary, "categories": {k: {kk: vv for kk, vv in v.items() if kk != "match"} for k, v in CATEGORIES.items()}, "items": items}
    (catalog_dir / "paid_templates.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    (Path(catalog_dir).parent / "docs" / "PAID_TEMPLATES.md").write_text(to_markdown(out))
    return out


def load_intent(catalog_dir: Path = CATALOG_DIR) -> Dict[str, Any]:
    """Analysis intent + reference sources per category (catalog/analysis_intent.json, built from Investopedia,
    Wall Street Prep, Macabacus and CFI resource pages)."""
    p = Path(catalog_dir) / "analysis_intent.json"
    return json.loads(p.read_text())["categories"] if p.exists() else {}


def to_markdown(out: Dict[str, Any]) -> str:
    s = out["summary"]; intent = out.get("intent") or load_intent()
    md = ["# Paid-only CFI templates: what they do, public analogues, literature, toolkit coverage", "",
          f"{s['paid_titles']} titles on the CFI dashboard need a paid plan. {s['with_cfi_page']} have a public CFI resource page (description scraped), {s['with_analogues']} have a public analogue in the catalog. Toolkit coverage: {s['coverage']}.", "",
          "## Categories", "", "| category | titles | what the templates do | literature | toolkit coverage |", "|---|---|---|---|---|"]
    for k, v in out["categories"].items():
        md.append(f"| {k} | {s['by_category'].get(k, 0)} | {v['does']} | {v['literature']} | {v['toolkit']} ({v['coverage']}) |")
    if intent:
        md += ["", "## Analysis intent by category (what the paid templates are for, per the public literature)", ""]
        for k, v in intent.items():
            if not v.get("intent") and not v.get("sources"): continue
            md += [f"### {k}", ""]
            if v.get("intent"): md += [v["intent"], ""]
            for src in v.get("sources", [])[:8]:
                md.append(f"- {src['site']}: [{src['title']}]({src['url']})")
            md.append("")
    md += ["", "## Titles", ""]
    for c in list(out["categories"]) + ["Other"]:
        rows = [i for i in out["items"] if i["category"] == c]
        if not rows: continue
        md += [f"### {c}", ""]
        for i in rows:
            line = f"- **{i['title']}**"
            if i["cfi_description"]: line += f" — {i['cfi_description']}"
            if i["cfi_page"]: line += f" ([CFI page]({i['cfi_page']}))"
            if i["cfi_sections"]: line += f" Sections: {'; '.join(i['cfi_sections'][:5])}."
            if i["analogues"]: line += " Analogues: " + "; ".join(f"[{a['source']}: {a['title']}]({a['url']})" for a in i["analogues"][:3]) + "."
            md.append(line)
        md.append("")
    return "\n".join(md)
