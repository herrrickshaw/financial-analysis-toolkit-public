"""Second real-company check of the CFI 'Comps, Precedents, Football Field' template — same method as
`scripts/football_field_stld.py`, applied to Chevron (CVX) in the oil & gas majors sector instead of steel:

  Trading comps    — ExxonMobil, ConocoPhillips, EOG Resources, Occidental Petroleum (SEC EDGAR fundamentals,
                     market_data warehouse closing prices, 2026-07-02).
  Precedent deals  — two real, verifiable, recent E&P mega-mergers: ExxonMobil / Pioneer Natural Resources
                     (all-stock, 2023-10-11) and ConocoPhillips / Marathon Oil (all-stock, 2024-05-29). Multiples
                     from SEC EDGAR fundamentals for the target's last full fiscal year before announcement and
                     the acquirer's own warehouse closing price on the announcement date x the disclosed exchange
                     ratio (both are real, public deal terms). As with the steel precedents, premiums to the
                     target's own undisturbed price are omitted: both PXD and MRO are delisted and absent from
                     the warehouse, so there's no independently verifiable target price series.
  DCF               — two scenarios built from CVX's own FY2025 EDGAR base year and its own 2018-2025 EBIT-margin
                     history (a war story in itself: -7.1% in the 2020 COVID crash to +20.4% in the 2022 price
                     spike), discounted at the WACC from `finmodel wacc examples/wacc_cvx.json` (8.26%).
  52-week range    — the real trailing 252-trading-day high/low from the warehouse.

Run: python scripts/football_field_cvx.py → docs/FOOTBALL_FIELD_CVX.md, out/comps_football_field_cvx.json,
out/charts_football_field_cvx.html"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finmodel import comps, charts, dcf, edgar, sectors  # noqa: E402

CORE = ["XOM", "COP", "EOG", "OXY"]   # integrated majors and large-cap E&P; refiners (PSX/VLO/MPC) and oilfield services (SLB) excluded as different business models
TARGET = "CVX"
PRICE_DATE = "2026-07-02"


def prices(tickers):
    out = subprocess.run(["psql", "-d", "market_data", "-Atc",
                          f"select s.ticker, h.close_price from ohlcv_history h join stocks s on s.stock_id=h.stock_id "
                          f"where s.market_id=2 and s.ticker in ({','.join(repr(t) for t in tickers)}) and h.date='{PRICE_DATE}'"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    return {l.split("|")[0]: float(l.split("|")[1]) for l in out.splitlines() if l}


def price_on(ticker, date_str):
    out = subprocess.run(["psql", "-d", "market_data", "-Atc",
                          f"select close_price from ohlcv_history h join stocks s on s.stock_id=h.stock_id where s.market_id=2 and s.ticker='{ticker}' and h.date='{date_str}'"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    return float(out) if out else None


def week52(ticker):
    out = subprocess.run(["psql", "-d", "market_data", "-Atc",
                          f"with r as (select h.date, h.close_price, row_number() over (order by h.date desc) rn "
                          f"from ohlcv_history h join stocks s on s.stock_id=h.stock_id where s.market_id=2 and s.ticker='{ticker}') "
                          f"select min(close_price), max(close_price), min(date), max(date), count(*) from r where rn<=252"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    lo, hi, d0, d1, n = out.split("|")
    return {"low": float(lo), "high": float(hi), "from": d0, "to": d1, "n_days": int(n)}


def _oxford_join(items):
    items = list(items)
    if not items: return "no method"
    if len(items) == 1: return items[0]
    if len(items) == 2: return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def fy(ticker, fy_end):
    return json.loads((ROOT / "data" / "edgar" / f"{ticker}.json").read_text())["years"][fy_end]


def xom_pxd_precedent():
    """ExxonMobil / Pioneer Natural Resources: all-stock, 2.3234 XOM shares per PXD share, announced 2023-10-11
    (publicly disclosed exchange ratio). Implied offer value/share = ratio x XOM's own warehouse closing price
    that day. PXD fundamentals: its last full fiscal year before announcement, FY2022."""
    r = fy("PXD", "2022-12-31")
    xom_close = price_on("XOM", "2023-10-11")
    ratio = 2.3234
    offer_price = ratio * xom_close if xom_close else None
    equity_value = offer_price * r["diluted_shares"] if offer_price else None
    net_debt = r["debt_total"] - r["cash"]
    ev = equity_value + net_debt if equity_value else None
    return {"acquirer": "Exxon Mobil Corporation", "target": "Pioneer Natural Resources Company", "date": "2023-10-11",
            "enterprise_value": ev, "ltm_revenue": r["revenue"], "ltm_ebitda": r["operating_income"] + r["da"], "ltm_ebit": r["operating_income"],
            "offer_price": offer_price, "_detail": {"fy": "2022-12-31", "exchange_ratio": ratio, "xom_close_on_announcement": xom_close,
                                                     "equity_value": equity_value, "net_debt": net_debt, "diluted_shares": r["diluted_shares"],
                                                     "source": "exchange ratio: publicly disclosed deal terms; XOM close: market_data warehouse; PXD revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K"}}


def cop_mro_precedent():
    """ConocoPhillips / Marathon Oil: all-stock, 0.2550 COP shares per MRO share, announced 2024-05-29.
    MRO fundamentals: its last full fiscal year before announcement, FY2023 (filed before the deal)."""
    r = fy("MRO", "2023-12-31")
    cop_close = price_on("COP", "2024-05-29")
    ratio = 0.2550
    offer_price = ratio * cop_close if cop_close else None
    equity_value = offer_price * r["diluted_shares"] if offer_price else None
    net_debt = r["debt_total"] - r["cash"]
    ev = equity_value + net_debt if equity_value else None
    return {"acquirer": "ConocoPhillips", "target": "Marathon Oil Corporation", "date": "2024-05-29",
            "enterprise_value": ev, "ltm_revenue": r["revenue"], "ltm_ebitda": r["operating_income"] + r["da"], "ltm_ebit": r["operating_income"],
            "offer_price": offer_price, "_detail": {"fy": "2023-12-31", "exchange_ratio": ratio, "cop_close_on_announcement": cop_close,
                                                     "equity_value": equity_value, "net_debt": net_debt, "diluted_shares": r["diluted_shares"],
                                                     "source": "exchange ratio: publicly disclosed deal terms; COP close: market_data warehouse; MRO revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K"}}


def cvx_dcf_scenario(name: str, growth: float, margin_target: float, da_pct: float, capex_pct: float, discount_rate: float, current_price: float):
    r = fy("CVX", "2025-12-31")
    rev0 = r["revenue"] / 1e6; margin0 = r["operating_income"] / r["revenue"]; nwc0_pct = (r["current_assets"] - r["current_liabilities"]) / r["revenue"]
    n = 5
    rev = [rev0]
    for _ in range(n): rev.append(rev[-1] * (1 + growth))
    margins = [margin0 + (margin_target - margin0) * t / n for t in range(1, n + 1)]
    ebit = [rev[t] * margins[t - 1] for t in range(1, n + 1)]
    da = [rev[t] * da_pct for t in range(1, n + 1)]
    capex = [rev[t] * capex_pct for t in range(1, n + 1)]
    change_nwc = [nwc0_pct * (rev[t] - rev[t - 1]) for t in range(1, n + 1)]
    inp = dcf.DCFInputs(ebit=ebit, da=da, change_nwc=change_nwc, capex=capex, tax_rate=0.3676, discount_rate=discount_rate,
                        perpetual_growth=0.025, terminal_method="perpetuity", transaction_date="2025-12-31", fiscal_year_end="2026-12-31",
                        current_price=current_price, shares_outstanding=r["diluted_shares"] / 1e6, debt=r["debt_total"] / 1e6, cash=r["cash"] / 1e6)
    res = dcf.run(inp)
    sens = dcf.sensitivity(inp, [discount_rate - 0.005, discount_rate, discount_rate + 0.005], [0.02, 0.025, 0.03])
    flat = [v for row in sens["table"] for v in row]
    return {"name": name, "base_value_per_share": res["equity_value_per_share"], "low": min(flat), "high": max(flat),
            "assumptions": {"revenue_growth": growth, "ebit_margin_target_year5": margin_target, "da_pct_revenue": da_pct, "capex_pct_revenue": capex_pct, "discount_rate": discount_rate, "terminal_growth": 0.025}}


def build_normalized(px):
    """Same football field, rebuilt with finmodel.sectors: peer/target EBIT+EBITDA use the trailing-8yr median
    (through-cycle) instead of the raw LTM year; precedent-deal targets (PXD, MRO) use their own trailing-history
    median EBIT/EBITDA as of the announcement instead of the deal-year figure; the two DCF scenarios use
    finmodel.sectors.dcf_scenarios_from_history's data-driven bear/base/blue-sky margins. Every other assumption
    (growth, D&A%, capex%, discount rate, tax rate) is held identical to the raw run."""
    peers = []
    for t in CORE:
        hist = json.loads((ROOT / "data" / "edgar" / f"{t}.json").read_text())["years"]
        r = fy(t, "2025-12-31")
        m = sectors.normalized_comps_metrics(hist, sector="oil_gas")
        peers.append(comps.Peer(t, px[t], r["diluted_shares"], cash=r["cash"] + r.get("short_term_investments", 0), debt=r["debt_total"], nci=r.get("nci", 0), metrics=m, ticker=t))
    trading = comps.spread(peers)

    pxd_hist = json.loads((ROOT / "data" / "edgar" / "PXD.json").read_text())["years"]
    mro_hist = json.loads((ROOT / "data" / "edgar" / "MRO.json").read_text())["years"]
    pxd_n = sectors.normalize_metric(pxd_hist, "operating_income", periods=8, method="median", as_of="2022-12-31")["value"]
    pxd_da_n = sectors.normalize_metric(pxd_hist, "da", periods=8, method="median", as_of="2022-12-31")["value"]
    mro_n = sectors.normalize_metric(mro_hist, "operating_income", periods=8, method="median", as_of="2023-12-31")["value"]
    mro_da_n = sectors.normalize_metric(mro_hist, "da", periods=8, method="median", as_of="2023-12-31")["value"]
    x_deal, c_deal = xom_pxd_precedent(), cop_mro_precedent()
    from finmodel.comps import Deal
    deals = [Deal(x_deal["acquirer"], x_deal["target"], x_deal["date"], x_deal["enterprise_value"], ltm_revenue=x_deal["ltm_revenue"], ltm_ebitda=pxd_n + pxd_da_n, ltm_ebit=pxd_n),
             Deal(c_deal["acquirer"], c_deal["target"], c_deal["date"], c_deal["enterprise_value"], ltm_revenue=c_deal["ltm_revenue"], ltm_ebitda=mro_n + mro_da_n, ltm_ebit=mro_n)]
    precedents = comps.precedents(deals)

    cvx_hist = json.loads((ROOT / "data" / "edgar" / "CVX.json").read_text())["years"]
    tr = fy(TARGET, "2025-12-31")
    tm = sectors.normalized_comps_metrics(cvx_hist, sector="oil_gas")
    target = comps.Target("Chevron Corporation", px[TARGET], tr["diluted_shares"], metrics=tm,
                          bridge={"cash": tr["cash"] + tr.get("short_term_investments", 0), "debt": -tr["debt_total"], "nci": -tr.get("nci", 0)})

    s = sectors.dcf_scenarios_from_history(cvx_hist, periods=8)
    base = cvx_dcf_scenario("DCF - base case (sector-normalized: trailing median margin)", growth=0.02, margin_target=s["base_margin"], da_pct=0.095, capex_pct=0.075, discount_rate=0.0826, current_price=px[TARGET])
    blue = cvx_dcf_scenario("DCF - blue sky (sector-normalized: trailing peak margin)", growth=0.05, margin_target=s["blue_sky_margin"], da_pct=0.07, capex_pct=0.06, discount_rate=0.0826, current_price=px[TARGET])
    wk52 = week52(TARGET)

    ff = comps.football_field(target, {"Trading comps": trading, "Precedent transactions": precedents},
                              extra={base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"]), "52-week range": (wk52["low"], wk52["high"])},
                              stat_low="p25", stat_high="p75")
    return {"trading_comps": trading, "precedents": precedents, "dcf_base": base, "dcf_blue_sky": blue, "dcf_scenarios_from_history": s, "football_field": ff}


def run():
    px = prices(CORE + [TARGET])
    peers = []
    for t in CORE:
        r = fy(t, "2025-12-31")
        m = {"revenue": r["revenue"], "ebitda": r["operating_income"] + r["da"], "ebit": r["operating_income"], "net_income": r["net_income"]}
        peers.append(comps.Peer(t, px[t], r["diluted_shares"], cash=r["cash"] + r.get("short_term_investments", 0), debt=r["debt_total"], nci=r.get("nci", 0), metrics=m, ticker=t))
    trading = comps.spread(peers)

    x_deal, c_deal = xom_pxd_precedent(), cop_mro_precedent()
    from finmodel.comps import Deal
    deals = [Deal(x_deal["acquirer"], x_deal["target"], x_deal["date"], x_deal["enterprise_value"], ltm_revenue=x_deal["ltm_revenue"], ltm_ebitda=x_deal["ltm_ebitda"], ltm_ebit=x_deal["ltm_ebit"]),
             Deal(c_deal["acquirer"], c_deal["target"], c_deal["date"], c_deal["enterprise_value"], ltm_revenue=c_deal["ltm_revenue"], ltm_ebitda=c_deal["ltm_ebitda"], ltm_ebit=c_deal["ltm_ebit"])]
    precedents = comps.precedents(deals)

    tr = fy(TARGET, "2025-12-31")
    target = comps.Target("Chevron Corporation", px[TARGET], tr["diluted_shares"], metrics={"revenue": tr["revenue"], "ebitda": tr["operating_income"] + tr["da"], "ebit": tr["operating_income"], "net_income": tr["net_income"]},
                          bridge={"cash": tr["cash"] + tr.get("short_term_investments", 0), "debt": -tr["debt_total"], "nci": -tr.get("nci", 0)})

    # Chevron's own 2018-2025 EBIT margin ranged from -7.1% (2020 COVID crash) to +20.4% (2022 price spike);
    # base case holds near the recent 2023-2025 average, blue sky recovers toward the 2022 peak.
    base = cvx_dcf_scenario("DCF - base case (margin near 2023-25 average)", growth=0.02, margin_target=0.135, da_pct=0.095, capex_pct=0.075, discount_rate=0.0826, current_price=px[TARGET])
    blue = cvx_dcf_scenario("DCF - blue sky (margin recovers toward 2022 peak)", growth=0.05, margin_target=0.20, da_pct=0.07, capex_pct=0.06, discount_rate=0.0826, current_price=px[TARGET])
    wk52 = week52(TARGET)

    ff = comps.football_field(target, {"Trading comps": trading, "Precedent transactions": precedents},
                              extra={base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"]), "52-week range": (wk52["low"], wk52["high"])},
                              stat_low="p25", stat_high="p75")

    normalized = build_normalized(px)

    out = {"price": px[TARGET], "price_date": PRICE_DATE, "trading_comps": trading, "precedents": precedents,
           "xom_pxd_detail": x_deal, "cop_mro_detail": c_deal, "dcf_base": base, "dcf_blue_sky": blue, "week52": wk52, "football_field": ff,
           "cvx_fy2025_margin": tr["operating_income"] / tr["revenue"], "normalized": normalized}
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "comps_football_field_cvx.json").write_text(json.dumps(out, indent=1, default=str))
    charts.report_for("comps", {"comps": trading, "precedents": precedents, "football_field": ff}, ROOT / "out" / "charts_football_field_cvx.html", title="Chevron — CFI football-field template on real data")

    md = write_doc(out)
    (ROOT / "docs" / "FOOTBALL_FIELD_CVX.md").write_text(md)
    print(f"CVX price {px[TARGET]:.2f} ({PRICE_DATE})")
    for it in ff["items"]:
        print(f"  {it['method']:55} {it['low']:8.2f} - {it['high']:8.2f}")


def write_doc(out):
    px = out["price"]; ff = out["football_field"]
    md = ["# Second real-company check: the CFI football-field template against Chevron (CVX)", "",
          f"Same method as `docs/FOOTBALL_FIELD_STLD.md`, applied to a different industry (oil & gas majors "
          f"instead of steel) to check the method generalizes rather than being tuned to one sector. Real peer "
          f"trading comps, two real verifiable E&P precedent deals, two DCF scenarios grounded in Chevron's own "
          f"margin history, and Chevron's real 52-week range — compared to Chevron's actual price of "
          f"**${px:.2f}** (warehouse close, {out['price_date']}).", "",
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
    if not price_above and not price_below:
        headline = "Every method brackets the actual price."
    else:
        headline = f"Only {_oxford_join(brackets)} bracket{'s' if len(brackets) == 1 else ''} the actual price."
    md += ["", headline, ""]
    if price_above:
        parts = [f"{it['method']} (high {it['high']:.2f})" for it in price_above]
        md.append("Ranges the price sits **above** (implied values too low): " + ", ".join(parts) + ".")
    if price_below:
        parts = [f"{it['method']} (low {it['low']:.2f})" for it in price_below]
        md.append("Ranges the price sits **below** (implied values too high): " + ", ".join(parts) + ".")
    md += ["", "## 1. Trading comps (real: SEC EDGAR fundamentals + market_data warehouse prices)", "",
           f"Peers: ExxonMobil, ConocoPhillips, EOG Resources, Occidental Petroleum — FY2025 fundamentals, {out['price_date']} closing prices.", "",
           "| Ticker | Price | EV/Revenue | EV/EBITDA | EV/EBIT | P/E |", "|---|---|---|---|---|---|"]
    for p in out["trading_comps"]["peers"]:
        f = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
        md.append(f"| {p['ticker']} | {p['price']:.2f} | {f(p['multiples']['EV / Revenue LTM'])} | {f(p['multiples']['EV / EBITDA LTM'])} | {f(p['multiples']['EV / EBIT LTM'])} | {f(p['multiples']['P / E LTM'])} |")
    md += ["", "| Multiple | 25th | Median | 75th |", "|---|---|---|---|"]
    for label in ("EV / Revenue LTM", "EV / EBITDA LTM", "EV / EBIT LTM"):
        s = out["trading_comps"]["summary"][label]
        md.append(f"| {label} | {s['p25']:.2f}x | {s['median']:.2f}x | {s['p75']:.2f}x |")
    md += ["", "## 2. Precedent transactions (real, verifiable deals)", ""]
    for key, title in (("xom_pxd_detail", "ExxonMobil / Pioneer Natural Resources"), ("cop_mro_detail", "ConocoPhillips / Marathon Oil")):
        d = out[key]; det = d["_detail"]
        md += [f"### {title} — announced {d['date']}", "",
               f"All-stock: {det['exchange_ratio']} acquirer shares per target share x the acquirer's own warehouse closing price on the announcement date "
               f"= offer **${d['offer_price']:.2f}**/target share. Enterprise value **${d['enterprise_value']/1e6:,.0f}M** = equity value "
               f"${det['equity_value']/1e6:,.0f}M ({det['diluted_shares']/1e6:.1f}M target diluted shares) + net debt ${det['net_debt']/1e6:,.0f}M, "
               f"target fundamentals from its FY{det['fy'][:4]} 10-K (SEC EDGAR).", "",
               f"LTM revenue ${d['ltm_revenue']/1e6:,.0f}M, LTM EBITDA ${d['ltm_ebitda']/1e6:,.0f}M, LTM EBIT ${d['ltm_ebit']/1e6:,.0f}M → "
               f"**EV/Revenue {d['enterprise_value']/d['ltm_revenue']:.2f}x, EV/EBITDA {d['enterprise_value']/d['ltm_ebitda']:.2f}x, "
               f"EV/EBIT {d['enterprise_value']/d['ltm_ebit']:.2f}x**.", "",
               f"*Source: {det['source']}.*", ""]
    md += ["Note the direction of the earnings-cycle distortion here is the **opposite** of the steel precedents in "
           "`docs/FOOTBALL_FIELD_STLD.md`: both target fiscal years (PXD FY2022, MRO FY2023) fell in or just after the "
           "2022 oil-and-gas price spike, so LTM EBITDA was unusually *high* — this makes the resulting EV/EBITDA "
           "multiples look unusually *cheap* rather than expensive, the mirror image of steel's 2025 trough-earnings "
           "problem. Trailing multiples get distorted by the cycle in both directions; which direction depends on "
           "when the deal happened to close relative to the target's own earnings cycle, not on any property of the "
           "target's business.", ""]
    md += ["## 3. DCF (illustrative scenarios built from Chevron's own historical range, not analyst consensus)", "",
           f"Discount rate 8.26% for both scenarios (`finmodel wacc examples/wacc_cvx.json`); terminal growth 2.5%, perpetuity method. "
           "Chevron's own EBIT margin ranged from -7.1% (2020, COVID demand collapse) to +20.4% (2022, post-invasion oil price spike) "
           "over FY2018-2025 — an even wider real range than steel's, since a commodity producer's margin swings with a price it does "
           "not control. The low-high range is a small discount-rate (±0.5pt) x terminal-growth (2.0%/2.5%/3.0%) sensitivity grid.", ""]
    for key in ("dcf_base", "dcf_blue_sky"):
        d = out[key]; a = d["assumptions"]
        md += [f"**{d['name']}**: revenue grows {a['revenue_growth']*100:.0f}%/yr, EBIT margin reaches {a['ebit_margin_target_year5']*100:.1f}% by year 5 "
               f"(FY2025 was {out['cvx_fy2025_margin']*100:.1f}%) → implied share price **{d['base_value_per_share']:.2f}** "
               f"(range {d['low']:.2f} – {d['high']:.2f} across the sensitivity grid).", ""]
    md += ["", "## 4. 52-week trading range (real, market_data warehouse)", "",
           f"${out['week52']['low']:.2f} – ${out['week52']['high']:.2f} ({out['week52']['from']} to {out['week52']['to']}, {out['week52']['n_days']} trading days).", ""]
    md += ["## 5. Sector-tuned comparison: does cycle-normalizing the inputs change the answer?", "",
           "The same `finmodel.sectors` treatment as `docs/FOOTBALL_FIELD_STLD.md`, applied here. Chevron's own FY2025 margin sits only "
           "modestly below its own trailing 8-year median (`finmodel cycle data/edgar/CVX.json --sector oil_gas` calls it 'near normal', "
           "not a trough) — a real, useful contrast with STLD, where FY2025 WAS flagged as a trough. The precedent-deal targets are a "
           "different story: both PXD (as of FY2022) and MRO (as of FY2023) sit at or near their own historical peaks. This section "
           "rebuilds every input with each company's own trailing-history median EBIT/EBITDA instead of its raw LTM year, holding every "
           "other assumption identical.", ""]
    norm = out["normalized"]; nff = norm["football_field"]
    md += ["| Method | Raw LTM range | Sector-normalized range | Normalized brackets price? |", "|---|---|---|---|"]
    n_brackets = []
    for it, nit in zip(ff["items"], nff["items"]):
        inside = nit["low"] <= px <= nit["high"]
        if inside: n_brackets.append(nit["method"])
        note = " (unchanged — real price history)" if nit["method"] == "52-week range" else ""
        md.append(f"| {it['method'].split(' (')[0]} | {it['low']:.2f} – {it['high']:.2f} | {nit['low']:.2f} – {nit['high']:.2f}{note} | {'yes' if inside else 'no'} |")
    s = norm["dcf_scenarios_from_history"]
    peak_year = max(s["margin_history"], key=s["margin_history"].get)[:4]
    md += ["", f"Data-driven margin targets from Chevron's own trailing 8 fiscal years (`finmodel cycle`): bear {s['bear_margin']:.1%}, "
           f"base (trailing median) {s['base_margin']:.1%}, blue sky (trailing peak, FY{peak_year}) {s['blue_sky_margin']:.1%} — versus "
           f"the hand-picked 13.5%/20.0% used in the raw run above.", ""]
    if _oxford_join(n_brackets) != _oxford_join(brackets):
        md.append(f"Normalizing changes which methods bracket the price: raw run → {_oxford_join(brackets)}; normalized run → {_oxford_join(n_brackets)}.")
    else:
        md.append(f"Normalizing does not change which methods bracket the price here (still {_oxford_join(n_brackets)}).")
    n_prec = nff["items"][1]
    md += ["", f"The trading comps and both DCF scenarios barely move — Chevron's own peer set and its own margin history were never far "
           f"from normal, so there was little to correct. The precedent-transaction range moves the most, and moves up: normalizing PXD's "
           f"and MRO's EBIT/EBITDA down from their own 2022/2023 cycle peaks toward their trailing-history median makes the deals' EV/EBITDA "
           f"multiples meaningfully more expensive (as flagged qualitatively in section 2), which pushes the whole precedent-implied range up "
           f"to {n_prec['low']:.2f} – {n_prec['high']:.2f} — high enough that it stops bracketing the price at all, this time because the raw "
           f"range's low end no longer reaches down to Chevron's actual price. Read together with the STLD result, the pattern is that "
           f"normalization corrects the specific method it's applied to in the direction the sign of that method's own cycle distortion "
           f"predicts — it doesn't automatically make every football field converge on the market price, because the market price reflects "
           f"information (forward estimates, buybacks, sentiment) that none of these backward-looking methods carry.", ""]
    md += ["## Method note", "",
           "Same standard as the STLD check: every revenue/EBIT/D&A/debt/cash figure is from an SEC 10-K (via `finmodel.edgar`), "
           "every price is a live database query against `market_data`, the two deals' exchange ratios and announcement dates are "
           "public record, and the two DCF scenarios are explicitly labelled illustrative assumptions grounded in the target's own "
           "historical margin range, not analyst consensus. Target-side deal premiums are omitted for the same reason as before: "
           "both PXD and MRO are delisted and absent from the warehouse.", "",
           "Regenerate with `python scripts/football_field_cvx.py`; chart at `out/charts_football_field_cvx.html`."]
    return "\n".join(md)


if __name__ == "__main__":
    run()
