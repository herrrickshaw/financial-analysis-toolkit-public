"""India incentive commands plus audit / charts / glossary / demo tools."""
from __future__ import annotations

import json
from pathlib import Path

from ._common import _load_json


def cmd_investment_incentives(a):
    from .. import investment_incentives as INC
    res = INC.from_dict(_load_json(a.inputs))
    if "capital_investment_subsidy" in res:
        r = res["capital_investment_subsidy"]
        print(f"Capital subsidy: {r['subsidy_amount']:,.2f}" + ("  (capped)" if r["capped"] else ""))
    if "interest_subsidy_schedule" in res:
        r = res["interest_subsidy_schedule"]
        print(f"Interest subsidy: {len(r['schedule'])} years, total {r['total_subsidy']:,.2f}")
    if "net_tax_reimbursement_schedule" in res:
        r = res["net_tax_reimbursement_schedule"]
        print(f"Net-tax reimbursement: total {r['total_reimbursement']:,.2f} of overall cap {r['overall_cap']:,.2f}"
              f"  (exhausted: {r['overall_cap_exhausted']})")
    if "employment_generation_subsidy" in res:
        r = res["employment_generation_subsidy"]
        print(f"Employment generation subsidy: {r['subsidy_amount']:,.2f}" + ("  (capped)" if r["capped"] else ""))
    if "ad_valorem_duty_exemptions" in res:
        for r in res["ad_valorem_duty_exemptions"]:
            print(f"  Duty exemption: {r['exempted_amount']:,.2f} exempted, net payable {r['net_payable']:,.2f}")
    if "incremental_metric_linked_incentive" in res:
        r = res["incremental_metric_linked_incentive"]
        print(f"Incremental-metric incentive: {r['incentive_amount']:,.2f}" + ("  (capped)" if r["capped"] else ""))
    if "combined_incentive_package" in res:
        r = res["combined_incentive_package"]
        print(f"Total incentive package: {r['total_incentive_value']:,.2f}")
        for jur, amt in r["by_jurisdiction"].items():
            print(f"  {jur:10} {amt:,.2f}")
    if "effective_capex_after_incentives" in res:
        r = res["effective_capex_after_incentives"]
        print(f"Effective capex: {r['gross_capex']:,.2f} -> {r['net_capex']:,.2f}  "
              f"(effective subsidy {r['effective_subsidy_pct']:.2%})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_sector_investment_model(a):
    from .. import sector_investment_model as SIM
    res = SIM.from_dict(_load_json(a.inputs))
    if "industrial_land_cost" in res:
        r = res["industrial_land_cost"]
        print(f"Land cost: {r['area_acres']:,.2f} acres @ {r['rate_per_acre']:,.2f}/acre = {r['land_cost']:,.2f}")
    if "leasehold_land_cost" in res:
        r = res["leasehold_land_cost"]
        print(f"Leasehold land: {r['area_acres']:,.2f} acres @ {r['base_annual_rent_per_acre']:,.2f}/acre/yr, "
              f"{r['lease_term_years']} yrs -- nominal total rent {r['nominal_total_rent']:,.2f}, "
              f"capitalized cost {r['capitalized_cost']:,.2f}")
    if "project_capex_stack" in res:
        r = res["project_capex_stack"]
        for name, amt in r["components"].items():
            print(f"  {name:28} {amt:>12,.2f}")
        print(f"Total capex: {r['total_capex']:,.2f}")
    if "incentive_present_value" in res:
        r = res["incentive_present_value"]
        print(f"Incentives: nominal total {r['nominal_total']:,.2f}  present value {r['total_present_value']:,.2f}")
    if "sample_project_model" in res:
        r = res["sample_project_model"]
        print(f"Sample project: {r['sector']} in {r['state']}")
        print(f"  Total capex: {r['capex']['total_capex']:,.2f}")
        print(f"  Incentives (nominal {r['incentives']['nominal_total']:,.2f}, "
              f"present value {r['incentives']['total_present_value']:,.2f})")
        print(f"  Net effective investment: {r['net_effective_investment']:,.2f}  "
              f"(effective subsidy, PV basis: {r['effective_subsidy_pct_pv_basis']:.2%})")
    if "sample_project_matrix" in res:
        m = res["sample_project_matrix"]
        for r in m["projects"]:
            note = f"  [{r['note']}]" if r.get("note") else ""
            print(f"  {r['state']:16} {r['sector']:28} capex {r['capex']['total_capex']:>10,.2f}  "
                  f"net effective {r['net_effective_investment']:>10,.2f}{note}")
        print(f"Total capex across projects: {m['total_capex_across_projects']:,.2f}  "
              f"total incentive PV: {m['total_incentive_present_value_across_projects']:,.2f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_project_bankability(a):
    from .. import project_bankability as PB
    res = PB.from_dict(_load_json(a.inputs))
    if "project_returns" in res:
        r = res["project_returns"]
        print(f"IRR without incentives: {r['irr_without_incentives']:.2%}   with: {r['irr_with_incentives']:.2%}   "
              f"(uplift {r['irr_uplift']:+.2%})")
        print(f"Simple ROI without: {r['simple_roi_without_incentives']:.2%}   with: {r['simple_roi_with_incentives']:.2%}")
        print(f"Payback (years) without: {r['payback_years_without_incentives']:.2f}   "
              f"with: {r['payback_years_with_incentives']:.2f}")
    if "rank_projects" in res:
        r = res["rank_projects"]
        print(f"Hurdle rate: {r['hurdle_rate']:.2%}")
        print("Ranked by IRR without incentives (highest ROI on its own merits):")
        for p in r["ranked_by_irr_without_incentives"]:
            print(f"  {p['state']:16} {p['sector']:38} {p['irr_without_incentives']:>8.2%}")
        print("Ranked by IRR with incentives:")
        for p in r["ranked_by_irr_with_incentives"]:
            print(f"  {p['state']:16} {p['sector']:38} {p['irr_with_incentives']:>8.2%}")
        if r["incentive_enabled_projects"]:
            print("Incentive-enabled projects (below hurdle without, at/above hurdle with incentives):")
            for p in r["incentive_enabled_projects"]:
                print(f"  {p['state']:16} {p['sector']:38} {p['irr_without_incentives']:>8.2%} -> {p['irr_with_incentives']:>8.2%}")
        else:
            print("No project crosses the hurdle rate solely because of incentives.")
    if "debt_service_coverage_ratio" in res:
        r = res["debt_service_coverage_ratio"]
        status = "OK" if r["compliant"] else "*** BREACH ***"
        print(f"DSCR: {r['dscr']:.3f}  (min required {r['min_dscr_required']:.2f}, annual debt service "
              f"{r['annual_debt_service']:,.2f})  {status}")
    if "dscr_matrix" in res:
        for r in res["dscr_matrix"]:
            status = "OK" if r["compliant"] else "*** BREACH ***"
            lender = f" [{r['lender']}]" if r.get("lender") else ""
            print(f"  {r['state']:16} {r['sector']:38} DSCR {r['dscr']:>6.3f} (min {r['min_dscr_required']:.2f})  {status}{lender}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_india_corporate_tax_regimes(a):
    from .. import india_corporate_tax_regimes as TAX
    res = TAX.from_dict(_load_json(a.inputs))
    if "tax_regime_comparison" in res:
        r = res["tax_regime_comparison"]
        for name, regime in r["regimes"].items():
            marker = " *** BEST ***" if name == r["best_regime"] else ""
            print(f"  {name:12} effective rate {regime['effective_rate']:.3%}  post-tax CF {regime['post_tax_annual_cash_flow']:,.2f}  "
                  f"IRR {regime['irr_post_tax']:.2%}{marker}")
        print(f"IRR uplift, best vs worst regime: {r['irr_uplift_of_best_vs_worst']:+.2%}")
    if "cgtmse_adjusted_dscr" in res:
        r = res["cgtmse_adjusted_dscr"]
        status = "OK" if r["compliant"] else "*** BREACH ***"
        print(f"DSCR without CGTMSE fee: {r['dscr_without_fee_for_comparison']:.3f}   "
              f"with fee ({r['annual_guarantee_fee']:,.3f}/yr): {r['dscr_with_cgtmse_fee']:.3f} "
              f"(min {r['min_dscr_required']:.2f})  {status}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_india_depreciation_schedule(a):
    from .. import india_depreciation_schedule as DEP
    res = DEP.from_dict(_load_json(a.inputs))
    if "block_depreciation" in res:
        r = res["block_depreciation"]
        note = " *** BLOCK EXTINGUISHED, STCG " + f"{r['short_term_capital_gain']:,.2f} ***" if r["block_extinguished"] else ""
        print(f"Depreciation: {r['depreciation']:,.2f}   closing WDV: {r['closing_wdv']:,.2f}{note}")
    if "multi_year_block_schedule" in res:
        r = res["multi_year_block_schedule"]
        for row in r["rows"]:
            flag = " *** EXTINGUISHED ***" if row["block_extinguished"] else ""
            print(f"  Year {row['year']}: opening {row['opening_wdv']:,.2f} -> depreciation {row['depreciation']:,.2f} "
                  f"-> closing {row['closing_wdv']:,.2f}{flag}")
        print(f"Total depreciation: {r['total_depreciation']:,.2f}   Total STCG: {r['total_short_term_capital_gain']:,.2f}")
    if "additional_depreciation_sec32_1_iia" in res:
        r = res["additional_depreciation_sec32_1_iia"]
        print(f"Additional depreciation (sec 32(1)(iia)): current year {r['current_year']:,.2f}, "
              f"carried forward {r['carried_forward_to_next_year']:,.2f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_india_incentive_workbook(a):
    from .. import india_incentive_workbook as WB
    path = WB.build_workbook(a.output)
    print(f"Wrote {path}")


def cmd_audit(a):
    from .. import audit as A
    res = A.audit(a.file, recompute=a.recompute)
    print(f"{res['file']}: {res['sheets']} sheets, {res['cells']:,} cells, {res['formulas']:,} formulas")
    print(f"By severity: {res['by_severity']}")
    print(f"By kind: {res['counts']}")
    if res.get("recompute"): print(f"Recompute: {res['recompute']}")
    if a.markdown_out: Path(a.markdown_out).write_text(A.to_markdown(res))
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))
    for f in res["findings"][: a.show]:
        print(f"  [{f['severity']}] {f['sheet']}!{f['cell']} {f['kind']}: {f['message']}")


def cmd_charts(a):
    from .. import charts
    d = _load_json(a.inputs)
    if a.engine == "three_statement":
        from .. import three_statement as ts; res = ts.from_dict(d).to_dict()
    elif a.engine == "dcf":
        from .. import dcf; inp = dcf.DCFInputs(**dcf.clean(d)); res = dcf.run(inp)
        res["sensitivity"] = dcf.sensitivity(inp, [inp.discount_rate + x for x in (-0.02, -0.01, 0, 0.01, 0.02)], [inp.perpetual_growth + x for x in (-0.01, -0.005, 0, 0.005, 0.01)])
    elif a.engine == "lbo":
        from .. import lbo; res = lbo.from_dict(d)
    elif a.engine == "merger":
        from .. import merger; res = merger.from_dict(d)
    elif a.engine == "comps":
        from .. import comps; res = comps.from_dict(d)
    else:
        from .. import projection; res = projection.from_dict(d)
    p = charts.report_for(a.engine, res, a.out, title=a.title)
    print(f"wrote {p} ({len(charts.CATALOG[a.engine]['charts'])} chart templates)")


def cmd_glossary(a):
    g = _load_json(Path(__file__).resolve().parents[2] / "data" / "glossary.json")
    q = " ".join(a.query).lower()
    hits = [e for e in g["entries"] if q in e["term"].lower() or any(q in s.lower() for s in e["synonyms"])]
    if not hits and a.deep:
        hits = [e for e in g["entries"] if q in e["definition"].lower()]
    for e in hits[: a.limit]:
        print(f"\n{e['term']}  [{e['category']}]" + (f"  (also: {', '.join(e['synonyms'])})" if e["synonyms"] else ""))
        print("  " + e["definition"])
        for k, lab in (("formula", "Formula"), ("gaap_vs_ifrs", "GAAP vs IFRS"), ("how_to_evaluate", "Evaluate"), ("toolkit", "Toolkit")):
            if e.get(k): print(f"  {lab}: {e[k]}")
    if not hits:
        rows = [r for r in g["gaap_vs_ifrs"] if q in r["topic"].lower()]
        for r in rows: print(f"\n{r['topic']}\n  US GAAP: {r['us_gaap']}\n  IFRS: {r['ifrs']}\n  Evaluate: {r['how_to_evaluate']}")
        if not rows: print("no match; try --deep to search definitions")


def cmd_demo(a):
    ex = Path(__file__).resolve().parents[2] / "examples"
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    from .. import three_statement as ts, dcf, projection
    from ..excel import write_three_statement, write_dcf, write_projection
    d = _load_json(ex / "cfi_three_statement.json")
    r = ts.from_dict(d)
    write_three_statement(out / "three_statement.xlsx", [ts.HistoricalYear(**h) for h in d["historical"]], ts.ForecastAssumptions(**d["forecast"]), d.get("ppe_opening0"), d.get("debt_opening0"), r)
    print(r.table("income_statement")); print(); print(r.table("balance_sheet")); print(f"balanced={r.balanced}\n")
    dd = _load_json(ex / "cfi_dcf.json"); inp = dcf.DCFInputs(**dcf.clean(dd)); rr = dcf.run(inp); write_dcf(out / "dcf.xlsx", inp)
    print(f"DCF: EV={rr['enterprise_value']:,.0f} equity/share={rr['equity_value_per_share']:.2f} upside={rr['target_price_upside']:.1%} IRR={rr['irr']:.1%}\n")
    pr = projection.from_dict(_load_json(ex / "projection_demo.json")); write_projection(out / "projection.xlsx", pr)
    print(f"Projection: years={pr['years']} revenue={[round(x) for x in pr['income_statement']['Revenue']]} balanced={pr['balanced']}")
    from .. import charts
    charts.report_for("three_statement", r.to_dict(), out / "charts_three_statement.html")
    rr["sensitivity"] = dcf.sensitivity(inp, [inp.discount_rate + x for x in (-0.02, -0.01, 0, 0.01, 0.02)], [inp.perpetual_growth + x for x in (-0.01, -0.005, 0, 0.005, 0.01)])
    charts.report_for("dcf", rr, out / "charts_dcf.html"); charts.report_for("projection", pr, out / "charts_projection.html")
    from .. import lbo, merger
    charts.report_for("lbo", lbo.from_dict(_load_json(ex / "lbo_asm.json")), out / "charts_lbo.html")
    charts.report_for("merger", merger.from_dict(_load_json(ex / "merger_biws.json")), out / "charts_merger.html")
    print(f"\nworkbooks and chart reports written to {out}/")
