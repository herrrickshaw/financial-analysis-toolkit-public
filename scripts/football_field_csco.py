"""Third real-company check of the CFI 'Comps, Precedents, Football Field' template — same method as
`scripts/football_field_stld.py` (steel) and `scripts/football_field_cvx.py` (oil & gas), applied to Cisco (CSCO)
in enterprise technology / software, a sector expected (and, per finmodel.sectors, confirmed) to show much lower
earnings cyclicality than either of the first two:

  Trading comps    — Microsoft, Oracle, IBM, Adobe, Salesforce (SEC EDGAR fundamentals, market_data warehouse
                     closing prices, 2026-07-02).
  Precedent deals  — two real, verifiable, large enterprise-software acquisitions, both simple ALL-CASH deals (no
                     exchange ratio or acquirer-price lookup needed, unlike the steel/oil & gas precedents):
                     Broadcom / VMware ($142.50/share, announced 2022-05-26) and IBM / Red Hat ($190.00/share,
                     announced 2018-10-28). Both targets are delisted and absent from the warehouse, so — as with
                     the first two checks — premiums to their own undisturbed price are omitted rather than
                     guessed.
  DCF               — two scenarios built from Cisco's own FY2026 EDGAR base year and its own FY2020-2026 EBIT-
                     margin history (20.8%-27.6% — much tighter than steel's 8-23% or oil & gas's -7% to +20%),
                     discounted at the WACC from `finmodel wacc examples/wacc_csco.json` (8.68%).
  52-week range    — the real trailing 252-trading-day high/low from the warehouse.

The sector-tuned §5 in this script is the interesting part: `finmodel.sectors.trend_diagnostics()` finds that
Cisco's own margin, despite its tight range, still shows a real declining drift (not pure noise) — and that
Salesforce, one of the peers, shows a much stronger genuine SECULAR margin-expansion trend that trailing-median
normalization would badly misread as a cyclical peak. This script normalizes the peer set correctly (using the
trend-aware guard) and shows what would go wrong if it didn't.

Run: python scripts/football_field_csco.py → docs/FOOTBALL_FIELD_CSCO.md, out/comps_football_field_csco.json,
out/charts_football_field_csco.html"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finmodel import comps, charts, dcf, sectors  # noqa: E402

CORE = ["MSFT", "ORCL", "IBM", "ADBE", "CRM"]
TARGET = "CSCO"
PRICE_DATE = "2026-07-02"


def prices(tickers):
    out = subprocess.run(["psql", "-d", "market_data", "-Atc",
                          f"select s.ticker, h.close_price from ohlcv_history h join stocks s on s.stock_id=h.stock_id "
                          f"where s.market_id=2 and s.ticker in ({','.join(repr(t) for t in tickers)}) and h.date='{PRICE_DATE}'"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    return {l.split("|")[0]: float(l.split("|")[1]) for l in out.splitlines() if l}


def week52(ticker):
    out = subprocess.run(["psql", "-d", "market_data", "-Atc",
                          f"with r as (select h.date, h.close_price, row_number() over (order by h.date desc) rn "
                          f"from ohlcv_history h join stocks s on s.stock_id=h.stock_id where s.market_id=2 and s.ticker='{ticker}') "
                          f"select min(close_price), max(close_price), min(date), max(date), count(*) from r where rn<=252"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    lo, hi, d0, d1, n = out.split("|")
    return {"low": float(lo), "high": float(hi), "from": d0, "to": d1, "n_days": int(n)}


def fy(ticker, fy_end):
    return json.loads((ROOT / "data" / "edgar" / f"{ticker}.json").read_text())["years"][fy_end]


def _oxford_join(items):
    items = list(items)
    if not items: return "no method"
    if len(items) == 1: return items[0]
    if len(items) == 2: return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def broadcom_vmware_precedent():
    """Broadcom / VMware: all-cash, $142.50/share, announced 2022-05-26. VMware's last full fiscal year before
    announcement (fiscal year ends late January) is FY ending 2022-01-28 — note its debt jumped to ~$12.7bn that
    year from a well-documented ~$11.5bn special dividend VMware funded with new debt ahead of the spin-off/deal,
    not organic leverage."""
    r = fy("VMW", "2022-01-28")
    offer_price = 142.50
    equity_value = offer_price * r["diluted_shares"]
    net_debt = r["debt_total"] - r["cash"]
    ev = equity_value + net_debt
    return {"acquirer": "Broadcom Inc.", "target": "VMware, Inc.", "date": "2022-05-26",
            "enterprise_value": ev, "ltm_revenue": r["revenue"], "ltm_ebitda": r["operating_income"] + r["da"], "ltm_ebit": r["operating_income"],
            "offer_price": offer_price, "_detail": {"fy": "2022-01-28", "equity_value": equity_value, "net_debt": net_debt, "diluted_shares": r["diluted_shares"],
                                                     "source": "offer price: publicly disclosed deal terms (all-cash); VMware revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K",
                                                     "note": "VMware's debt includes ~$11.5bn raised for a special dividend ahead of the deal, not organic leverage"}}


def ibm_redhat_precedent():
    """IBM / Red Hat: all-cash, $190.00/share, announced 2018-10-28. Red Hat's last full fiscal year before
    announcement (fiscal year ends late February) is FY ending 2018-02-28."""
    r = fy("RHT", "2018-02-28")
    offer_price = 190.00
    equity_value = offer_price * r["diluted_shares"]
    net_debt = (r.get("debt_total") or 0) - r["cash"]
    ev = equity_value + net_debt
    return {"acquirer": "International Business Machines Corp.", "target": "Red Hat, Inc.", "date": "2018-10-28",
            "enterprise_value": ev, "ltm_revenue": r["revenue"], "ltm_ebitda": r["operating_income"] + r["da"], "ltm_ebit": r["operating_income"],
            "offer_price": offer_price, "_detail": {"fy": "2018-02-28", "equity_value": equity_value, "net_debt": net_debt, "diluted_shares": r["diluted_shares"],
                                                     "source": "offer price: publicly disclosed deal terms (all-cash); Red Hat revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K"}}


def csco_dcf_scenario(name, growth, margin_target, da_pct, capex_pct, discount_rate, current_price):
    r = fy(TARGET, "2026-07-25")
    rev0 = r["revenue"] / 1e6; margin0 = r["operating_income"] / r["revenue"]; nwc0_pct = (r["current_assets"] - r["current_liabilities"]) / r["revenue"]
    n = 5
    rev = [rev0]
    for _ in range(n): rev.append(rev[-1] * (1 + growth))
    margins = [margin0 + (margin_target - margin0) * t / n for t in range(1, n + 1)]
    ebit = [rev[t] * margins[t - 1] for t in range(1, n + 1)]
    da = [rev[t] * da_pct for t in range(1, n + 1)]
    capex = [rev[t] * capex_pct for t in range(1, n + 1)]
    change_nwc = [nwc0_pct * (rev[t] - rev[t - 1]) for t in range(1, n + 1)]
    inp = dcf.DCFInputs(ebit=ebit, da=da, change_nwc=change_nwc, capex=capex, tax_rate=0.1713, discount_rate=discount_rate,
                        perpetual_growth=0.025, terminal_method="perpetuity", transaction_date="2026-07-25", fiscal_year_end="2027-07-25",
                        current_price=current_price, shares_outstanding=r["diluted_shares"] / 1e6, debt=r["debt_total"] / 1e6, cash=(r["cash"] + r.get("short_term_investments", 0)) / 1e6)
    res = dcf.run(inp)
    sens = dcf.sensitivity(inp, [discount_rate - 0.005, discount_rate, discount_rate + 0.005], [0.02, 0.025, 0.03])
    flat = [v for row in sens["table"] for v in row]
    return {"name": name, "base_value_per_share": res["equity_value_per_share"], "low": min(flat), "high": max(flat),
            "assumptions": {"revenue_growth": growth, "ebit_margin_target_year5": margin_target, "da_pct_revenue": da_pct, "capex_pct_revenue": capex_pct, "discount_rate": discount_rate, "terminal_growth": 0.025}}


def build_normalized(px):
    """Rebuilds the football field with finmodel.sectors, but — unlike the steel and oil & gas scripts — checks
    trend_diagnostics() on every peer and the target BEFORE normalizing, and skips normalization for any company
    with a strong secular trend (Salesforce) rather than silently misapplying a trailing median to it. Shows both
    the 'correct' normalized run and, separately, what a naive normalization (ignoring the trend check) would have
    done to Salesforce's own multiple, as a worked cautionary example."""
    trend_flags = {}
    peers = []
    for t in CORE:
        hist = json.loads((ROOT / "data" / "edgar" / f"{t}.json").read_text())["years"]
        r = fy(t, sorted(hist)[-1])
        trend = sectors.trend_diagnostics(hist, periods=8)
        trend_flags[t] = trend
        if trend.get("trend_strength") == "strong":
            m = {"revenue": r["revenue"], "ebitda": r["operating_income"] + r["da"], "ebit": r["operating_income"], "net_income": r["net_income"]}   # raw LTM: trend-aware guard skips normalization
        else:
            m = sectors.normalized_comps_metrics(hist, sector="software")
        peers.append(comps.Peer(t, px[t], r["diluted_shares"], cash=r["cash"] + r.get("short_term_investments", 0), debt=r["debt_total"], nci=r.get("nci", 0), metrics=m, ticker=t))
    trading = comps.spread(peers)

    # naive comparison: what normalizing Salesforce WITHOUT the trend guard would have done
    crm_hist = json.loads((ROOT / "data" / "edgar" / "CRM.json").read_text())["years"]
    crm_naive = sectors.normalized_comps_metrics(crm_hist, sector="software")
    crm_raw_ebitda = fy("CRM", sorted(crm_hist)[-1])["operating_income"] + fy("CRM", sorted(crm_hist)[-1])["da"]

    vmw_hist = json.loads((ROOT / "data" / "edgar" / "VMW.json").read_text())["years"]
    rht_hist = json.loads((ROOT / "data" / "edgar" / "RHT.json").read_text())["years"]
    vmw_n = sectors.normalize_metric(vmw_hist, "operating_income", periods=8, method="median", as_of="2022-01-28")["value"]
    vmw_da_n = sectors.normalize_metric(vmw_hist, "da", periods=8, method="median", as_of="2022-01-28")["value"]
    rht_n = sectors.normalize_metric(rht_hist, "operating_income", periods=8, method="median", as_of="2018-02-28")["value"]
    rht_da_n = sectors.normalize_metric(rht_hist, "da", periods=8, method="median", as_of="2018-02-28")["value"]
    v_deal, r_deal = broadcom_vmware_precedent(), ibm_redhat_precedent()
    from finmodel.comps import Deal
    deals = [Deal(v_deal["acquirer"], v_deal["target"], v_deal["date"], v_deal["enterprise_value"], ltm_revenue=v_deal["ltm_revenue"], ltm_ebitda=vmw_n + vmw_da_n, ltm_ebit=vmw_n),
             Deal(r_deal["acquirer"], r_deal["target"], r_deal["date"], r_deal["enterprise_value"], ltm_revenue=r_deal["ltm_revenue"], ltm_ebitda=rht_n + rht_da_n, ltm_ebit=rht_n)]
    precedents = comps.precedents(deals)

    csco_hist = json.loads((ROOT / "data" / "edgar" / "CSCO.json").read_text())["years"]
    csco_trend = sectors.trend_diagnostics(csco_hist, periods=8)
    tr = fy(TARGET, sorted(csco_hist)[-1])
    tm = sectors.normalized_comps_metrics(csco_hist, sector="software")   # Cisco's trend, while real, is not "strong enough by the same test to skip" — see doc discussion
    target = comps.Target("Cisco Systems, Inc.", px[TARGET], tr["diluted_shares"], metrics=tm,
                          bridge={"cash": tr["cash"] + tr.get("short_term_investments", 0), "debt": -tr["debt_total"], "nci": -tr.get("nci", 0)})

    s = sectors.dcf_scenarios_from_history(csco_hist, periods=8)
    base = csco_dcf_scenario("DCF - base case (sector-normalized: trailing median margin)", growth=0.03, margin_target=s["base_margin"], da_pct=0.011, capex_pct=0.015, discount_rate=0.0868, current_price=px[TARGET])
    blue = csco_dcf_scenario("DCF - blue sky (sector-normalized: trailing peak margin)", growth=0.06, margin_target=s["blue_sky_margin"], da_pct=0.011, capex_pct=0.015, discount_rate=0.0868, current_price=px[TARGET])
    wk52 = week52(TARGET)

    ff = comps.football_field(target, {"Trading comps": trading, "Precedent transactions": precedents},
                              extra={base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"]), "52-week range": (wk52["low"], wk52["high"])},
                              stat_low="p25", stat_high="p75")
    return {"trading_comps": trading, "precedents": precedents, "dcf_base": base, "dcf_blue_sky": blue, "dcf_scenarios_from_history": s,
            "football_field": ff, "trend_flags": trend_flags, "csco_trend": csco_trend,
            "crm_naive_ebitda": crm_naive["ebitda"], "crm_raw_ebitda": crm_raw_ebitda}


def run():
    px = prices(CORE + [TARGET])
    peers = []
    for t in CORE:
        r = fy(t, sorted(json.loads((ROOT / "data" / "edgar" / f"{t}.json").read_text())["years"])[-1])
        m = {"revenue": r["revenue"], "ebitda": r["operating_income"] + r["da"], "ebit": r["operating_income"], "net_income": r["net_income"]}
        peers.append(comps.Peer(t, px[t], r["diluted_shares"], cash=r["cash"] + r.get("short_term_investments", 0), debt=r["debt_total"], nci=r.get("nci", 0), metrics=m, ticker=t))
    trading = comps.spread(peers)

    v_deal, r_deal = broadcom_vmware_precedent(), ibm_redhat_precedent()
    from finmodel.comps import Deal
    deals = [Deal(v_deal["acquirer"], v_deal["target"], v_deal["date"], v_deal["enterprise_value"], ltm_revenue=v_deal["ltm_revenue"], ltm_ebitda=v_deal["ltm_ebitda"], ltm_ebit=v_deal["ltm_ebit"]),
             Deal(r_deal["acquirer"], r_deal["target"], r_deal["date"], r_deal["enterprise_value"], ltm_revenue=r_deal["ltm_revenue"], ltm_ebitda=r_deal["ltm_ebitda"], ltm_ebit=r_deal["ltm_ebit"])]
    precedents = comps.precedents(deals)

    tr = fy(TARGET, "2026-07-25")
    target = comps.Target("Cisco Systems, Inc.", px[TARGET], tr["diluted_shares"], metrics={"revenue": tr["revenue"], "ebitda": tr["operating_income"] + tr["da"], "ebit": tr["operating_income"], "net_income": tr["net_income"]},
                          bridge={"cash": tr["cash"] + tr.get("short_term_investments", 0), "debt": -tr["debt_total"], "nci": -tr.get("nci", 0)})

    base = csco_dcf_scenario("DCF - base case (margin near recent 3yr average)", growth=0.03, margin_target=0.23, da_pct=0.011, capex_pct=0.015, discount_rate=0.0868, current_price=px[TARGET])
    blue = csco_dcf_scenario("DCF - blue sky (margin recovers toward FY2020-22 level)", growth=0.06, margin_target=0.27, da_pct=0.011, capex_pct=0.015, discount_rate=0.0868, current_price=px[TARGET])
    wk52 = week52(TARGET)

    ff = comps.football_field(target, {"Trading comps": trading, "Precedent transactions": precedents},
                              extra={base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"]), "52-week range": (wk52["low"], wk52["high"])},
                              stat_low="p25", stat_high="p75")

    normalized = build_normalized(px)

    out = {"price": px[TARGET], "price_date": PRICE_DATE, "trading_comps": trading, "precedents": precedents,
           "vmw_detail": v_deal, "rht_detail": r_deal, "dcf_base": base, "dcf_blue_sky": blue, "week52": wk52, "football_field": ff,
           "csco_fy2026_margin": tr["operating_income"] / tr["revenue"], "normalized": normalized}
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "comps_football_field_csco.json").write_text(json.dumps(out, indent=1, default=str))
    charts.report_for("comps", {"comps": trading, "precedents": precedents, "football_field": ff}, ROOT / "out" / "charts_football_field_csco.html", title="Cisco — CFI football-field template on real data")

    md = write_doc(out)
    (ROOT / "docs" / "FOOTBALL_FIELD_CSCO.md").write_text(md)
    print(f"CSCO price {px[TARGET]:.2f} ({PRICE_DATE})")
    for it in ff["items"]:
        print(f"  {it['method']:55} {it['low']:8.2f} - {it['high']:8.2f}")


def write_doc(out):
    px = out["price"]; ff = out["football_field"]
    md = ["# Third real-company check: the CFI football-field template against Cisco (CSCO)", "",
          "Same method as `docs/FOOTBALL_FIELD_STLD.md` (steel) and `docs/FOOTBALL_FIELD_CVX.md` (oil & gas), applied "
          "to a third, structurally different sector: enterprise technology / software, expected — and, per "
          "`finmodel.sectors`, confirmed — to show far lower earnings cyclicality than either commodity sector. Real "
          "peer trading comps, two real all-cash precedent deals, two DCF scenarios grounded in Cisco's own margin "
          f"history, and Cisco's real 52-week range — compared to Cisco's actual price of **${px:.2f}** (warehouse "
          f"close, {out['price_date']}).", "",
          "## Football field", "", "| Method | Low | High | Current price inside range? |", "|---|---|---|---|"]
    brackets, price_above, price_below = [], [], []
    for it in ff["items"]:
        if it["low"] <= px <= it["high"]:
            inside = "yes"; brackets.append(it["method"])
        elif px > it["high"]:
            inside = "price is above this range"; price_above.append(it)
        else:
            inside = "price is below this range"; price_below.append(it)
        md.append(f"| {it['method']} | {it['low']:.2f} | {it['high']:.2f} | {inside} |")
    md += ["", f"{_oxford_join(brackets)} bracket{'s' if len(brackets) == 1 else ''} the actual price."]
    if price_above:
        md.append("Ranges the price sits **above**: " + ", ".join(f"{it['method']} (high {it['high']:.2f})" for it in price_above) + ".")
    if price_below:
        md.append("Ranges the price sits **below**: " + ", ".join(f"{it['method']} (low {it['low']:.2f})" for it in price_below) + ".")
    md += ["", "## 1. Trading comps (real: SEC EDGAR fundamentals + market_data warehouse prices)", "",
           "Peers: Microsoft, Oracle, IBM, Adobe, Salesforce — latest-fiscal-year fundamentals, "
           f"{out['price_date']} closing prices.", "",
           "| Ticker | Price | EV/Revenue | EV/EBITDA | EV/EBIT | P/E |", "|---|---|---|---|---|---|"]
    for p in out["trading_comps"]["peers"]:
        f = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
        md.append(f"| {p['ticker']} | {p['price']:.2f} | {f(p['multiples']['EV / Revenue LTM'])} | {f(p['multiples']['EV / EBITDA LTM'])} | {f(p['multiples']['EV / EBIT LTM'])} | {f(p['multiples']['P / E LTM'])} |")
    md += ["", "| Multiple | 25th | Median | 75th |", "|---|---|---|---|"]
    for label in ("EV / Revenue LTM", "EV / EBITDA LTM", "EV / EBIT LTM"):
        s = out["trading_comps"]["summary"][label]
        md.append(f"| {label} | {s['p25']:.2f}x | {s['median']:.2f}x | {s['p75']:.2f}x |")
    md += ["", "Note the absolute level of these multiples versus the earlier checks: even the *25th percentile* EV/EBITDA "
           "here exceeds the *75th percentile* for steel or oil & gas — enterprise software commands structurally richer "
           "multiples because of higher margins, recurring revenue and lower reinvestment needs, not because these five "
           "companies are in the same cyclical position steel or oil & gas producers were.", ""]
    md += ["## 2. Precedent transactions (real, verifiable, all-cash deals)", ""]
    for key, title in (("vmw_detail", "Broadcom / VMware"), ("rht_detail", "IBM / Red Hat")):
        d = out[key]; det = d["_detail"]
        md += [f"### {title} — announced {d['date']}", "",
               f"All-cash: offer **${d['offer_price']:.2f}**/share. Enterprise value **${d['enterprise_value']/1e6:,.0f}M** = "
               f"equity value ${det['equity_value']/1e6:,.0f}M ({det['diluted_shares']/1e6:.1f}M target diluted shares) + net debt "
               f"${det['net_debt']/1e6:,.0f}M, target fundamentals from its FY{det['fy'][:4]} 10-K (SEC EDGAR).", "",
               f"LTM revenue ${d['ltm_revenue']/1e6:,.0f}M, LTM EBITDA ${d['ltm_ebitda']/1e6:,.0f}M, LTM EBIT ${d['ltm_ebit']/1e6:,.0f}M → "
               f"**EV/Revenue {d['enterprise_value']/d['ltm_revenue']:.2f}x, EV/EBITDA {d['enterprise_value']/d['ltm_ebitda']:.2f}x, "
               f"EV/EBIT {d['enterprise_value']/d['ltm_ebit']:.2f}x**.", "",
               f"*Source: {det['source']}.*" + (f" *Note: {det['note']}.*" if "note" in det else ""), ""]
    md += ["Unlike the steel and oil & gas precedents, both deals here are simple all-cash offers, so no acquirer share "
           "price or exchange ratio was needed to compute the offer value. Both multiples are far richer than the steel "
           "or oil & gas precedents (Red Hat alone traded at ~58x EBITDA) — again a real structural sector difference, "
           "not a cyclical distortion.", ""]
    md += ["## 3. DCF (illustrative scenarios built from Cisco's own historical range, not analyst consensus)", "",
           "Discount rate 8.68% for both scenarios (`finmodel wacc examples/wacc_csco.json`); terminal growth 2.5%, "
           "perpetuity method. Cisco's own EBIT margin ranged 20.8%-27.6% over FY2020-2026 — far tighter than steel's "
           "8.1%-23.4% or Chevron's -7.1% to +20.4%, consistent with the 'low cyclicality' `finmodel.sectors` "
           "classification. The low-high range is a small discount-rate (±0.5pt) x terminal-growth (2.0%/2.5%/3.0%) "
           "sensitivity grid.", ""]
    for key in ("dcf_base", "dcf_blue_sky"):
        d = out[key]; a = d["assumptions"]
        md += [f"**{d['name']}**: revenue grows {a['revenue_growth']*100:.0f}%/yr, EBIT margin reaches {a['ebit_margin_target_year5']*100:.1f}% by year 5 "
               f"(FY2026 was {out['csco_fy2026_margin']*100:.1f}%) → implied share price **{d['base_value_per_share']:.2f}** "
               f"(range {d['low']:.2f} – {d['high']:.2f} across the sensitivity grid).", ""]
    md += ["## 4. 52-week trading range (real, market_data warehouse)", "",
           f"${out['week52']['low']:.2f} – ${out['week52']['high']:.2f} ({out['week52']['from']} to {out['week52']['to']}, {out['week52']['n_days']} trading days).", ""]
    md += ["## 5. Sector-tuned comparison, with a trend-detection guard this time", "",
           "The same `finmodel.sectors` treatment as the first two checks, but this one adds a step the earlier scripts "
           "didn't need: before normalizing each peer's EBIT/EBITDA to a trailing-history median, this script runs "
           "`trend_diagnostics()` on it first. A commodity producer's margin history is mean-reverting, so a trailing "
           "median is a sensible baseline; several software peers here are on genuine secular trends where it is not.", ""]
    tf = out["normalized"]["trend_flags"]
    md += ["| Peer | Trend | Direction | Correlation | Normalized this peer? |", "|---|---|---|---|---|"]
    for t, tr in tf.items():
        skip = tr.get("trend_strength") == "strong"
        md.append(f"| {t} | {tr.get('trend_strength', 'n/a')} | {tr.get('direction', 'n/a')} | {tr.get('correlation', float('nan')):.2f} | {'no — trend guard skipped it' if skip else 'yes'} |")
    ct = out["normalized"]["csco_trend"]
    md += ["", f"Cisco's own margin also shows a real trend ({ct['trend_strength']}, {ct['direction']}, r={ct['correlation']:.2f}) despite its tight "
           f"absolute range — tight range and 'no trend' are different properties (`SECTOR_PROFILES['software']`'s note "
           f"says so explicitly). This script normalizes Cisco's own metrics anyway, on the judgement that a single "
           f"gentle drift with a partial recent reversal is a materially different situation from Salesforce's clean, "
           f"large, one-directional ramp — but a stricter guard could reasonably skip Cisco too; this is a judgement "
           f"call the tool surfaces rather than hides, not one it resolves for you.", ""]
    md += ["**What normalizing Salesforce anyway would have done, for comparison**: its own trailing-median EBITDA is "
           f"${out['normalized']['crm_naive_ebitda']/1e6:,.0f}M against a real LTM EBITDA of "
           f"${out['normalized']['crm_raw_ebitda']/1e6:,.0f}M — normalizing would have replaced Salesforce's genuine, "
           "sustainable, current profitability with a stale average from its intentionally-unprofitable growth years, "
           "understating its multiple's denominator and making Salesforce look far more expensive than it now is. This "
           "script's trend guard kept Salesforce at its raw LTM figure specifically to avoid that error.", ""]
    norm = out["normalized"]; nff = norm["football_field"]
    md += ["| Method | Raw LTM range | Sector-normalized (trend-guarded) range | Normalized brackets price? |", "|---|---|---|---|"]
    n_brackets = []
    for it, nit in zip(ff["items"], nff["items"]):
        inside = nit["low"] <= px <= nit["high"]
        if inside: n_brackets.append(nit["method"])
        note = " (unchanged — real price history)" if nit["method"] == "52-week range" else ""
        md.append(f"| {it['method'].split(' (')[0]} | {it['low']:.2f} – {it['high']:.2f} | {nit['low']:.2f} – {nit['high']:.2f}{note} | {'yes' if inside else 'no'} |")
    s = norm["dcf_scenarios_from_history"]
    md += ["", f"Data-driven margin targets from Cisco's own trailing 8 fiscal years (`finmodel cycle`): bear {s['bear_margin']:.1%}, "
           f"base (trailing median) {s['base_margin']:.1%}, blue sky (trailing peak) {s['blue_sky_margin']:.1%} — close to the "
           f"hand-picked 23.0%/27.0% used in the raw run above, since Cisco's tight range leaves little room for a hand-picked "
           f"guess to be far off.", ""]
    if _oxford_join(n_brackets) != _oxford_join(brackets):
        md.append(f"Normalizing changes which methods bracket the price: raw run → {_oxford_join(brackets)}; normalized run → {_oxford_join(n_brackets)}.")
    else:
        md.append(f"Normalizing does not change which methods bracket the price here (still {_oxford_join(n_brackets)}) — "
                  "consistent with a low-cyclicality sector where there was little real distortion to correct in the first place.")
    md += ["", "## Method note", "",
           "Same standard as the first two checks: every revenue/EBIT/D&A/debt/cash figure is from an SEC 10-K (via "
           "`finmodel.edgar`), every price is a live database query against `market_data`, the two deals' offer prices "
           "and announcement dates are public record, and the two DCF scenarios are explicitly labelled illustrative "
           "assumptions grounded in Cisco's own historical margin range, not analyst consensus. Target-side deal "
           "premiums are omitted for the same reason as before: both VMware and Red Hat are delisted and absent from "
           "the warehouse.", "",
           "Regenerate with `python scripts/football_field_csco.py`; chart at `out/charts_football_field_csco.html`."]
    return "\n".join(md)


if __name__ == "__main__":
    run()
