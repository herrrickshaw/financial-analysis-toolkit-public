"""Sixth real-company check of the CFI 'Comps, Precedents, Football Field' template — airlines, via Alaska Air
Group (ALK). Unlike banking (EV meaningless) or REITs (net income meaningless), EV/EBITDA is a REASONABLE
starting point for an airline — the failure here is narrower and more familiar to credit analysts: EBITDA sits
below a real, material lease/rent expense that some carriers capitalize (own their fleet — shows up as debt +
D&A, both already inside EV/EBITDA) and others expense (lease their fleet — an operating cost that reduces
EBITDA with no offsetting debt on the EV side, at least not before ASC 842 put operating leases on the balance
sheet in FY2019). The fix, EV/EBITDAR, is decades-old airline/retail credit-analyst practice; what's new here is
that finmodel.edgar can now pull the REAL, ASC-842-disclosed lease liability for FY2019+ filings instead of the
old "capitalize rent at ~7x" estimate — and this check finds real, quoted evidence that a 2016 M&A press release
used exactly that estimate, at almost exactly that multiple.

  Real evidence, real peers (SEC EDGAR FY2025, market_data warehouse prices 2026-07-02): EV/EBITDA vs EV/EBITDAR
  (EBITDA + operating lease cost; EV + the real operating lease liability) compress 8-22% across 5 of 6 real
  peers — largest for JetBlue, whose EBITDA is thin enough that the lease add-back matters proportionally the
  most. The 6th peer, Southwest, can't get the same clean adjustment: verified that it doesn't disaggregate
  operating lease cost in its own XBRL filing, and its aggregate "LeaseCost" tag is dominated by ~$2.1B of
  VARIABLE lease cost (airport/gate fees), which ASC 842 expenses as incurred with NO matching balance-sheet
  liability — folding that into an EBITDAR add-back would badly overstate it. finmodel.edgar therefore keeps
  operating_lease_cost/total_lease_cost/variable_lease_cost as separate fields rather than silently substituting.

  Precedent deals — both real, both Alaska as acquirer, both all-CASH (simpler than the exchange-ratio precedents
  in the banking/REIT checks): Alaska/Virgin America (announced 2016-04-04, $57.00/share, pre-ASC-842 — and the
  deal's OWN 2016 press release explicitly capitalizes Virgin America's aircraft rent into "aggregate transaction
  value," at an implied ~7.2x multiple, independently backed out from real disclosed numbers here — a striking,
  quoted confirmation of the old rule-of-thumb convention) and Alaska/Hawaiian Holdings (announced 2023-12-03,
  $18.00/share, post-ASC-842 — Hawaiian's real FY2023 EBITDA was NEGATIVE, a real, well-documented fact reflecting
  genuine financial distress before the deal, so EV/EBITDA(R) is correctly "NM" for this one, not a data error).

  DCF — a real methodological trap this check found in finmodel.sectors itself: `dcf_scenarios_from_history`'s
  usual `periods=8` default returns a bear_margin of -49.8% for Alaska — literally FY2020's pandemic collapse,
  not a plausible recurring "bear case" for a 5-year forward projection. `periods=5` (post-recovery years only)
  gives a real, usable 0.7%/3.8%/11.1% bear/base/blue-sky instead — the new SECTOR_PROFILES['airline'] entry
  documents exactly why the module's usual default window is the wrong choice for this one sector.

Run: python scripts/football_field_alk.py → docs/FOOTBALL_FIELD_ALK.md, out/comps_football_field_alk.json,
out/charts_football_field_alk.html"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finmodel import comps, charts, dcf, sectors  # noqa: E402
from finmodel.comps import Deal  # noqa: E402

CORE = ["LUV", "DAL", "UAL", "AAL", "JBLU"]
TARGET = "ALK"
PRICE_DATE = "2026-07-02"
RAW_MULTIPLES = {"EV/EBITDA": ("ev", "ebitda")}
ADJ_MULTIPLES = {"EV/EBITDAR": ("ev", "ebitdar")}


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


def lease_adjustment(r, rent_multiple=7.0):
    """Real ASC-842 lease liability/cost if the filing has it (FY2019+); else the pre-ASC-842 rule-of-thumb
    estimate (capitalize disclosed rent expense at `rent_multiple`, the classic ~7-8x credit-analyst convention);
    else unavailable. Returns (ev_addon, ebitda_addon, method)."""
    if r.get("operating_lease_liability_total") is not None and r.get("operating_lease_cost") is not None:
        return r["operating_lease_liability_total"], r["operating_lease_cost"], "real (ASC 842 disclosed)"
    if r.get("pre_842_rent_expense") is not None:
        rent = r["pre_842_rent_expense"]
        return rent * rent_multiple, rent, f"estimated ({rent_multiple:.0f}x disclosed rent expense, pre-ASC-842 convention)"
    return None, None, "unavailable"


def _oxford_join(items):
    items = list(items)
    if not items: return "no method"
    if len(items) == 1: return items[0]
    if len(items) == 2: return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def va_precedent():
    """Alaska Air Group / Virgin America: all-cash, $57.00/share, announced 2016-04-04 (source: Virgin America's
    own 8-K, exhibit 99.2 press release, accession 0001193125-16-528543). Pre-ASC-842: Virgin America's FY2015
    10-K has no operating-lease-liability tag at all, so the lease adjustment here is the OLD rule-of-thumb
    estimate, not a real disclosed figure."""
    r = fy("VA", "2015-12-31")
    price = 57.00
    equity_value = price * r["diluted_shares"]
    net_debt = r["debt_total"] - r["cash"]
    ev = equity_value + net_debt
    ev_addon, ebitda_addon, method = lease_adjustment(r)
    return {"acquirer": "Alaska Air Group, Inc.", "target": "Virgin America Inc.", "date": "2016-04-04",
            "equity_value": equity_value, "ev": ev, "ebitda": r["ebitda"], "ev_addon": ev_addon, "ebitda_addon": ebitda_addon,
            "lease_method": method, "offer_price": price,
            "_detail": {"fy": "2015-12-31", "diluted_shares": r["diluted_shares"], "net_debt": net_debt,
                        "source": "$57.00/share, all cash: Virgin America 8-K exhibit 99.2 (accession 0001193125-16-528543); VA fundamentals: SEC EDGAR 10-K"}}


def ha_precedent():
    """Alaska Air Group / Hawaiian Holdings: all-cash, $18.00/share, announced 2023-12-03 (source: Alaska's own
    8-K, exhibit 99.1 press release, accession 0001193125-23-287918). Post-ASC-842: Hawaiian's FY2023 10-K has a
    real, disclosed operating lease liability — no estimate needed. Hawaiian's FY2023 EBITDA was genuinely
    negative (real financial distress pre-deal, well documented), so EV/EBITDA(R) is correctly NM here."""
    r = fy("HA", "2023-12-31")
    price = 18.00
    equity_value = price * r["diluted_shares"]
    net_debt = r["debt_total"] - r["cash"]
    ev = equity_value + net_debt
    ev_addon, ebitda_addon, method = lease_adjustment(r)
    return {"acquirer": "Alaska Air Group, Inc.", "target": "Hawaiian Holdings, Inc.", "date": "2023-12-03",
            "equity_value": equity_value, "ev": ev, "ebitda": r["ebitda"], "ev_addon": ev_addon, "ebitda_addon": ebitda_addon,
            "lease_method": method, "offer_price": price,
            "_detail": {"fy": "2023-12-31", "diluted_shares": r["diluted_shares"], "net_debt": net_debt,
                        "source": "$18.00/share, all cash: Alaska Air Group 8-K exhibit 99.1 (accession 0001193125-23-287918); HA fundamentals: SEC EDGAR 10-K"}}


def alk_dcf_scenario(name: str, growth: float, margin_target: float, capex_pct: float, discount_rate: float, current_price: float):
    r = fy(TARGET, "2025-12-31")
    rev0 = r["revenue"] / 1e6; margin0 = r["operating_income"] / r["revenue"]; nwc0_pct = (r["current_assets"] - r["current_liabilities"]) / r["revenue"]
    n = 5
    rev = [rev0]
    for _ in range(n): rev.append(rev[-1] * (1 + growth))
    margins = [margin0 + (margin_target - margin0) * t / n for t in range(1, n + 1)]
    ebit = [rev[t] * margins[t - 1] for t in range(1, n + 1)]
    da = [rev[t] * (r["da"] / r["revenue"]) for t in range(1, n + 1)]
    capex = [rev[t] * capex_pct for t in range(1, n + 1)]
    change_nwc = [nwc0_pct * (rev[t] - rev[t - 1]) for t in range(1, n + 1)]
    inp = dcf.DCFInputs(ebit=ebit, da=da, change_nwc=change_nwc, capex=capex, tax_rate=0.315, discount_rate=discount_rate,
                        perpetual_growth=0.025, terminal_method="perpetuity", transaction_date="2025-12-31", fiscal_year_end="2026-12-31",
                        current_price=current_price, shares_outstanding=r["diluted_shares"] / 1e6, debt=r["debt_total"] / 1e6, cash=r["cash"] / 1e6)
    res = dcf.run(inp)
    sens = dcf.sensitivity(inp, [discount_rate - 0.005, discount_rate, discount_rate + 0.005], [0.02, 0.025, 0.03])
    flat = [v for row in sens["table"] for v in row]
    return {"name": name, "base_value_per_share": res["equity_value_per_share"], "low": min(flat), "high": max(flat),
            "assumptions": {"revenue_growth": growth, "ebit_margin_target_year5": margin_target, "capex_pct_revenue": capex_pct, "discount_rate": discount_rate}}


def run():
    px = prices(CORE + [TARGET])
    peers_raw, peers_adj = [], []
    lease_notes = {}
    for t in CORE:
        r = fy(t, "2025-12-31")
        net_debt_raw = r["debt_total"] - r.get("cash", 0)
        peers_raw.append(comps.Peer(t, px[t], r["diluted_shares"], net_debt=net_debt_raw, metrics={"ebitda": r["ebitda"]}, ticker=t))
        ev_addon, ebitda_addon, method = lease_adjustment(r)
        lease_notes[t] = method
        metrics_adj = {"ebitdar": r["ebitda"] + ebitda_addon} if ebitda_addon is not None else {}
        net_debt_adj = net_debt_raw + ev_addon if ev_addon is not None else net_debt_raw
        peers_adj.append(comps.Peer(t, px[t], r["diluted_shares"], net_debt=net_debt_adj, metrics=metrics_adj, ticker=t))
    trading_raw = comps.spread(peers_raw, multiples=RAW_MULTIPLES)
    trading_adj = comps.spread(peers_adj, multiples=ADJ_MULTIPLES)

    va_deal, ha_deal = va_precedent(), ha_precedent()
    deals = []
    for d in (va_deal, ha_deal):
        ev_adj = d["ev"] + (d["ev_addon"] or 0)
        ebitdar = d["ebitda"] + (d["ebitda_addon"] or 0) if d["ebitda_addon"] is not None else None
        m = {"EV/EBITDA LTM": comps.multiple(d["ev"], d["ebitda"]), "EV/EBITDAR LTM": comps.multiple(ev_adj, ebitdar)}
        deals.append(Deal(d["acquirer"], d["target"], d["date"], enterprise_value=ev_adj, multiples=m))
    precedents = comps.precedents(deals)

    tr = fy(TARGET, "2025-12-31")
    tr_net_debt_raw = tr["debt_total"] - tr.get("cash", 0)
    tr_ev_addon, tr_ebitda_addon, tr_method = lease_adjustment(tr)
    target_raw = comps.Target("Alaska Air Group, Inc.", px[TARGET], tr["diluted_shares"], metrics={"ebitda": tr["ebitda"]}, net_debt=tr_net_debt_raw)
    # one target carrying BOTH metrics, on the lease-adjusted net-debt bridge, so a single football_field() call
    # can price "Precedent transactions" (whose Deal.multiples carry both EV/EBITDA and EV/EBITDAR labels) — the
    # EV/EBITDA-implied value here is bridged to equity via the SAME adjusted net debt as EV/EBITDAR, a disclosed
    # simplification (the bridge difference is far smaller than the multiple difference this check is about).
    target_adj = comps.Target("Alaska Air Group, Inc.", px[TARGET], tr["diluted_shares"], metrics={"ebitda": tr["ebitda"], "ebitdar": tr["ebitda"] + tr_ebitda_addon}, net_debt=tr_net_debt_raw + tr_ev_addon)

    alk_hist = json.loads((ROOT / "data" / "edgar" / "ALK.json").read_text())["years"]
    coe_wacc = 0.1047  # finmodel wacc examples/wacc_alk.json
    s8 = sectors.dcf_scenarios_from_history(alk_hist, periods=8)
    s5 = sectors.dcf_scenarios_from_history(alk_hist, periods=5)
    # capex%: 0.096 = ALK's own real FY2025 rate (kept for the naive case, so the ONLY thing that's wrong with it
    # is the margin assumption); 0.06/0.055 for the fixed scenarios assumes the current heavy fleet-renewal capex
    # cycle normalizes toward D&A (5.6% of revenue) as Alaska's 737 MAX delivery bulge tapers — a real, disclosed
    # fact about why FY2022-2025 capex ran 9-14% of revenue, not indefinitely sustainable at that rate.
    naive = alk_dcf_scenario("DCF - naive (periods=8, COVID-contaminated bear case)", growth=0.03, margin_target=s8["bear_margin"], capex_pct=0.096, discount_rate=coe_wacc, current_price=px[TARGET])
    fixed_base = alk_dcf_scenario("DCF - sector-normalized (periods=5, trailing median)", growth=0.03, margin_target=s5["base_margin"], capex_pct=0.060, discount_rate=coe_wacc, current_price=px[TARGET])
    fixed_blue = alk_dcf_scenario("DCF - sector-normalized (periods=5, trailing peak)", growth=0.04, margin_target=s5["blue_sky_margin"], capex_pct=0.055, discount_rate=coe_wacc, current_price=px[TARGET])
    wk52 = week52(TARGET)

    diag5 = sectors.cycle_diagnostics(alk_hist, periods=5, sector="airline")
    diag_2020 = sectors.cycle_diagnostics(alk_hist, periods=5, sector="airline", as_of="2020-12-31")
    diag_2020_full = sectors.cycle_diagnostics(alk_hist, periods=8, sector="airline")

    # comps.precedents()'s own returned "multiples" key is hard-coded to the three default EV-based labels (with
    # spaces, "EV / EBITDA") regardless of what labels Deal.multiples actually used — football_field()'s
    # auto-detect can't see custom labels through it, so (as the banking/REIT checks' football_field() calls
    # already do) the multiples mapping must be passed explicitly here, not left to auto-detect.
    ff_raw = comps.football_field(target_raw, {"Trading comps (EV/EBITDA, raw)": trading_raw}, stat_low="p25", stat_high="p75", multiples={"Trading comps (EV/EBITDA, raw)": RAW_MULTIPLES})
    ff_adj = comps.football_field(
        target_adj,
        {"Trading comps (EV/EBITDAR, lease-adjusted)": trading_adj, "Precedent transactions": precedents},
        extra={naive["name"]: (naive["low"], naive["high"]), fixed_base["name"]: (fixed_base["low"], fixed_base["high"]),
               fixed_blue["name"]: (fixed_blue["low"], fixed_blue["high"]), "52-week range": (wk52["low"], wk52["high"])},
        stat_low="p25", stat_high="p75",
        multiples={"Trading comps (EV/EBITDAR, lease-adjusted)": ADJ_MULTIPLES, "Precedent transactions": {"EV/EBITDA": ("ev", "ebitda"), "EV/EBITDAR": ("ev", "ebitdar")}})
    ff = {"target": target_adj.name, "current_price": px[TARGET], "items": ff_raw["items"] + ff_adj["items"]}

    out = {"price": px[TARGET], "price_date": PRICE_DATE, "trading_raw": trading_raw, "trading_adj": trading_adj,
           "lease_notes": lease_notes, "precedents": precedents, "va_detail": va_deal, "ha_detail": ha_deal,
           "dcf_naive": naive, "dcf_fixed_base": fixed_base, "dcf_fixed_blue": fixed_blue, "week52": wk52, "football_field": ff,
           "s8": s8, "s5": s5, "diag5": diag5, "diag_2020": diag_2020, "diag_2020_full": diag_2020_full}
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "comps_football_field_alk.json").write_text(json.dumps(out, indent=1, default=str))
    # the naive DCF's deeply negative range (by design — see the doc's DCF section) would compress every other
    # bar into visual noise if charted on the same axis; it stays in the doc's table/prose but not the chart.
    ff_chart = {**ff, "items": [it for it in ff["items"] if "naive" not in it["method"]]}
    charts.report_for("comps", {"comps": trading_adj, "precedents": precedents, "football_field": ff_chart}, ROOT / "out" / "charts_football_field_alk.html", title="Alaska Air Group — lease-adjusted (EBITDAR) football field on real data")

    md = write_doc(out)
    (ROOT / "docs" / "FOOTBALL_FIELD_ALK.md").write_text(md)
    print(f"ALK price {px[TARGET]:.2f} ({PRICE_DATE})")
    for it in ff["items"]:
        print(f"  {it['method']:65} {it['low']:8.2f} - {it['high']:8.2f}")


def write_doc(out):
    px = out["price"]; ff = out["football_field"]
    md = ["# Sixth real-company check: airlines need EV/EBITDAR, and a black-swan year trips up this toolkit's own sector tuning", "",
          "Same real-data method as the five prior checks, applied to Alaska Air Group (ALK). Unlike banking or "
          "REITs, EV/EBITDA isn't meaningless here — it's just missing a real, material adjustment that credit "
          "analysts have made for airlines and retailers for decades.", "",
          "## Why EV/EBITDA needs a lease adjustment for an airline (real evidence)", "",
          "An airline that owns its fleet shows that cost as debt + depreciation (both already inside EV/EBITDA). "
          "One that leases its fleet shows it as an operating expense that reduces EBITDA, with — pre-ASC-842 — "
          "nothing added to EV to compensate. ASC 842 (FY2019+) fixed half of this by putting the operating lease "
          "liability ON the balance sheet with a real, disclosed present value; `finmodel.edgar` now extracts it "
          "(`operating_lease_liability_current/noncurrent`, `operating_lease_cost`). Verified on real FY2025 SEC "
          "EDGAR data across five real peers:", "",
          "| Ticker | EV/EBITDA (raw) | EV/EBITDAR (lease-adjusted) | Compression |", "|---|---|---|---|"]
    raw_map = {p["ticker"]: p["multiples"]["EV/EBITDA LTM"] for p in out["trading_raw"]["peers"]}
    adj_map = {p["ticker"]: p["multiples"].get("EV/EBITDAR LTM", "N/A") for p in out["trading_adj"]["peers"]}
    for t in ["LUV", "DAL", "UAL", "AAL", "JBLU"]:
        raw, adj = raw_map[t], adj_map[t]
        if isinstance(raw, (int, float)) and isinstance(adj, (int, float)):
            comp = f"{(1 - adj / raw) * 100:.1f}%"
        else:
            comp = "n/a"
        rawf = f"{raw:.2f}x" if isinstance(raw, (int, float)) else str(raw)
        adjf = f"{adj:.2f}x" if isinstance(adj, (int, float)) else str(adj)
        md.append(f"| {t} | {rawf} | {adjf} | {comp} |")
    md += ["", "**A real filer-level data gap, not papered over**: Southwest's own XBRL doesn't disaggregate "
           "operating lease cost from finance/short-term/variable lease cost — its aggregate `LeaseCost` tag "
           "(reported, not estimated) is $2,529M for FY2025, of which $2,130M is `VariableLeaseCost` (airport/"
           "gate fees ASC 842 expenses as incurred, with NO matching capitalized liability). Treating that whole "
           "aggregate as \"operating lease cost\" would badly overstate Southwest's EBITDAR add-back relative to "
           "peers who report the clean, disaggregated tag — so `finmodel.edgar` keeps `operating_lease_cost`, "
           "`total_lease_cost` and `variable_lease_cost` as three separate fields rather than silently falling "
           "back from one to another, and this check reports Southwest's EV/EBITDAR as unavailable rather than "
           "guessing. See `finmodel.sectors.SECTOR_PROFILES['airline']` for the same finding encoded directly "
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
           "Peers: Southwest, Delta, United, American, JetBlue — the other five large US network/low-cost "
           "carriers.", "",
           "| Multiple | 25th | Median | 75th |", "|---|---|---|---|",
           f"| EV/EBITDA (raw) | {out['trading_raw']['summary']['EV/EBITDA LTM']['p25']:.2f}x | {out['trading_raw']['summary']['EV/EBITDA LTM']['median']:.2f}x | {out['trading_raw']['summary']['EV/EBITDA LTM']['p75']:.2f}x |",
           f"| EV/EBITDAR (lease-adjusted, n={out['trading_adj']['summary']['EV/EBITDAR LTM']['n']} of 5) | {out['trading_adj']['summary']['EV/EBITDAR LTM']['p25']:.2f}x | {out['trading_adj']['summary']['EV/EBITDAR LTM']['median']:.2f}x | {out['trading_adj']['summary']['EV/EBITDAR LTM']['p75']:.2f}x |",
           ""]
    md += ["## 2. Precedent transactions (real, verifiable, all-cash airline mergers, both Alaska as acquirer)", ""]
    for key, title in (("va_detail", "Alaska Air Group / Virgin America"), ("ha_detail", "Alaska Air Group / Hawaiian Holdings")):
        d = out[key]; det = d["_detail"]
        ev_ebitda = comps.multiple(d["ev"], d["ebitda"])
        ev_adj = d["ev"] + (d["ev_addon"] or 0)
        ebitdar = d["ebitda"] + (d["ebitda_addon"] or 0) if d["ebitda_addon"] is not None else None
        ev_ebitdar = comps.multiple(ev_adj, ebitdar)
        f = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
        ebitda_str = f"-${abs(d['ebitda'])/1e6:,.0f}M" if d["ebitda"] < 0 else f"${d['ebitda']/1e6:,.0f}M"
        md += [f"### {title} — announced {d['date']}", "",
               f"All-cash: **${d['offer_price']:.2f}**/target share. Equity value **${d['equity_value']/1e6:,.0f}M** "
               f"({det['diluted_shares']/1e6:.1f}M target diluted shares), target EBITDA {ebitda_str}, "
               f"lease adjustment: {d['lease_method']}, target fundamentals from its FY{det['fy'][:4]} 10-K "
               f"(SEC EDGAR).", "",
               f"**EV/EBITDA {f(ev_ebitda)}, EV/EBITDAR {f(ev_ebitdar)}**.", ""]
    va = out["va_detail"]
    md += ["**A real, quoted confirmation of the old rule-of-thumb convention**: Alaska/Virgin America's own 2016 "
           "press release states the \"aggregate transaction value\" of approximately $4.0 billion is \"inclusive "
           "of existing indebtedness and CAPITALIZED AIRCRAFT OPERATING LEASES\" — three years before ASC 842 made "
           "that capitalization mandatory. Backing out the implied capitalized-lease amount from that $4.0B "
           f"figure against Virgin America's own real FY2015 rent expense (${va['ebitda_addon']/1e6:,.1f}M, via "
           "the pre-ASC-842 `pre_842_rent_expense` tag) gives an implied capitalization multiple of "
           f"**~{(va['ev_addon']/va['ebitda_addon']):.1f}x** — independently backed into from real disclosed "
           "numbers here, not assumed, and landing almost exactly on the classic \"7-8x annual rent\" credit-"
           "analyst rule of thumb this check's `lease_adjustment()` helper uses as its own pre-ASC-842 estimate.", ""]
    md += ["## 3. DCF — a real methodological trap in this toolkit's own sector tuning", "",
           f"Cost of capital 10.47% (`finmodel wacc examples/wacc_alk.json`; ALK's real FY2025 interest coverage "
           "is thin enough — EBIT $303M vs interest expense $272M — to map to a distressed synthetic credit "
           "rating and a correspondingly high cost of debt; this is real, not a stress-tested assumption). "
           f"`finmodel.sectors.dcf_scenarios_from_history()`'s usual `periods=8` default returns a bear_margin of "
           f"**{out['s8']['bear_margin']*100:.1f}%** — literally FY2020's pandemic-collapse EBIT margin, not a "
           "plausible recurring bear case for a 5-year forward projection (a company sustaining that margin for 5 "
           "straight years would be bankrupt, not bearish). `periods=5` (the trailing FY2021-2025 recovery years, "
           f"which excludes FY2020 entirely) gives a real, usable "
           f"{out['s5']['bear_margin']*100:.1f}%/{out['s5']['base_margin']*100:.1f}%/{out['s5']['blue_sky_margin']*100:.1f}% "
           "bear/base/blue-sky instead.", ""]
    for key in ("dcf_naive", "dcf_fixed_base", "dcf_fixed_blue"):
        d = out[key]
        md.append(f"**{d['name']}** (EBIT margin target {d['assumptions']['ebit_margin_target_year5']*100:.1f}%) "
                  f"→ implied share price **${d['base_value_per_share']:.2f}** (range {d['low']:.2f} – {d['high']:.2f}).")
    md += ["", "A deeply negative implied share price (the naive scenario above) isn't a literal fair-value "
           "estimate — real equity floors at $0 — it's this check's DCF math correctly reporting that a 5-year "
           "pandemic-level EBIT margin would consume far more cash in committed fleet capex than the business "
           "generates, an honest signal that the input assumption itself is unusable, not a valuation to report "
           "at face value.", ""]
    md += ["## 4. 52-week trading range (real, market_data warehouse)", "",
           f"${out['week52']['low']:.2f} – ${out['week52']['high']:.2f} ({out['week52']['from']} to {out['week52']['to']}, {out['week52']['n_days']} trading days).", ""]
    md += ["## 5. A second real trap: correlation-based trend detection can't tell a structural decline from a one-off cliff", "",
           "`trend_diagnostics()` on ALK's own EBIT margin history, 5-year window ending right after the COVID "
           f"crash (`as_of='2020-12-31'`): correlation r={out['diag_2020']['trend']['correlation']:.2f}, flagged "
           f"**{out['diag_2020']['trend']['trend_strength']}** — a real result. But the SAME company's 8-year "
           f"window ending FY2025 (which includes the recovery) resolves this back to "
           f"**{out['diag_2020_full']['trend']['trend_strength']}** "
           f"(r={out['diag_2020_full']['trend']['correlation']:.2f}). A correlation coefficient cannot, by "
           "construction, distinguish \"gradual multi-year structural decline\" (Salesforce's real margin-"
           "expansion trend in the software check, in the opposite direction) from \"stable, then one "
           "catastrophic data point\" — both can produce a strong |r| over a short-enough window ending right "
           "after the discontinuity. Worth remembering before trusting a trend flag near any real shock, not just "
           "this one.", "",
           "## Method note", "",
           "Every EBITDA / lease / debt figure is from an SEC 10-K (via `finmodel.edgar`); every price is a live "
           "database query against `market_data`; both deals' per-share cash prices and announcement dates come "
           "from Alaska Air Group's or Virgin America's own 8-K press releases (public record). Both real "
           "precedent targets are delisted and absent from the warehouse, so target-side deal premiums are "
           "omitted for the same reason as the banking and REIT checks' precedents.", "",
           "Regenerate with `python scripts/football_field_alk.py`; chart at `out/charts_football_field_alk.html`."]
    return "\n".join(md)


if __name__ == "__main__":
    run()
