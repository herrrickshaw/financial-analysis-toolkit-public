"""Tenth real-company check of the CFI 'Comps, Precedents, Football Field' template — pharmaceuticals, via
AbbVie (ABBV). The real, sector-defining finding is different from every prior check: AbbVie's own real Humira
patent-cliff (US exclusivity lost in 2023) is genuine and large (global Humira revenue $21.2B in 2022 -> $14.4B
in 2023 -> $8.99B in 2024, AbbVie's own real disclosed figures) — but AbbVie's TOTAL revenue kept GROWING through
it (58.1B -> 54.3B -> 56.3B -> 61.2B, FY2022-2025) because its own real, disclosed Skyrizi+Rinvoq replacement
franchise grew faster than Humira eroded (combined ~$16B in 2024 -> $25.9B in 2025, guided to $31B by 2027). A
naive "patent cliff means the company falls off a cliff" DCF assumption is real for a single-product biotech (see
the Seagen precedent below) but WRONG for a diversified major pharma with a real, funded pipeline.

  Two further real, verified findings: (1) a genuine EDGAR extraction gap — AbbVie's (and Merck's) own "da" tag
  resolves all the way down to plain PP&E `Depreciation` with none of finmodel.edgar's combined tags ever
  populated, silently dropping real, material intangible amortization ($7.4B of AbbVie's real $8.1B FY2025 total
  — now fixed as a real additive component, `finmodel.edgar`'s TAGS['amortization_of_intangibles']). (2) AbbVie's
  own real, GAAP-mandated acquired-in-process-R&D write-offs (ASC 730-10-25-2c — expensed immediately, no
  alternative future use) distort a single year's reported operating margin the way a restructuring charge would:
  a real $5.0B charge in FY2025 alone compresses reported operating margin by 8.2 percentage points (24.6% ->
  32.8% adjusted) — a real, lumpy, ACQUISITION-driven distortion, mechanically different from the semiconductor
  check's ORGANIC R&D capitalization, and a direct, natural real-world use case for this toolkit's own
  `finmodel.ppa_valuation`/`finmodel.impairment_testing` modules (both built from the same Big 4 market survey
  that flagged acquired-IPR&D accounting as a real automation topic).

  A third, unrelated real finding surfaced while pulling live prices: the `market_data` warehouse carries TWO
  rows per trading day for ABBV specifically (250 of the last 260 trading days) — an older, unadjusted batch
  never purged after a newer, dividend-adjusted reload (batch_id 4 vs 7, loaded a day apart) — the exact same
  class of bug this repo's own recent `fix: stop the OHLC cache serving stale frames as today's price` commit
  fixed elsewhere, now found in a second table. Fixed here by de-duplicating on the latest `batch_id` per date.

  What this script does — reusing existing generic engines, no new comps/valuation code:
  Trading comps    — the standard EV/Revenue, EV/EBITDA, EV/EBIT, P/E framework (no override needed, like
                     airlines/semiconductors/utilities) for Pfizer, Merck, Bristol-Myers Squibb, Eli Lilly.
  Precedent deals  — two real, verifiable, all-cash 2022-2023 biotech acquisitions with a deliberate real
                     contrast: Pfizer/Seagen (a genuinely pre-profitability, negative-EBIT growth biotech — only
                     EV/Revenue is usable) and Amgen/Horizon Therapeutics (a profitable specialty pharma — the
                     full multiple set works).
  DCF              — unlevered DCF via finmodel.dcf, WACC from `finmodel wacc examples/wacc_abbv.json` (7.33%),
                     margin scenarios from ABBV's own IPR&D-ADJUSTED history (trend_diagnostics() correctly shows
                     a genuinely weak trend once the acquired-IPR&D noise is removed, so the GENERIC
                     `dcf_scenarios_from_history()` trailing min/median/max is appropriate here — unlike the
                     DUK/TRV/CSCO checks, no trend-guard override is needed once the right adjustment is made).
  52-week range    — the real trailing 252-trading-day high/low from the warehouse, de-duplicated by batch.

Run: python scripts/football_field_abbv.py -> docs/FOOTBALL_FIELD_ABBV.md, out/comps_football_field_abbv.json,
out/charts_football_field_abbv.html"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finmodel import comps, charts, dcf, sectors  # noqa: E402
from finmodel.comps import Deal  # noqa: E402

CORE = ["PFE", "MRK", "BMY", "LLY"]
TARGET = "ABBV"
PRICE_DATE = "2026-07-02"


def prices(tickers):
    # DISTINCT ON ... ORDER BY date, batch_id DESC: a real fix, not cosmetic -- see the module docstring's third
    # finding. Without it, ABBV's own duplicate-batch rows make a plain "date = X" lookup return an arbitrary one
    # of two different (raw vs dividend-adjusted) close prices.
    out = subprocess.run(["psql", "-d", "market_data", "-Atc",
                          f"select distinct on (s.ticker) s.ticker, h.close_price from ohlcv_history h join stocks s on s.stock_id=h.stock_id "
                          f"where s.market_id=2 and s.ticker in ({','.join(repr(t) for t in tickers)}) and h.date='{PRICE_DATE}' "
                          f"order by s.ticker, h.batch_id desc"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    return {l.split("|")[0]: float(l.split("|")[1]) for l in out.splitlines() if l}


def week52(ticker):
    out = subprocess.run(["psql", "-d", "market_data", "-Atc",
                          f"with d as (select distinct on (h.date) h.date, h.close_price from ohlcv_history h join stocks s on s.stock_id=h.stock_id "
                          f"where s.market_id=2 and s.ticker='{ticker}' order by h.date, h.batch_id desc), "
                          f"r as (select date, close_price, row_number() over (order by date desc) rn from d) "
                          f"select min(close_price), max(close_price), min(date), max(date), count(*) from r where rn<=252"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    lo, hi, d0, d1, n = out.split("|")
    return {"low": float(lo), "high": float(hi), "from": d0, "to": d1, "n_days": int(n)}


def fy(ticker, fy_end):
    return json.loads((ROOT / "data" / "edgar" / f"{ticker}.json").read_text())["years"][fy_end]


def pharma_metrics(r):
    return {"revenue": r["revenue"], "ebitda": r["operating_income"] + r["da"], "ebit": r["operating_income"], "net_income": r["net_income"]}


def seagen_precedent():
    """Pfizer / Seagen: all-cash, $229.00/share, announced 2023-03-13 (Pfizer's own 8-K, exhibit 99.1 press
    release). Seagen's last full fiscal year before announcement: FY2022 -- a real, genuinely negative operating
    income (-$613M) AND negative EBITDA (-$566M, its own D&A of $47M isn't enough to turn it positive) for a
    still-scaling, pre-profitability oncology biotech -- both EV/EBIT and EV/EBITDA are correctly NM here, not a
    data error; EV/Revenue is the only usable multiple for this specific deal. Seagen carries no reported
    corporate debt at all (a real, clean biotech balance sheet -- verified no LongTermDebt/ConvertibleDebt tag is
    populated), so net debt is simply negative cash."""
    r = fy("SGEN", "2022-12-31")
    price = 229.00
    equity_value = price * r["diluted_shares"]
    net_debt = (r.get("debt_total") or 0) - r["cash"]
    ev = equity_value + net_debt
    m = pharma_metrics(r)
    return {"acquirer": "Pfizer Inc.", "target": "Seagen Inc.", "date": "2023-03-13",
            "enterprise_value": ev, "ltm_revenue": m["revenue"], "ltm_ebitda": m["ebitda"], "ltm_ebit": m["ebit"], "ltm_net_income": m["net_income"],
            "offer_price": price, "_detail": {"fy": "2022-12-31", "equity_value": equity_value, "net_debt": net_debt, "diluted_shares": r["diluted_shares"],
                                               "source": "$229.00/share, all cash: Pfizer 8-K exhibit 99.1; Seagen fundamentals: SEC EDGAR 10-K"}}


def horizon_precedent():
    """Amgen / Horizon Therapeutics: all-cash, $116.50/share, announced 2022-12-12 (Amgen's own 8-K, exhibit 99.1
    press release). Horizon's last full fiscal year before announcement: FY2021 -- a real, profitable specialty
    pharma (17% operating margin), a deliberate contrast to Seagen's pre-profitability profile within the same
    broader pharma/biotech M&A wave."""
    r = fy("HZNP", "2021-12-31")
    price = 116.50
    equity_value = price * r["diluted_shares"]
    net_debt = r["debt_total"] - r["cash"]
    ev = equity_value + net_debt
    m = pharma_metrics(r)
    return {"acquirer": "Amgen Inc.", "target": "Horizon Therapeutics Public Limited Company", "date": "2022-12-12",
            "enterprise_value": ev, "ltm_revenue": m["revenue"], "ltm_ebitda": m["ebitda"], "ltm_ebit": m["ebit"], "ltm_net_income": m["net_income"],
            "offer_price": price, "_detail": {"fy": "2021-12-31", "equity_value": equity_value, "net_debt": net_debt, "diluted_shares": r["diluted_shares"],
                                               "source": "$116.50/share, all cash: Amgen 8-K exhibit 99.1; Horizon fundamentals: SEC EDGAR 10-K"}}


def abbv_dcf_scenario(name, growth, margin_target, discount_rate, current_price):
    """Margin targets come from ABBV's own IPR&D-adjusted operating-margin history (adjusted_operating_income,
    precomputed into data/edgar/ABBV.json), not the raw GAAP figure -- using the raw figure would let a real,
    one-time acquisition charge (see the module docstring) masquerade as a genuine margin deterioration."""
    r = fy(TARGET, "2025-12-31")
    rev0 = r["revenue"] / 1e6; margin0 = r["adjusted_operating_income"] / r["revenue"]; nwc0_pct = (r["current_assets"] - r["current_liabilities"]) / r["revenue"]
    capex0_pct = r["capex"] / r["revenue"]
    n = 5
    rev = [rev0]
    for _ in range(n): rev.append(rev[-1] * (1 + growth))
    margins = [margin0 + (margin_target - margin0) * t / n for t in range(1, n + 1)]
    ebit = [rev[t] * margins[t - 1] for t in range(1, n + 1)]
    da = [rev[t] * (r["da"] / r["revenue"]) for t in range(1, n + 1)]
    capex = [rev[t] * capex0_pct for t in range(1, n + 1)]
    change_nwc = [nwc0_pct * (rev[t] - rev[t - 1]) for t in range(1, n + 1)]
    inp = dcf.DCFInputs(ebit=ebit, da=da, change_nwc=change_nwc, capex=capex, tax_rate=0.358, discount_rate=discount_rate,
                        perpetual_growth=0.03, terminal_method="perpetuity", transaction_date="2025-12-31", fiscal_year_end="2026-12-31",
                        current_price=current_price, shares_outstanding=r["diluted_shares"] / 1e6, debt=r["debt_total"] / 1e6, cash=r["cash"] / 1e6)
    res = dcf.run(inp)
    sens = dcf.sensitivity(inp, [discount_rate - 0.005, discount_rate, discount_rate + 0.005], [0.02, 0.03, 0.04])
    flat = [v for row in sens["table"] for v in row]
    return {"name": name, "base_value_per_share": res["equity_value_per_share"], "low": min(flat), "high": max(flat),
            "assumptions": {"revenue_growth": growth, "adjusted_ebit_margin_target_year5": margin_target, "discount_rate": discount_rate}}


def run():
    px = prices(CORE + [TARGET])
    peers = []
    for t in CORE:
        r = fy(t, "2025-12-31")
        net_debt = r["debt_total"] - r["cash"]
        peers.append(comps.Peer(t, px[t], r["diluted_shares"], net_debt=net_debt, metrics=pharma_metrics(r), ticker=t))
    trading = comps.spread(peers)

    sgen, hznp = seagen_precedent(), horizon_precedent()
    deals = [Deal(sgen["acquirer"], sgen["target"], sgen["date"], sgen["enterprise_value"], ltm_revenue=sgen["ltm_revenue"], ltm_ebitda=sgen["ltm_ebitda"], ltm_ebit=sgen["ltm_ebit"]),
             Deal(hznp["acquirer"], hznp["target"], hznp["date"], hznp["enterprise_value"], ltm_revenue=hznp["ltm_revenue"], ltm_ebitda=hznp["ltm_ebitda"], ltm_ebit=hznp["ltm_ebit"])]
    precedents = comps.precedents(deals)

    tr = fy(TARGET, "2025-12-31")
    net_debt_target = tr["debt_total"] - tr["cash"]
    target = comps.Target("AbbVie Inc.", px[TARGET], tr["diluted_shares"], metrics=pharma_metrics(tr), net_debt=net_debt_target)

    coe_wacc = 0.0733  # finmodel wacc examples/wacc_abbv.json
    abbv_hist = json.loads((ROOT / "data" / "edgar" / "ABBV.json").read_text())["years"]
    scn = sectors.dcf_scenarios_from_history(abbv_hist, field="adjusted_operating_income", revenue_field="revenue", periods=8)

    bear = abbv_dcf_scenario("DCF - bear (2%/yr growth, trailing-8yr min adjusted margin)", growth=0.02, margin_target=scn["bear_margin"], discount_rate=coe_wacc, current_price=px[TARGET])
    base = abbv_dcf_scenario("DCF - base (6%/yr growth, trailing-8yr median adjusted margin)", growth=0.06, margin_target=scn["base_margin"], discount_rate=coe_wacc, current_price=px[TARGET])
    blue = abbv_dcf_scenario("DCF - blue sky (9%/yr growth, trailing-8yr max adjusted margin)", growth=0.09, margin_target=scn["blue_sky_margin"], discount_rate=coe_wacc, current_price=px[TARGET])
    wk52 = week52(TARGET)

    ff = comps.football_field(target, {"Trading comps": trading, "Precedent transactions": precedents},
                              extra={base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"]), "52-week range": (wk52["low"], wk52["high"])},
                              stat_low="p25", stat_high="p75")

    normalized = build_normalized(abbv_hist)
    iprd_history = build_iprd_history(abbv_hist)
    humira_offset = build_humira_offset()

    out = {"price": px[TARGET], "price_date": PRICE_DATE, "trading_comps": trading, "precedents": precedents,
           "sgen_detail": sgen, "hznp_detail": hznp, "dcf_bear": bear, "dcf_base": base, "dcf_blue_sky": blue, "week52": wk52, "football_field": ff,
           "dcf_scenarios_from_history": scn, "normalized": normalized, "iprd_history": iprd_history, "humira_offset": humira_offset}
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "comps_football_field_abbv.json").write_text(json.dumps(out, indent=1, default=str))
    charts.report_for("comps", {"comps": trading, "precedents": precedents, "football_field": ff}, ROOT / "out" / "charts_football_field_abbv.html", title="AbbVie — pharmaceuticals football field on real data")

    md = write_doc(out)
    (ROOT / "docs" / "FOOTBALL_FIELD_ABBV.md").write_text(md)
    print(f"ABBV price {px[TARGET]:.2f} ({PRICE_DATE})")
    for it in ff["items"]:
        print(f"  {it['method']:60} {it['low']:8.2f} - {it['high']:8.2f}")


def build_normalized(abbv_hist):
    diag_raw = sectors.cycle_diagnostics(abbv_hist, field="operating_income", revenue_field="revenue", periods=8, sector="pharma")
    trend_raw = sectors.trend_diagnostics(abbv_hist, field="operating_income", revenue_field="revenue", periods=8)
    diag_adj = sectors.cycle_diagnostics(abbv_hist, field="adjusted_operating_income", revenue_field="revenue", periods=8, sector="pharma")
    trend_adj = sectors.trend_diagnostics(abbv_hist, field="adjusted_operating_income", revenue_field="revenue", periods=8)
    return {"raw": {"cycle_diagnostics": diag_raw, "trend_diagnostics": trend_raw}, "adjusted": {"cycle_diagnostics": diag_adj, "trend_diagnostics": trend_adj}}


def build_iprd_history(abbv_hist):
    rows = []
    for y in sorted(abbv_hist)[-6:]:
        r = abbv_hist[y]
        if not r.get("revenue") or r.get("acquired_iprd_writeoff") is None:
            continue
        rows.append({"fy": y, "acquired_iprd_writeoff": r["acquired_iprd_writeoff"], "iprd_pct_revenue": r["acquired_iprd_writeoff"] / r["revenue"],
                     "reported_margin": r["operating_income"] / r["revenue"], "adjusted_margin": r["adjusted_operating_income"] / r["revenue"]})
    return rows


def build_humira_offset():
    """Real, publicly disclosed AbbVie figures (its own quarterly/annual earnings releases), not derivable from
    EDGAR's standard XBRL tags -- product-level revenue isn't tagged the way consolidated revenue is."""
    return {"humira_global_revenue": {"2022": 21237000000, "2023": 14401000000, "2024": 8993000000},
            "skyrizi_rinvoq_combined_revenue": {"2024": 16000000000, "2025": 25900000000},
            "skyrizi_rinvoq_2027_guidance": 31000000000,
            "abbv_total_revenue": {"2022": 58054000000, "2023": 54318000000, "2024": 56334000000, "2025": 61160000000}}


def write_doc(out):
    px = out["price"]; ff = out["football_field"]
    md = ["# Tenth real-company check: a real patent cliff, offset by a real pipeline — and two real data-plumbing bugs found along the way", "",
          "Same real-data method as the nine prior checks, applied to AbbVie (ABBV). Like airlines/semiconductors/"
          "utilities, the standard EV-based comps framework needs no override here — the real story is a genuine "
          "patent cliff that didn't sink the company, plus a real GAAP accounting quirk for acquisitive pharma "
          "and two real bugs (one in `finmodel.edgar`, one in the `market_data` warehouse) found while building "
          "this check.", "",
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
           "Peers: Pfizer, Merck, Bristol-Myers Squibb, Eli Lilly — real large-cap US pharmaceutical companies.", "",
           "| Ticker | Price | EV/Revenue | EV/EBITDA | EV/EBIT | P/E |", "|---|---|---|---|---|---|"]
    for p in out["trading_comps"]["peers"]:
        f = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
        md.append(f"| {p['ticker']} | {p['price']:.2f} | {f(p['multiples']['EV / Revenue LTM'])} | {f(p['multiples']['EV / EBITDA LTM'])} | {f(p['multiples']['EV / EBIT LTM'])} | {f(p['multiples']['P / E LTM'])} |")
    md += ["", "| Multiple | 25th | Median | 75th |", "|---|---|---|---|"]
    for label in ("EV / Revenue LTM", "EV / EBITDA LTM", "EV / EBIT LTM", "P / E LTM"):
        s = out["trading_comps"]["summary"][label]
        md.append(f"| {label.replace(' LTM', '')} | {s['p25']:.2f}x | {s['median']:.2f}x | {s['p75']:.2f}x |")
    md += ["", "## 2. Precedent transactions (real, verifiable, all-cash 2022-2023 biotech mergers — a deliberate profitability contrast)", ""]
    f_mult = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
    for key, title in (("sgen_detail", "Pfizer / Seagen"), ("hznp_detail", "Amgen / Horizon Therapeutics")):
        d = out[key]; det = d["_detail"]
        ni_str = f"-${abs(d['ltm_net_income'])/1e6:,.0f}M" if d["ltm_net_income"] < 0 else f"${d['ltm_net_income']/1e6:,.0f}M"
        md += [f"### {title} — announced {d['date']}", "",
               f"All-cash: **${d['offer_price']:.2f}**/target share. Equity value ${det['equity_value']/1e6:,.0f}M "
               f"({det['diluted_shares']/1e6:.1f}M target diluted shares) + net debt ${det['net_debt']/1e6:,.0f}M "
               f"= enterprise value **${d['enterprise_value']/1e6:,.0f}M**, target fundamentals from its FY{det['fy'][:4]} 10-K (SEC EDGAR).", "",
               f"**EV/Revenue {f_mult(comps.multiple(d['enterprise_value'], d['ltm_revenue']))}, "
               f"EV/EBITDA {f_mult(comps.multiple(d['enterprise_value'], d['ltm_ebitda']))}, "
               f"EV/EBIT {f_mult(comps.multiple(d['enterprise_value'], d['ltm_ebit']))}** (target net income {ni_str}).", ""]
    md += ["Seagen's real FY2022 operating income (-$613M) AND EBITDA (-$566M) are both genuinely negative — a "
           "still-scaling, pre-profitability oncology biotech, not a data error — so EV/EBIT and EV/EBITDA are "
           "correctly NM for that $42B real deal; EV/Revenue (~21x) is the only usable multiple. Horizon "
           "Therapeutics, by contrast, was solidly profitable (17% operating margin) at the time of its own real "
           "$27B deal — the full multiple set applies there. A single 'pharma M&A multiple' doesn't exist; it "
           "depends entirely on whether the target has reached profitability yet.", ""]
    md += ["## 3. The real, sector-defining finding: a genuine patent cliff, offset by a genuine pipeline", "",
           "Real, publicly disclosed AbbVie figures (its own earnings releases — product revenue isn't tagged in "
           "standard EDGAR XBRL the way consolidated revenue is):", "",
           "| | 2022 | 2023 | 2024 | 2025 |", "|---|---|---|---|---|"]
    ho = out["humira_offset"]
    md.append("| Humira (global) | $" + f"{ho['humira_global_revenue']['2022']/1e9:.1f}B | $"
              + f"{ho['humira_global_revenue']['2023']/1e9:.1f}B | $" + f"{ho['humira_global_revenue']['2024']/1e9:.1f}B | — |")
    md.append("| Skyrizi + Rinvoq (combined) | — | — | $" + f"{ho['skyrizi_rinvoq_combined_revenue']['2024']/1e9:.1f}B | $"
              + f"{ho['skyrizi_rinvoq_combined_revenue']['2025']/1e9:.1f}B |")
    md.append("| AbbVie total revenue | $" + f"{ho['abbv_total_revenue']['2022']/1e9:.1f}B | $"
              + f"{ho['abbv_total_revenue']['2023']/1e9:.1f}B | $" + f"{ho['abbv_total_revenue']['2024']/1e9:.1f}B | $"
              + f"{ho['abbv_total_revenue']['2025']/1e9:.1f}B |")
    md += ["", "Humira lost US patent exclusivity in 2023 and its real global revenue collapsed by more than half "
           "in two years — a genuine, severe patent cliff, exactly the risk pharma equity research spends years "
           "modeling. But AbbVie's TOTAL revenue never fell by more than 6.4% in any single year and fully "
           "recovered within two — because its own real, disclosed Skyrizi+Rinvoq replacement franchise "
           "(management's own stated decade-long strategy) grew from roughly $16B to $25.9B in a single year, "
           "with 2027 guidance raised to a combined $31B. The real lesson for pharma DCF/comps work: a naive "
           "'assume the flagship product's patent cliff sinks the company' assumption is right for a single-"
           "product biotech (Seagen, above, has no such offset to fall back on) and WRONG for a diversified major "
           "pharma with a real, funded pipeline — the two require genuinely different treatment, not the same "
           "haircut applied uniformly.", ""]
    md += ["## 4. A real GAAP quirk this toolkit's own PPA/impairment modules are built for: acquired IPR&D write-offs", "",
           "| FY | Acquired IPR&D write-off | % of revenue | Reported margin | IPR&D-adjusted margin |", "|---|---|---|---|---|"]
    for r in out["iprd_history"]:
        md.append(f"| {r['fy'][:4]} | ${r['acquired_iprd_writeoff']/1e6:,.0f}M | {r['iprd_pct_revenue']*100:.1f}% | {r['reported_margin']*100:.1f}% | {r['adjusted_margin']*100:.1f}% |")
    md += ["", "Real, GAAP-mandated (ASC 730-10-25-2c): in-process R&D acquired via an asset acquisition with no "
           "alternative future use is expensed immediately, not capitalized. AbbVie's own real FY2025 charge "
           "($5.0B, from its 2024-closed ImmunoGen and Cerevel Therapeutics acquisitions) alone compresses "
           "reported operating margin by 8.2 percentage points versus the adjusted figure — a real, lumpy, "
           "ACQUISITION-driven distortion, mechanically different from the semiconductor check's capitalization "
           "of ORGANIC R&D spend (`finmodel.rd_capitalization`): that module amortizes a real multi-year asset "
           "GAAP expenses too early; this charge is a real one-time cost that GAAP correctly expenses all at "
           "once, and normalizing it means adding it BACK for comps purposes (like a restructuring charge), not "
           "amortizing it forward. This is the exact real automation topic `finmodel.ppa_valuation` and "
           "`finmodel.impairment_testing` (built from this toolkit's own Big 4 market survey, "
           "docs/BIG4_AUTOMATION.md) exist for — the acquired assets behind these write-offs are the same "
           "category of intangible a real ASC 805 purchase price allocation values.", ""]
    md += ["## 5. A real, verified EDGAR extraction gap this check found and fixed: `finmodel.edgar`'s \"da\" tag", "",
           "AbbVie's own `da` figure resolved all the way down to the narrow `Depreciation` tag (PP&E only, "
           "$762M for FY2025) because none of `finmodel.edgar`'s combined D&A tags were ever populated for this "
           "filer — silently dropping AbbVie's real, separately-tagged `AmortizationOfIntangibleAssets` ($7,377M "
           "for FY2025, ~10x the PP&E depreciation alone, and real given AbbVie's ~$63B Allergan acquisition "
           "alone). Merck shows the exact same real gap (`AmortizationOfIntangibleAssets` = $2.8B for FY2025, "
           "invisible to the old extraction). Now fixed as a real additive component in `finmodel.edgar` — "
           "summed into `da` only when the tag actually picked was the narrow `Depreciation` one, since a "
           "combined tag (when a filer does report one, like Pfizer/BMS/Eli Lilly) already includes intangible "
           "amortization by its own XBRL definition and summing unconditionally would double-count it.", ""]
    md += ["## 6. A real, unrelated data-hygiene bug found while pulling live prices", "",
           "The `market_data` warehouse carries TWO rows per trading day for ABBV specifically — 250 of the last "
           "260 trading days, verified — an older, unadjusted OHLC batch (`batch_id` 4, loaded 2026-07-17) never "
           "purged after a newer, dividend-adjusted reload (`batch_id` 7, loaded one day later). Every peer "
           "ticker in this check (PFE/MRK/BMY/LLY) is clean. This is the exact same class of bug this repo's own "
           "recent 'stop the OHLC cache serving stale frames' fix addressed elsewhere, now found in a second "
           "table — fixed here by de-duplicating on the latest `batch_id` per date (`DISTINCT ON` in both the "
           "`prices()` and `week52()` queries above) rather than trusting a plain date-equality lookup.", ""]
    md += ["## 7. DCF (unlevered, margin scenarios from ABBV's own IPR&D-adjusted history)", "",
           f"Discount rate 7.33% (`finmodel wacc examples/wacc_abbv.json`). Once the acquired-IPR&D noise is "
           f"removed, `trend_diagnostics()` on the adjusted margin shows a genuinely weak trend (see §8), so — "
           "unlike the DUK/TRV/CSCO checks — the GENERIC `dcf_scenarios_from_history()` trailing min/median/max "
           "is appropriate here rather than needing a trend-guard override.", ""]
    for key in ("dcf_bear", "dcf_base", "dcf_blue_sky"):
        d = out[key]
        md.append(f"**{d['name']}** -> implied share price **{d['base_value_per_share']:.2f}** (range {d['low']:.2f} - {d['high']:.2f}).")
    md += ["", "## 8. Why the generic scenario tool is appropriate here (unlike DUK/TRV/CSCO)", "",
           "`finmodel cycle data/edgar/ABBV.json --sector pharma` on the RAW field shows a misleadingly negative-"
           "leaning correlation driven by the FY2024 IPR&D-charge trough; the ADJUSTED field (removing the "
           "acquired-IPR&D noise) resolves it to a genuinely weak trend instead:", ""]
    for label, key in (("Raw (unadjusted)", "raw"), ("IPR&D-adjusted", "adjusted")):
        t = out["normalized"][key]["trend_diagnostics"]
        md.append(f"- {label}: `trend_strength` **{t['trend_strength']}** (r={t['correlation']:.2f}, {t['direction']}).")
    md += ["", "Neither is a real, actionable secular trend the way Cisco's, Travelers' or Duke Energy's were — "
           "the real lesson here isn't 'apply a trend guard,' it's 'fix the input before checking for a trend at "
           "all,' since the raw series' apparent decline is a real accounting artifact, not a real business one.", "",
           "## 9. 52-week trading range (real, market_data warehouse, de-duplicated by batch)", "",
           f"${out['week52']['low']:.2f} - ${out['week52']['high']:.2f} ({out['week52']['from']} to {out['week52']['to']}, {out['week52']['n_days']} trading days).", "",
           "## Method note", "",
           "Every revenue/EBIT/D&A/debt/cash figure is from an SEC 10-K (via `finmodel.edgar`); every price is a "
           "live database query against `market_data`; both deals' per-share cash prices and announcement dates "
           "come from the acquirer's own 8-K press releases (public record); Humira/Skyrizi/Rinvoq product "
           "revenue figures are from AbbVie's own public earnings releases (not derivable from standard EDGAR "
           "XBRL tags). Both real precedent targets are delisted, so target-side deal premiums are omitted for "
           "the same reason as every prior check's precedents.", "",
           "Regenerate with `python scripts/football_field_abbv.py`; chart at `out/charts_football_field_abbv.html`."]
    return "\n".join(md)


if __name__ == "__main__":
    run()
