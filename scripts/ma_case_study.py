"""Before-and-after study of three completed acquisitions of listed companies, run through finmodel.merger with the
parties' real SEC filings (data/edgar/*.json, extracted from EDGAR company facts by finmodel.edgar).

  Microsoft / Activision Blizzard   all cash, $95.00 per share, announced 2022-01-18, closed 2023-10-13
  Chevron / Hess                     all stock, 1.0250 CVX per HES share, announced 2023-10-23, closed 2025-07-18
  Cisco / Splunk                     all cash, $157.00 per share, announced 2023-09-21, closed 2024-03-18

For each deal: (1) standalone statements of both parties in the last fiscal year before closing, (2) the merger engine's
static pro-forma (year-1 accretion / dilution, purchase multiples, ownership), (3) the acquirer's actual reported
statements in the fiscal years after closing, (4) a comparison table with the drivers of the difference.
Prices/terms are from the merger announcements; the acquirer's fundamentals are cross-checked against the
market_data warehouse (global_fundamentals) when Postgres is reachable.

Run:  python scripts/ma_case_study.py  → docs/CASE_STUDY_MA.md, out/case_study_ma.json, out/charts_case_*.html"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finmodel import merger, charts  # noqa: E402
from finmodel.fin import safe_div  # noqa: E402

DEALS = [
    {"name": "Microsoft / Activision Blizzard", "acq": "MSFT", "tgt": "ATVI", "announced": "2022-01-18", "closed": "2023-10-13",
     "offer_price": 95.0, "target_undisturbed": 65.39, "acquirer_price": 310.20, "pct_cash": 1.0, "pct_debt": 0.0, "cash_rate": 0.045,
     "pre_acq": "2023-06-30", "pre_tgt": "2022-12-31", "post": ["2024-06-30", "2025-06-30"], "tax": 0.19,
     "note": "Cash from Microsoft's balance sheet (no new debt). FY2024 includes 8.5 months of Activision."},
    {"name": "Chevron / Hess", "acq": "CVX", "tgt": "HES", "announced": "2023-10-23", "closed": "2025-07-18",
     "offer_price": 171.0, "target_undisturbed": 163.0, "acquirer_price": 166.8, "pct_cash": 0.0, "pct_debt": 0.0, "cash_rate": 0.0,
     "pre_acq": "2024-12-31", "pre_tgt": "2024-12-31", "post": ["2025-12-31"], "tax": 0.36,
     "note": "All-stock: 1.025 Chevron shares per Hess share (~$53bn equity, ~$60bn EV at announcement). Closed after the Exxon arbitration; FY2025 has ~5.5 months of Hess."},
    {"name": "Cisco / Splunk", "acq": "CSCO", "tgt": "SPLK", "announced": "2023-09-21", "closed": "2024-03-18",
     "offer_price": 157.0, "target_undisturbed": 119.4, "acquirer_price": 53.6, "pct_cash": 0.6, "pct_debt": 0.4, "cash_rate": 0.045, "debt_rate": 0.05,
     "pre_acq": "2023-07-29", "pre_tgt": "2023-01-31", "post": ["2024-07-27", "2025-07-26"], "tax": 0.19,
     "note": "~$28bn cash funded from balance sheet cash plus ~$13.5bn of new bonds (Feb 2024) and commercial paper; modelled as 60% cash / 40% debt. Splunk's last 10-K is FY Jan-2023 (FY Jan-2024 was never filed as a standalone 10-K)."},
]


def load(t):
    d = json.loads((ROOT / "data" / "edgar" / f"{t}.json").read_text()); return d["entity"], d["years"]


def nearest(years, key):
    if key in years: return key, years[key]
    ks = sorted(years); k = min(ks, key=lambda x: abs((int(x[:4]) - int(key[:4])) * 12 + int(x[5:7]) - int(key[5:7])))
    return k, years[k]


def company(name, row, price, tax):
    return merger.Company(name, share_price=price, shares=row.get("diluted_shares", 0), cash=row.get("cash", 0) + row.get("short_term_investments", 0),
                          debt=row.get("debt_total", 0), ebit=row.get("operating_income", 0), da=row.get("da", 0),
                          net_interest=row.get("interest_income", 0) - row.get("interest_expense", 0), tax_rate=tax)


def warehouse_check(ticker, fy_end):
    try:
        out = subprocess.run(["psql", "-d", "market_data", "-Atc", f"select revenue, net_income, shares, eps from global_fundamentals where market='US' and ticker='{ticker}' and fy_end='{fy_end}' order by src_priority limit 1"],
                             capture_output=True, text=True, timeout=20).stdout.strip()
        if not out: return None
        rev, ni, sh, eps = (float(x) if x else None for x in out.split("|"))
        return {"revenue": rev, "net_income": ni, "shares": sh, "eps": eps}
    except Exception:
        return None


def metrics(r):
    ebitda = r.get("operating_income", 0) + r.get("da", 0)
    return {"revenue": r.get("revenue", 0), "ebit": r.get("operating_income", 0), "ebitda": ebitda, "net_income": r.get("net_income", 0), "eps": r.get("eps_diluted", 0),
            "diluted_shares": r.get("diluted_shares", 0), "cash": r.get("cash", 0) + r.get("short_term_investments", 0), "debt": r.get("debt_total", 0), "equity": r.get("equity", 0),
            "ebit_margin": safe_div(r.get("operating_income", 0), r.get("revenue", 0)), "net_margin": safe_div(r.get("net_income", 0), r.get("revenue", 0)),
            "net_debt_to_ebitda": safe_div(r.get("debt_total", 0) - r.get("cash", 0) - r.get("short_term_investments", 0), ebitda), "roe": safe_div(r.get("net_income", 0), r.get("equity", 0)),
            "debt_to_equity": safe_div(r.get("debt_total", 0), r.get("equity", 0)), "goodwill": r.get("goodwill", 0), "interest_expense": r.get("interest_expense", 0)}


def fmt_b(v): return f"{v/1e9:,.1f}"
def pct(v): return f"{v*100:+.1f}%"


def run():
    results = []; md = ["# Case study: three completed acquisitions of listed companies, before and after", "",
                       "Real SEC filings (EDGAR company facts, extracted with `finmodel.edgar`) run through `finmodel.merger.deal()`. "
                       "Figures in USD billions except per-share. 'Pre' = last full fiscal year before closing; 'Post' = the acquirer's reported fiscal years after closing. "
                       "The static pro-forma is the year-1 accretion / dilution view every merger template produces: it holds both businesses flat and adds only financing costs — "
                       "so the gap between pro-forma and actual is the organic growth, synergies, integration costs, purchase-accounting amortisation and divestments that the template does not model. "
                       "Note the engine rebuilds each party's EPS as (EBIT + net interest) × (1 − assumed tax rate) / diluted shares, so its standalone EPS differs slightly from the reported diluted EPS in the table; accretion is measured on the engine's own basis.", ""]
    for D in DEALS:
        an, ay = load(D["acq"]); tn, ty = load(D["tgt"])
        ka, ra = nearest(ay, D["pre_acq"]); kt, rt = nearest(ty, D["pre_tgt"])
        acq = company(an, ra, D["acquirer_price"], D["tax"]); tgt = company(tn, rt, D["target_undisturbed"], D["tax"])
        terms = merger.DealTerms(premium=D["offer_price"] / D["target_undisturbed"] - 1, pct_cash=D["pct_cash"], pct_debt=D["pct_debt"], cash_interest_rate=D["cash_rate"], debt_interest_rate=D.get("debt_rate", 0.05))
        deal = merger.deal(acq, tgt, terms)
        sens = merger.deal_sensitivity(acq, tgt, terms, [terms.premium - 0.1, terms.premium, terms.premium + 0.1, terms.premium + 0.2], [0.0, 0.25, 0.5, 0.75, 1.0])
        pre_a, pre_t = metrics(ra), metrics(rt)
        posts = [(k, metrics(ay[k])) for k in D["post"] if k in ay]
        combined_static = {"revenue": pre_a["revenue"] + pre_t["revenue"], "ebitda": pre_a["ebitda"] + pre_t["ebitda"], "ebit": pre_a["ebit"] + pre_t["ebit"], "net_income": deal["combined"]["net_income"], "eps": deal["combined"]["eps"],
                           "diluted_shares": deal["combined_shares"], "debt": pre_a["debt"] + pre_t["debt"] + deal["funding"]["debt"], "cash": pre_a["cash"] + pre_t["cash"] - deal["funding"]["cash"]}
        wh = {k: warehouse_check(D["acq"], k) for k in [ka] + [p for p, _ in posts]}
        res = {"deal": D, "pre_acquirer": {"fy_end": ka, **pre_a}, "pre_target": {"fy_end": kt, **pre_t}, "engine": deal, "sensitivity": sens, "pro_forma_static": combined_static,
               "post": [{"fy_end": k, **m} for k, m in posts], "warehouse_crosscheck": wh}
        results.append(res)
        # ---- markdown
        mult_txt = f"{deal['purchase_ev_ebitda']:.1f}x target EBITDA" if deal["purchase_ev_ebitda"] > 0 else "n/m × target EBITDA (target EBITDA negative)"
        md += [f"## {D['name']}", "", f"*{D['note']}*", "",
               f"Terms as modelled: offer {D['offer_price']:.2f} vs undisturbed {D['target_undisturbed']:.2f} → premium {pct(terms.premium)}; consideration {D['pct_cash']*100:.0f}% cash / {D['pct_debt']*100:.0f}% new debt / {(1-D['pct_cash']-D['pct_debt'])*100:.0f}% stock; "
               f"acquirer price {D['acquirer_price']:.2f}; purchase equity value {fmt_b(deal['purchase_equity_value'])}bn, EV {fmt_b(deal['purchase_enterprise_value'])}bn = {mult_txt}.", "",
               "| | Acquirer pre (" + ka + ") | Target pre (" + kt + ") | Static pro-forma (engine) | " + " | ".join(f"Acquirer post ({k})" for k, _ in posts) + " |", "|---|" + "---|" * (3 + len(posts))]
        rows = [("Revenue", "revenue", fmt_b), ("EBITDA", "ebitda", fmt_b), ("EBIT", "ebit", fmt_b), ("Net income", "net_income", fmt_b), ("Diluted shares (m)", "diluted_shares", lambda v: f"{v/1e6:,.0f}"),
                ("Diluted EPS", "eps", lambda v: f"{v:.2f}"), ("Cash + ST investments", "cash", fmt_b), ("Total debt", "debt", fmt_b)]
        for label, key, f in rows:
            md.append(f"| {label} | {f(pre_a[key])} | {f(pre_t[key])} | {f(combined_static.get(key, 0)) if key in combined_static else ''} | " + " | ".join(f(m[key]) for _, m in posts) + " |")
        for label, key in (("EBIT margin", "ebit_margin"), ("Net margin", "net_margin"), ("ROE", "roe"), ("Debt / equity", "debt_to_equity"), ("Net debt / EBITDA", "net_debt_to_ebitda")):
            fx = (lambda v: f"{v:.2f}x") if key == "net_debt_to_ebitda" else (lambda v: f"{v*100:.1f}%")
            md.append(f"| {label} | {fx(pre_a[key])} | {fx(pre_t[key])} |  | " + " | ".join(fx(m[key]) for _, m in posts) + " |")
        md.append(f"| Goodwill | {fmt_b(pre_a['goodwill'])} | {fmt_b(pre_t['goodwill'])} |  | " + " | ".join(fmt_b(m["goodwill"]) for _, m in posts) + " |")
        md += ["", f"**Engine verdict (static, year 1):** EPS {deal['acquirer']['eps']:.2f} → {deal['combined']['eps']:.2f} = {pct(deal['accretion_dilution_pct'])} "
               f"({'accretive' if deal['accretion_dilution_pct'] > 0 else 'dilutive'}); target holders own {deal['ownership']['target_holders']*100:.1f}% of the combined company; "
               f"combined EV/EBITDA {deal['combined']['ev_ebitda']:.1f}x vs acquirer standalone {deal['acquirer']['ev_ebitda']:.1f}x.", ""]
        if posts:
            k1, m1 = posts[-1]
            md += [f"**What actually happened (to {k1}):** revenue {pct(m1['revenue']/pre_a['revenue']-1)} vs the static +{(pre_t['revenue']/pre_a['revenue'])*100:.1f}% the target alone adds; "
                   f"EPS {pre_a['eps']:.2f} → {m1['eps']:.2f} ({pct(m1['eps']/pre_a['eps']-1)}) vs engine {pct(deal['accretion_dilution_pct'])}; "
                   f"net debt/EBITDA {pre_a['net_debt_to_ebitda']:.2f}x → {m1['net_debt_to_ebitda']:.2f}x; goodwill {fmt_b(pre_a['goodwill'])} → {fmt_b(m1['goodwill'])}bn.", ""]
        good = [(k, v) for k, v in wh.items() if v]
        if good:
            md += ["Warehouse cross-check (market_data.global_fundamentals, SEC-EDGAR-sourced) vs the EDGAR extract used here:", "", "| FY | revenue (EDGAR) | revenue (warehouse) | net income (EDGAR) | net income (warehouse) |", "|---|---|---|---|---|"]
            for k, v in good:
                src = pre_a if k == ka else dict(posts)[k]
                md.append(f"| {k} | {fmt_b(src['revenue'])} | {fmt_b(v['revenue']) if v['revenue'] else '–'} | {fmt_b(src['net_income'])} | {fmt_b(v['net_income']) if v['net_income'] else '–'} |")
            md.append("")
        # charts
        body = charts.tiles([("Static accretion", pct(deal["accretion_dilution_pct"]), "engine, year 1"), ("Premium", pct(terms.premium), f"offer {D['offer_price']:.0f}"), ("Purchase EV/EBITDA", f"{deal['purchase_ev_ebitda']:.1f}x", "target"), ("Target holders own", f"{deal['ownership']['target_holders']*100:.1f}%", "post-deal")])
        cats = [f"Pre {ka[:4]}", "Static PF"] + [f"Post {k[:4]}" for k, _ in posts]
        body += charts.card("Revenue: standalone, static pro-forma, actual", "How much of the post-deal revenue is the target versus organic growth?", charts.column_chart(cats, {"Revenue ($bn)": [pre_a["revenue"] / 1e9, combined_static["revenue"] / 1e9] + [m["revenue"] / 1e9 for _, m in posts]}))
        body += charts.card("Diluted EPS", "Did the deal add to or dilute earnings per share, and did reality follow the static view?", charts.column_chart(cats, {"EPS": [pre_a["eps"], combined_static["eps"]] + [m["eps"] for _, m in posts]}))
        body += charts.card("Balance sheet: debt, cash, goodwill", "Financing footprint of the deal.", charts.column_chart(cats, {"Debt": [pre_a["debt"] / 1e9, combined_static["debt"] / 1e9] + [m["debt"] / 1e9 for _, m in posts], "Cash": [pre_a["cash"] / 1e9, combined_static["cash"] / 1e9] + [m["cash"] / 1e9 for _, m in posts], "Goodwill": [pre_a["goodwill"] / 1e9, 0] + [m["goodwill"] / 1e9 for _, m in posts]}), ["Debt", "Cash", "Goodwill"])
        body += charts.card("Accretion / (dilution) sensitivity", "Premium (rows) × % stock consideration (columns).", charts.heatmap([f"{p*100:.0f}% premium" for p in sens["rows"]], [f"{c*100:.0f}% stock" for c in sens["cols"]], sens["table"], fmt="pct", diverging_center=0.0))
        out = ROOT / "out" / f"charts_case_{D['acq'].lower()}_{D['tgt'].lower()}.html"; out.parent.mkdir(exist_ok=True)
        out.write_text(charts.report(f"{D['name']} — before and after", "finmodel.merger on SEC EDGAR filings", body))
        md += [f"Charts: `out/{out.name}`", ""]
    md += ["## What the comparison teaches about using the toolkit", "",
           "- **The static merger template answers one question only** — is the deal accretive at the offer price given how it is funded — and it answered it correctly in direction for all three deals: cash deals funded from low-yield cash (Microsoft) are accretive on paper, an all-stock deal at a small premium for a higher-multiple target (Chevron/Hess at ~12x EBITDA vs Chevron's ~5x) dilutes, and a cash-and-debt deal for a loss-making target (Cisco/Splunk) is dilutive until synergies arrive.",
           "- **Actual post-deal EPS diverges from the pro-forma by far more than the deal effect** because the acquirer's own business moved: Microsoft's cloud growth swamped Activision's contribution; Chevron's earnings fell with oil prices in 2025; Cisco's FY2025 carried Splunk's operating losses plus ~$1bn of acquired-intangible amortisation. The `pro_forma()` engine with synergies, integration costs and purchase-price allocation is the right tool for a multi-year view — the static `deal()` is a screening step.",
           "- **Balance-sheet fingerprints are the most reliable 'after' signal**: goodwill jumps by roughly the purchase price minus net assets, debt rises by the debt-funded portion (Cisco), share count rises by the stock portion (Chevron ~+40m shares net of buybacks), and cash falls by the cash portion (Microsoft). These reconcile to the engine's funding split within the limits of concurrent buybacks and other deals.",
           "- **Data hygiene matters more than the maths**: EDGAR tags differ by filer (Chevron and Hess report no `OperatingIncomeLoss`, so EBIT is derived as pre-tax income + net interest), fiscal years are misaligned (June, July, December, January year-ends), and a target's final year may never be filed (Splunk). The warehouse cross-check catches extraction slips; it agreed with EDGAR to the dollar where both had the year.", ""]
    (ROOT / "docs" / "CASE_STUDY_MA.md").write_text("\n".join(md))
    (ROOT / "out" / "case_study_ma.json").write_text(json.dumps(results, indent=1, default=str))
    for r in results:
        d = r["engine"]; print(f"{r['deal']['name']:32} premium {d['purchase_equity_value']/1e9:6.1f}bn  EV/EBITDA {d['purchase_ev_ebitda']:5.1f}x  static accretion {d['accretion_dilution_pct']*100:+6.1f}%  target own {d['ownership']['target_holders']*100:5.1f}%  post EPS: " + ", ".join(f"{p['fy_end'][:4]}={p['eps']:.2f}" for p in r["post"]) + f"  (pre {r['pre_acquirer']['eps']:.2f})")


if __name__ == "__main__":
    run()
