"""Ninth real-company check of the CFI 'Comps, Precedents, Football Field' template — regulated electric & gas
utilities, via Duke Energy (DUK). Deliberately the LOW-cyclicality bookend to the eight prior checks (steel, oil &
gas, software, banking, REIT, airline, insurance, semiconductor): a regulated utility's cost-of-service revenue is
the lowest-systematic-risk cash flow this toolkit has profiled, and — unlike banking/REIT/insurance — the STANDARD
EV-based comps framework (EV/Revenue, EV/EBITDA, EV/EBIT, P/E) just works, no equity-only substitute needed.

  The real, sector-defining finding: a standard unlevered DCF technically runs, but DUK's own real FY2019-2025
  unlevered free cash flow (before working capital) was negative in 2 of 7 years and never exceeded ~$1.3B,
  because real capex ran 39.6%-45.7% of revenue every single year — a persistent ~1.8-2.1x real D&A, not a
  temporary supercycle like the semiconductor check's (which tapered capex back down over the forecast). For a
  utility the opposite fix applies: elevated capex IS the steady state (rate-base growth is the entire regulated-
  return mechanism), so this DCF holds the capex/revenue ratio flat rather than tapering it.

  A second, sharper consequence of that thin UFCF, verified by actually running the numbers: with terminal value
  carrying the large majority of enterprise value, the DCF result is extremely sensitive to the perpetuity growth
  assumption — a generic, "mature company" 2.5% terminal growth rate (this toolkit's usual default) produces a
  NONSENSICAL NEGATIVE implied equity value for a real, solvent, investment-grade, dividend-paying company,
  because it silently assumes DUK's real, currently-disclosed $103B/2026-2030 capital plan (which DUK itself
  guides to 5%-7% long-run EPS growth and 9.6% rate-base growth) stops mattering the moment the 5-year forecast
  ends. The fix: anchor terminal growth to the company's own real, disclosed long-run guidance (moderated to stay
  safely below WACC, since a Gordon-growth perpetuity is mathematically undefined once growth reaches the
  discount rate) rather than a generic assumption — kept here as an explicit "bear" scenario alongside the fix,
  not silently replaced, since the failure mode itself is the finding.

  Two further real findings, both real and verified: (1) DUK's real FY2025 interest coverage (2.37x) maps to a
  synthetic 'BB+' junk rating on finmodel.wacc's Damodaran coverage table, but DUK's REAL rating is investment-
  grade (BBB/S&P, Baa2/Moody's, Feb 2026) — regulated utilities are allowed structurally thin coverage because
  rate-of-return regulation makes debt-service recovery through rates close to guaranteed. (2) peer Xcel Energy's
  (XEL) real ROE held a tight 10.1%-10.4% band for seven straight years before dropping to 8.5% in FY2025 —
  `trend_diagnostics()` correctly flags a 'declining' trend, but the real cause is a ~$1.18B forward equity
  offering (closed Nov 2024) plus a $4.3B equity program funding XEL's capital plan, mechanically diluting ROE in
  the issuance year. See finmodel.sectors.SECTOR_PROFILES['utility'] for the full write-up, including two further
  real EDGAR-extraction findings (a new revenue-tag fallback, and a stale SEC companyfacts entityName).

  What this script does — reusing existing generic engines, no new comps/valuation code:
  Trading comps    — EV/Revenue, EV/EBITDA, EV/EBIT, P/E (finmodel.comps' own DEFAULT_MULTIPLES — no override
                     needed, unlike every financial-services-like sector this toolkit has checked) for Southern
                     Company, American Electric Power, Dominion Energy, Exelon, Xcel Energy.
  Precedent deals  — two real, verifiable, all-CASH regulated-utility mergers: Exelon / Pepco Holdings
                     (2014-04-30, $27.25/share) and Southern Company / AGL Resources (2015-08-24, $66.00/share).
  DCF              — unlevered DCF via finmodel.dcf, WACC from `finmodel wacc examples/wacc_duk.json` (6.19%),
                     capex/revenue held at DUK's own real FY2025 level across the forecast (not tapered).
  52-week range    — the real trailing 252-trading-day high/low from the warehouse.

Run: python scripts/football_field_duk.py → docs/FOOTBALL_FIELD_DUK.md, out/comps_football_field_duk.json,
out/charts_football_field_duk.html"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finmodel import comps, charts, dcf, sectors  # noqa: E402
from finmodel.comps import Deal  # noqa: E402
from finmodel.fin import xnpv, to_date  # noqa: E402

CORE = ["SO", "AEP", "D", "EXC", "XEL"]
TARGET = "DUK"
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


def utility_metrics(r):
    return {"revenue": r["revenue"], "ebitda": r["operating_income"] + r["da"], "ebit": r["operating_income"], "net_income": r["net_income"]}


def pom_precedent():
    """Exelon / Pepco Holdings: all-cash, $27.25/share, announced 2014-04-30 (Exelon's own 8-K, exhibit 99.1
    press release). Pepco Holdings' last full fiscal year before announcement: FY2013 — a real net LOSS year
    (net income -$212M, EPS -$0.86, both confirmed against SEC's live XBRL data), so its P/E is correctly NM
    below, not a data error; EV/EBITDA and EV/EBIT are unaffected since operating income stayed positive."""
    r = fy("POM", "2013-12-31")
    price = 27.25
    equity_value = price * r["diluted_shares"]
    net_debt = r["debt_total"] - r["cash"]
    ev = equity_value + net_debt
    m = utility_metrics(r)
    return {"acquirer": "Exelon Corporation", "target": "Pepco Holdings, Inc.", "date": "2014-04-30",
            "enterprise_value": ev, "ltm_revenue": m["revenue"], "ltm_ebitda": m["ebitda"], "ltm_ebit": m["ebit"], "ltm_net_income": m["net_income"],
            "offer_price": price, "_detail": {"fy": "2013-12-31", "equity_value": equity_value, "net_debt": net_debt, "diluted_shares": r["diluted_shares"],
                                               "source": "$27.25/share, all cash: Exelon 8-K exhibit 99.1; Pepco Holdings fundamentals: SEC EDGAR 10-K"}}


def agl_precedent():
    """Southern Company / AGL Resources: all-cash, $66.00/share, announced 2015-08-24 (Southern's own 8-K,
    exhibit 99.1 press release). AGL Resources' last full fiscal year before announcement: FY2014. AGL Resources
    was renamed 'Southern Co Gas' on the real 2016-07-11 merger-close date and still files under the same CIK
    (1004155) — see finmodel.sectors.SECTOR_PROFILES['utility'] for a real, verified SEC companyfacts API quirk
    (a stale entityName) surfaced while pulling this exact filer's data."""
    r = fy("GAS", "2014-12-31")
    price = 66.00
    equity_value = price * r["diluted_shares"]
    net_debt = r["debt_total"] - r["cash"]
    ev = equity_value + net_debt
    m = utility_metrics(r)
    return {"acquirer": "Southern Company", "target": "AGL Resources Inc.", "date": "2015-08-24",
            "enterprise_value": ev, "ltm_revenue": m["revenue"], "ltm_ebitda": m["ebitda"], "ltm_ebit": m["ebit"], "ltm_net_income": m["net_income"],
            "offer_price": price, "_detail": {"fy": "2014-12-31", "equity_value": equity_value, "net_debt": net_debt, "diluted_shares": r["diluted_shares"],
                                               "source": "$66.00/share, all cash: Southern Company 8-K exhibit 99.1; AGL Resources fundamentals: SEC EDGAR 10-K"}}


def duk_dcf_scenario(name, growth, margin_target, discount_rate, current_price, perpetual_growth):
    """Unlike the semiconductor check's tapered capex, this scenario holds DUK's own real FY2025 capex/revenue
    ratio (44.2%) FLAT across the forecast — elevated capex is a regulated utility's steady state (rate-base
    growth IS the return mechanism), not a temporary peak to fade. `perpetual_growth` is deliberately a parameter,
    not hardcoded: with UFCF this thin, terminal value carries the large majority of enterprise value (see
    `pv_terminal_value_pct` below), so the result is extremely sensitive to it — the real, headline finding this
    check is built around (see the module docstring and docs/FOOTBALL_FIELD_DUK.md §4)."""
    r = fy(TARGET, "2025-12-31")
    rev0 = r["revenue"] / 1e6; margin0 = r["operating_income"] / r["revenue"]; nwc0_pct = (r["current_assets"] - r["current_liabilities"]) / r["revenue"]
    capex0_pct = r["capex"] / r["revenue"]
    n = 5
    rev = [rev0]
    for _ in range(n): rev.append(rev[-1] * (1 + growth))
    margins = [margin0 + (margin_target - margin0) * t / n for t in range(1, n + 1)]
    ebit = [rev[t] * margins[t - 1] for t in range(1, n + 1)]
    da = [rev[t] * (r["da"] / r["revenue"]) for t in range(1, n + 1)]
    capex = [rev[t] * capex0_pct for t in range(1, n + 1)]
    change_nwc = [nwc0_pct * (rev[t] - rev[t - 1]) for t in range(1, n + 1)]
    inp = dcf.DCFInputs(ebit=ebit, da=da, change_nwc=change_nwc, capex=capex, tax_rate=0.1124, discount_rate=discount_rate,
                        perpetual_growth=perpetual_growth, terminal_method="perpetuity", transaction_date="2025-12-31", fiscal_year_end="2026-12-31",
                        current_price=current_price, shares_outstanding=r["diluted_shares"] / 1e6, debt=r["debt_total"] / 1e6, cash=r["cash"] / 1e6)
    res = dcf.run(inp)
    # a Gordon-growth terminal value's (r - g) denominator is far more fragile here than for a normal-WACC
    # sector, since DUK's own WACC (6.19%) is already low — a wide sensitivity band can push g within a hair of
    # r and blow the terminal value up to a non-informative multiple; keep the band tight enough (+/-0.25pp on
    # the discount rate, +/-0.5pp on perpetual growth) to stay a real sensitivity check, not a degenerate one.
    lo_g, hi_g = max(0.005, perpetual_growth - 0.005), min(discount_rate - 0.015, perpetual_growth + 0.005)
    sens = dcf.sensitivity(inp, [discount_rate - 0.0025, discount_rate, discount_rate + 0.0025], [lo_g, perpetual_growth, hi_g])
    flat = [v for row in sens["table"] for v in row]
    pv_explicit = xnpv(discount_rate, [0.0] + [res["ufcf"][t] * res["year_fraction"][t] for t in range(n)], [to_date(d) for d in res["dates"]])
    pv_tv_pct = 1 - pv_explicit / res["enterprise_value"]
    return {"name": name, "base_value_per_share": res["equity_value_per_share"], "low": min(flat), "high": max(flat),
            "pv_terminal_value_pct": pv_tv_pct, "ufcf": res["ufcf"],
            "assumptions": {"revenue_growth": growth, "ebit_margin_target_year5": margin_target, "discount_rate": discount_rate,
                            "capex_pct_of_revenue": capex0_pct, "perpetual_growth": perpetual_growth}}


def run():
    px = prices(CORE + [TARGET])
    peers = []
    for t in CORE:
        r = fy(t, "2025-12-31")
        net_debt = r["debt_total"] - r["cash"]
        peers.append(comps.Peer(t, px[t], r["diluted_shares"], net_debt=net_debt, metrics=utility_metrics(r), ticker=t))
    trading = comps.spread(peers)

    pom, agl = pom_precedent(), agl_precedent()
    deals = [Deal(pom["acquirer"], pom["target"], pom["date"], pom["enterprise_value"], ltm_revenue=pom["ltm_revenue"], ltm_ebitda=pom["ltm_ebitda"], ltm_ebit=pom["ltm_ebit"]),
             Deal(agl["acquirer"], agl["target"], agl["date"], agl["enterprise_value"], ltm_revenue=agl["ltm_revenue"], ltm_ebitda=agl["ltm_ebitda"], ltm_ebit=agl["ltm_ebit"])]
    precedents = comps.precedents(deals)

    tr = fy(TARGET, "2025-12-31")
    net_debt_target = tr["debt_total"] - tr["cash"]
    target = comps.Target("Duke Energy Corporation", px[TARGET], tr["diluted_shares"], metrics=utility_metrics(tr), net_debt=net_debt_target)

    coe_wacc = 0.0619  # finmodel wacc examples/wacc_duk.json
    duk_hist = json.loads((ROOT / "data" / "edgar" / "DUK.json").read_text())["years"]
    margin_2025 = tr["operating_income"] / tr["revenue"]
    margin_3yr = sum(duk_hist[f"{y}-12-31"]["operating_income"] / duk_hist[f"{y}-12-31"]["revenue"] for y in (2023, 2024, 2025)) / 3
    margin_8yr_median_years = sorted(duk_hist)[-8:]
    import statistics as _st
    margin_8yr_median = _st.median(duk_hist[y]["operating_income"] / duk_hist[y]["revenue"] for y in margin_8yr_median_years if duk_hist[y].get("revenue"))

    bear = duk_dcf_scenario("DCF - bear (generic 2.5% terminal growth, revert to trailing 8yr median margin)", growth=0.03, margin_target=margin_8yr_median, discount_rate=coe_wacc, current_price=px[TARGET], perpetual_growth=0.025)
    base = duk_dcf_scenario("DCF - base (terminal growth anchored to DUK's own real 5-7% EPS guidance)", growth=0.06, margin_target=margin_3yr, discount_rate=coe_wacc, current_price=px[TARGET], perpetual_growth=0.045)
    blue = duk_dcf_scenario("DCF - blue sky (top of DUK's own real guidance range, FY2025 actual margin sustained)", growth=0.07, margin_target=margin_2025, discount_rate=coe_wacc, current_price=px[TARGET], perpetual_growth=0.05)
    wk52 = week52(TARGET)

    ff = comps.football_field(target, {"Trading comps": trading, "Precedent transactions": precedents},
                              extra={base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"]), "52-week range": (wk52["low"], wk52["high"])},
                              stat_low="p25", stat_high="p75")

    normalized = build_normalized(duk_hist)
    xel_normalized = build_xel_normalized()
    ufcf_history = build_ufcf_history(duk_hist)
    rating = build_rating_check()

    out = {"price": px[TARGET], "price_date": PRICE_DATE, "trading_comps": trading, "precedents": precedents,
           "pom_detail": pom, "agl_detail": agl, "dcf_bear": bear, "dcf_base": base, "dcf_blue_sky": blue, "week52": wk52, "football_field": ff,
           "margin_2025": margin_2025, "margin_3yr": margin_3yr, "margin_8yr_median": margin_8yr_median,
           "normalized": normalized, "xel_normalized": xel_normalized, "ufcf_history": ufcf_history, "rating": rating}
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "comps_football_field_duk.json").write_text(json.dumps(out, indent=1, default=str))
    charts.report_for("comps", {"comps": trading, "precedents": precedents, "football_field": ff}, ROOT / "out" / "charts_football_field_duk.html", title="Duke Energy — regulated-utility football field on real data")

    md = write_doc(out)
    (ROOT / "docs" / "FOOTBALL_FIELD_DUK.md").write_text(md)
    print(f"DUK price {px[TARGET]:.2f} ({PRICE_DATE})")
    for it in ff["items"]:
        print(f"  {it['method']:60} {it['low']:8.2f} - {it['high']:8.2f}")


def build_normalized(duk_hist):
    diag = sectors.cycle_diagnostics(duk_hist, field="operating_income", revenue_field="revenue", periods=8, sector="utility")
    trend = sectors.trend_diagnostics(duk_hist, field="operating_income", revenue_field="revenue", periods=8)
    return {"cycle_diagnostics": diag, "trend_diagnostics": trend}


def build_xel_normalized():
    xel_hist = json.loads((ROOT / "data" / "edgar" / "XEL.json").read_text())["years"]
    diag = sectors.cycle_diagnostics(xel_hist, field="net_income", revenue_field="equity", periods=8, sector="utility")
    trend = sectors.trend_diagnostics(xel_hist, field="net_income", revenue_field="equity", periods=8)
    return {"cycle_diagnostics": diag, "trend_diagnostics": trend}


def build_ufcf_history(duk_hist):
    """Real DUK UFCF (before working capital) FY2019-2025, using each year's own real effective tax rate — the
    real, sector-defining finding this check is built around (see the module docstring)."""
    rows = []
    for y in sorted(duk_hist)[-7:]:
        r = duk_hist[y]
        if not r.get("revenue") or not r.get("capex"):
            continue
        eff_tax = r["tax"] / r["pretax_income"] if r.get("pretax_income") else 0.21
        nopat = r["operating_income"] * (1 - eff_tax)
        ufcf = nopat + r["da"] - r["capex"]
        rows.append({"fy": y, "capex_pct_revenue": r["capex"] / r["revenue"], "da_pct_revenue": r["da"] / r["revenue"], "ufcf": ufcf})
    return rows


def build_rating_check():
    from finmodel.wacc import synthetic_rating
    r = fy(TARGET, "2025-12-31")
    rat = synthetic_rating(r["operating_income"], r["interest_expense"], large_firm=True)
    return {"ebit": r["operating_income"], "interest_expense": r["interest_expense"], "synthetic": rat,
            "real_rating": {"sp": "BBB", "moodys": "Baa2", "outlook": "stable", "as_of": "2026-02", "source": "public credit-rating agency releases"}}


def write_doc(out):
    px = out["price"]; ff = out["football_field"]
    md = ["# Ninth real-company check: regulated utilities are the low-cyclicality bookend — and the standard framework mostly just works", "",
          "Same real-data method as the eight prior checks, applied to Duke Energy (DUK). Unlike banking, REITs, "
          "insurance and (partially) semiconductors, the STANDARD EV-based comps framework (EV/Revenue, "
          "EV/EBITDA, EV/EBIT, P/E) needs no override here — the interesting findings are elsewhere: a real "
          "secular margin trend, a persistently thin unlevered free cash flow that's a feature not a bug, a real "
          "credit-rating mismatch, and a real equity-dilution mechanism at a peer.", "",
          "## Football field", "", "| Method | Low | High | Current price inside range? |", "|---|---|---|---|"]
    def _oxford_join(items):
        items = list(items)
        if not items: return "no method"
        if len(items) == 1: return items[0]
        if len(items) == 2: return f"{items[0]} and {items[1]}"
        return ", ".join(items[:-1]) + f" and {items[-1]}"
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
    md += ["", "## 1. Trading comps (EV/Revenue, EV/EBITDA, EV/EBIT, P/E — the standard framework, no override needed)", "",
           "Peers: Southern Company, American Electric Power, Dominion Energy, Exelon, Xcel Energy — real large-cap "
           "US regulated electric/gas utilities.", "",
           "| Ticker | Price | EV/Revenue | EV/EBITDA | EV/EBIT | P/E |", "|---|---|---|---|---|---|"]
    for p in out["trading_comps"]["peers"]:
        f = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
        md.append(f"| {p['ticker']} | {p['price']:.2f} | {f(p['multiples']['EV / Revenue LTM'])} | {f(p['multiples']['EV / EBITDA LTM'])} | {f(p['multiples']['EV / EBIT LTM'])} | {f(p['multiples']['P / E LTM'])} |")
    md += ["", "| Multiple | 25th | Median | 75th |", "|---|---|---|---|"]
    for label in ("EV / Revenue LTM", "EV / EBITDA LTM", "EV / EBIT LTM", "P / E LTM"):
        s = out["trading_comps"]["summary"][label]
        md.append(f"| {label.replace(' LTM', '')} | {s['p25']:.2f}x | {s['median']:.2f}x | {s['p75']:.2f}x |")
    md += ["", "## 2. Precedent transactions (real, verifiable, all-cash regulated-utility mergers)", ""]
    f_mult = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
    for key, title in (("pom_detail", "Exelon / Pepco Holdings"), ("agl_detail", "Southern Company / AGL Resources")):
        d = out[key]; det = d["_detail"]
        ni_str = f"-${abs(d['ltm_net_income'])/1e6:,.0f}M" if d["ltm_net_income"] < 0 else f"${d['ltm_net_income']/1e6:,.0f}M"
        md += [f"### {title} — announced {d['date']}", "",
               f"All-cash: **${d['offer_price']:.2f}**/target share. Equity value ${det['equity_value']/1e6:,.0f}M "
               f"({det['diluted_shares']/1e6:.1f}M target diluted shares) + net debt ${det['net_debt']/1e6:,.0f}M "
               f"= enterprise value **${d['enterprise_value']/1e6:,.0f}M**, target fundamentals from its FY{det['fy'][:4]} 10-K (SEC EDGAR).", "",
               f"**EV/Revenue {f_mult(comps.multiple(d['enterprise_value'], d['ltm_revenue']))}, "
               f"EV/EBITDA {f_mult(comps.multiple(d['enterprise_value'], d['ltm_ebitda']))}, "
               f"EV/EBIT {f_mult(comps.multiple(d['enterprise_value'], d['ltm_ebit']))}, "
               f"P/E {f_mult(comps.multiple(d['enterprise_value'] - det['net_debt'], d['ltm_net_income']))}** (target net income {ni_str}).", ""]
    md += ["Pepco Holdings' real FY2013 net loss isn't a data error — confirmed against SEC's live XBRL data "
           "(`EarningsPerShareDiluted` = -$0.86 for that year) — and `comps.multiple()`'s NM-cap logic correctly "
           "reports its P/E as NM rather than a nonsensical negative multiple, the same real pattern the steel, "
           "airline and insurance checks' precedents hit.", "",
           "A real, smaller finding visible in the football field itself: the EV/Revenue precedent bracket's low "
           "end implies a NEGATIVE equity value for DUK (see the table below), while EV/EBITDA and EV/EBIT from "
           "the same two deals don't have this problem. The cause is real, not a data error: both 2014-2015 "
           "targets were meaningfully less levered per dollar of revenue than Duke Energy is today (Pepco "
           "Holdings' net debt was 0.95x its own revenue, AGL Resources' 0.68x, versus DUK's real 2.74x) — "
           "EV/Revenue implicitly assumes similar leverage-per-revenue-dollar across targets, which breaks down "
           "for a much larger, more heavily-levered multi-state holding company; EV/EBITDA and EV/EBIT scale with "
           "capital intensity rather than raw revenue and don't inherit the same problem.", ""]
    md += ["## 3. The real, sector-defining finding: elevated capex is the steady state, not a peak to fade", "",
           "| FY | Capex/Revenue | D&A/Revenue | Unlevered FCF (before NWC, $M) |", "|---|---|---|---|"]
    for r in out["ufcf_history"]:
        md.append(f"| {r['fy'][:4]} | {r['capex_pct_revenue']*100:.1f}% | {r['da_pct_revenue']*100:.1f}% | {r['ufcf']/1e6:,.0f} |")
    md += ["", "Real capex ran 39.6%-45.7% of revenue every single year FY2019-2025 — a persistent ~1.8-2.1x real "
           "D&A — and unlevered free cash flow (before working capital) was **negative** in 2 of those 7 years, "
           "never exceeding roughly $1.3B against $87B of debt and a ~$100B market cap. This isn't distress: it's "
           "the entire regulated-return mechanism working as designed — a utility earns its allowed ROE on a "
           "rate base that only grows if it keeps building it, so capex staying elevated forever (not fading back "
           "toward D&A the way the semiconductor check's temporary supercycle did) is the real, correct "
           "assumption for a utility DCF. The practical consequence, verified in the DCF below: with near-term "
           "UFCF this thin, terminal value carries the large majority of enterprise value — functionally, a "
           "'standard' unlevered DCF ends up shaped like a perpetuity-dominated dividend discount model without "
           "actually needing to swap engines the way banking/REITs/insurance did.", ""]
    md += ["## 4. DCF (unlevered, capex held at DUK's own real FY2025 ratio — not tapered) — and why the terminal growth rate matters more here than anywhere else this toolkit has checked", "",
           f"Discount rate 6.19% (`finmodel wacc examples/wacc_duk.json`) — itself the LOWEST WACC of any sector "
           f"this toolkit has profiled, a direct consequence of DUK's low 0.35 unlevered beta and heavy "
           f"tax-advantaged debt weighting. Margin scenarios use DUK's own real recent levels — FY2025 actual "
           f"margin {out['margin_2025']*100:.1f}%, trailing-3yr average {out['margin_3yr']*100:.1f}%, "
           f"trailing-8yr median {out['margin_8yr_median']*100:.1f}% — not a blind trailing-median reversion, "
           "since §5 below confirms DUK's real margin trend is a genuine, sustained improvement, not a cyclical "
           "extreme to revert away from.", "",
           "With UFCF this thin (§3), terminal value dominates enterprise value so completely that the perpetuity "
           "growth assumption, not the 5-year forecast, drives the whole result — verified by actually running "
           "both a generic and a real-guidance-anchored assumption side by side:", ""]
    for key in ("dcf_bear", "dcf_base", "dcf_blue_sky"):
        d = out[key]
        md.append(f"**{d['name']}** (perpetual growth {d['assumptions']['perpetual_growth']*100:.1f}%, margin "
                  f"target {d['assumptions']['ebit_margin_target_year5']*100:.1f}%, revenue growth "
                  f"{d['assumptions']['revenue_growth']*100:.1f}%/yr) -> implied share price "
                  f"**{d['base_value_per_share']:.2f}** (range {d['low']:.2f} - {d['high']:.2f}); terminal value is "
                  f"{d['pv_terminal_value_pct']*100:.0f}% of enterprise value.")
    md += ["", f"The bear case's generic 2.5% terminal growth rate — this toolkit's usual default, and a "
           "perfectly ordinary assumption for a mature industrial — produces a NEGATIVE implied equity value here. "
           "That is not a sign DUK is worth less than zero; it's a tell that 2.5% silently assumes DUK's real, "
           "currently-disclosed $103B 2026-2030 capital plan (which DUK itself guides to 5%-7% long-run EPS "
           "growth off a 9.6% rate-base growth rate) stops mattering the instant the 5-year forecast window ends. "
           "The base and blue-sky cases instead anchor terminal growth to DUK's own real guidance (4.5% and 5.0% "
           "respectively — moderated below the low end of that 5%-7% range specifically to stay safely under the "
           "6.19% discount rate, since a Gordon-growth perpetuity is mathematically undefined once growth reaches "
           "it), producing positive, far more defensible values. No prior sector check in this series has been "
           "this sensitive to the terminal growth assumption — a direct, real consequence of pairing thin UFCF "
           "with a low WACC, both of which are structural to how a regulated utility is financed.", ""]
    md += ["", "## 5. A real callback on a third, independent sector: the trend guard from software/insurance, on regulated rate-base growth", "",
           "`finmodel cycle data/edgar/DUK.json --sector utility` — the default field (operating_income/revenue) "
           "needs no override here, unlike banking/REIT/insurance:", ""]
    diag = out["normalized"]["cycle_diagnostics"]; trend = out["normalized"]["trend_diagnostics"]
    md += [f"FY{diag['fiscal_year'][:4]} margin {diag['latest_margin']*100:.1f}% vs trailing-8yr median "
           f"{diag['median_margin_trailing_years']*100:.1f}% ({diag['deviation_pct']*100:+.1f}%) -> "
           f"**{diag['flag'].split(' — CAUTION')[0]}**. `trend_diagnostics()` fires **{trend['trend_strength']}** "
           f"(r={trend['correlation']:.2f}, {trend['direction']}) — the same guard `docs/FOOTBALL_FIELD_CSCO.md` "
           "(software) and `docs/FOOTBALL_FIELD_TRV.md` (insurance) established, now confirmed on a THIRD, "
           "independent sector: DUK's real margin genuinely improved (23.4% -> 27.2%, FY2019-2025) because its "
           "real rate base has been growing (the capex table in §3), not because of a cyclical peak a "
           "trailing-median would be right to fade.", ""]
    md += ["## 6. A real, verified caveat for `finmodel.wacc.synthetic_rating()` on regulated entities", ""]
    rt = out["rating"]
    md += [f"DUK's real FY2025 interest coverage (EBIT ${rt['ebit']/1e6:,.0f}M / interest expense "
           f"${rt['interest_expense']/1e6:,.0f}M = {rt['synthetic']['interest_coverage']:.2f}x) maps to a "
           f"synthetic **'{rt['synthetic']['rating']}'** rating on Damodaran's large-firm coverage table — "
           f"sub-investment-grade. DUK's REAL rating, as of {rt['real_rating']['as_of']}, is investment-grade: "
           f"**{rt['real_rating']['sp']}** (S&P) / **{rt['real_rating']['moodys']}** (Moody's), both "
           f"{rt['real_rating']['outlook']} outlook. The coverage table was built for unregulated industrials; "
           "a regulated utility is ALLOWED to run structurally thin coverage because rate-of-return regulation "
           "makes debt-service recovery through rates close to guaranteed — the same low-coverage SIGNAL the "
           "airline check saw on a genuinely distressed ALK, with the opposite real-world meaning here. Always "
           "sanity-check a coverage-based synthetic rating against the filer's actual published rating before "
           "using it for a regulated entity.", ""]
    md += ["## 7. A real, independent finding at a peer: Xcel Energy's ROE dilution from funding its capital plan", ""]
    xdiag = out["xel_normalized"]["cycle_diagnostics"]; xtrend = out["xel_normalized"]["trend_diagnostics"]
    md += [f"`finmodel cycle data/edgar/XEL.json --sector utility --field net_income --revenue-field equity` — "
           f"XEL's own ROE held a tight 10.1%-10.4% band FY2018-2024 before dropping to "
           f"{xdiag['latest_margin']*100:.1f}% in FY2025 ({xdiag['deviation_pct']*100:+.1f}% vs the trailing-8yr "
           f"median). `trend_diagnostics()` fires **{xtrend['trend_strength']}** (r={xtrend['correlation']:.2f}, "
           f"{xtrend['direction']}) — but the real cause isn't earnings deterioration: Xcel Energy closed a "
           "real ~$1.18B forward common-stock offering in November 2024 (18,320,610 shares at $65.50) and "
           "disclosed a further $4.3B equity distribution program funding its multi-year capital plan, "
           "mechanically diluting ROE in the issuance year before the new equity has earned a full year's "
           "return — a real, utility-specific mechanism distinct from every other sector's cyclicality driver "
           "this module has been tuned against (commodity price, credit losses, rate-sensitivity, demand "
           "shock, catastrophe losses, the silicon cycle).", ""]
    md += ["## 8. 52-week trading range (real, market_data warehouse)", "",
           f"${out['week52']['low']:.2f} - ${out['week52']['high']:.2f} ({out['week52']['from']} to {out['week52']['to']}, {out['week52']['n_days']} trading days).", "",
           "## Method note", "",
           "Every revenue/EBIT/D&A/debt/cash figure is from an SEC 10-K (via `finmodel.edgar`); every price is a "
           "live database query against `market_data`; both deals' per-share cash prices and announcement dates "
           "come from the acquirer's own 8-K press releases (public record). Both real precedent targets are "
           "delisted (though the same CIKs still file as wholly-owned subsidiaries with public debt outstanding, "
           "which is how their historical fundamentals were pulled), so target-side deal premiums are omitted for "
           "the same reason as the banking, REIT, airline and insurance checks' precedents.", "",
           "Regenerate with `python scripts/football_field_duk.py`; chart at `out/charts_football_field_duk.html`."]
    return "\n".join(md)


if __name__ == "__main__":
    run()
