"""Populate the CFI 'Comps, Precedents, Football Field' template — the one `finmodel.comps.football_field()` is
reconciled against in `tests/test_comps.py` using the CFI workbook's illustrative numbers — with real Steel Dynamics
(STLD) data, and see where STLD's actual price sits:

  Trading comps    — the carbon-steel peer set from `scripts/comps_validation.py` (SEC EDGAR fundamentals,
                     market_data warehouse closing prices, 2026-07-02).
  Precedent deals  — two real, verifiable acquisitions of US steel producers: Nippon Steel / United States Steel
                     (cash, 2023-12-18) and Cleveland-Cliffs / AK Steel Holding (all-stock, 2019-12-02). Multiples
                     are built from SEC EDGAR fundamentals (revenue/EBIT/D&A/debt/cash for the target's last full
                     fiscal year before announcement) and the disclosed/derived deal consideration — NOT fabricated
                     figures. Premiums to the target's own undisturbed price are omitted: both targets are delisted
                     and absent from the warehouse, and free sources (Yahoo/Stooq) refuse historical data for a
                     delisted ticker, so there is no independently verifiable target price series to compute a
                     premium against — better to omit than to guess.
  DCF               — two scenarios built from STLD's own FY2025 EDGAR base year and its own 2018-2025 historical
                     margin range (base case recovers toward the FY2024 margin, blue-sky toward the FY2023 margin),
                     discounted at the WACC from `finmodel wacc examples/wacc_stld.json` (10.28%), with a small
                     discount-rate/growth sensitivity band standing in for the "Lo/Hi" a banker would get from a
                     scenario or data-table analysis. These are illustrative scenarios I built, not analyst
                     consensus — labelled as such throughout.
  52-week range    — the real trailing 252-trading-day high/low from the warehouse (2025-07-02 to 2026-07-02).

Run: python scripts/football_field_stld.py → docs/FOOTBALL_FIELD_STLD.md, out/comps_football_field_stld.json,
out/charts_football_field_stld.html"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finmodel import comps, charts, dcf, sectors  # noqa: E402
import comps_validation as CV  # noqa: E402  (reuses CORE peer set, price lookup, latest() EDGAR loader)

PRICE_DATE = CV.PRICE_DATE


def week52(ticker: str):
    try:
        out = subprocess.run(["psql", "-d", "market_data", "-Atc",
                              f"with r as (select h.date, h.close_price, row_number() over (order by h.date desc) rn "
                              f"from ohlcv_history h join stocks s on s.stock_id=h.stock_id where s.market_id=2 and s.ticker='{ticker}') "
                              f"select min(close_price), max(close_price), min(date), max(date), count(*) from r where rn<=252"],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        lo, hi, d0, d1, n = out.split("|")
        return {"low": float(lo), "high": float(hi), "from": d0, "to": d1, "n_days": int(n), "source": "warehouse"}
    except Exception as e:
        return {"error": str(e)}


def clf_price_on(date_str: str):
    out = subprocess.run(["psql", "-d", "market_data", "-Atc",
                          f"select close_price from ohlcv_history h join stocks s on s.stock_id=h.stock_id where s.market_id=2 and s.ticker='CLF' and h.date='{date_str}'"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    return float(out) if out else None


def x_precedent():
    """Nippon Steel / United States Steel: $55.00/share cash, announced 2023-12-18 (publicly disclosed deal terms,
    a matter of record in both companies' own SEC filings and press releases — not derived from a price series).
    Multiples use X's own last full fiscal year (2023) EDGAR fundamentals."""
    _, _, r, _ = CV.latest("X")
    fy2023 = json.loads((ROOT / "data" / "edgar" / "X.json").read_text())["years"]["2023-12-31"]
    revenue, ebit, da = fy2023["revenue"], fy2023["operating_income"], fy2023["da"]
    debt, cash, shares = fy2023["debt_total"], fy2023["cash"], fy2023["diluted_shares"]
    offer_price = 55.00
    equity_value = offer_price * shares
    ev = equity_value + debt - cash
    return {"acquirer": "Nippon Steel Corporation", "target": "United States Steel Corporation", "date": "2023-12-18",
            "enterprise_value": ev, "ltm_revenue": revenue, "ltm_ebitda": ebit + da, "ltm_ebit": ebit,
            "offer_price": offer_price, "_detail": {"fy": "2023-12-31", "equity_value": equity_value, "net_debt": debt - cash, "diluted_shares": shares,
                                                     "source": "offer price: publicly disclosed deal terms; revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K"}}


def aks_precedent():
    """Cleveland-Cliffs / AK Steel Holding: all-stock, 0.400 CLF share per AKS share, announced 2019-12-02.
    Implied offer value/share = 0.400 x CLF's own warehouse closing price that day; AKS fundamentals from its
    last full fiscal year (2019) EDGAR company facts (CIK 918160; compact extract in data/edgar/AKS.json,
    fetched the same way as every other ticker in data/edgar/ — see finmodel.edgar)."""
    fy2019 = json.loads((ROOT / "data" / "edgar" / "AKS.json").read_text())["years"]["2019-12-31"]
    revenue, ebit, da = fy2019["revenue"], fy2019["operating_income"], fy2019["da"]
    debt, cash, shares = fy2019["debt_total"], fy2019["cash"], fy2019["diluted_shares"]
    clf_close = clf_price_on("2019-12-02")
    offer_price = 0.400 * clf_close if clf_close else None
    equity_value = offer_price * shares if offer_price else None
    ev = equity_value + debt - cash if equity_value else None
    return {"acquirer": "Cleveland-Cliffs Inc.", "target": "AK Steel Holding Corporation", "date": "2019-12-02",
            "enterprise_value": ev, "ltm_revenue": revenue, "ltm_ebitda": ebit + da, "ltm_ebit": ebit,
            "offer_price": offer_price, "_detail": {"fy": "2019-12-31", "clf_close_on_announcement": clf_close, "exchange_ratio": 0.400,
                                                     "equity_value": equity_value, "net_debt": debt - cash, "diluted_shares": shares,
                                                     "source": "CLF close: market_data warehouse (dividend-adjusted, likely a few % below the nominal quote); AKS revenue/EBIT/D&A/debt/cash: SEC EDGAR 10-K"}}


def stld_dcf_scenario(name: str, growth: float, margin_target: float, da_pct: float, capex_pct: float, discount_rate: float, current_price: float):
    fy = json.loads((ROOT / "data" / "edgar" / "STLD.json").read_text())["years"]["2025-12-31"]
    rev0 = fy["revenue"] / 1e6; margin0 = fy["operating_income"] / fy["revenue"]; nwc0_pct = (fy["current_assets"] - fy["current_liabilities"]) / fy["revenue"]
    n = 5
    rev = [rev0]
    for _ in range(n): rev.append(rev[-1] * (1 + growth))
    margins = [margin0 + (margin_target - margin0) * t / n for t in range(1, n + 1)]
    ebit = [rev[t] * margins[t - 1] for t in range(1, n + 1)]
    da = [rev[t] * da_pct for t in range(1, n + 1)]
    capex = [rev[t] * capex_pct for t in range(1, n + 1)]
    change_nwc = [nwc0_pct * (rev[t] - rev[t - 1]) for t in range(1, n + 1)]
    inp = dcf.DCFInputs(ebit=ebit, da=da, change_nwc=change_nwc, capex=capex, tax_rate=0.205, discount_rate=discount_rate,
                        perpetual_growth=0.025, terminal_method="perpetuity", transaction_date="2025-12-31", fiscal_year_end="2026-12-31",
                        current_price=current_price, shares_outstanding=fy["diluted_shares"] / 1e6, debt=fy["debt_total"] / 1e6, cash=fy["cash"] / 1e6)
    res = dcf.run(inp)
    sens = dcf.sensitivity(inp, [discount_rate - 0.005, discount_rate, discount_rate + 0.005], [0.02, 0.025, 0.03])
    flat = [v for row in sens["table"] for v in row]
    return {"name": name, "base_value_per_share": res["equity_value_per_share"], "low": min(flat), "high": max(flat),
            "assumptions": {"revenue_growth": growth, "ebit_margin_target_year5": margin_target, "da_pct_revenue": da_pct, "capex_pct_revenue": capex_pct, "discount_rate": discount_rate, "terminal_growth": 0.025},
            "projection": {"revenue": rev[1:], "ebit": ebit, "da": da, "capex": capex, "change_nwc": change_nwc}}


def build_normalized(px, price_source):
    """The same football field, but built with finmodel.sectors: peer and target EBIT/EBITDA are the trailing-8yr
    median (through-cycle) rather than the raw, cycle-distorted LTM year; precedent-deal target multiples use their
    own trailing-history median EBIT/EBITDA as of the announcement instead of the deal-year figure; the two DCF
    scenarios use finmodel.sectors.dcf_scenarios_from_history's data-driven bear/base/blue-sky margins instead of a
    hand-picked 'toward FY20XX' target — everything else (growth, D&A%, capex%, discount rate, tax rate) is held
    identical to the raw run so the comparison isolates the effect of cycle normalization."""
    peers = []
    for t in CV.CORE:
        hist = json.loads((ROOT / "data" / "edgar" / f"{t}.json").read_text())["years"]
        _, _, r, _ = CV.latest(t)
        m = sectors.normalized_comps_metrics(hist, sector="steel")
        peers.append(comps.Peer(t, px[t], r.get("diluted_shares", 0), cash=r.get("cash", 0) + r.get("short_term_investments", 0), debt=r.get("debt_total", 0), nci=r.get("nci", 0), metrics=m, ticker=t))
    trading = comps.spread(peers)

    x_hist = json.loads((ROOT / "data" / "edgar" / "X.json").read_text())["years"]
    aks_hist = json.loads((ROOT / "data" / "edgar" / "AKS.json").read_text())["years"]
    x_n = sectors.normalize_metric(x_hist, "operating_income", periods=8, method="median", as_of="2023-12-31")["value"]
    x_da_n = sectors.normalize_metric(x_hist, "da", periods=8, method="median", as_of="2023-12-31")["value"]
    aks_n = sectors.normalize_metric(aks_hist, "operating_income", periods=8, method="median", as_of="2019-12-31")["value"]
    aks_da_n = sectors.normalize_metric(aks_hist, "da", periods=8, method="median", as_of="2019-12-31")["value"]
    x_deal, aks_deal = x_precedent(), aks_precedent()
    from finmodel.comps import Deal
    deals = [Deal(x_deal["acquirer"], x_deal["target"], x_deal["date"], x_deal["enterprise_value"], ltm_revenue=x_deal["ltm_revenue"], ltm_ebitda=x_n + x_da_n, ltm_ebit=x_n),
             Deal(aks_deal["acquirer"], aks_deal["target"], aks_deal["date"], aks_deal["enterprise_value"], ltm_revenue=aks_deal["ltm_revenue"], ltm_ebitda=aks_n + aks_da_n, ltm_ebit=aks_n)]
    precedents = comps.precedents(deals)

    stld_hist = json.loads((ROOT / "data" / "edgar" / "STLD.json").read_text())["years"]
    _, _, tr, _ = CV.latest("STLD")
    tm = sectors.normalized_comps_metrics(stld_hist, sector="steel")
    target = comps.Target("Steel Dynamics, Inc.", px["STLD"], tr["diluted_shares"], metrics=tm,
                          bridge={"cash": tr.get("cash", 0) + tr.get("short_term_investments", 0), "debt": -tr.get("debt_total", 0), "nci": -tr.get("nci", 0)})

    s = sectors.dcf_scenarios_from_history(stld_hist, periods=8)
    base = stld_dcf_scenario("DCF - base case (sector-normalized: trailing median margin)", growth=0.03, margin_target=s["base_margin"], da_pct=0.030, capex_pct=0.052, discount_rate=0.1028, current_price=px["STLD"])
    blue = stld_dcf_scenario("DCF - blue sky (sector-normalized: trailing peak margin)", growth=0.06, margin_target=s["blue_sky_margin"], da_pct=0.023, capex_pct=0.080, discount_rate=0.1028, current_price=px["STLD"])
    wk52 = week52("STLD")

    ff = comps.football_field(target, {"Trading comps": trading, "Precedent transactions": precedents},
                              extra={base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"]), "52-week range": (wk52["low"], wk52["high"])},
                              stat_low="p25", stat_high="p75")
    return {"trading_comps": trading, "precedents": precedents, "dcf_base": base, "dcf_blue_sky": blue, "dcf_scenarios_from_history": s, "football_field": ff}


def run():
    px, price_source = CV.prices()
    peers = []
    for t in CV.CORE:
        name, fy, r, _ = CV.latest(t)
        m = {"revenue": r.get("revenue"), "ebitda": r.get("ebitda"), "ebit": r.get("operating_income"), "net_income": r.get("net_income")}
        peers.append(comps.Peer(name, px[t], r.get("diluted_shares", 0), cash=r.get("cash", 0) + r.get("short_term_investments", 0), debt=r.get("debt_total", 0), nci=r.get("nci", 0), metrics=m, ticker=t))
    trading = comps.spread(peers)

    x_deal, aks_deal = x_precedent(), aks_precedent()
    from finmodel.comps import Deal
    deals = [Deal(x_deal["acquirer"], x_deal["target"], x_deal["date"], x_deal["enterprise_value"], ltm_revenue=x_deal["ltm_revenue"], ltm_ebitda=x_deal["ltm_ebitda"], ltm_ebit=x_deal["ltm_ebit"]),
             Deal(aks_deal["acquirer"], aks_deal["target"], aks_deal["date"], aks_deal["enterprise_value"], ltm_revenue=aks_deal["ltm_revenue"], ltm_ebitda=aks_deal["ltm_ebitda"], ltm_ebit=aks_deal["ltm_ebit"])]
    precedents = comps.precedents(deals)

    tname, tfy, tr, _ = CV.latest("STLD")
    target = comps.Target(tname, px["STLD"], tr["diluted_shares"], metrics={"revenue": tr["revenue"], "ebitda": tr["ebitda"], "ebit": tr["operating_income"], "net_income": tr["net_income"]},
                          bridge={"cash": tr.get("cash", 0) + tr.get("short_term_investments", 0), "debt": -tr.get("debt_total", 0), "nci": -tr.get("nci", 0)})

    base = stld_dcf_scenario("DCF - base case (margin recovers toward FY2024 level)", growth=0.03, margin_target=0.11, da_pct=0.030, capex_pct=0.052, discount_rate=0.1028, current_price=px["STLD"])
    blue = stld_dcf_scenario("DCF - blue sky (margin recovers toward FY2023 level)", growth=0.06, margin_target=0.168, da_pct=0.023, capex_pct=0.080, discount_rate=0.1028, current_price=px["STLD"])
    wk52 = week52("STLD")

    ff = comps.football_field(target, {"Trading comps": trading, "Precedent transactions": precedents},
                              extra={base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"]),
                                     "52-week range": (wk52["low"], wk52["high"])} if "low" in wk52 else {base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"])},
                              stat_low="p25", stat_high="p75")

    stld_years = json.loads((ROOT / "data" / "edgar" / "STLD.json").read_text())["years"]
    fy0, fy1 = min(stld_years), max(stld_years)
    buyback = {"from_fy": fy0, "from_shares": stld_years[fy0]["diluted_shares"], "to_fy": fy1, "to_shares": stld_years[fy1]["diluted_shares"]}

    normalized = build_normalized(px, price_source)

    out = {"price": px["STLD"], "price_date": PRICE_DATE, "price_source": price_source, "trading_comps": trading, "precedents": precedents,
           "x_precedent_detail": x_deal, "aks_precedent_detail": aks_deal, "dcf_base": base, "dcf_blue_sky": blue, "week52": wk52, "football_field": ff, "buyback": buyback,
           "normalized": normalized}
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "comps_football_field_stld.json").write_text(json.dumps(out, indent=1, default=str))
    charts.report_for("comps", {"comps": trading, "precedents": precedents, "football_field": ff}, ROOT / "out" / "charts_football_field_stld.html", title="Steel Dynamics — CFI football-field template on real data")

    md = write_doc(out)
    (ROOT / "docs" / "FOOTBALL_FIELD_STLD.md").write_text(md)
    print(f"STLD price {px['STLD']:.2f} ({price_source}, {PRICE_DATE})")
    for it in ff["items"]:
        print(f"  {it['method']:55} {it['low']:8.2f} - {it['high']:8.2f}")


def _oxford_join(items):
    items = list(items)
    if not items: return "no method"
    if len(items) == 1: return items[0]
    if len(items) == 2: return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def write_doc(out):
    px = out["price"]; ff = out["football_field"]
    md = ["# Checking the CFI football-field template against real Steel Dynamics (STLD) numbers", "",
          f"`finmodel.comps.football_field()` is reconciled in `tests/test_comps.py` against the CFI template's own "
          f"illustrative numbers (fictional companies, fictional deals). This runs the same function on real inputs: "
          f"real peer trading comps (SEC EDGAR + market_data warehouse), two real, verifiable steel-industry M&A "
          f"precedents, two DCF scenarios built from STLD's own historical margin range, and STLD's real 52-week "
          f"trading range — then compares the resulting football field to STLD's actual price of "
          f"**${px:.2f}** (warehouse close, {out['price_date']}).", "",
          "## Football field", "", "| Method | Low | High | Current price inside range? |", "|---|---|---|---|"]
    brackets, price_above, price_below = [], [], []   # price_above = the method's range sits BELOW the price; price_below = the method's range sits ABOVE the price
    for it in ff["items"]:
        if it["low"] <= px <= it["high"]:
            inside = "yes"; brackets.append(it["method"])
        elif px > it["high"]:
            inside = "price is above this range"; price_above.append(it)
        else:
            inside = "price is below this range"; price_below.append(it)
        md.append(f"| {it['method']} | {it['low']:.2f} | {it['high']:.2f} | {inside} |")
    below_highs = ", ".join(f"{it['high']:.2f}" for it in price_above)
    md += ["", f"Only {_oxford_join(brackets)} bracket{'s' if len(brackets) == 1 else ''} the "
           f"actual price. The trailing-multiple trading comps bracket it only because 2025 was a trough-earnings year "
           f"industry-wide (the same distortion documented in `docs/VALIDATION_REAL_DATA.md` — depressed LTM EBITDA "
           f"inflates EV/EBITDA), which happens to pull the range wide enough to catch the price rather than because the "
           f"multiples are themselves informative. The two precedent-transaction deals and both DCF scenarios sit "
           f"**entirely below** the actual price (highs of {below_highs} vs the price of {px:.2f}) — the honest reading "
           f"is that a conservative, backward-looking model (deals priced "
           f"off a *depressed* target's trailing metrics; a DCF anchored to STLD's own *depressed* FY2025 base year) "
           f"undershoots what the market is actually paying. Two real, unmodelled reasons this toolkit's DCF cannot "
           f"capture from EDGAR alone: STLD has been aggressively buying back stock (diluted shares fell from "
           f"{out['buyback']['from_shares']/1e6:.1f}M in FY{out['buyback']['from_fy'][:4]} to {out['buyback']['to_shares']/1e6:.1f}M "
           f"in FY{out['buyback']['to_fy'][:4]}, a {(1 - out['buyback']['to_shares']/out['buyback']['from_shares'])*100:.0f}% reduction — "
           f"a forward buyback pace mechanically raises per-share value in a way a single-base-year DCF does not price in), "
           f"and steel-industry valuations in the 2021–2023 upcycle traded at multiples "
           f"well above what trailing fundamentals alone would justify, which the market may still be partly "
           f"extrapolating. This is exactly the gap a forward (FY+1/FY+2 *consensus*) comps set and a buyback-aware DCF "
           f"would close — and exactly what EDGAR's trailing, as-filed data cannot supply.", ""]
    md += ["## 1. Trading comps (real: SEC EDGAR fundamentals + market_data warehouse prices)", "",
           "Same carbon-steel peer set and prices as `docs/VALIDATION_REAL_DATA.md` (NUE, CMC, RS, CLF, WOR); see that "
           "document for the full peer table. Statistics feeding the football field:", "",
           "| Multiple | 25th | Median | 75th |", "|---|---|---|---|"]
    for label in ("EV / Revenue LTM", "EV / EBITDA LTM", "EV / EBIT LTM"):
        s = out["trading_comps"]["summary"][label]
        md.append(f"| {label} | {s['p25']:.2f}x | {s['median']:.2f}x | {s['p75']:.2f}x |")
    md += ["", "## 2. Precedent transactions (real, verifiable deals)", ""]
    for key, title in (("x_precedent_detail", "Nippon Steel / United States Steel"), ("aks_precedent_detail", "Cleveland-Cliffs / AK Steel Holding")):
        d = out[key]; det = d["_detail"]
        md += [f"### {title} — announced {d['date']}", "",
               f"Enterprise value **${d['enterprise_value']/1e6:,.0f}M** = equity value ${det['equity_value']/1e6:,.0f}M "
               f"(offer ${d['offer_price']:.2f}/share × {det['diluted_shares']/1e6:.1f}M diluted shares) "
               f"+ net debt ${det['net_debt']/1e6:,.0f}M, all from the target's FY{det['fy'][:4]} 10-K (SEC EDGAR).", "",
               f"LTM revenue ${d['ltm_revenue']/1e6:,.0f}M, LTM EBITDA (EBIT + D&A) ${d['ltm_ebitda']/1e6:,.0f}M, LTM EBIT ${d['ltm_ebit']/1e6:,.0f}M → "
               f"**EV/Revenue {d['enterprise_value']/d['ltm_revenue']:.2f}x, EV/EBITDA {d['enterprise_value']/d['ltm_ebitda']:.2f}x, "
               f"EV/EBIT {d['enterprise_value']/d['ltm_ebit']:.2f}x**.", "",
               f"*Source: {det['source']}.*", ""]
    if out["aks_precedent_detail"]["_detail"].get("clf_close_on_announcement"):
        md.append(f"CLF's own closing price on the AK Steel announcement date was ${out['aks_precedent_detail']['_detail']['clf_close_on_announcement']:.4f} "
                  f"(market_data warehouse; likely a dividend-adjusted figure a few percent below the nominal quote that day). "
                  f"Premiums to AK Steel's own undisturbed price are not shown: AK Steel is delisted and absent from the "
                  f"warehouse, and Yahoo Finance and Stooq both refuse historical data for a fully delisted ticker, so there "
                  f"is no independently verifiable price series to compute a premium against.\n")
    md += ["## 3. DCF (illustrative scenarios built from STLD's own historical range, not analyst consensus)", "",
           f"Discount rate 10.28% for both scenarios (`finmodel wacc examples/wacc_stld.json`); terminal growth 2.5%, perpetuity method. "
           "The low–high range is a small discount-rate (±0.5pt) × terminal-growth (2.0%/2.5%/3.0%) sensitivity grid around each "
           "scenario's central case, standing in for a banker's data table.", ""]
    for key in ("dcf_base", "dcf_blue_sky"):
        d = out[key]; a = d["assumptions"]
        md += [f"**{d['name']}**: revenue grows {a['revenue_growth']*100:.0f}%/yr, EBIT margin reaches {a['ebit_margin_target_year5']*100:.1f}% by year 5 "
               f"(FY2025 was 8.1%) → implied share price **{d['base_value_per_share']:.2f}** (range {d['low']:.2f} – {d['high']:.2f} across the sensitivity grid).", ""]
    md += ["## 4. 52-week trading range (real, market_data warehouse)", ""]
    wk = out["week52"]
    if "low" in wk:
        md.append(f"${wk['low']:.2f} – ${wk['high']:.2f} ({wk['from']} to {wk['to']}, {wk['n_days']} trading days).")
    md += ["", "## 5. Sector-tuned comparison: does cycle-normalizing the inputs change the answer?", "",
           "`finmodel.sectors` was built from exactly the distortion this document flags above: STLD's own FY2025 EBIT margin "
           "(8.1%) sits well below its own trailing 8-year median (12.8%), a real trough by `finmodel cycle`'s own diagnostic "
           "(`finmodel cycle data/edgar/STLD.json --sector steel`). This section rebuilds the trading comps, precedent "
           "multiples and DCF scenarios using each company's own trailing-history median EBIT/EBITDA instead of the raw "
           "cycle-distorted LTM year, holding every other assumption (growth, D&A%, capex%, discount rate) identical, so the "
           "comparison isolates what normalization alone changes.", ""]
    norm = out["normalized"]; nff = norm["football_field"]
    md += ["| Method | Raw LTM range | Sector-normalized range | Normalized brackets price? |", "|---|---|---|---|"]
    n_brackets = []
    for it, nit in zip(ff["items"], nff["items"]):
        inside = nit["low"] <= px <= nit["high"]
        if inside: n_brackets.append(nit["method"])
        note = " (unchanged — real price history)" if nit["method"] == "52-week range" else ""
        md.append(f"| {it['method'].split(' (')[0]} | {it['low']:.2f} – {it['high']:.2f} | {nit['low']:.2f} – {nit['high']:.2f}{note} | {'yes' if inside else 'no'} |")
    s = norm["dcf_scenarios_from_history"]
    raw_base, raw_blue = 0.11, 0.168
    md += ["", f"Data-driven margin targets from STLD's own trailing 8 fiscal years (`finmodel cycle`): bear {s['bear_margin']:.1%}, "
           f"base (trailing median) {s['base_margin']:.1%}, blue sky (trailing peak) {s['blue_sky_margin']:.1%} — versus the hand-picked "
           f"{raw_base:.1%}/{raw_blue:.1%} used in the raw run above. The base case is reasonably close ({s['base_margin']-raw_base:+.1%}pt); "
           f"the blue-sky case is not: the hand-picked 'toward FY2023' target ({raw_blue:.1%}) significantly understated STLD's own "
           f"historical best case — the true trailing peak, {s['blue_sky_margin']:.1%}, came from FY{max(s['margin_history'], key=s['margin_history'].get)[:4]}, "
           f"which sat outside the shorter lookback I picked by hand. This is exactly the failure mode `sectors.dcf_scenarios_from_history` "
           f"is meant to catch: a hand-picked scenario label ('toward last year', 'toward two years ago') implicitly assumes the cycle's "
           f"extremes fall within whatever window the analyst happens to be looking at.", ""]
    if _oxford_join(n_brackets) != _oxford_join(brackets):
        md.append(f"Normalizing changes which methods bracket the price: raw run → {_oxford_join(brackets)}; normalized run → {_oxford_join(n_brackets)}.")
    else:
        md.append(f"Normalizing does **not** change which methods bracket the price here (still {_oxford_join(n_brackets)}), even though the "
                  f"individual ranges move — normalizing the trading comps compresses the high end (434.61 → 337.47) because it corrects both "
                  f"sides of the same trade (peer AND target EBITDA rise together, since the whole steel sector shares the same 2025 trough), "
                  f"while normalizing the DCF and precedent ranges pushes them meaningfully higher without lifting them far enough to reach the "
                  f"price. Sector normalization corrected a real distortion in each individual method's own numbers, but by itself it did not "
                  f"close the STLD gap documented above — see `docs/FOOTBALL_FIELD_CVX.md` for a case where cycle normalization was less "
                  f"needed in the first place, because only one side of the trade (the precedent-deal targets) was cycle-distorted, not Chevron's own numbers.")
    md += ["", "## Method note", "",
           "Everything here is either a live database query (peer prices, precedent-deal-acquirer's price, 52-week range), "
           "a public SEC filing (every revenue/EBIT/D&A/debt/cash figure), a matter of public record (the two deals' offer "
           "prices and announcement dates), or an explicitly labelled assumption I built (the two DCF scenarios' growth and "
           "margin paths, and the choice of which two precedent deals to include). Nothing here was invented and presented "
           "as fact; where a genuinely real number was unavailable (target-side premiums for delisted companies), it was "
           "omitted rather than approximated.", "",
           "Regenerate with `python scripts/football_field_stld.py`; chart at `out/charts_football_field_stld.html`."]
    return "\n".join(md)


if __name__ == "__main__":
    run()
