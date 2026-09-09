"""finmodel command-line interface."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__


def _load_json(p: str):
    return json.loads(Path(p).read_text())


def _dump(obj, out: str | None):
    s = json.dumps(obj, indent=1, default=str)
    if out:
        Path(out).write_text(s)
        print(f"wrote {out}")
    else:
        print(s)


def cmd_extract(a):
    from .extract import extract_workbook
    for f in a.files:
        spec = extract_workbook(f, a.out)
        print(f"{Path(f).name}: {len(spec['sheets'])} sheets, {spec.get('totals')}")
        for s in spec["sheets"]:
            print(f"  - {s['name']:40} cells={s['stats']['cells']:5} formulas={s['stats']['formulas']:5} inputs={s['stats']['inputs']:4}  links={[x['sheet'] for x in s['cross_sheet_refs']]}")
    if a.out:
        print(f"specs written to {a.out}/")


def cmd_catalog(a):
    from . import catalog as C
    cat = C.build() if a.action in ("build", "verify", "fetch") else C.load()
    if a.action == "verify":
        cat = C.verify(cat, a.source, a.auth)
        (C.CATALOG_DIR / "catalog.json").write_text(json.dumps(cat, indent=1))
        (C.CATALOG_DIR / "catalog.md").write_text(C.to_markdown(cat))
    if a.action == "paid":
        from . import paid_templates
        r = paid_templates.build()
        print(f"paid titles: {r['summary']} -> catalog/paid_templates.json, docs/PAID_TEMPLATES.md")
        if a.title:
            for i in r["items"]:
                if a.title.lower() in i["title"].lower():
                    print(f"\n{i['title']}  [{i['category']}]  coverage={i['coverage']}\n  CFI: {i['cfi_description'] or '(no public page found)'}\n  Does: {i['what_it_does']}\n  Analogues: " + "; ".join(f"{x['source']}: {x['title']}" for x in i["analogues"]) + f"\n  Literature: {i['literature']}\n  Toolkit: {i['toolkit']}")
        return
    if a.action == "fetch-signed":
        rows = C.fetch_signed(Path(a.urls), Path(a.dest), (a.source or ["cfi"])[0])
        print(f"fetched {sum(1 for r in rows if r['ok'])}/{len(rows)} signed URLs -> {a.dest}/")
        return
    if a.action == "alternatives":
        from . import alternatives
        r = alternatives.build()
        print(f"alternatives: {r['summary']} -> catalog/alternatives.md")
        return
    if a.action == "fetch":
        man = C.fetch(cat, Path(a.dest), a.source, a.auth, a.overwrite, limit=a.limit)
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
    from . import three_statement as ts
    d = _load_json(a.inputs)
    res = ts.from_dict(d)
    if a.xlsx:
        from .excel import write_three_statement
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
    from . import dcf
    d = _load_json(a.inputs)
    inp = dcf.DCFInputs(**dcf.clean(d))
    res = dcf.run(inp)
    if a.sensitivity:
        rs = [inp.discount_rate + x for x in (-0.02, -0.01, 0, 0.01, 0.02)]
        gs = [inp.perpetual_growth + x for x in (-0.01, -0.005, 0, 0.005, 0.01)]
        res["sensitivity"] = dcf.sensitivity(inp, rs, gs)
    if a.xlsx:
        from .excel import write_dcf
        write_dcf(a.xlsx, inp)
        print(f"wrote {a.xlsx}")
    _dump(res, a.json_out) if (a.json_out or not a.xlsx) else None
    print(f"EV={res['enterprise_value']:,.0f}  equity/share={res['equity_value_per_share']:,.2f}  upside={res['target_price_upside']:.1%}  IRR={res['irr']:.1%}")


def cmd_projection(a):
    from . import projection
    res = projection.from_dict(_load_json(a.inputs))
    if a.xlsx:
        from .excel import write_projection
        write_projection(a.xlsx, res)
        print(f"wrote {a.xlsx}")
    if a.json_out or not a.xlsx:
        _dump(res, a.json_out)
    ni = res["income_statement"]["Net Earnings"]
    print(f"years={res['years']}  revenue={[round(x) for x in res['income_statement']['Revenue']]}  net={[round(x) for x in ni]}  balanced={res['balanced']}")


def cmd_ratios(a):
    from . import ratios
    d = _load_json(a.inputs)
    _dump(ratios.compute(d["is"], d["bs"], d.get("days", 365)), a.json_out)


def cmd_lbo(a):
    from . import lbo
    res = lbo.from_dict(_load_json(a.inputs))
    if a.xlsx:
        from .excel import write_generic
        write_generic(a.xlsx, {"Income Statement": (res["years"], res["income_statement"]), "Balance Sheet": (res["years"], res["balance_sheet"]),
                               "Cash Flow": (res["years"], res["cash_flow"]), **{f"Debt - {k}": (res["years"], v) for k, v in res["debt_schedule"].items()}})
        print(f"wrote {a.xlsx}")
    if a.json_out or not a.xlsx:
        _dump(res, a.json_out)
    R = res["returns"]
    print(f"sponsor IRR={R['sponsor']['irr']:.1%} MOIC={R['sponsor']['moic']:.2f}x  exit equity={R['exit_equity_value']:,.0f}  balanced={res['balanced']}")


def cmd_merger(a):
    from . import merger
    res = merger.from_dict(_load_json(a.inputs))
    if a.xlsx and "pro_forma" in res:
        from .excel import write_generic
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
    from .xlcalc import XlModel, to_python_source
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
    from . import comps
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
        from .excel import write_generic
        c = res["comps"]; names = [p["name"] for p in c["peers"]]
        rows = {"Equity value": [p["equity_value"] for p in c["peers"]], "Enterprise value": [p["enterprise_value"] for p in c["peers"]]}
        for lab in c["peers"][0]["multiples"]:
            rows[lab] = [p["multiples"][lab] if isinstance(p["multiples"][lab], (int, float)) else None for p in c["peers"]]
        write_generic(a.xlsx, {"Comps": (names, rows)})
        print(f"wrote {a.xlsx}")


def cmd_scores(a):
    from . import scores
    d = _load_json(a.inputs)
    res = scores.health(d["current"], d.get("prior", d["current"]), d.get("market_cap"), d.get("variant", "public"))
    print(f"Altman Z ({res['altman']['variant']}): {res['altman']['z']:.2f} → {res['altman']['zone']}")
    print(f"Piotroski F: {res['piotroski']['f']}/9 ({res['piotroski']['grade']}): " + ", ".join(k for k, v in res["piotroski"]["signals"].items() if v))
    print(f"Beneish M: {res['beneish']['m']:.2f} → {'likely manipulator' if res['beneish']['likely_manipulator'] else 'not flagged'}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_costing(a):
    from . import costing
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
    from . import edgar
    facts = edgar.fetch(a.cik, user_agent=a.user_agent, cache_dir=a.cache_dir)
    c = edgar.compact(facts, years=a.years)
    if a.json_out: Path(a.json_out).write_text(json.dumps(c, indent=1))
    print(f"{c['entity']} (CIK {c['cik']}): {len(c['years'])} fiscal years")
    for fy, r in c["years"].items():
        print(f"  {fy}  revenue {r.get('revenue', 0)/1e6:>12,.0f}m  EBIT {r.get('operating_income', 0)/1e6:>10,.0f}m  NI {r.get('net_income', 0)/1e6:>10,.0f}m  diluted EPS {r.get('eps_diluted', 0):>7.2f}  cash {r.get('cash', 0)/1e6:>10,.0f}m  debt {r.get('debt_total', 0)/1e6:>10,.0f}m")


def cmd_cycle(a):
    from . import sectors
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
    from . import wacc as W
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
    from . import residual_income as RI
    res = RI.from_dict(_load_json(a.inputs))
    if "residual_income" in res:
        r = res["residual_income"]
        print(f"Residual income: {['%.2f' % x for x in r['residual_income']]}  →  equity value {r['equity_value']:,.2f}" + (f", per share {r['value_per_share']:.2f}" if "value_per_share" in r else ""))
    if "eva" in res:
        e = res["eva"]
        print(f"EVA: {['%.2f' % x for x in e['eva']]}  →  firm value {e['firm_value']:,.2f}, equity value {e['equity_value']:,.2f}" + (f", per share {e['value_per_share']:.2f}" if "value_per_share" in e else ""))
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_sotp(a):
    from . import sotp as S
    res = S.from_dict(_load_json(a.inputs))
    for r in res["segments"]:
        print(f"  {r['segment']:20} {r['metric_name']:8} {r['metric']:>12,.1f} × {r['multiple']:6.2f} = {r['gross_value']:>14,.1f}  ({r['ownership']:.0%} owned → {r['attributable_value']:>14,.1f}, {r['share_of_gross']:.1%} of sum)")
    print(f"Gross EV {res['gross_enterprise_value']:,.1f}  corporate costs {res['capitalised_corporate_costs']:,.1f}  discount {res['conglomerate_discount']:,.1f}  EV {res['enterprise_value']:,.1f}")
    print(f"Equity value {res['equity_value']:,.1f}" + (f"  per share {res['value_per_share']:.2f}" if "value_per_share" in res else ""))
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_startup(a):
    from . import startup_model as SM
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
    from . import cap_table as CT
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
    from . import vc_fund_metrics as VC
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
    from . import percentage_of_completion as POC
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
    from . import cash_flow_forecast as CF
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
    from . import impact_scoring as IS
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


def cmd_strategy(a):
    from . import strategy_frameworks as SF
    res = SF.from_dict(_load_json(a.inputs))
    if "market_sizing_top_down" in res:
        m = res["market_sizing_top_down"]
        print(f"Market sizing (top-down): TAM {m['tam']:,.0f}  SAM {m['sam']:,.0f}  SOM {m['som']:,.0f}  (SOM = {m['som_pct_of_tam']:.2%} of TAM)")
    if "market_sizing_bottom_up" in res:
        m = res["market_sizing_bottom_up"]
        print(f"Market sizing (bottom-up): TAM {m['tam']:,.0f}  SOM {m['som']:,.0f}  (SOM = {m['som_pct_of_tam']:.2%} of TAM)")
        for s in m["segments"]:
            print(f"  {s['segment']:16} TAM {s['segment_tam']:>14,.0f}  SOM {s['segment_som']:>14,.0f}")
    if "bcg_matrix" in res:
        print("BCG Growth-Share Matrix:")
        for u in res["bcg_matrix"]["units"]:
            print(f"  {u['name']:16} rel. share {u['relative_market_share']:.2f}x  growth {u['market_growth_rate']:.1%}  → {u['classification']}")
    if "ge_mckinsey_matrix" in res:
        print("GE-McKinsey Nine-Box Matrix:")
        for u in res["ge_mckinsey_matrix"]["units"]:
            print(f"  {u['name']:16} attractiveness {u['industry_attractiveness_bucket']:6} ({u['industry_attractiveness_score']:.2f})  "
                  f"strength {u['business_strength_bucket']:6} ({u['business_strength_score']:.2f})  → {u['zone']}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_ppa(a):
    from . import ppa_valuation as PPA
    res = PPA.from_dict(_load_json(a.inputs))
    for src in ("relief_from_royalty", "mpeem", "cost_approach"):
        if src in res:
            for name, r in res[src].items():
                print(f"{src} — {name}: value {r['value']:,.0f}" + (f" (TAB factor {r['tab_factor']:.3f})" if "tab_factor" in r else ""))
    if "allocation" in res:
        al = res["allocation"]
        print(f"Allocation: intangibles {al['total_intangibles']:,.0f} + net identifiable assets {al['net_identifiable_assets_fair_value']:,.0f} "
              f"= {al['total_identifiable_assets']:,.0f}  →  goodwill {al['goodwill']:,.0f} ({al['goodwill_pct_of_price']:.1%} of price)")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_impairment(a):
    from . import impairment_testing as IT
    res = IT.from_dict(_load_json(a.inputs))
    if "goodwill" in res:
        r = res["goodwill"]
        print(f"Goodwill (ASC 350): impaired={r['impaired']}, loss {r['impairment_loss']:,.0f}, remaining goodwill {r['remaining_goodwill']:,.0f}")
    if "indefinite_lived_intangible" in res:
        r = res["indefinite_lived_intangible"]
        print(f"Indefinite-lived intangible (ASC 350-30): impaired={r['impaired']}, loss {r['impairment_loss']:,.0f}")
    if "long_lived_asset" in res:
        r = res["long_lived_asset"]
        print(f"Long-lived asset (ASC 360): Step 1 recoverable={r['step1_recoverable']}, impaired={r['impaired']}, loss {r['impairment_loss']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_audit_analytics(a):
    from . import audit_analytics as AA
    res = AA.from_dict(_load_json(a.inputs))
    if "benford" in res:
        b = res["benford"]
        print(f"Benford's Law (n={b['n']}): MAD {b['mad']:.4f} → {b['conformity']}")
    if "journal_entries" in res:
        j = res["journal_entries"]
        print(f"Journal entry testing: {j['n_flagged']}/{j['n_entries']} entries flagged")
        for f in j["flagged"]:
            print(f"  {f.get('id', '?'):>6}  amount {f.get('amount', 0):>12,.0f}  flags: {', '.join(f['flags'])}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_options(a):
    from . import options as O
    res = O.from_dict(_load_json(a.inputs))
    if "black_scholes" in res:
        r = res["black_scholes"]
        print(f"{r['option_type'].capitalize()} price: {r['price']:.4f}  (d1={r['d1']:.4f}, d2={r['d2']:.4f})")
    if "greeks" in res:
        g = res["greeks"]
        print(f"Greeks: delta {g['delta']:.4f}  gamma {g['gamma']:.4f}  vega {g['vega']:.4f}  theta {g['theta']:.4f}  rho {g['rho']:.4f}")
    if "put_call_parity" in res:
        p = res["put_call_parity"]
        print(f"Put-call parity: C-P={p['lhs_call_minus_put']:.4f} vs synthetic forward {p['rhs_synthetic_forward']:.4f}  →  holds={p['holds']} (gap {p['arbitrage_gap']:.6f})")
    if "implied_volatility" in res:
        print(f"Implied volatility: {res['implied_volatility']:.4%}")
    if "geometric_asian_option" in res:
        r = res["geometric_asian_option"]
        print(f"Geometric Asian {r['option_type']}: {r['price']:.4f}  (adjusted vol {r['adjusted_volatility']:.4f}, cost of carry {r['effective_cost_of_carry']:.4f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_project_finance(a):
    from . import project_finance as PF
    res = PF.from_dict(_load_json(a.inputs))
    if "size_debt_by_dscr" in res:
        r = res["size_debt_by_dscr"]
        print(f"Debt sized to target DSCR {r['target_dscr']:.2f}x: max debt {r['max_debt_sized']:,.0f}")
    if "sculpted_amortization" in res:
        r = res["sculpted_amortization"]
        for i, row in enumerate(r["schedule"], 1):
            print(f"  period {i}: CFADS {row['cfads']:>12,.0f}  debt service {row['debt_service']:>12,.0f}  DSCR {row['dscr']:.2f}x  closing balance {row['closing_balance']:>12,.0f}")
        print(f"Fully repaid: {r['fully_repaid']}")
    if "llcr" in res:
        print(f"LLCR: {res['llcr']['llcr']:.2f}x")
    if "cap_rate_valuation" in res:
        print(f"Cap rate valuation: NOI {res['cap_rate_valuation']['noi']:,.0f} / {res['cap_rate_valuation']['cap_rate']:.2%}  →  value {res['cap_rate_valuation']['value']:,.0f}")
    if "levered_cash_on_cash" in res:
        print(f"Cash-on-cash return: {res['levered_cash_on_cash']['cash_on_cash_return']:.2%}")
    if "level_annuity_schedule" in res:
        r = res["level_annuity_schedule"]
        print(f"Level annuity: payment {r['level_payment']:,.0f}/yr, total interest {r['total_interest']:,.0f}")
    if "interest_only_bullet_schedule" in res:
        r = res["interest_only_bullet_schedule"]
        print(f"Interest-only + bullet: total interest {r['total_interest']:,.0f}, bullet {r['bullet_principal']:,.0f} at maturity")
    if "balloon_coverage_ratio" in res:
        print(f"Balloon coverage: {res['balloon_coverage_ratio']['coverage_ratio']:.2f}x")
    if "compare_debt_structures" in res:
        print("Debt structure comparison:")
        for name, s in res["compare_debt_structures"].items():
            print(f"  {name:20} total interest {s['total_interest']:>12,.0f}  year-1 debt service {s['year1_debt_service']:>12,.0f}  min DSCR {s['min_dscr']:.2f}x  avg DSCR {s['average_dscr']:.2f}x")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_dcf_diagnostics(a):
    from . import dcf as D
    d = _load_json(a.inputs)
    out = D.check_unlevered_tax_consistency(d["ebit"], d["cash_taxes_used"], d["tax_rate"], tolerance=d.get("tolerance", 0.01))
    print(f"Likely uses levered (double-counted-shield) tax in an unlevered FCF: {out['likely_uses_levered_tax']}")
    if out["flagged_periods"]:
        print(f"Flagged periods (0-indexed): {out['flagged_periods']}")
    print(f"Total gap vs. a correctly unlevered tax build (undiscounted): {out['total_gap_undiscounted']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(out, indent=1))


def cmd_portfolio(a):
    from . import portfolio_optimization as PO
    res = PO.from_dict(_load_json(a.inputs))
    if "global_minimum_variance" in res:
        r = res["global_minimum_variance"]
        print(f"Global minimum-variance portfolio: weights {['%.2f%%' % (w*100) for w in r['weights']]}  vol {r['volatility']:.2%}")
    if "efficient_frontier" in res:
        print("Efficient frontier:")
        for p in res["efficient_frontier"]:
            print(f"  target return {p['target_return']:.2%}  →  vol {p['volatility']:.2%}  weights {['%.2f%%' % (w*100) for w in p['weights']]}")
    if "tangency" in res:
        t = res["tangency"]
        print(f"Tangency portfolio: weights {['%.2f%%' % (w*100) for w in t['weights']]}  return {t['expected_return']:.2%}  vol {t['volatility']:.2%}  Sharpe {t['sharpe_ratio']:.3f}")
    if "capital_allocation_line" in res:
        print("Capital Allocation Line:")
        for p in res["capital_allocation_line"]:
            print(f"  vol {p['volatility']:.2%}  →  return {p['expected_return']:.2%}  ({p['weight_in_tangency_portfolio']:.1%} in tangency, {p['weight_in_risk_free']:.1%} in risk-free)")
    if "portfolio_stats" in res:
        s = res["portfolio_stats"]
        print(f"Portfolio: return {s['expected_return']:.2%}  vol {s['volatility']:.2%}" + (f"  Sharpe {s['sharpe_ratio']:.3f}" if "sharpe_ratio" in s else ""))
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_restructuring(a):
    from . import restructuring as R
    res = R.from_dict(_load_json(a.inputs))
    if "recovery_waterfall" in res:
        wf = res["recovery_waterfall"]
        print(f"Recovery waterfall (reorg value {wf['reorg_value']:,.0f}):")
        for t in wf["tranches"]:
            print(f"  {t['name']:28} seniority {t['seniority']}  claim {t['claim_amount']:>14,.0f}  recovery {t['recovery']:>14,.0f}  ({t['recovery_pct']:.1%})")
        print(f"  Residual to equity: {wf['residual_to_equity']:,.0f}")
    if "fulcrum_security" in res:
        f = res["fulcrum_security"]
        print(f"Fulcrum security: {f['name']}" + (f" ({f['recovery_pct']:.1%} recovery)" if f.get("name") else f" — {f.get('note')}"))
    if "absolute_priority_check" in res:
        c = res["absolute_priority_check"]
        print(f"Absolute priority respected: {c['absolute_priority_respected']}" + (f"  departures: {c['departures']}" if c["departures"] else ""))
    if "dip_financing_sizing" in res:
        d = res["dip_financing_sizing"]
        print(f"DIP financing required: {d['required_dip_facility']:,.0f} (minimum projected cash {d['minimum_projected_cash']:,.0f} vs covenant {d['minimum_liquidity_covenant']:,.0f})")
    if "post_emergence_capital_structure" in res:
        p = res["post_emergence_capital_structure"]
        print(f"Post-emergence new debt: {p['new_debt']:,.0f} ({p['target_net_debt_to_ebitda']:.2f}x EBITDA {p['emergence_ebitda']:,.0f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_bank_model(a):
    from . import bank_model as B
    res = B.from_dict(_load_json(a.inputs))
    if "income_statement" in res:
        r = res["income_statement"]
        print(f"NII {r['nii']:,.0f} (NIM {r['nim']:.2%})  provision {r['provision']:,.0f}  efficiency ratio {r['efficiency_ratio']:.1%}  net income {r['net_income']:,.0f}")
    if "projection" in res:
        for row in res["projection"]:
            print(f"  year {row['year']}: NII {row['nii']:>14,.0f}  net income {row['net_income']:>14,.0f}  efficiency ratio {row['efficiency_ratio']:.1%}")
    if "regulatory_capital_ratios" in res:
        r = res["regulatory_capital_ratios"]
        print(f"CET1 {r['cet1_ratio']:.2%}  Tier1 {r['tier1_ratio']:.2%}  Total capital {r['total_capital_ratio']:.2%}  leverage {r['leverage_ratio']:.2%}  well-capitalized={r['well_capitalized']}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_cohort_analysis(a):
    from . import cohort_analysis as C
    res = C.from_dict(_load_json(a.inputs))
    if "retention_curve" in res:
        print(f"Retention curve: {['%.1f%%' % (p*100) for p in res['retention_curve']['retention_pct']]}")
    if "ltv_from_retention_curve" in res:
        print(f"LTV (from retention curve): {res['ltv_from_retention_curve']['ltv']:,.2f}")
    if "ltv_simplified" in res:
        print(f"LTV (simplified, ARPU x margin / churn): {res['ltv_simplified']['ltv']:,.2f}  (avg lifetime {res['ltv_simplified']['average_customer_lifetime_months']:.1f} months)")
    if "revenue_retention" in res:
        r = res["revenue_retention"]
        print(f"GRR {r['gross_revenue_retention']:.1%}  NRR {r['net_revenue_retention']:.1%}")
    if "ltv_to_cac" in res:
        print(f"LTV:CAC ratio: {res['ltv_to_cac']['ratio']:.2f}x")
    if "cac_payback_months" in res:
        print(f"CAC payback: {res['cac_payback_months']['cac_payback_months']:.1f} months")
    if "cohort_revenue_projection" in res:
        print(f"Cohort revenue by period: {['%.0f' % v for v in res['cohort_revenue_projection']['revenue_by_period']]}  total {res['cohort_revenue_projection']['total_revenue']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_insurance_pricing(a):
    from . import insurance_pricing as I
    res = I.from_dict(_load_json(a.inputs))
    if "combined_ratio" in res:
        r = res["combined_ratio"]
        print(f"Loss ratio {r['loss_ratio']:.1%}  expense ratio {r['expense_ratio']:.1%}  combined ratio {r['combined_ratio']:.1%}  underwriting profitable={r['underwriting_profitable']}")
    if "operating_ratio" in res:
        r = res["operating_ratio"]
        print(f"Operating ratio {r['operating_ratio']:.1%}  overall profitable={r['overall_profitable']}")
    if "rate_making_premium" in res:
        r = res["rate_making_premium"]
        print(f"Gross premium: {r['gross_premium']:,.2f}  (loss cost multiplier {r['loss_cost_multiplier']:.3f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_convertible_bonds(a):
    from . import convertible_bonds as CB
    res = CB.from_dict(_load_json(a.inputs))
    if "bond_floor" in res:
        print(f"Bond floor: {res['bond_floor']['bond_floor']:,.2f}")
    if "convertible_bond_value" in res:
        v = res["convertible_bond_value"]
        print(f"Conversion ratio {v['conversion_ratio']:.2f}  bond floor {v['bond_floor']:,.2f}  option value {v['option_value']:,.2f}  "
              f"conversion value {v['conversion_value']:,.2f}  estimated value {v['estimated_value']:,.2f}")
    if "conversion_premium" in res:
        print(f"Conversion premium: {res['conversion_premium']:.2%}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_cmo(a):
    from . import cmo as C
    res = C.from_dict(_load_json(a.inputs))
    if "cmo_deal" in res:
        r = res["cmo_deal"]
        print(f"Pool fully amortizes in {len(r['pool_cash_flows'])} months at {r['psa_pct']:.0%} PSA")
        for name, wal in r["weighted_average_life"].items():
            print(f"  Tranche {name}: WAL {wal:.2f} years")
    if "psa_sensitivity" in res:
        print("PSA sensitivity (Weighted Average Life by tranche):")
        for speed, wal in res["psa_sensitivity"].items():
            print(f"  {speed:>8}: " + "  ".join(f"{name} {w:.2f}y" for name, w in wal.items()))
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_variance_analysis(a):
    from . import variance_analysis as V
    res = V.from_dict(_load_json(a.inputs))
    if "budget_vs_actual_variance" in res:
        r = res["budget_vs_actual_variance"]
        print(f"Budget {r['budget_total']:,.0f}  actual {r['actual_total']:,.0f}  →  total variance {r['total_variance']:,.0f} "
              f"(volume {r['volume_variance']:,.0f}, price {r['price_variance']:,.0f})")
    if "sales_mix_and_volume_variance" in res:
        r = res["sales_mix_and_volume_variance"]
        for p in r["products"]:
            print(f"  {p['name']:16} mix variance {p['mix_variance']:>12,.0f}  quantity variance {p['quantity_variance']:>12,.0f}")
        print(f"Total: mix {r['total_sales_mix_variance']:,.0f}  quantity {r['total_sales_quantity_variance']:,.0f}")
    if "horizontal_analysis" in res:
        for name, r in res["horizontal_analysis"].items():
            pct = ["n/a" if p is None else f"{p:+.1%}" for p in r["pct_change"]]
            print(f"  {name:24} {r['values']}  →  {pct}")
    if "vertical_analysis" in res:
        for name, pcts in res["vertical_analysis"].items():
            print(f"  {name:24} {['%.1f%%' % (p*100) for p in pcts]}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_fpa_planning(a):
    from . import fpa_planning as F
    res = F.from_dict(_load_json(a.inputs))
    if "headcount_cost_schedule" in res:
        r = res["headcount_cost_schedule"]
        print(f"Headcount monthly cost: {['%.0f' % v for v in r['monthly_cost']]}  total {r['total_cost']:,.0f}")
    if "rolling_forecast" in res:
        r = res["rolling_forecast"]
        print(f"Rolling forecast: actuals {r['actuals_to_date']}  →  forecast {['%.1f' % v for v in r['forecast']]}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_breakeven(a):
    from . import breakeven as B
    res = B.from_dict(_load_json(a.inputs))
    if "break_even_point" in res:
        r = res["break_even_point"]
        print(f"Break-even: {r['break_even_units']:,.0f} units ({r['break_even_revenue']:,.0f} revenue), contribution margin {r['contribution_margin_ratio']:.1%}")
    if "margin_of_safety" in res:
        r = res["margin_of_safety"]
        print(f"Margin of safety: {r['unit_cushion']:,.0f} units ({r['margin_of_safety_pct']:.1%})")
    if "degree_of_operating_leverage" in res:
        r = res["degree_of_operating_leverage"]
        print(f"Degree of operating leverage: {r['degree_of_operating_leverage']:.2f}x (operating profit {r['operating_profit']:,.0f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_loss_reserving(a):
    from . import loss_reserving as LR
    res = LR.from_dict(_load_json(a.inputs))
    if "chain_ladder" in res:
        r = res["chain_ladder"]
        print(f"Age-to-age factors: {['%.4f' % f for f in r['age_to_age_factors']]}")
        for ay in r["accident_years"]:
            print(f"  AY{ay['accident_year_index']}: latest {ay['latest_cumulative']:,.0f}  ultimate {ay['ultimate']:,.0f}  IBNR {ay['ibnr']:,.0f}")
        print(f"Total IBNR: {r['total_ibnr']:,.0f}  (total ultimate {r['total_ultimate']:,.0f})")
    if "bornhuetter_ferguson" in res:
        r = res["bornhuetter_ferguson"]
        for ay in r["accident_years"]:
            print(f"  AY{ay['accident_year_index']}: {ay['pct_reported']:.1%} reported  BF ultimate {ay['bf_ultimate']:,.0f}  (chain-ladder {ay['chain_ladder_ultimate']:,.0f})")
        print(f"Total BF ultimate: {r['total_bf_ultimate']:,.0f}  (BF IBNR {r['total_bf_ibnr']:,.0f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_earnout_valuation(a):
    from . import earnout_valuation as EO
    res = EO.from_dict(_load_json(a.inputs))
    if "scenario_weighted_earnout" in res:
        r = res["scenario_weighted_earnout"]
        print(f"Scenario-weighted earnout: expected payout {r['expected_payout']:,.0f}  PV {r['present_value']:,.0f}")
    if "binary_metric_earnout" in res:
        r = res["binary_metric_earnout"]
        print(f"Binary metric earnout: P(achieved) {r['risk_neutral_probability_achieved']:.1%}  PV {r['present_value']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_tax_provision(a):
    from . import tax_provision as TP
    res = TP.from_dict(_load_json(a.inputs))
    if "deferred_tax_position" in res:
        r = res["deferred_tax_position"]
        print(f"Deferred tax: gross DTA {r['gross_dta']:,.0f}  gross DTL {r['gross_dtl']:,.0f}  net {r['net_deferred_tax']:,.0f}")
    if "valuation_allowance" in res:
        r = res["valuation_allowance"]
        print(f"Valuation allowance: {'required' if r['valuation_allowance_required'] else 'not required'} ({r['valuation_allowance']:,.0f}), net DTA {r['net_dta']:,.0f}")
    if "nol_carryforward_schedule" in res:
        r = res["nol_carryforward_schedule"]
        print(f"NOL schedule: total cash tax {r['total_cash_tax']:,.0f}  expired NOL {r['total_expired_nol']:,.0f}")
    if "effective_tax_rate_reconciliation" in res:
        r = res["effective_tax_rate_reconciliation"]
        print(f"Effective tax rate: {r['effective_tax_rate']:.1%} (statutory tax {r['statutory_tax']:,.0f}, total tax {r['total_tax']:,.0f})")
    if "deferred_tax_rollforward" in res:
        r = res["deferred_tax_rollforward"]
        print(f"Deferred tax rollforward: {r['beginning_balance']:,.0f} -> {r['ending_balance']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_real_estate_development(a):
    from . import real_estate_development as RE
    res = RE.from_dict(_load_json(a.inputs))
    if "total_development_cost" in res:
        r = res["total_development_cost"]
        print(f"Total development cost: {r['total_development_cost']:,.0f} (contingency {r['contingency']:,.0f})")
    if "development_pro_forma" in res:
        r = res["development_pro_forma"]
        print(f"Development pro forma: cost basis {r['total_cost_basis']:,.0f}  exit value {r['exit_value']:,.0f}  "
              f"profit {r['development_profit']:,.0f}  yield on cost {r['yield_on_cost']:.2%}  "
              f"spread {r['development_spread_bps']:,.0f} bps  unlevered IRR {r['unlevered_irr_annual']:.1%}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_working_capital_financing(a):
    from . import working_capital_financing as WCF
    res = WCF.from_dict(_load_json(a.inputs))
    if "factoring_cost" in res:
        r = res["factoring_cost"]
        print(f"Factoring: advance {r['advance_amount']:,.0f}  fee {r['fee_amount']:,.0f}  net proceeds {r['net_proceeds']:,.0f}  effective APR {r['effective_annual_rate']:.1%}")
    if "early_payment_discount_apr" in res:
        print(f"Early-payment discount APR: {res['early_payment_discount_apr']:.1%}")
    if "asset_based_lending_availability" in res:
        r = res["asset_based_lending_availability"]
        print(f"ABL availability: borrowing base {r['borrowing_base']:,.0f}  available to draw {r['available_to_draw']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_retail_loans(a):
    from . import retail_loans as RL
    res = RL.from_dict(_load_json(a.inputs))
    if "emi_calculation" in res:
        print(f"EMI: {res['emi_calculation']['emi']:,.2f}")
    if "amortization_schedule" in res:
        r = res["amortization_schedule"]
        print(f"Amortization: EMI {r['emi']:,.2f}  total interest {r['total_interest']:,.0f}  total payment {r['total_payment']:,.0f}")
    if "prepayment_impact" in res:
        r = res["prepayment_impact"]
        if r["loan_fully_repaid"]:
            print(f"Prepayment ({r['strategy']}): loan fully repaid, interest saved {r['interest_saved']:,.0f}")
        else:
            print(f"Prepayment ({r['strategy']}): new EMI {r['new_emi']:,.2f}  new tenure {r['new_tenure_months']} months  interest saved {r['interest_saved']:,.0f}")
    if "floating_rate_reset" in res:
        r = res["floating_rate_reset"]
        print(f"Rate reset ({r['strategy']}): {r['old_rate']:.2%} -> {r['new_rate']:.2%}  new EMI {r['new_emi']:,.2f}  new tenure {r['new_tenure_months']} months")
    if "foreclosure_payoff" in res:
        r = res["foreclosure_payoff"]
        print(f"Foreclosure payoff: {r['payoff_amount']:,.0f}  interest saved vs completing tenure {r['interest_saved_vs_completing_tenure']:,.0f}")
    if "loan_eligibility_foir" in res:
        r = res["loan_eligibility_foir"]
        print(f"Loan eligibility (FOIR): max eligible principal {r['max_eligible_principal']:,.0f} (available EMI capacity {r['available_emi_capacity']:,.0f})")
    if "step_up_emi_schedule" in res:
        r = res["step_up_emi_schedule"]
        print(f"Step-up EMI: base {r['base_emi']:,.2f} -> final {r['final_emi']:,.2f}  total interest {r['total_interest']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_retail_deposits(a):
    from . import retail_deposits as RD
    res = RD.from_dict(_load_json(a.inputs))
    if "fixed_deposit_maturity" in res:
        r = res["fixed_deposit_maturity"]
        print(f"FD maturity: {r['maturity_value']:,.0f} (interest earned {r['interest_earned']:,.0f})")
    if "recurring_deposit_maturity" in res:
        r = res["recurring_deposit_maturity"]
        print(f"RD maturity: {r['maturity_value']:,.0f} (deposited {r['total_deposited']:,.0f}, interest earned {r['interest_earned']:,.0f})")
    if "recurring_deposit_premature_value" in res:
        r = res["recurring_deposit_premature_value"]
        print(f"RD premature closure value: {r['premature_value']:,.0f} (interest earned {r['interest_earned']:,.0f})")
    if "tds_on_interest" in res:
        r = res["tds_on_interest"]
        print(f"TDS: {'applicable' if r['tds_applicable'] else 'not applicable'} ({r['tds_amount']:,.0f}), net interest {r['net_interest']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_carry_trade(a):
    from . import carry_trade as CT
    res = CT.from_dict(_load_json(a.inputs))
    if "covered_interest_rate_parity" in res:
        r = res["covered_interest_rate_parity"]
        print(f"CIP forward rate: {r['forward_rate']:,.4f}  (forward premium {r['forward_premium_pct']:.2%})")
    if "uncovered_carry_return" in res:
        r = res["uncovered_carry_return"]
        print(f"Uncovered carry return: {r['return_pct']:.2%}  (profit {r['profit']:,.0f})")
    if "break_even_depreciation" in res:
        r = res["break_even_depreciation"]
        print(f"Break-even depreciation: {r['break_even_depreciation_pct']:.2%}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_revolving_credit(a):
    from . import revolving_credit as RC
    res = RC.from_dict(_load_json(a.inputs))
    if "daily_balance_interest" in res:
        r = res["daily_balance_interest"]
        print(f"Daily-balance interest: {r['total_interest']:,.2f} over {r['num_days']} days (average balance {r['average_balance']:,.0f})")
    if "credit_card_minimum_payment_schedule" in res:
        r = res["credit_card_minimum_payment_schedule"]
        if r["paid_off"]:
            print(f"Minimum-payment schedule: paid off in {r['months_to_payoff']} months, total interest {r['total_interest_paid']:,.0f}")
        else:
            print(f"Minimum-payment schedule: NOT paid off within the simulated window (negative amortization or too slow); interest so far {r['total_interest_paid']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_npa_classification(a):
    from . import npa_classification as NPA
    res = NPA.from_dict(_load_json(a.inputs))
    if "npa_provisioning" in res:
        r = res["npa_provisioning"]
        seg = f" ({r['segment']})" if "segment" in r else ""
        print(f"Classification: {r['classification']}{seg}  provision required {r['provision_required']:,.0f} ({r['provision_rate_effective']:.2%} of outstanding)")
    if "loan_book" in res:
        for r in res["loan_book"]:
            seg = f" [{r['segment']}]" if "segment" in r else ""
            print(f"  {r['classification']:12}{seg:28} outstanding {r['outstanding_amount']:>12,.0f}  provision {r['provision_required']:>12,.0f}")
        print(f"Total provision required: {res['total_provision_required']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_pipeline(a):
    from . import pipeline as PL
    res = PL.from_dict(_load_json(a.inputs))
    for name in res["order"]:
        print(f"Step '{name}': {', '.join(res['steps'][name].keys())}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_credit_risk(a):
    from . import credit_risk as CR
    res = CR.from_dict(_load_json(a.inputs))
    if "expected_loss" in res:
        r = res["expected_loss"]
        print(f"Expected loss: {r['expected_loss']:,.2f} (PD {r['pd']:.2%} x LGD {r['lgd']:.2%} x EAD {r['ead']:,.0f})")
    if "basel_irb_corporate" in res:
        r = res["basel_irb_corporate"]
        print(f"Basel IRB: risk weight {r['risk_weight_pct']:.1%}  RWA {r['risk_weighted_assets']:,.0f}  min capital {r['minimum_capital_required']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_interest_rate_risk(a):
    from . import interest_rate_risk as IRR
    res = IRR.from_dict(_load_json(a.inputs))
    if "repricing_gap" in res:
        r = res["repricing_gap"]
        for b in r["buckets"]:
            print(f"  {b['name']:10} gap {b['gap']:>14,.0f}  cumulative {b['cumulative_gap']:>14,.0f}")
        print(f"Total gap: {r['total_gap']:,.0f}  (gap ratio {r['gap_ratio']:.1%})")
    if "nii_sensitivity" in res:
        r = res["nii_sensitivity"]
        print(f"NII sensitivity to {r['rate_shock']:+.2%} rate shock: {r['delta_nii']:+,.0f} ({'asset' if r['nii_rises_with_rates'] else 'liability'}-sensitive)")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_fixed_income_risk(a):
    from . import fixed_income_risk as FIR
    res = FIR.from_dict(_load_json(a.inputs))
    if "bond_price_and_duration" in res:
        r = res["bond_price_and_duration"]
        print(f"Bond: price {r['price']:,.4f}  Macaulay duration {r['macaulay_duration_years']:.4f}y  "
              f"modified duration {r['modified_duration']:.4f}  DV01 {r['dv01']:.4f}  convexity {r['convexity']:.4f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_credit_card_abs(a):
    from . import credit_card_abs as CCA
    res = CCA.from_dict(_load_json(a.inputs))
    if "excess_spread" in res:
        print(f"Excess spread: {res['excess_spread']['value']:.2%}")
    if "early_amortization_trigger" in res:
        r = res["early_amortization_trigger"]
        status = f"triggered at month {r['triggered_month']}" if r["triggered"] else "not triggered"
        print(f"Early amortization: {status}")
    if "master_trust_cash_flows" in res:
        r = res["master_trust_cash_flows"]
        print(f"Master trust: {r['months_to_full_paydown']} months to full paydown "
              f"({r['revolving_period_months']} revolving, fully paid down: {r['fully_paid_down']})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_sales_capacity_planning(a):
    from . import sales_capacity_planning as SCP
    res = SCP.from_dict(_load_json(a.inputs))
    if "sales_capacity_schedule" in res:
        r = res["sales_capacity_schedule"]
        for p in r["periods"]:
            print(f"  Period {p['period']}: headcount {p['headcount']:.1f}  bookings capacity {p['bookings_capacity']:,.0f}")
        print(f"Total capacity: {r['total_capacity']:,.0f}")
    if "reps_needed_for_target" in res:
        r = res["reps_needed_for_target"]
        print(f"Reps needed: {r['reps_needed']:.1f} (effective quota {r['effective_quota_per_rep']:,.0f} at {r['ramp_fraction_at_target_period']:.0%} ramp)")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_lease_accounting(a):
    from . import lease_accounting as LA
    res = LA.from_dict(_load_json(a.inputs))
    if "classify_lease" in res:
        r = res["classify_lease"]
        print(f"Lease classification: {r['classification']}" + (f" ({'; '.join(r['reasons'])})" if r["reasons"] else ""))
    if "initial_measurement" in res:
        r = res["initial_measurement"]
        print(f"Initial measurement: lease liability {r['lease_liability']:,.0f}  ROU asset {r['rou_asset']:,.0f}")
    if "finance_lease_schedule" in res:
        r = res["finance_lease_schedule"]
        print(f"Finance lease: period 1 expense {r['schedule'][0]['total_expense']:,.0f} -> "
              f"period {len(r['schedule'])} expense {r['schedule'][-1]['total_expense']:,.0f} (front-loaded)")
    if "operating_lease_schedule" in res:
        r = res["operating_lease_schedule"]
        print(f"Operating lease: flat expense {r['straight_line_expense']:,.0f} every period")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_fx_hedging(a):
    from . import fx_hedging as FXH
    res = FXH.from_dict(_load_json(a.inputs))
    if "fx_hedge_comparison" in res:
        r = res["fx_hedge_comparison"]
        line = f"Forward hedge {r['forward_hedge_value']:,.0f}  Money-market hedge {r['money_market_hedge_value']:,.0f}"
        if "unhedged_value" in r:
            line += f"  Unhedged {r['unhedged_value']:,.0f}"
        print(line)
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_stock_based_compensation(a):
    from . import stock_based_compensation as SBC
    res = SBC.from_dict(_load_json(a.inputs))
    if "rsu_grant_fair_value" in res:
        print(f"RSU grant fair value: {res['rsu_grant_fair_value']['value']:,.0f}")
    if "stock_option_grant_fair_value" in res:
        r = res["stock_option_grant_fair_value"]
        print(f"Option grant fair value: {r['total_fair_value']:,.0f}  ({r['fair_value_per_share']:.4f} per share)")
    if "straight_line_expense_schedule" in res:
        r = res["straight_line_expense_schedule"]
        print(f"Straight-line expense: {r['period_expense']:,.0f} per period over {len(r['schedule'])} periods")
    if "graded_vesting_expense_schedule" in res:
        r = res["graded_vesting_expense_schedule"]
        print(f"Graded vesting: period 1 expense {r['schedule'][0]['expense']:,.0f} -> "
              f"period {len(r['schedule'])} expense {r['schedule'][-1]['expense']:,.0f} (front-loaded)")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_bond_amortization(a):
    from . import bond_amortization as BA
    res = BA.from_dict(_load_json(a.inputs))
    if "bond_amortization_schedule" in res:
        r = res["bond_amortization_schedule"]
        print(f"Bond issued at {r['issued_at']}: issue price {r['issue_price']:,.2f}  "
              f"(premium/discount {r['premium_or_discount']:,.2f})  ending carrying value {r['schedule'][-1]['carrying_value']:,.2f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_foreign_currency_translation(a):
    from . import foreign_currency_translation as FCT
    res = FCT.from_dict(_load_json(a.inputs))
    if "current_rate_translation" in res:
        r = res["current_rate_translation"]
        print(f"Translated net income: {r['translated_net_income']:,.2f}")
        print(f"Translated assets {r['translated_assets']:,.2f} = liabilities {r['translated_liabilities']:,.2f} + "
              f"equity {r['total_translated_equity']:,.2f}  (CTA {r['cumulative_translation_adjustment']:+,.2f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_inventory_costing(a):
    from . import inventory_costing as IC
    res = IC.from_dict(_load_json(a.inputs))
    for method in ("fifo", "lifo", "weighted_average"):
        if method in res:
            r = res[method]
            print(f"{method}: COGS {r['cogs']:,.2f}  ending inventory {r['ending_inventory_value']:,.2f}")
    if "compare_costing_methods" in res:
        r = res["compare_costing_methods"]
        print(f"Total cost available: {r['total_cost_available']:,.2f}")
        for method in ("fifo", "weighted_average", "lifo"):
            print(f"  {method:16} COGS {r[method]['cogs']:>12,.2f}  ending inventory {r[method]['ending_inventory_value']:>12,.2f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_pension_accounting(a):
    from . import pension_accounting as PA
    res = PA.from_dict(_load_json(a.inputs))
    if "pbo_rollforward" in res:
        r = res["pbo_rollforward"]
        print(f"PBO: {r['beginning_pbo']:,.0f} -> {r['ending_pbo']:,.0f}")
    if "plan_assets_rollforward" in res:
        r = res["plan_assets_rollforward"]
        print(f"Plan assets: {r['beginning_plan_assets']:,.0f} -> {r['ending_plan_assets']:,.0f}")
    if "funded_status" in res:
        r = res["funded_status"]
        print(f"Funded status: {r['funded_status']:+,.0f} ({r['classification']})")
    if "net_periodic_pension_cost" in res:
        r = res["net_periodic_pension_cost"]
        print(f"Net periodic pension cost: {r['net_periodic_pension_cost']:,.0f}")
    if "asset_gain_loss" in res:
        print(f"Asset gain/loss: {res['asset_gain_loss']['value']:+,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_nwc_peg(a):
    from . import nwc_peg as NWC
    res = NWC.from_dict(_load_json(a.inputs))
    for key in ("nwc_true_up", "working_capital_adjustment"):
        if key in res:
            r = res[key]
            print(f"NWC true-up: actual {r['actual_nwc_at_closing']:,.0f} vs peg {r['peg_nwc']:,.0f}  "
                  f"adjustment {r['purchase_price_adjustment']:+,.0f} ({r['direction']})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_eps_calculation(a):
    from . import eps_calculation as EPSC
    res = EPSC.from_dict(_load_json(a.inputs))
    if "basic_eps" in res:
        print(f"Basic EPS: {res['basic_eps']['basic_eps']:.4f}")
    if "diluted_eps" in res:
        r = res["diluted_eps"]
        print(f"Diluted EPS: {r['diluted_eps']:.4f}  (basic {r['basic_eps']:.4f}, "
              f"{len(r['dilutive_securities_included'])} dilutive securities included)")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_investment_securities(a):
    from . import investment_securities as IS
    res = IS.from_dict(_load_json(a.inputs))
    if "classify_and_measure" in res:
        r = res["classify_and_measure"]
        print(f"{r['classification']}: carrying value {r['carrying_value']:,.0f}  "
              f"(income statement impact {r['income_statement_impact']:+,.0f}, OCI impact {r['oci_impact']:+,.0f})")
    if "realized_gain_loss_on_sale" in res:
        r = res["realized_gain_loss_on_sale"]
        print(f"Realized gain/loss: {r['realized_gain_loss']:+,.0f}  (reclassified from OCI {r['reclassification_adjustment_from_oci']:+,.0f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_consolidation(a):
    from . import consolidation as CONS
    res = CONS.from_dict(_load_json(a.inputs))
    if "consolidated_net_income" in res:
        r = res["consolidated_net_income"]
        print(f"Consolidated NI: {r['consolidated_net_income']:,.0f}  NCI share {r['nci_share_of_net_income']:,.0f}  "
              f"attributable to parent {r['net_income_attributable_to_parent']:,.0f}")
    if "nci_balance_sheet" in res:
        r = res["nci_balance_sheet"]
        print(f"NCI balance: {r['nci_balance']:,.0f}  (parent share {r['parent_share_of_subsidiary_equity']:,.0f})")
    if "nci_at_acquisition_fair_value_method" in res:
        print(f"NCI at acquisition (fair value method): {res['nci_at_acquisition_fair_value_method']['nci_initial_value']:,.0f}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_debt_covenants(a):
    from . import debt_covenants as DC
    res = DC.from_dict(_load_json(a.inputs))
    for key in ("leverage_ratio_covenant", "interest_coverage_covenant", "fixed_charge_coverage_covenant"):
        if key in res:
            r = res[key]
            status = "OK" if r["compliant"] else "*** BREACH ***"
            print(f"  {r['covenant']:28} headroom {r['headroom']:+.3f}  {status}")
    if "covenant_compliance_summary" in res:
        s = res["covenant_compliance_summary"]
        print(f"Covenant summary: {s['total_covenants_tested']} tested, all compliant: {s['all_compliant']}")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_asset_retirement_obligations(a):
    from . import asset_retirement_obligations as ARO
    res = ARO.from_dict(_load_json(a.inputs))
    if "initial_aro_recognition" in res:
        r = res["initial_aro_recognition"]
        print(f"Initial ARO liability: {r['initial_aro_liability']:,.2f}")
    if "accretion_schedule" in res:
        r = res["accretion_schedule"]
        print(f"Accretion schedule: {len(r['schedule'])} years  final ARO liability {r['final_aro_liability']:,.2f}")
    if "settlement_gain_loss" in res:
        r = res["settlement_gain_loss"]
        print(f"Settlement: {r['gain_loss']:+,.2f} ({r['classification']})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_warranty_and_receivables_allowance(a):
    from . import warranty_and_receivables_allowance as WRA
    res = WRA.from_dict(_load_json(a.inputs))
    if "warranty_reserve_rollforward" in res:
        r = res["warranty_reserve_rollforward"]
        print(f"Warranty reserve: {r['beginning_reserve']:,.0f} -> {r['ending_reserve']:,.0f}  (additions {r['additions']:,.0f})")
    if "receivables_allowance_aging_method" in res:
        r = res["receivables_allowance_aging_method"]
        for b in r["buckets"]:
            print(f"  {b['bucket']:10} balance {b['balance']:>12,.0f}  allowance {b['allowance']:>10,.0f}")
        print(f"Total allowance: {r['total_allowance']:,.0f}  (net realizable {r['net_realizable_receivables']:,.0f})")
    if a.json_out: Path(a.json_out).write_text(json.dumps(res, indent=1))


def cmd_investment_incentives(a):
    from . import investment_incentives as INC
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
    from . import sector_investment_model as SIM
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
    from . import project_bankability as PB
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
    from . import india_corporate_tax_regimes as TAX
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
    from . import india_depreciation_schedule as DEP
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
    from . import india_incentive_workbook as WB
    path = WB.build_workbook(a.output)
    print(f"Wrote {path}")


def cmd_audit(a):
    from . import audit as A
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
    from . import charts
    d = _load_json(a.inputs)
    if a.engine == "three_statement":
        from . import three_statement as ts; res = ts.from_dict(d).to_dict()
    elif a.engine == "dcf":
        from . import dcf; inp = dcf.DCFInputs(**dcf.clean(d)); res = dcf.run(inp)
        res["sensitivity"] = dcf.sensitivity(inp, [inp.discount_rate + x for x in (-0.02, -0.01, 0, 0.01, 0.02)], [inp.perpetual_growth + x for x in (-0.01, -0.005, 0, 0.005, 0.01)])
    elif a.engine == "lbo":
        from . import lbo; res = lbo.from_dict(d)
    elif a.engine == "merger":
        from . import merger; res = merger.from_dict(d)
    elif a.engine == "comps":
        from . import comps; res = comps.from_dict(d)
    else:
        from . import projection; res = projection.from_dict(d)
    p = charts.report_for(a.engine, res, a.out, title=a.title)
    print(f"wrote {p} ({len(charts.CATALOG[a.engine]['charts'])} chart templates)")


def cmd_glossary(a):
    g = _load_json(Path(__file__).resolve().parent.parent / "data" / "glossary.json")
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
    ex = Path(__file__).resolve().parent.parent / "examples"
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    from . import three_statement as ts, dcf, projection
    from .excel import write_three_statement, write_dcf, write_projection
    d = _load_json(ex / "cfi_three_statement.json")
    r = ts.from_dict(d)
    write_three_statement(out / "three_statement.xlsx", [ts.HistoricalYear(**h) for h in d["historical"]], ts.ForecastAssumptions(**d["forecast"]), d.get("ppe_opening0"), d.get("debt_opening0"), r)
    print(r.table("income_statement")); print(); print(r.table("balance_sheet")); print(f"balanced={r.balanced}\n")
    dd = _load_json(ex / "cfi_dcf.json"); inp = dcf.DCFInputs(**dcf.clean(dd)); rr = dcf.run(inp); write_dcf(out / "dcf.xlsx", inp)
    print(f"DCF: EV={rr['enterprise_value']:,.0f} equity/share={rr['equity_value_per_share']:.2f} upside={rr['target_price_upside']:.1%} IRR={rr['irr']:.1%}\n")
    pr = projection.from_dict(_load_json(ex / "projection_demo.json")); write_projection(out / "projection.xlsx", pr)
    print(f"Projection: years={pr['years']} revenue={[round(x) for x in pr['income_statement']['Revenue']]} balanced={pr['balanced']}")
    from . import charts
    charts.report_for("three_statement", r.to_dict(), out / "charts_three_statement.html")
    rr["sensitivity"] = dcf.sensitivity(inp, [inp.discount_rate + x for x in (-0.02, -0.01, 0, 0.01, 0.02)], [inp.perpetual_growth + x for x in (-0.01, -0.005, 0, 0.005, 0.01)])
    charts.report_for("dcf", rr, out / "charts_dcf.html"); charts.report_for("projection", pr, out / "charts_projection.html")
    from . import lbo, merger
    charts.report_for("lbo", lbo.from_dict(_load_json(ex / "lbo_asm.json")), out / "charts_lbo.html")
    charts.report_for("merger", merger.from_dict(_load_json(ex / "merger_biws.json")), out / "charts_merger.html")
    print(f"\nworkbooks and chart reports written to {out}/")


def main(argv=None):
    p = argparse.ArgumentParser(prog="finmodel", description="Financial modelling toolkit distilled from CFI templates")
    p.add_argument("--version", action="version", version=__version__)
    sp = p.add_subparsers(dest="cmd", required=True)

    x = sp.add_parser("extract", help="extract an Excel template into JSON+Markdown spec"); x.add_argument("files", nargs="+"); x.add_argument("-o", "--out", default="extracted"); x.set_defaults(fn=cmd_extract)
    c = sp.add_parser("catalog", help="build / list / verify / fetch template sources / alternatives"); c.add_argument("action", choices=["build", "list", "verify", "fetch", "alternatives", "fetch-signed", "paid"]); c.add_argument("--title", help="paid: filter titles containing this text")
    c.add_argument("--source", nargs="*", help="damodaran asimplemodel exinfm cfi"); c.add_argument("--auth", help='CFI header, e.g. "Cookie: ..." (or env FINMODEL_CFI_AUTH)')
    c.add_argument("--dest", default="downloads"); c.add_argument("--urls", help="fetch-signed: text file with one pre-signed URL per line"); c.add_argument("--overwrite", action="store_true"); c.add_argument("--limit", type=int); c.set_defaults(fn=cmd_catalog)
    t = sp.add_parser("three-statement", help="run the linked 3-statement model"); t.add_argument("inputs"); t.add_argument("--xlsx"); t.add_argument("--json-out"); t.add_argument("--table", help="income_statement|balance_sheet|cash_flow|schedules|all"); t.set_defaults(fn=cmd_three)
    d = sp.add_parser("dcf", help="run the unlevered DCF"); d.add_argument("inputs"); d.add_argument("--xlsx"); d.add_argument("--json-out"); d.add_argument("--sensitivity", action="store_true"); d.set_defaults(fn=cmd_dcf)
    j = sp.add_parser("projection", help="run the bottom-up projection"); j.add_argument("inputs"); j.add_argument("--xlsx"); j.add_argument("--json-out"); j.set_defaults(fn=cmd_projection)
    r = sp.add_parser("ratios", help="ratio analysis from {is:{}, bs:{}}"); r.add_argument("inputs"); r.add_argument("--json-out"); r.set_defaults(fn=cmd_ratios)
    l = sp.add_parser("lbo", help="run the LBO model"); l.add_argument("inputs"); l.add_argument("--xlsx"); l.add_argument("--json-out"); l.set_defaults(fn=cmd_lbo)
    g = sp.add_parser("merger", help="run the merger (accretion/dilution) model"); g.add_argument("inputs"); g.add_argument("--xlsx"); g.add_argument("--json-out"); g.set_defaults(fn=cmd_merger)
    tp = sp.add_parser("transpile", help="convert a workbook's formulas to Python and verify against cached values"); tp.add_argument("files", nargs="+"); tp.add_argument("-o", "--out"); tp.add_argument("--show", type=int, default=5); tp.set_defaults(fn=cmd_transpile)
    cp = sp.add_parser("comps", help="trading comps, precedent transactions, implied valuation and football field"); cp.add_argument("inputs"); cp.add_argument("--xlsx"); cp.add_argument("--json-out"); cp.set_defaults(fn=cmd_comps)
    sc = sp.add_parser("scores", help="Altman Z, Piotroski F, Beneish M from two fiscal years of statement data"); sc.add_argument("inputs"); sc.add_argument("--json-out"); sc.set_defaults(fn=cmd_scores)
    co = sp.add_parser("costing", help="EUA-style resource allocation, cost allocation and income diversification"); co.add_argument("inputs"); co.add_argument("--json-out"); co.set_defaults(fn=cmd_costing)
    ed = sp.add_parser("edgar", help="pull annual statements for a CIK from SEC EDGAR company facts"); ed.add_argument("cik"); ed.add_argument("--user-agent", required=True, help="e.g. 'my-tool name@example.com' (SEC requires a contact)"); ed.add_argument("--years", type=int, default=8); ed.add_argument("--cache-dir"); ed.add_argument("--json-out"); ed.set_defaults(fn=cmd_edgar)
    cy = sp.add_parser("cycle", help="where a company's LTM year sits in its own margin cycle, and data-driven DCF scenario targets from its own history"); cy.add_argument("edgar_json", help="a data/edgar/<TICKER>.json extract (finmodel edgar --json-out)"); cy.add_argument("--sector", default="default", choices=["steel", "oil_gas", "software", "banking", "reit", "airline", "insurance", "semiconductor", "utility", "pharma", "default"]); cy.add_argument("--field", help="numerator field, e.g. net_income for banks (default: operating_income)"); cy.add_argument("--revenue-field", dest="revenue_field", default="revenue", help="denominator field, e.g. equity for banks' ROE (default: revenue)"); cy.add_argument("--periods", type=int, default=8); cy.add_argument("--as-of"); cy.add_argument("--json-out"); cy.set_defaults(fn=cmd_cycle)
    wc = sp.add_parser("wacc", help="CAPM cost of equity, synthetic-rating cost of debt, bottom-up beta and WACC"); wc.add_argument("inputs"); wc.add_argument("--json-out"); wc.set_defaults(fn=cmd_wacc)
    ri = sp.add_parser("residual-income", help="residual-income (EBO) equity valuation and/or EVA firm valuation"); ri.add_argument("inputs"); ri.add_argument("--json-out"); ri.set_defaults(fn=cmd_residual_income)
    so = sp.add_parser("sotp", help="sum-of-the-parts valuation across segments"); so.add_argument("inputs"); so.add_argument("--json-out"); so.set_defaults(fn=cmd_sotp)
    from . import startup_model as _SM
    su = sp.add_parser("startup", help="new-business 3-statement projection + DCF valuation, benchmarked against real sector peer data"); su.add_argument("inputs"); su.add_argument("--benchmark-sector", choices=list(_SM.SECTOR_PEER_TICKERS)); su.add_argument("--json-out"); su.set_defaults(fn=cmd_startup)
    ct = sp.add_parser("cap-table", help="priced-round dilution (with the option-pool shuffle) and an exit liquidation-preference waterfall"); ct.add_argument("inputs"); ct.add_argument("--json-out"); ct.set_defaults(fn=cmd_cap_table)
    vf = sp.add_parser("vc-fund", help="VC/PE fund LP metrics (DPI/RVPI/TVPI/IRR), deal-level MOIC/IRR, and European or American (deal-by-deal, with clawback) carry waterfalls"); vf.add_argument("inputs"); vf.add_argument("--json-out"); vf.set_defaults(fn=cmd_vc_fund)
    cf = sp.add_parser("cash-flow-forecast", help="13-week rolling direct-method cash flow forecast, covenant-breach flagging, forecast-vs-actual variance"); cf.add_argument("inputs"); cf.add_argument("--json-out"); cf.set_defaults(fn=cmd_cash_flow_forecast)
    ic = sp.add_parser("impact", help="2X Criteria gender-lens screen, Impact Management Project ABC classification, GHG intensity"); ic.add_argument("inputs"); ic.add_argument("--json-out"); ic.set_defaults(fn=cmd_impact)
    sf = sp.add_parser("strategy", help="TAM/SAM/SOM market sizing, BCG growth-share matrix, GE-McKinsey nine-box matrix"); sf.add_argument("inputs"); sf.add_argument("--json-out"); sf.set_defaults(fn=cmd_strategy)
    ppa = sp.add_parser("ppa", help="purchase price allocation: relief-from-royalty, MPEEM, cost approach, ASC 805 goodwill residual"); ppa.add_argument("inputs"); ppa.add_argument("--json-out"); ppa.set_defaults(fn=cmd_ppa)
    imp = sp.add_parser("impairment", help="ASC 350 goodwill / ASC 350-30 indefinite-lived intangible / ASC 360 long-lived-asset impairment tests"); imp.add_argument("inputs"); imp.add_argument("--json-out"); imp.set_defaults(fn=cmd_impairment)
    aa = sp.add_parser("audit-analytics", help="Benford's Law digit-conformity test and rule-based journal-entry testing (JET)"); aa.add_argument("inputs"); aa.add_argument("--json-out"); aa.set_defaults(fn=cmd_audit_analytics)
    opt = sp.add_parser("options", help="Black-Scholes option pricing, the Greeks, put-call parity, implied volatility"); opt.add_argument("inputs"); opt.add_argument("--json-out"); opt.set_defaults(fn=cmd_options)
    pf = sp.add_parser("project-finance", help="DSCR-based debt sizing/sculpting, LLCR, cap rate/NOI real-estate valuation"); pf.add_argument("inputs"); pf.add_argument("--json-out"); pf.set_defaults(fn=cmd_project_finance)
    pfo = sp.add_parser("portfolio", help="Markowitz efficient frontier, global minimum-variance and tangency portfolios, Capital Allocation Line"); pfo.add_argument("inputs"); pfo.add_argument("--json-out"); pfo.set_defaults(fn=cmd_portfolio)
    rs = sp.add_parser("restructuring", help="absolute-priority recovery waterfall, fulcrum security, DIP financing sizing, post-emergence capital structure"); rs.add_argument("inputs"); rs.add_argument("--json-out"); rs.set_defaults(fn=cmd_restructuring)
    bm = sp.add_parser("bank-model", help="bank operating model: NII/NIM, provision for credit losses, efficiency ratio, regulatory capital ratios"); bm.add_argument("inputs"); bm.add_argument("--json-out"); bm.set_defaults(fn=cmd_bank_model)
    ca = sp.add_parser("cohort", help="SaaS cohort retention curves, GRR/NRR, LTV, LTV:CAC, CAC payback"); ca.add_argument("inputs"); ca.add_argument("--json-out"); ca.set_defaults(fn=cmd_cohort_analysis)
    ip = sp.add_parser("insurance-pricing", help="loss/expense/combined/operating ratios, loss-cost-multiplier rate making"); ip.add_argument("inputs"); ip.add_argument("--json-out"); ip.set_defaults(fn=cmd_insurance_pricing)
    cvb = sp.add_parser("convertible", help="convertible bond bond-floor + embedded-option (two-component) valuation, conversion premium"); cvb.add_argument("inputs"); cvb.add_argument("--json-out"); cvb.set_defaults(fn=cmd_convertible_bonds)
    cmo = sp.add_parser("cmo", help="CMO: PSA prepayment modeling, sequential-pay tranching, weighted average life"); cmo.add_argument("inputs"); cmo.add_argument("--json-out"); cmo.set_defaults(fn=cmd_cmo)
    dcfd = sp.add_parser("dcf-diagnostics", help="flags a DCF that double-counts the interest tax shield (levered cash taxes in an unlevered FCF)"); dcfd.add_argument("inputs"); dcfd.add_argument("--json-out"); dcfd.set_defaults(fn=cmd_dcf_diagnostics)
    va = sp.add_parser("variance-analysis", help="budget-vs-actual volume/price/mix variance, horizontal and vertical (common-size) analysis"); va.add_argument("inputs"); va.add_argument("--json-out"); va.set_defaults(fn=cmd_variance_analysis)
    fpap = sp.add_parser("fpa-planning", help="headcount/workforce cost schedule, driver-based rolling forecast"); fpap.add_argument("inputs"); fpap.add_argument("--json-out"); fpap.set_defaults(fn=cmd_fpa_planning)
    bke = sp.add_parser("breakeven", help="break-even point, margin of safety, degree of operating leverage (CVP analysis)"); bke.add_argument("inputs"); bke.add_argument("--json-out"); bke.set_defaults(fn=cmd_breakeven)
    lr = sp.add_parser("loss-reserving", help="chain-ladder loss development triangle (age-to-age factors, projected ultimates, IBNR) and Bornhuetter-Ferguson"); lr.add_argument("inputs"); lr.add_argument("--json-out"); lr.set_defaults(fn=cmd_loss_reserving)
    eov = sp.add_parser("earnout-valuation", help="M&A contingent-consideration fair value: scenario-weighted expected payout, or a binary metric-threshold digital option"); eov.add_argument("inputs"); eov.add_argument("--json-out"); eov.set_defaults(fn=cmd_earnout_valuation)
    poc = sp.add_parser("percentage-of-completion", help="cost-to-cost revenue recognition for long-term contracts: percent complete, revenue/gross profit to date, over/under-billing"); poc.add_argument("inputs"); poc.add_argument("--json-out"); poc.set_defaults(fn=cmd_percentage_of_completion)
    cca = sp.add_parser("credit-card-abs", help="credit-card master-trust securitization: excess spread, the 3-month early-amortization trigger, revolving/amortization cash flows"); cca.add_argument("inputs"); cca.add_argument("--json-out"); cca.set_defaults(fn=cmd_credit_card_abs)
    scp = sp.add_parser("sales-capacity-planning", help="rep productivity ramp curves, bookings-capacity forecasting, reps needed to hit a target"); scp.add_argument("inputs"); scp.add_argument("--json-out"); scp.set_defaults(fn=cmd_sales_capacity_planning)
    lac = sp.add_parser("lease-accounting", help="ASC 842 lease classification, initial measurement, and finance/operating lease expense schedules"); lac.add_argument("inputs"); lac.add_argument("--json-out"); lac.set_defaults(fn=cmd_lease_accounting)
    fxh = sp.add_parser("fx-hedging", help="corporate FX exposure hedging: forward hedge vs money-market hedge vs unhedged"); fxh.add_argument("inputs"); fxh.add_argument("--json-out"); fxh.set_defaults(fn=cmd_fx_hedging)
    sbc = sp.add_parser("stock-based-compensation", help="ASC 718 RSU/option grant fair value and straight-line vs graded-vesting expense attribution"); sbc.add_argument("inputs"); sbc.add_argument("--json-out"); sbc.set_defaults(fn=cmd_stock_based_compensation)
    bam = sp.add_parser("bond-amortization", help="effective-interest bond premium/discount amortization schedule"); bam.add_argument("inputs"); bam.add_argument("--json-out"); bam.set_defaults(fn=cmd_bond_amortization)
    fct = sp.add_parser("fx-translation", help="ASC 830 current-rate method: translate a foreign subsidiary's statements, with the Cumulative Translation Adjustment plug"); fct.add_argument("inputs"); fct.add_argument("--json-out"); fct.set_defaults(fn=cmd_foreign_currency_translation)
    ivc = sp.add_parser("inventory-costing", help="FIFO, LIFO, and weighted-average cost-flow assumptions for cost of goods sold and ending inventory"); ivc.add_argument("inputs"); ivc.add_argument("--json-out"); ivc.set_defaults(fn=cmd_inventory_costing)
    pea = sp.add_parser("pension-accounting", help="ASC 715 PBO/plan-asset roll-forwards, funded status, and net periodic pension cost"); pea.add_argument("inputs"); pea.add_argument("--json-out"); pea.set_defaults(fn=cmd_pension_accounting)
    nwc = sp.add_parser("nwc-peg", help="M&A net-working-capital peg and closing true-up purchase-price adjustment"); nwc.add_argument("inputs"); nwc.add_argument("--json-out"); nwc.set_defaults(fn=cmd_nwc_peg)
    epsc = sp.add_parser("eps", help="ASC 260 basic and diluted EPS (treasury stock method, if-converted method, antidilution test)"); epsc.add_argument("inputs"); epsc.add_argument("--json-out"); epsc.set_defaults(fn=cmd_eps_calculation)
    invs = sp.add_parser("investment-securities", help="ASC 320 trading/AFS/HTM classification and unrealized gain/loss routing, OCI reclassification on sale"); invs.add_argument("inputs"); invs.add_argument("--json-out"); invs.set_defaults(fn=cmd_investment_securities)
    cons = sp.add_parser("consolidation", help="ASC 810 consolidated net income, noncontrolling interest (NCI) carve-out, NCI at acquisition"); cons.add_argument("inputs"); cons.add_argument("--json-out"); cons.set_defaults(fn=cmd_consolidation)
    dcv = sp.add_parser("debt-covenants", help="borrower-side leverage/interest-coverage/fixed-charge-coverage covenant compliance testing"); dcv.add_argument("inputs"); dcv.add_argument("--json-out"); dcv.set_defaults(fn=cmd_debt_covenants)
    aro = sp.add_parser("aro", help="ASC 410 asset retirement obligation: initial PV recognition, accretion schedule, settlement gain/loss"); aro.add_argument("inputs"); aro.add_argument("--json-out"); aro.set_defaults(fn=cmd_asset_retirement_obligations)
    wra = sp.add_parser("warranty-receivables", help="warranty reserve roll-forward (expected-cost method) and CECL aging-method receivables allowance"); wra.add_argument("inputs"); wra.add_argument("--json-out"); wra.set_defaults(fn=cmd_warranty_and_receivables_allowance)
    ii = sp.add_parser("investment-incentives", help="capital/interest/net-tax/employment investment-incentive mechanics used by Indian central and state schemes (PLI, BIPA-style state schemes, etc.)"); ii.add_argument("inputs"); ii.add_argument("--json-out"); ii.set_defaults(fn=cmd_investment_incentives)
    sim = sp.add_parser("sector-investment-model", help="sample state/sector investment model: land cost + capex stack netted against a discounted central+state incentive package"); sim.add_argument("inputs"); sim.add_argument("--json-out"); sim.set_defaults(fn=cmd_sector_investment_model)
    pbk = sp.add_parser("project-bankability", help="IRR/ROI/payback with and without incentives, plus a state/sector ranking that flags projects incentives make bankable"); pbk.add_argument("inputs"); pbk.add_argument("--json-out"); pbk.set_defaults(fn=cmd_project_bankability)
    iiw = sp.add_parser("india-incentive-workbook", help="write the consolidated India state/central incentive + land-cost + 28-state matrix Excel workbook"); iiw.add_argument("output", help="output .xlsx path"); iiw.set_defaults(fn=cmd_india_incentive_workbook)
    tax = sp.add_parser("india-tax-regimes", help="Section 115BAB vs 115BAA vs standard-regime post-tax IRR comparison, and the CGTMSE guarantee fee's effect on DSCR"); tax.add_argument("inputs"); tax.add_argument("--json-out"); tax.set_defaults(fn=cmd_india_corporate_tax_regimes)
    dep = sp.add_parser("india-depreciation-schedule", help="Income Tax Act WDV block-of-assets depreciation, section 50 short-term capital gain on block extinguishment, section 32(1)(iia) additional depreciation"); dep.add_argument("inputs"); dep.add_argument("--json-out"); dep.set_defaults(fn=cmd_india_depreciation_schedule)
    txp = sp.add_parser("tax-provision", help="deferred tax position, valuation allowance, NOL carryforward (pre-2018/post-2017 baskets), effective-rate reconciliation"); txp.add_argument("inputs"); txp.add_argument("--json-out"); txp.set_defaults(fn=cmd_tax_provision)
    red = sp.add_parser("real-estate-development", help="ground-up development pro forma: TDC, construction-loan draw schedule, yield on cost, development spread, unlevered IRR"); red.add_argument("inputs"); red.add_argument("--json-out"); red.set_defaults(fn=cmd_real_estate_development)
    wcf = sp.add_parser("working-capital-financing", help="invoice factoring cost, early-payment-discount APR, asset-based-lending borrowing-base availability"); wcf.add_argument("inputs"); wcf.add_argument("--json-out"); wcf.set_defaults(fn=cmd_working_capital_financing)
    rl = sp.add_parser("retail-loans", help="EMI, amortization schedule, prepayment (reduce-tenure/reduce-EMI), floating-rate reset, foreclosure payoff, FOIR loan eligibility, step-up EMI"); rl.add_argument("inputs"); rl.add_argument("--json-out"); rl.set_defaults(fn=cmd_retail_loans)
    rdp = sp.add_parser("retail-deposits", help="fixed deposit maturity, recurring deposit maturity (per-installment compounding), premature RD closure, Section 194A TDS"); rdp.add_argument("inputs"); rdp.add_argument("--json-out"); rdp.set_defaults(fn=cmd_retail_deposits)
    ctd = sp.add_parser("carry-trade", help="covered interest rate parity forward rate, unhedged FX carry return, break-even depreciation"); ctd.add_argument("inputs"); ctd.add_argument("--json-out"); ctd.set_defaults(fn=cmd_carry_trade)
    rvc = sp.add_parser("revolving-credit", help="cash-credit/overdraft and credit-card daily-balance interest; the minimum-payment trap"); rvc.add_argument("inputs"); rvc.add_argument("--json-out"); rvc.set_defaults(fn=cmd_revolving_credit)
    npa = sp.add_parser("npa-classification", help="RBI IRAC asset classification (Standard/SMA/NPA buckets) and secured/unsecured provisioning"); npa.add_argument("inputs"); npa.add_argument("--json-out"); npa.set_defaults(fn=cmd_npa_classification)
    pln = sp.add_parser("pipeline", help="chain multiple finmodel modules together, referencing earlier steps' outputs with ${step.path} placeholders"); pln.add_argument("inputs"); pln.add_argument("--json-out"); pln.set_defaults(fn=cmd_pipeline)
    crk = sp.add_parser("credit-risk", help="expected loss (PD x LGD x EAD) and the Basel IRB risk-weighted-assets formula"); crk.add_argument("inputs"); crk.add_argument("--json-out"); crk.set_defaults(fn=cmd_credit_risk)
    irr = sp.add_parser("interest-rate-risk", help="bank repricing gap and first-order NII sensitivity to a rate shock"); irr.add_argument("inputs"); irr.add_argument("--json-out"); irr.set_defaults(fn=cmd_interest_rate_risk)
    fir = sp.add_parser("fixed-income-risk", help="bond price, Macaulay/modified duration, DV01, convexity"); fir.add_argument("inputs"); fir.add_argument("--json-out"); fir.set_defaults(fn=cmd_fixed_income_risk)
    au = sp.add_parser("audit", help="workbook audit: error values, hard-coded plugs, inconsistent formulas, links, hidden sheets"); au.add_argument("file"); au.add_argument("--recompute", action="store_true", help="also verify every formula against its cached value (finmodel.xlcalc)"); au.add_argument("--show", type=int, default=20); au.add_argument("--json-out"); au.add_argument("--markdown-out"); au.set_defaults(fn=cmd_audit)
    ch = sp.add_parser("charts", help="render the chart template for an engine's inputs to a self-contained HTML report"); ch.add_argument("engine", choices=["three_statement", "dcf", "lbo", "merger", "projection", "comps"]); ch.add_argument("inputs"); ch.add_argument("-o", "--out", default="out/charts.html"); ch.add_argument("--title"); ch.set_defaults(fn=cmd_charts)
    gl = sp.add_parser("glossary", help="look up a financial term (definition, formula, GAAP vs IFRS note)"); gl.add_argument("query", nargs="+"); gl.add_argument("--deep", action="store_true"); gl.add_argument("--limit", type=int, default=5); gl.set_defaults(fn=cmd_glossary)
    m = sp.add_parser("demo", help="run all engines on the bundled examples and write workbooks"); m.add_argument("--out", default="out"); m.set_defaults(fn=cmd_demo)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
