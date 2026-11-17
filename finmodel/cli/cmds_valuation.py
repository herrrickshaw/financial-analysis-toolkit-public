"""Valuation, scoring and venture commands."""
from __future__ import annotations

import json
from pathlib import Path

from ._common import _dump, _load_json


def cmd_extract(a):
    from ..extract import extract_workbook
    for f in a.files:
        spec = extract_workbook(f, a.out)
        print(f"{Path(f).name}: {len(spec['sheets'])} sheets, {spec.get('totals')}")
        for s in spec["sheets"]:
            print(f"  - {s['name']:40} cells={s['stats']['cells']:5} formulas={s['stats']['formulas']:5} inputs={s['stats']['inputs']:4}  links={[x['sheet'] for x in s['cross_sheet_refs']]}")
    if a.out:
        print(f"specs written to {a.out}/")


def cmd_catalog(a):
    from .. import catalog as C
    cat = C.build() if a.action in ("build", "verify", "fetch") else C.load()
    if a.action == "verify":
        cat = C.verify(cat, a.source)
        (C.CATALOG_DIR / "catalog.json").write_text(json.dumps(cat, indent=1))
        (C.CATALOG_DIR / "catalog.md").write_text(C.to_markdown(cat))
    if a.action == "paid":
        from .. import paid_templates
        r = paid_templates.build()
        print(f"paid titles: {r['summary']} -> catalog/paid_templates.json, docs/PAID_TEMPLATES.md")
        if a.title:
            for i in r["items"]:
                if a.title.lower() in i["title"].lower():
                    print(f"\n{i['title']}  [{i['category']}]  coverage={i['coverage']}\n  CFI: {i['cfi_description'] or '(no public page found)'}\n  Does: {i['what_it_does']}\n  Analogues: " + "; ".join(f"{x['source']}: {x['title']}" for x in i["analogues"]) + f"\n  Literature: {i['literature']}\n  Toolkit: {i['toolkit']}")
        return
    if a.action == "alternatives":
        from .. import alternatives
        r = alternatives.build()
        print(f"alternatives: {r['summary']} -> catalog/alternatives.md")
        return
    if a.action == "fetch":
        man = C.fetch(cat, Path(a.dest), a.source, a.overwrite, limit=a.limit)
        ok = sum(1 for m in man if m.get("ok"))
        print(f"fetched {ok}/{len(man)} -> {a.dest}/ (manifest.json)")
        for m in man:
            if not m.get("ok"):
                print(f"  FAILED {m['id']}: {m.get('error')}")
        return
    print(f"catalog: {len(cat['entries'])} entries  counts={cat['counts']}")
    if a.action == "list":
        for e in cat["entries"]:
            if a.source and e["source"] not in a.source:
                continue
            print(f"{e['source']:13} {e['access']:10} {e['title'][:60]:60} {e['url'] or ''}")


def cmd_three(a):
    from .. import three_statement as ts
    d = _load_json(a.inputs)
    res = ts.from_dict(d)
    if a.xlsx:
        from ..excel import write_three_statement
        hist = [ts.HistoricalYear(**h) for h in d["historical"]]
        write_three_statement(a.xlsx, hist, ts.ForecastAssumptions(**d["forecast"]), d.get("ppe_opening0"), d.get("debt_opening0"), res)
        print(f"wrote {a.xlsx}")
    if a.json_out or not a.xlsx:
        if a.table:
            print(res.table(a.table if a.table != "all" else None))
        else:
            _dump(res.to_dict(), a.json_out)
    print(f"balance sheet {'OK' if res.balanced else 'ERROR'}")


def cmd_dcf(a):
    from .. import dcf
    d = _load_json(a.inputs)
    inp = dcf.DCFInputs(**dcf.clean(d))
    res = dcf.run(inp)
    if a.sensitivity:
        rs = [inp.discount_rate + x for x in (-0.02, -0.01, 0, 0.01, 0.02)]
        gs = [inp.perpetual_growth + x for x in (-0.01, -0.005, 0, 0.005, 0.01)]
        res["sensitivity"] = dcf.sensitivity(inp, rs, gs)
    if a.xlsx:
        from ..excel import write_dcf
        write_dcf(a.xlsx, inp)
        print(f"wrote {a.xlsx}")
    _dump(res, a.json_out) if (a.json_out or not a.xlsx) else None
    print(f"EV={res['enterprise_value']:,.0f}  equity/share={res['equity_value_per_share']:,.2f}  upside={res['target_price_upside']:.1%}  IRR={res['irr']:.1%}")


def cmd_projection(a):
    from .. import projection
    res = projection.from_dict(_load_json(a.inputs))
    if a.xlsx:
        from ..excel import write_projection
        write_projection(a.xlsx, res)
        print(f"wrote {a.xlsx}")
    if a.json_out or not a.xlsx:
        _dump(res, a.json_out)
    ni = res["income_statement"]["Net Earnings"]
    print(f"years={res['years']}  revenue={[round(x) for x in res['income_statement']['Revenue']]}  net={[round(x) for x in ni]}  balanced={res['balanced']}")


def cmd_ratios(a):
    from .. import ratios
    d = _load_json(a.inputs)
    _dump(ratios.compute(d["is"], d["bs"], d.get("days", 365)), a.json_out)


def cmd_lbo(a):
    from .. import lbo
    res = lbo.from_dict(_load_json(a.inputs))
    if a.xlsx:
        from ..excel import write_generic
        write_generic(a.xlsx, {"Income Statement": (res["years"], res["income_statement"]), "Balance Sheet": (res["years"], res["balance_sheet"]),
                               "Cash Flow": (res["years"], res["cash_flow"]), **{f"Debt - {k}": (res["years"], v) for k, v in res["debt_schedule"].items()}})
        print(f"wrote {a.xlsx}")
    if a.json_out or not a.xlsx:
        _dump(res, a.json_out)
    R = res["returns"]
    print(f"sponsor IRR={R['sponsor']['irr']:.1%} MOIC={R['sponsor']['moic']:.2f}x  exit equity={R['exit_equity_value']:,.0f}  balanced={res['balanced']}")


def cmd_merger(a):
    from .. import merger
    res = merger.from_dict(_load_json(a.inputs))
    if a.xlsx and "pro_forma" in res:
        from ..excel import write_generic
        pf = res["pro_forma"]
        write_generic(a.xlsx, {"Pro Forma IS": (pf["years"], pf["income_statement"]), "Debt": (pf["years"], pf["debt_schedule"])})
        print(f"wrote {a.xlsx}")
    if a.json_out or not a.xlsx:
        _dump(res, a.json_out)
    if "deal" in res:
        d = res["deal"]; print(f"deal: EPS {d['acquirer']['eps']:.3f} -> {d['combined']['eps']:.3f}  accretion {d['accretion_dilution_pct']:+.1%}  new shares {d['new_shares_issued']:,.2f}")
    if "pro_forma" in res:
        IS = res["pro_forma"]["income_statement"]; print("pro forma accretion %:", [f"{x:+.1%}" for x in IS["Accretion / (Dilution) %"]])


def cmd_transpile(a):
    from ..xlcalc import XlModel, to_python_source
    for f in a.files:
        m = XlModel(f)
        r = m.verify()
        print(f"{r['file']}: {r['checked']} formulas, {r['ok']} match cached values ({r['match_rate']:.2%}), {r['compile_errors']} compile errors, {r['circular']} circular")
        for ex in r["examples"][: a.show]:
            print("   ", ex[0], "|", str(ex[1])[:70], "| got", repr(ex[2])[:40], "| cached", repr(ex[3])[:30])
        if a.out:
            out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
            p = out / (Path(f).stem.replace(" ", "_").replace("-", "_") + "_model.py")
            p.write_text(to_python_source(m)); print("    ->", p)


def cmd_comps(a):
    from .. import comps
    res = comps.from_dict(_load_json(a.inputs))
    if a.json_out:
        Path(a.json_out).parent.mkdir(parents=True, exist_ok=True); Path(a.json_out).write_text(json.dumps(res, indent=1, default=str))
    if "comps" in res:
        print("Trading comps — peer multiples (max / 75th / median / 25th / min):")
        for label, s in res["comps"]["summary"].items():
            print(f"  {label:20} " + "  ".join(f"{s[k]:7.2f}x" if s['n'] else "     n/a" for k in ("max", "p75", "median", "p25", "min")))
    if "precedents" in res:
        print("Precedent transactions — deal multiples:")
        for label, s in res["precedents"]["summary"].items():
            print(f"  {label:20} " + "  ".join(f"{s[k]:7.2f}x" if s['n'] else "     n/a" for k in ("max", "p75", "median", "p25", "min")))
        for label, s in res["precedents"]["premium_summary"].items():
            print(f"  premium {label:12} median {s['median']:.1%}  25th {s['p25']:.1%}  75th {s['p75']:.1%}")
    if "implied_from_comps" in res:
        iv = res["implied_from_comps"]
        print(f"Implied share price for {iv['target']} (current {iv['current_price']:.2f}):")
        for r in iv["rows"]:
            im = r["implied"]
            print(f"  {r['multiple']:20} " + "  ".join(f"{im[k]['share_price']:7.2f}" for k in ("min", "p25", "median", "p75", "max") if k in im))
    if "football_field" in res:
        print("Football field (low – high implied share price):")
        for it in res["football_field"]["items"]:
            print(f"  {it['method']:24} {it['low']:7.2f} – {it['high']:7.2f}")
    if a.xlsx and "comps" in res:
        from ..excel import write_generic
        c = res["comps"]; names = [p["name"] for p in c["peers"]]
        rows = {"Equity value": [p["equity_value"] for p in c["peers"]], "Enterprise value": [p["enterprise_value"] for p in c["peers"]]}
        for lab in c["peers"][0]["multiples"]:
            rows[lab] = [p["multiples"][lab] if isinstance(p["multiples"][lab], (int, float)) else None for p in c["peers"]]
        write_generic(a.xlsx, {"Comps": (names, rows)})
        print(f"wrote {a.xlsx}")


def cmd_scores(a):
    from .. import scores
    d = _load_json(a.inputs)
    res = scores.health(d["current"], d.get("prior", d["current"]), d.get("market_cap"), d.get("variant", "public"))
    print(f"Altman Z ({res['altman']['variant']}): {res['altman']['z']:.2f} → {res['altman']['zone']}")
    print(f"Piotroski F: {res['piotroski']['f']}/9 ({res['piotroski']['grade']}): " + ", ".join(k for k, v in res["piotroski"]["signals"].items() if v))
    print(f"Beneish M: {res['beneish']['m']:.2f} → {'likely manipulator' if res['beneish']['likely_manipulator'] else 'not flagged'}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_costing(a):
    from .. import costing
    res = costing.from_dict(_load_json(a.inputs))
    if "resource_allocation" in res:
        r = res["resource_allocation"]; print(f"Resource allocation: envelope {r['envelope']:,.0f}, top-slice {r['top_slice']:,.0f}, formula pool {r['formula_pool']:,.0f} (check {r['check']})")
        for u, v in r["units"].items(): print(f"  {u:24} direct {v['direct']:>10,.0f}  formula {v['formula']:>10,.0f}  strategic {v['strategic']:>10,.0f}  total {v['total']:>10,.0f}")
    if "costing" in res:
        c = res["costing"]; print(f"Costing: pools {c['pools_total']:,.0f}, allocated {c['allocated']:,.0f}, unallocated {c['unallocated']} (check {c['check']})")
        for o in c["objects"]: print(f"  {o['object']:24} {o['activity']:9} direct {o['direct']:>10,.0f}  indirect {o['indirect']:>10,.0f}  full {o['full_cost']:>10,.0f}  indirect rate on salary {o['indirect_rate_on_salary']:.0%}")
        for k, v in c["by_activity"].items(): print(f"  by activity {k:12} full cost {v['full_cost']:>12,.0f}  indirect rate {v['indirect_rate_on_salary']:.0%}")
    if "income_diversification" in res:
        i = res["income_diversification"]; print(f"Income: total {i['total']:,.0f}, HHI {i['hhi']:.3f}, effective sources {i['effective_sources']:.2f}; priority: {', '.join(i['ranking'])}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_edgar(a):
    from .. import edgar
    facts = edgar.fetch(a.cik, user_agent=a.user_agent, cache_dir=a.cache_dir)
    c = edgar.compact(facts, years=a.years)
    if a.json_out: Path(a.json_out).write_text(json.dumps(c, indent=1))
    print(f"{c['entity']} (CIK {c['cik']}): {len(c['years'])} fiscal years")
    for fy, r in c["years"].items():
        print(f"  {fy}  revenue {r.get('revenue', 0)/1e6:>12,.0f}m  EBIT {r.get('operating_income', 0)/1e6:>10,.0f}m  NI {r.get('net_income', 0)/1e6:>10,.0f}m  diluted EPS {r.get('eps_diluted', 0):>7.2f}  cash {r.get('cash', 0)/1e6:>10,.0f}m  debt {r.get('debt_total', 0)/1e6:>10,.0f}m")


def cmd_cycle(a):
    from .. import sectors
    history = json.loads(Path(a.edgar_json).read_text())["years"]
    kw = {"field": a.field, "revenue_field": a.revenue_field} if a.field else {}
    d = sectors.cycle_diagnostics(history, periods=a.periods, sector=a.sector, as_of=a.as_of, **kw)
    metric_label = f"{a.field}/{a.revenue_field}" if a.field else "margin"
    print(f"Sector: {d.get('sector', sectors.SECTOR_PROFILES.get(a.sector, sectors.SECTOR_PROFILES['default']).name)}")
    print(f"FY {d.get('fiscal_year')}: {metric_label} {d.get('latest_margin', float('nan')):.1%} vs trailing-{a.periods}yr median {d.get('median_margin_trailing_years', float('nan')):.1%} "
          f"({d.get('deviation_pct', float('nan')):+.1%}) → {d.get('flag')}")
    s = sectors.dcf_scenarios_from_history(history, periods=a.periods, **kw)
    print(f"Data-driven scenario targets ({metric_label}): bear {s['bear_margin']:.1%}  base {s['base_margin']:.1%}  blue sky {s['blue_sky_margin']:.1%}  (current {s['current_margin']:.1%})")
    if a.json_out:
        out = {"cycle_diagnostics": d, "dcf_scenarios": s, "sector_beta": sectors.sector_beta(a.sector)}
        Path(a.json_out).write_text(json.dumps(out, indent=1))


def cmd_wacc(a):
    from .. import wacc as W
    res = W.from_dict(_load_json(a.inputs))
    if "bottom_up_beta" in res:
        b = res["bottom_up_beta"]
        print(f"Bottom-up beta: peer unlevered {['%.3f' % x for x in b['peer_unlevered_betas']]}, average {b['average_unlevered_beta']:.3f}, relevered {b['relevered_beta']:.3f}")
    w = res["wacc"]
    print(f"Cost of equity {w['cost_of_equity']:.2%}, cost of debt pre-tax {w['cost_of_debt_pretax']:.2%} / after-tax {w['cost_of_debt_aftertax']:.2%}"
          + (f" (synthetic rating {w['synthetic_rating']['rating']}, coverage {w['synthetic_rating']['interest_coverage']:.2f}x)" if w["synthetic_rating"] else ""))
    print(f"Weights: equity {w['weights']['equity']:.1%}, debt {w['weights']['debt']:.1%}, preferred {w['weights']['preferred']:.1%}  →  WACC {w['wacc']:.2%}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_residual_income(a):
    from .. import residual_income as RI
    res = RI.from_dict(_load_json(a.inputs))
    if "residual_income" in res:
        r = res["residual_income"]
        print(f"Residual income: {['%.2f' % x for x in r['residual_income']]}  →  equity value {r['equity_value']:,.2f}" + (f", per share {r['value_per_share']:.2f}" if "value_per_share" in r else ""))
    if "eva" in res:
        e = res["eva"]
        print(f"EVA: {['%.2f' % x for x in e['eva']]}  →  firm value {e['firm_value']:,.2f}, equity value {e['equity_value']:,.2f}" + (f", per share {e['value_per_share']:.2f}" if "value_per_share" in e else ""))
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_sotp(a):
    from .. import sotp as S
    res = S.from_dict(_load_json(a.inputs))
    for r in res["segments"]:
        print(f"  {r['segment']:20} {r['metric_name']:8} {r['metric']:>12,.1f} × {r['multiple']:6.2f} = {r['gross_value']:>14,.1f}  ({r['ownership']:.0%} owned → {r['attributable_value']:>14,.1f}, {r['share_of_gross']:.1%} of sum)")
    print(f"Gross EV {res['gross_enterprise_value']:,.1f}  corporate costs {res['capitalised_corporate_costs']:,.1f}  discount {res['conglomerate_discount']:,.1f}  EV {res['enterprise_value']:,.1f}")
    print(f"Equity value {res['equity_value']:,.1f}" + (f"  per share {res['value_per_share']:.2f}" if "value_per_share" in res else ""))
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_startup(a):
    from .. import startup_model as SM
    d = _load_json(a.inputs)
    if a.benchmark_sector: d["benchmark_sector"] = a.benchmark_sector
    res = SM.from_dict(d)
    ts = res["three_statement"]
    print(ts_table_summary(ts))
    print(f"Balance sheet balances: {ts['balanced']}")
    if "dcf" in res:
        dd = res["dcf"]
        print(f"DCF: enterprise value {dd['enterprise_value']:,.0f}  equity value {dd['equity_value']:,.0f}  per share {dd['value_per_share']:.4f}")
    if "benchmark" in res:
        b = res["benchmark"]
        lo, hi = b["real_range"]["low"], b["real_range"]["high"]
        print(f"Benchmark vs real {b['sector']} peers ({b['field']}/{b['revenue_field']}, FY{b['exit_year']}): "
              f"this plan {b['startup_margin']:.1%} vs real range {lo:.1%}-{hi:.1%} → {b['note']}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def ts_table_summary(ts):
    years = ts["years"]; n_h = ts["n_hist"]; r = ts["rows"]
    lines = [f"{'':16}" + "".join(f"{y:>14}" for y in years)]
    for k in ("Revenue", "Gross Profit", "Net Earnings", "Cash", "Closing Cash Balance"):
        lines.append(f"{k:16}" + "".join(f"{v:>14,.0f}" for v in r[k]))
    return "\n".join(lines)


def cmd_cap_table(a):
    from .. import cap_table as CT
    res = CT.from_dict(_load_json(a.inputs))
    if "cap_table" in res:
        ct = res["cap_table"]
        for rnd in ct["rounds_applied"]:
            print(f"{rnd['round']:16} pre {rnd['pre_money']:>14,.0f}  +{rnd['investment']:>12,.0f}  "
                  f"price/sh {rnd['price_per_share']:>8.4f}  pool top-up {rnd['option_pool_topup']:>12,.0f}  "
                  f"investor owns {rnd['new_investor_ownership_pct']:.1%}")
        print("Final ownership:")
        for name, pct in sorted(ct["ownership"].items(), key=lambda kv: -kv[1]):
            print(f"  {name:24} {pct:.2%}")
    if "exit_waterfall" in res:
        w = res["exit_waterfall"]
        print(f"Exit waterfall on ${w['exit_proceeds']:,.0f}:")
        for name, amount in sorted(w["payouts"].items(), key=lambda kv: -kv[1]):
            print(f"  {name:24} {amount:>14,.0f}")
        if w["converted_to_common"]:
            print(f"  (converted to as-converted common: {', '.join(w['converted_to_common'])})")
    if "vc_method_valuation" in res:
        v = res["vc_method_valuation"]
        print(f"VC method: required multiple {v['required_multiple']:.2f}x, ownership required today {v['ownership_required_today']:.2%}, "
              f"implied pre-money {v['implied_pre_money_valuation']:,.0f}, post-money {v['implied_post_money_valuation']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_vc_fund(a):
    from .. import vc_fund_metrics as VC
    res = VC.from_dict(_load_json(a.inputs))
    m = res["fund_metrics"]
    irr_str = f"{m['irr']:.1%}" if m["irr"] is not None else "n/a"
    print(f"Paid-in {m['paid_in']:,.0f}  distributions {m['distributions']:,.0f}  NAV {m['nav']:,.0f}")
    print(f"DPI {m['dpi']:.2f}x  RVPI {m['rvpi']:.2f}x  TVPI {m['tvpi']:.2f}x  IRR {irr_str}")
    if "deals" in res:
        for name, d in res["deals"].items():
            irr_str = f"{d['irr']:.1%}" if d.get("irr") is not None else "n/a"
            print(f"  {name:24} MOIC {d['moic']:.2f}x  IRR {irr_str}")
    if "carry_waterfall" in res:
        w = res["carry_waterfall"]
        print(f"Carry waterfall (whole-fund, European): LP {w['lp_total']:,.0f} ({w['lp_net_tvpi']:.2f}x net)  "
              f"GP {w['gp_total']:,.0f}  (effective carry on profit {w['effective_carry_pct_of_profit']:.1%})")
    if "american_waterfall" in res:
        aw = res["american_waterfall"]
        for d in aw["deals"]:
            flag = f"  *** CLAWBACK {d['clawback_owed']:,.0f} ***" if d["clawback_owed"] > 1.0 else ""
            print(f"  {d['name']:12} GP {d['gp_payout']:>12,.0f}  LP {d['lp_payout']:>12,.0f}  cumulative GP received {d['cumulative_gp_received']:>12,.0f}{flag}")
        print(f"American waterfall (deal-by-deal): total GP {aw['total_gp_payout']:,.0f}  final clawback owed {aw['final_clawback_owed']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_percentage_of_completion(a):
    from .. import percentage_of_completion as POC
    res = POC.from_dict(_load_json(a.inputs))
    if "percentage_of_completion" in res:
        r = res["percentage_of_completion"]
        print(f"% complete {r['pct_complete']:.1%}  revenue to date {r['revenue_recognized_to_date']:,.0f}  "
              f"gross profit to date {r['gross_profit_to_date']:,.0f}  ({r['classification']}: {r['net_billing_position']:,.0f})")
    if "completion_schedule" in res:
        r = res["completion_schedule"]
        for p in r["periods"]:
            print(f"  Period {p['period']}: {p['pct_complete']:.1%} complete  revenue this period {p['current_period_revenue']:,.0f}")
        print(f"Total revenue recognized: {r['total_revenue_recognized']:,.0f}  total gross profit {r['total_gross_profit']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_cash_flow_forecast(a):
    from .. import cash_flow_forecast as CF
    res = CF.from_dict(_load_json(a.inputs))
    f = res["forecast"]
    print(f"Opening cash {f['opening_cash']:,.0f}")
    for w in f["weeks"]:
        flag = "  *** BELOW COVENANT ***" if w["covenant_breach"] else ""
        print(f"  {w['week_ending']}  receipts {w['total_receipts']:>12,.0f}  disbursements {w['total_disbursements']:>12,.0f}  closing {w['closing_cash']:>12,.0f}{flag}")
    print(f"13-week total: receipts {f['total_receipts']:,.0f}  disbursements {f['total_disbursements']:,.0f}  "
          f"closing {f['closing_cash']:,.0f}  min projected cash {f['min_projected_cash']:,.0f}")
    if f["covenant_breach_weeks"]:
        print(f"Covenant breach weeks: {', '.join(f['covenant_breach_weeks'])}")
    if "variance" in res:
        v = res["variance"]
        print(f"Forecast-vs-actual: total net variance {v['total_net_variance']:,.0f}  "
              f"mean |receipts variance| {v['mean_absolute_receipts_variance_pct']:.1%}  "
              f"mean |disbursements variance| {v['mean_absolute_disbursements_variance_pct']:.1%}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_impact(a):
    from .. import impact_scoring as IS
    res = IS.from_dict(_load_json(a.inputs))
    if "two_x" in res:
        t = res["two_x"]
        print(f"2X eligible: {t['eligible']} (dimensions met: {', '.join(t['dimensions_met_list']) or 'none'})")
    if "impact_classification" in res:
        c = res["impact_classification"]
        print(f"Impact classification: {c['class'] or 'none'} — {c['label']}" + (f" ({c['note']})" if c.get("note") else ""))
    if "ghg" in res:
        g = res["ghg"]
        line = f"GHG intensity: {g['scope1_2_intensity_per_million_revenue']:.1f} tCO2e/$M revenue (Scope 1+2)"
        if "scope1_2_3_intensity_per_million_revenue" in g:
            line += f", {g['scope1_2_3_intensity_per_million_revenue']:.1f} incl. Scope 3 ({g['scope3_share_of_total']:.0%} of total)"
        print(line)
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))
