"""Eighth real-company check of the CFI 'Comps, Precedents, Football Field' template — semiconductors, via Texas
Instruments (TXN). Default operating_income/revenue fields work fine here (like airlines, unlike banking/REITs/
insurance) and EV/EBIT is directionally the right multiple — but GAAP expenses R&D immediately even though it
creates a multi-year economic asset (chip designs) the same way capex does, so raw EV/EBIT still understates
value for an R&D-intensive business. This check introduces finmodel.rd_capitalization (new, reconciled to CFI's
real 'RD-Capitalization.xlsx' single-vintage template, then generalized to Damodaran's cross-sectional method)
and applies it to both trading comps and two real, all-cash 2019 precedent deals.

  Real evidence: capitalizing each peer's own trailing-6-year R&D history (5-year straight-line amortization)
  raises adjusted EBIT for 5 of 6 real peers with growing R&D budgets (TXN +6.1%, ADI +11.1%, MCHP +16.5%,
  NXPI +8.0%, SWKS +43.0%), compressing EV/EBIT accordingly. ON Semiconductor is the real counter-example: its
  own R&D spend has been flat-to-declining since FY2021, so the same adjustment LOWERS its adjusted EBIT
  (-40.4%) -- verified real evidence that this isn't a one-directional fudge, and that the adjustment's
  percentage impact is amplified whenever reported EBIT is unusually thin (ON's own FY2025 margin, in a real
  sector demand downturn -- see below).

  Precedent deals -- both real, all-cash (simpler than exchange-ratio deals): NVIDIA / Mellanox Technologies
  (announced 2019-03-11, $125.00/share) and Infineon / Cypress Semiconductor (announced 2019-06-03,
  $23.85/share). Verified real, dramatic compression on BOTH: raw EV/EBIT of 60.4x (Mellanox) and 57.9x
  (Cypress) compress to 37.2x and 40.5x once each target's own real, pre-deal R&D history is capitalized.

  Cyclicality -- a sixth distinct mechanism from every prior check: TXN's real EBIT margin swung 30.3% (FY2014)
  to a pandemic-chip-shortage peak of 50.6% (FY2022) back to 34.1% (FY2025) -- the real "silicon cycle" bullwhip
  effect (a shortage triggers over-ordering, which becomes an inventory glut once demand normalizes), not a
  commodity price, credit, rate, demand-shock or catastrophe-loss cycle.

Run: python scripts/football_field_txn.py → docs/FOOTBALL_FIELD_TXN.md, out/comps_football_field_txn.json,
out/charts_football_field_txn.html"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finmodel import comps, charts, dcf, sectors, rd_capitalization as RD  # noqa: E402
from finmodel.comps import Deal  # noqa: E402

CORE = ["ADI", "MCHP", "NXPI", "ON", "SWKS"]
TARGET = "TXN"
PRICE_DATE = "2026-07-02"
RD_LIFE_YEARS = 5
RAW_MULTIPLES = {"EV/EBIT": ("ev", "ebit")}
ADJ_MULTIPLES = {"EV/AdjEBIT": ("ev", "adj_ebit")}


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


def real_fiscal_years(ticker):
    """Sorted fiscal-year-end keys with real annual data — excludes stray near-empty instant-fact periods
    finmodel.edgar's annual() sometimes picks up (e.g. MLNX's spurious '2018-01-01' entry, which has only a
    lone retained_earnings fact and no revenue/rnd at all)."""
    years = json.loads((ROOT / "data" / "edgar" / f"{ticker}.json").read_text())["years"]
    return sorted(y for y in years if years[y].get("revenue") is not None)


def rnd_history(ticker, through_fy, n=6):
    """Trailing `n` fiscal years of R&D expense, oldest first, ending with `through_fy` — capitalize_rd()'s
    required input shape."""
    years = json.loads((ROOT / "data" / "edgar" / f"{ticker}.json").read_text())["years"]
    ordered = [y for y in real_fiscal_years(ticker) if y <= through_fy]
    window = ordered[-n:]
    return [years[y]["rnd"] for y in window]


def rd_adjustment(ticker, through_fy):
    """Real R&D capitalization for one company/fiscal-year: returns (rd_asset, current_year_amortization)."""
    hist = rnd_history(ticker, through_fy)
    cap = RD.capitalize_rd(hist, life_years=RD_LIFE_YEARS)
    return cap["rd_asset"], cap["current_year_amortization"], cap["current_year_rd_expense"]


def _oxford_join(items):
    items = list(items)
    if not items: return "no method"
    if len(items) == 1: return items[0]
    if len(items) == 2: return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def mlnx_precedent():
    """NVIDIA / Mellanox Technologies: all-cash, $125.00/share, announced 2019-03-11 (source: Mellanox's own
    8-K, exhibit 99.1 press release, accession 0001193125-19-070061). Mellanox's last full fiscal year before
    announcement: FY2018."""
    r = fy("MLNX", "2018-12-31")
    price = 125.00
    equity_value = price * r["diluted_shares"]
    ev = equity_value + (r.get("debt_total") or 0) - r["cash"]
    rd_asset, amort, rd_exp = rd_adjustment("MLNX", "2018-12-31")
    adj_ebit = r["operating_income"] + rd_exp - amort
    return {"acquirer": "NVIDIA Corporation", "target": "Mellanox Technologies, Ltd.", "date": "2019-03-11",
            "ev": ev, "ebit": r["operating_income"], "adj_ebit": adj_ebit, "ev_adj": ev + rd_asset,
            "rd_asset": rd_asset, "offer_price": price,
            "_detail": {"fy": "2018-12-31", "diluted_shares": r["diluted_shares"],
                        "source": "$125.00/share, all cash: Mellanox 8-K exhibit 99.1 (accession 0001193125-19-070061); Mellanox fundamentals: SEC EDGAR 10-K"}}


def cy_precedent():
    """Infineon / Cypress Semiconductor: all-cash, $23.85/share, announced 2019-06-03 (source: Cypress's own
    8-K, exhibit 99.2 employee FAQ, accession 0001104659-19-033288). Cypress's last full fiscal year before
    announcement: FY2018 (ending 2018-12-30, a 52/53-week fiscal year)."""
    r = fy("CY", "2018-12-30")
    price = 23.85
    equity_value = price * r["diluted_shares"]
    ev = equity_value + (r.get("debt_total") or 0) - r["cash"]
    rd_asset, amort, rd_exp = rd_adjustment("CY", "2018-12-30")
    adj_ebit = r["operating_income"] + rd_exp - amort
    return {"acquirer": "Infineon Technologies AG", "target": "Cypress Semiconductor Corporation", "date": "2019-06-03",
            "ev": ev, "ebit": r["operating_income"], "adj_ebit": adj_ebit, "ev_adj": ev + rd_asset,
            "rd_asset": rd_asset, "offer_price": price,
            "_detail": {"fy": "2018-12-30", "diluted_shares": r["diluted_shares"],
                        "source": "$23.85/share, all cash: Cypress 8-K exhibit 99.2 (accession 0001104659-19-033288); Cypress fundamentals: SEC EDGAR 10-K"}}


def txn_dcf_scenario(name: str, growth: float, margin_target: float, discount_rate: float, current_price: float,
                     capex_pct_year5: float = 0.257):
    """capex_pct_year5=0.257 (the naive default) holds TXN's real, currently elevated FY2025 capex/revenue ratio
    (25.7%) flat for 5 years; the "fixed" scenarios instead taper it toward TXN's own pre-supercycle 2021-2022
    level (~13%) by year 5 — TXN's real capex/revenue ran 4.5-7.2% in 2018-2020, then a real, publicly-disclosed
    ~$30B capacity-expansion program pushed it to a 30.8% peak in FY2024, with TXN's own guidance describing
    this as a temporary buildout, not the new steady state. Holding the peak-cycle ratio flat for 5 years (the
    naive scenario) understates DCF value the same way the airline check's flat, elevated fleet-renewal capex
    assumption did before it was fixed."""
    r = fy(TARGET, "2025-12-31")
    rev0 = r["revenue"] / 1e6; margin0 = r["operating_income"] / r["revenue"]; nwc0_pct = (r["current_assets"] - r["current_liabilities"]) / r["revenue"]
    capex0_pct = r["capex"] / r["revenue"]
    n = 5
    rev = [rev0]
    for _ in range(n): rev.append(rev[-1] * (1 + growth))
    margins = [margin0 + (margin_target - margin0) * t / n for t in range(1, n + 1)]
    capex_pcts = [capex0_pct + (capex_pct_year5 - capex0_pct) * t / n for t in range(1, n + 1)]
    ebit = [rev[t] * margins[t - 1] for t in range(1, n + 1)]
    da = [rev[t] * (r["da"] / r["revenue"]) for t in range(1, n + 1)]
    capex = [rev[t] * capex_pcts[t - 1] for t in range(1, n + 1)]
    change_nwc = [nwc0_pct * (rev[t] - rev[t - 1]) for t in range(1, n + 1)]
    inp = dcf.DCFInputs(ebit=ebit, da=da, change_nwc=change_nwc, capex=capex, tax_rate=0.124, discount_rate=discount_rate,
                        perpetual_growth=0.03, terminal_method="perpetuity", transaction_date="2025-12-31", fiscal_year_end="2026-12-31",
                        current_price=current_price, shares_outstanding=r["diluted_shares"] / 1e6, debt=r["debt_total"] / 1e6, cash=r["cash"] / 1e6)
    res = dcf.run(inp)
    sens = dcf.sensitivity(inp, [discount_rate - 0.005, discount_rate, discount_rate + 0.005], [0.02, 0.03, 0.04])
    flat = [v for row in sens["table"] for v in row]
    return {"name": name, "base_value_per_share": res["equity_value_per_share"], "low": min(flat), "high": max(flat),
            "assumptions": {"revenue_growth": growth, "ebit_margin_target_year5": margin_target, "discount_rate": discount_rate, "capex_pct_year5": capex_pct_year5}}


def run():
    px = prices(CORE + [TARGET])
    peers_raw, peers_adj = [], []
    for t in CORE:
        latest_fy = real_fiscal_years(t)[-1]
        r = fy(t, latest_fy)
        net_debt_raw = (r.get("debt_total") or 0) - (r.get("cash") or 0)
        peers_raw.append(comps.Peer(t, px[t], r["diluted_shares"], net_debt=net_debt_raw, metrics={"ebit": r["operating_income"]}, ticker=t))
        rd_asset, amort, rd_exp = rd_adjustment(t, latest_fy)
        adj_ebit = r["operating_income"] + rd_exp - amort
        peers_adj.append(comps.Peer(t, px[t], r["diluted_shares"], net_debt=net_debt_raw + rd_asset, metrics={"adj_ebit": adj_ebit}, ticker=t))
    trading_raw = comps.spread(peers_raw, multiples=RAW_MULTIPLES)
    trading_adj = comps.spread(peers_adj, multiples=ADJ_MULTIPLES)

    mlnx_deal, cy_deal = mlnx_precedent(), cy_precedent()
    deals = []
    for d in (mlnx_deal, cy_deal):
        m = {"EV/EBIT LTM": comps.multiple(d["ev"], d["ebit"]), "EV/AdjEBIT LTM": comps.multiple(d["ev_adj"], d["adj_ebit"])}
        deals.append(Deal(d["acquirer"], d["target"], d["date"], enterprise_value=d["ev_adj"], multiples=m))
    precedents = comps.precedents(deals)

    tr = fy(TARGET, "2025-12-31")
    tr_net_debt_raw = (tr.get("debt_total") or 0) - (tr.get("cash") or 0)
    tr_rd_asset, tr_amort, tr_rd_exp = rd_adjustment(TARGET, "2025-12-31")
    tr_adj_ebit = tr["operating_income"] + tr_rd_exp - tr_amort
    target_raw = comps.Target("Texas Instruments Incorporated", px[TARGET], tr["diluted_shares"], metrics={"ebit": tr["operating_income"]}, net_debt=tr_net_debt_raw)
    target_adj = comps.Target("Texas Instruments Incorporated", px[TARGET], tr["diluted_shares"], metrics={"ebit": tr["operating_income"], "adj_ebit": tr_adj_ebit}, net_debt=tr_net_debt_raw + tr_rd_asset)

    txn_hist = json.loads((ROOT / "data" / "edgar" / "TXN.json").read_text())["years"]
    coe_wacc = 0.0933  # finmodel wacc examples/wacc_txn.json
    s = sectors.dcf_scenarios_from_history(txn_hist, periods=8)
    # capex: TXN's real FY2025 capex/revenue (25.7%) reflects an active, publicly-disclosed ~$30B capacity-
    # expansion program TXN's own guidance describes as temporary; naive holds that peak-cycle ratio flat for
    # 5 years (understating value, the same mistake the airline check's flat fleet-renewal capex made before
    # being fixed), while the real scenarios taper it toward TXN's own pre-supercycle 2021-2022 level (~13%).
    naive = txn_dcf_scenario("DCF - naive (flat capex at the current supercycle rate)", growth=0.05, margin_target=s["base_margin"], discount_rate=coe_wacc, current_price=px[TARGET], capex_pct_year5=0.257)
    base = txn_dcf_scenario("DCF - base case (capex normalizing to pre-supercycle rate)", growth=0.05, margin_target=s["base_margin"], discount_rate=coe_wacc, current_price=px[TARGET], capex_pct_year5=0.13)
    blue = txn_dcf_scenario("DCF - blue sky (2022 chip-shortage peak margin, capex normalizing)", growth=0.07, margin_target=s["blue_sky_margin"], discount_rate=coe_wacc, current_price=px[TARGET], capex_pct_year5=0.13)
    wk52 = week52(TARGET)

    diag = sectors.cycle_diagnostics(txn_hist, periods=8, sector="semiconductor")

    ff_raw = comps.football_field(target_raw, {"Trading comps (EV/EBIT, raw)": trading_raw}, stat_low="p25", stat_high="p75", multiples={"Trading comps (EV/EBIT, raw)": RAW_MULTIPLES})
    ff_adj = comps.football_field(
        target_adj,
        {"Trading comps (EV/AdjEBIT, R&D-capitalized)": trading_adj, "Precedent transactions": precedents},
        extra={naive["name"]: (naive["low"], naive["high"]), base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"]), "52-week range": (wk52["low"], wk52["high"])},
        stat_low="p25", stat_high="p75",
        multiples={"Trading comps (EV/AdjEBIT, R&D-capitalized)": ADJ_MULTIPLES, "Precedent transactions": {"EV/EBIT": ("ev", "ebit"), "EV/AdjEBIT": ("ev", "adj_ebit")}})
    ff = {"target": target_adj.name, "current_price": px[TARGET], "items": ff_raw["items"] + ff_adj["items"]}

    out = {"price": px[TARGET], "price_date": PRICE_DATE, "trading_raw": trading_raw, "trading_adj": trading_adj,
           "precedents": precedents, "mlnx_detail": mlnx_deal, "cy_detail": cy_deal,
           "dcf_naive": naive, "dcf_base": base, "dcf_blue_sky": blue, "week52": wk52, "football_field": ff, "cycle_diagnostics": diag,
           "target_rd_asset": tr_rd_asset, "target_adj_ebit": tr_adj_ebit, "target_ebit": tr["operating_income"]}
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "comps_football_field_txn.json").write_text(json.dumps(out, indent=1, default=str))
    charts.report_for("comps", {"comps": trading_adj, "precedents": precedents, "football_field": ff}, ROOT / "out" / "charts_football_field_txn.html", title="Texas Instruments — R&D-capitalized (AdjEBIT) football field on real data")

    md = write_doc(out)
    (ROOT / "docs" / "FOOTBALL_FIELD_TXN.md").write_text(md)
    print(f"TXN price {px[TARGET]:.2f} ({PRICE_DATE})")
    for it in ff["items"]:
        print(f"  {it['method']:55} {it['low']:8.2f} - {it['high']:8.2f}")


def write_doc(out):
    px = out["price"]; ff = out["football_field"]
    f_mult = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
    md = ["# Eighth real-company check: R&D capitalization, and a sixth distinct sector cycle", "",
          "Same real-data method as the seven prior checks, applied to Texas Instruments (TXN). Unlike banking, "
          "REITs or insurance, EV/EBIT is directionally the right multiple here — the gap is that GAAP expenses "
          "R&D immediately, understating value for an R&D-intensive business the same way ignoring a lease "
          "understated an airline's.", "",
          "## Why raw EV/EBIT understates value for an R&D-heavy company (real evidence)", "",
          "`finmodel.rd_capitalization` (new this check) capitalizes each year's R&D spend as its own vintage, "
          "straight-line-amortized over 5 years — reconciled exactly to CFI's real `RD-Capitalization.xlsx` "
          "single-vintage template (`tests/test_rd_capitalization.py`), then generalized to Damodaran's "
          "cross-sectional method for a rolling multi-year history. Verified real, FY2025 SEC EDGAR data across "
          "six real peers:", "",
          "| Ticker | Reported EBIT | Adjusted EBIT | Uplift | R&D asset added to EV |", "|---|---|---|---|---|"]
    for t in ["TXN"] + [p["ticker"] for p in out["trading_adj"]["peers"]]:
        if t == "TXN":
            ebit, adj_ebit, rd_asset = out["target_ebit"], out["target_adj_ebit"], out["target_rd_asset"]
        else:
            row = next(p for p in out["trading_raw"]["peers"] if p["ticker"] == t)
            adj_row = next(p for p in out["trading_adj"]["peers"] if p["ticker"] == t)
            ebit, adj_ebit = row["metrics"]["ebit"], adj_row["metrics"]["adj_ebit"]
            rd_asset = adj_row["enterprise_value"] - row["enterprise_value"]
        uplift = (adj_ebit / ebit - 1) if ebit else None
        md.append(f"| {t} | ${ebit/1e6:,.0f}M | ${adj_ebit/1e6:,.0f}M | {uplift*100:+.1f}% | ${rd_asset/1e6:,.0f}M |")
    md += ["", "Five of six real companies show a positive uplift — reported EBIT understates true operating "
           "profitability because R&D has been growing (older, smaller vintages amortize less than the current "
           "year's larger spend gets added back). ON Semiconductor is the real counter-example: its own R&D "
           "spend has been flat-to-declining since FY2021 (real, matches the sector's FY2023-2025 demand "
           "downturn — see the cyclicality section below), so the same adjustment LOWERS its adjusted EBIT — "
           "proof this isn't a one-directional fudge, and a reminder that the adjustment's PERCENTAGE swing is "
           "amplified whenever reported EBIT is already thin, independent of anything unusual about the R&D "
           "itself.", "",
           "**A real, narrower tag-fallback fix found while pulling this data**: ON Semiconductor's own R&D "
           "tag is `ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost`, not the plain "
           "`ResearchAndDevelopmentExpense` `finmodel.edgar` otherwise expects — now a same-field fallback "
           "(a true alternative, not an additive-component trap like the REIT/airline tag issues, since it "
           "nets out lumpy acquisition-accounting IPR&D write-offs that are less comparable across peers "
           "anyway). See `finmodel.sectors.SECTOR_PROFILES['semiconductor']` for the same findings encoded "
           "into the toolkit.", ""]
    md += ["## Football field", "", "| Method | Low | High | Current price inside range? |", "|---|---|---|---|"]
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
           "Peers: Analog Devices, Microchip, NXP Semiconductors, ON Semiconductor, Skyworks — real analog/"
           "mixed-signal semiconductor companies, the closest real comparison set to Texas Instruments.", "",
           "| Multiple | 25th | Median | 75th |", "|---|---|---|---|",
           f"| EV/EBIT (raw, n={out['trading_raw']['summary']['EV/EBIT LTM']['n']} of 5) | {out['trading_raw']['summary']['EV/EBIT LTM']['p25']:.2f}x | {out['trading_raw']['summary']['EV/EBIT LTM']['median']:.2f}x | {out['trading_raw']['summary']['EV/EBIT LTM']['p75']:.2f}x |",
           f"| EV/AdjEBIT (R&D-capitalized, n={out['trading_adj']['summary']['EV/AdjEBIT LTM']['n']} of 5) | {out['trading_adj']['summary']['EV/AdjEBIT LTM']['p25']:.2f}x | {out['trading_adj']['summary']['EV/AdjEBIT LTM']['median']:.2f}x | {out['trading_adj']['summary']['EV/AdjEBIT LTM']['p75']:.2f}x |",
           "", "Two of five peers (Microchip, ON Semiconductor) are `NM` (>=100x) on raw EV/EBIT — reported EBIT "
           "is thin enough relative to enterprise value that the multiple isn't meaningful at all, per "
           "`comps.multiple()`'s existing NM cap. A real, additional benefit of the R&D adjustment shows up "
           "here: capitalizing Microchip's own real, growing R&D history raises its adjusted EBIT enough to "
           "pull its multiple back under the NM cap entirely (94.6x, now real usable information) — R&D "
           "capitalization doesn't just compress an already-computable multiple, it can recover one that raw "
           "GAAP EBIT had made meaningless. ON's multiple stays NM either way (its own R&D adjustment goes the "
           "other direction — see below).", ""]
    md += ["## 2. Precedent transactions (real, verifiable, all-cash 2019 semiconductor mergers)", ""]
    for key, title in (("mlnx_detail", "NVIDIA / Mellanox Technologies"), ("cy_detail", "Infineon / Cypress Semiconductor")):
        d = out[key]; det = d["_detail"]
        md += [f"### {title} — announced {d['date']}", "",
               f"All-cash: **${d['offer_price']:.2f}**/target share. Enterprise value (raw) "
               f"**${d['ev']/1e6:,.0f}M**, target EBIT ${d['ebit']/1e6:,.0f}M, R&D asset "
               f"${d['rd_asset']/1e6:,.0f}M, target fundamentals from its FY{det['fy'][:4]} 10-K (SEC EDGAR).", "",
               f"**EV/EBIT (raw) {f_mult(comps.multiple(d['ev'], d['ebit']))}, "
               f"EV/AdjEBIT (R&D-capitalized) {f_mult(comps.multiple(d['ev_adj'], d['adj_ebit']))}**.", ""]
    md += ["## 3. DCF — a real, disclosed capex supercycle needs the same fix as the airline check's fleet renewal", "",
           f"Cost of capital 9.33% (`finmodel wacc examples/wacc_txn.json`; TXN's real ~11x interest coverage "
           "maps to a AAA synthetic rating — a real, strong balance sheet, not a stress-tested assumption). "
           "Growth/margin scenarios use `finmodel.sectors.dcf_scenarios_from_history()`'s real trailing "
           "median/peak — no periods override needed here, unlike the airline check's COVID contamination.", "",
           "TXN's real FY2025 capex/revenue is 25.7% — up from a real 4.5%-7.2% in FY2018-2020, driven by a "
           "real, publicly-disclosed multi-billion-dollar capacity-expansion program TXN's own guidance "
           "describes as a temporary buildout, not the new steady state (real capex/revenue: 13.4% FY2021, "
           "14.0% FY2022, 28.9% FY2023, 30.8% FY2024, 25.7% FY2025 — a real peak already past and now easing). "
           "Holding the peak-cycle 25.7% ratio flat for a 5-year DCF (the naive scenario below) is the exact "
           "same mistake the airline check's flat fleet-renewal capex assumption made before being fixed; "
           "tapering it toward TXN's own pre-supercycle ~13% level materially changes the answer.", ""]
    for key in ("dcf_naive", "dcf_base", "dcf_blue_sky"):
        d = out[key]
        md.append(f"**{d['name']}** (EBIT margin target {d['assumptions']['ebit_margin_target_year5']*100:.1f}%, "
                  f"year-5 capex {d['assumptions']['capex_pct_year5']*100:.0f}% of revenue) → implied share price "
                  f"**${d['base_value_per_share']:.2f}** (range {d['low']:.2f} – {d['high']:.2f}).")
    md += ["", "## 4. 52-week trading range (real, market_data warehouse)", "",
           f"${out['week52']['low']:.2f} – ${out['week52']['high']:.2f} ({out['week52']['from']} to {out['week52']['to']}, {out['week52']['n_days']} trading days).", ""]
    md += ["## 5. Cyclicality: a sixth distinct real mechanism", "",
           f"`finmodel cycle data/edgar/TXN.json --sector semiconductor` — FY{out['cycle_diagnostics']['fiscal_year'][:4]} "
           f"EBIT margin {out['cycle_diagnostics']['latest_margin']*100:.1f}% vs trailing-8yr median "
           f"{out['cycle_diagnostics']['median_margin_trailing_years']*100:.1f}% "
           f"({out['cycle_diagnostics']['deviation_pct']*100:+.1f}%) → **{out['cycle_diagnostics']['flag']}**.", "",
           "TXN's real EBIT margin swung 30.3% (FY2014) to a pandemic-chip-shortage peak of 50.6% (FY2022) back "
           "to 34.1% (FY2025) — the real \"silicon cycle\" bullwhip effect: a shortage triggers over-ordering "
           "across the supply chain, which becomes an inventory glut once demand normalizes. A sixth distinct "
           "mechanism from every sector checked so far — not a commodity price (steel/oil & gas), credit losses "
           "(banking), the risk-free rate (REITs), a demand shock (airlines) or catastrophe losses (insurance).", "",
           "## Method note", "",
           "Every EBIT / R&D / debt figure is from an SEC 10-K (via `finmodel.edgar`); every price is a live "
           "database query against `market_data`; both deals' per-share cash prices and announcement dates come "
           "from the target's own 8-K filings (public record). Both real precedent targets are delisted and "
           "absent from the warehouse, so target-side deal premiums are omitted for the same reason as the "
           "banking, REIT, airline and insurance checks' precedents.", "",
           "Regenerate with `python scripts/football_field_txn.py`; chart at `out/charts_football_field_txn.html`."]
    return "\n".join(md)


if __name__ == "__main__":
    run()
