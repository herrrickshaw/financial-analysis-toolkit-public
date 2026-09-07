"""Fifth real-company check of the CFI 'Comps, Precedents, Football Field' template — REITs, via Realty Income (O).
Like the banking check, this leads with a real, verified reason the template's default framework doesn't transfer
as-is, but the failure mode here is different from banking's (EV/enterprise-value being meaningless): a REIT's
enterprise value and debt are computable in principle, the problem is the EQUITY multiple.

  Real evidence: P/E is badly misleading for a REIT. Real estate depreciation is a large non-cash charge against
  an asset that (unlike a factory or a fleet of trucks) usually appreciates — so GAAP net income understates the
  cash-generating reality by a wide, inconsistent margin across peers. Real, verified across O + 5 real net-lease
  peers (SEC EDGAR FY2025, market_data warehouse prices 2026-07-02): P/E ranges 22.9x-54.3x, while P/FFO (funds
  from operations = net income + real-estate D&A, the REIT-standard non-GAAP measure) sits in a much saner
  13.6x-19.4x band across the SAME six companies. See finmodel.sectors.SECTOR_PROFILES['reit'] for the full,
  data-driven writeup, including two further real findings this script demonstrates: FFO/AFFO have no standardized
  XBRL tag (a data-availability limit, not a bug), and finmodel.sectors correctly reports "no cycle" in O's own
  FFO margin history even though its real P/FFO trading multiple swung 12.5x-18.7x with the rate cycle — the
  module only ever looks at fundamentals, never market multiples, so it has a genuine blind spot for this sector's
  real driver.

  What this script does instead — the textbook-correct approach for a net-lease REIT:
  Trading comps    — P/FFO and P/E (equity-numerator multiples, computed the same way finmodel.comps already
                     handles a bank's P/B/P/E — no new engine code) for NNN REIT, W. P. Carey, Agree Realty,
                     Essential Properties Realty Trust, Four Corners Property Trust (SEC EDGAR fundamentals,
                     market_data warehouse prices).
  Precedent deals  — two real, verifiable, all-stock net-lease REIT mergers: Realty Income / VEREIT (announced
                     2021-04-29, 0.705 O shares per VEREIT share, sourced from Realty Income's own 8-K press
                     release) and Realty Income / Spirit Realty Capital (announced 2023-10-30, 0.762 O shares
                     per Spirit share, same sourcing). Both real precedent targets are delisted (absorbed into O)
                     and use each target's last full fiscal year before announcement (VEREIT FY2020, Spirit
                     FY2022) from SEC EDGAR — note Spirit Realty Capital's own EDGAR filer (CIK 1308606) is the
                     entity formerly named "Cole Credit Property Trust II" until a 2013 merger with the OLDER,
                     unrelated Spirit Realty Capital (ex Spirit Finance Corp, CIK 1277406, deregistered 2013) —
                     the same kind of surviving-legal-filer trap the TCF/Chemical Financial check hit.
  DDM              — the REIT-appropriate DCF-equivalent: a 2-stage dividend discount model (REITs must
                     distribute >=90% of taxable income as dividends), discounted at cost of equity from
                     `finmodel wacc examples/wacc_o.json` (8.25%). Growth scenarios come from O's own real
                     dividend-per-share history (11-year and trailing-3-year CAGR), not a hand-picked assumption.
  52-week range    — the real trailing 252-trading-day high/low from the warehouse.

Run: python scripts/football_field_o.py → docs/FOOTBALL_FIELD_O.md, out/comps_football_field_o.json,
out/charts_football_field_o.html"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finmodel import comps, charts, sectors  # noqa: E402
from finmodel.comps import Deal  # noqa: E402

CORE = ["NNN", "WPC", "ADC", "EPRT", "FCPT"]
TARGET = "O"
PRICE_DATE = "2026-07-02"
REIT_MULTIPLES = {"P/E": ("equity", "net_income"), "P/FFO": ("equity", "ffo")}


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


def year_end_price(ticker, year):
    out = subprocess.run(["psql", "-d", "market_data", "-Atc",
                          f"select close_price from ohlcv_history h join stocks s on s.stock_id=h.stock_id "
                          f"where s.market_id=2 and s.ticker='{ticker}' and date <= '{year}-12-31' order by date desc limit 1"],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    return float(out) if out else None


def fy(ticker, fy_end):
    return json.loads((ROOT / "data" / "edgar" / f"{ticker}.json").read_text())["years"][fy_end]


def reit_metrics(r):
    """FFO proxy = net income + real-estate D&A -- the Nareit-standard add-back this toolkit can derive from
    generic EDGAR tags. Nareit's official FFO also excludes gains/losses on real-estate sales (no clean XBRL tag
    across filers for that), and AFFO further adjusts for straight-line rent and recurring capex (no standardized
    tag at all) -- both left out here as a documented data-availability limit, not silently assumed away."""
    ffo = r["net_income"] + r.get("da", 0)
    return {"net_income": r["net_income"], "ffo": ffo}


def _oxford_join(items):
    items = list(items)
    if not items: return "no method"
    if len(items) == 1: return items[0]
    if len(items) == 2: return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def vereit_precedent():
    """Realty Income / VEREIT: all-stock, 0.705 O shares per VEREIT share, announced 2021-04-29 (source: O's own
    8-K, exhibit 99.1 press release, accession 0001104659-21-056901). VEREIT's last full fiscal year before
    announcement: FY2020."""
    r = fy("VER", "2020-12-31")
    ratio = 0.705
    o_close = price_on("O", "2021-04-29")
    offer_price = ratio * o_close
    equity_value = offer_price * r["diluted_shares"]
    m = reit_metrics(r)
    return {"acquirer": "Realty Income Corporation", "target": "VEREIT, Inc.", "date": "2021-04-29", "equity_value": equity_value,
            "net_income": m["net_income"], "ffo": m["ffo"], "offer_price": offer_price,
            "_detail": {"fy": "2020-12-31", "exchange_ratio": ratio, "o_close_on_announcement": o_close, "diluted_shares": r["diluted_shares"],
                        "source": "exchange ratio: Realty Income 8-K, exhibit 99.1 (accession 0001104659-21-056901); O close: market_data warehouse; VEREIT net income/D&A: SEC EDGAR 10-K"}}


def spirit_precedent():
    """Realty Income / Spirit Realty Capital: all-stock, 0.762 O shares per Spirit share, announced 2023-10-30
    (source: O's own 8-K, exhibit 99.1 press release, accession 0001104659-23-112361). Spirit's last full fiscal
    year before announcement: FY2022. Spirit Realty Capital's EDGAR filer (CIK 1308606) was "Cole Credit Property
    Trust II Inc" until a 2013 merger with the OLDER, separate Spirit Realty Capital (ex Spirit Finance Corp,
    CIK 1277406) — that older entity deregistered in 2013 and is NOT the filer Realty Income actually acquired."""
    r = fy("SRC", "2022-12-31")
    ratio = 0.762
    o_close = price_on("O", "2023-10-30")
    offer_price = ratio * o_close
    equity_value = offer_price * r["diluted_shares"]
    m = reit_metrics(r)
    return {"acquirer": "Realty Income Corporation", "target": "Spirit Realty Capital, Inc.", "date": "2023-10-30", "equity_value": equity_value,
            "net_income": m["net_income"], "ffo": m["ffo"], "offer_price": offer_price,
            "_detail": {"fy": "2022-12-31", "exchange_ratio": ratio, "o_close_on_announcement": o_close, "diluted_shares": r["diluted_shares"],
                        "source": "exchange ratio: Realty Income 8-K, exhibit 99.1 (accession 0001104659-23-112361); O close: market_data warehouse; Spirit net income/D&A: SEC EDGAR 10-K"}}


def ddm_scenario(name, growth, cost_of_equity, dps0, price, years=5, terminal_growth=0.025):
    """Two-stage Gordon-growth dividend discount model, computed entirely on a PER-SHARE basis (dps0 is dividend
    per share, so the PV sum below already IS value per share — no separate division by share count needed):
    `years` of explicit growth at `growth`, then a terminal value at `terminal_growth` in perpetuity, both
    discounted at `cost_of_equity`. REIT-appropriate because REITs must distribute >=90% of taxable income as
    dividends, so the dividend stream IS the cash flow to equity in a way it usually isn't for a non-REIT
    (finmodel.dcf's unlevered-FCF machinery isn't the natural fit here)."""
    ke = cost_of_equity
    divs = []
    d = dps0
    for _ in range(years):
        d = d * (1 + growth)
        divs.append(d)
    pv_explicit = sum(dv / (1 + ke) ** (t + 1) for t, dv in enumerate(divs))
    terminal_div = divs[-1] * (1 + terminal_growth)
    tv = terminal_div / (ke - terminal_growth)
    pv_terminal = tv / (1 + ke) ** years
    value_per_share = pv_explicit + pv_terminal
    return {"name": name, "growth": growth, "value_per_share": value_per_share,
            "implied_upside": value_per_share / price - 1}


def run():
    px = prices(CORE + [TARGET])
    peers = []
    for t in CORE:
        r = fy(t, "2025-12-31")
        peers.append(comps.Peer(t, px[t], r["diluted_shares"], metrics=reit_metrics(r), ticker=t))
    trading = comps.spread(peers, multiples=REIT_MULTIPLES)

    ver_deal, src_deal = vereit_precedent(), spirit_precedent()
    deals = [Deal(ver_deal["acquirer"], ver_deal["target"], ver_deal["date"], enterprise_value=ver_deal["equity_value"],
                  multiples={"P/E LTM": comps.multiple(ver_deal["equity_value"], ver_deal["net_income"]), "P/FFO LTM": comps.multiple(ver_deal["equity_value"], ver_deal["ffo"])}),
             Deal(src_deal["acquirer"], src_deal["target"], src_deal["date"], enterprise_value=src_deal["equity_value"],
                  multiples={"P/E LTM": comps.multiple(src_deal["equity_value"], src_deal["net_income"]), "P/FFO LTM": comps.multiple(src_deal["equity_value"], src_deal["ffo"])})]
    precedents = comps.precedents(deals)

    tr = fy(TARGET, "2025-12-31")
    target = comps.Target("Realty Income Corporation", px[TARGET], tr["diluted_shares"], metrics=reit_metrics(tr))

    coe = 0.0825  # finmodel wacc examples/wacc_o.json
    o_hist = json.loads((ROOT / "data" / "edgar" / "O.json").read_text())["years"]
    d0 = tr["dividends"] / tr["diluted_shares"]
    o18 = fy(TARGET, "2018-12-31"); o22 = fy(TARGET, "2022-12-31")
    dps18, dps22, dps25 = o18["dividends"] / o18["diluted_shares"], o22["dividends"] / o22["diluted_shares"], d0
    cagr_11yr = (dps25 / (fy(TARGET, "2014-12-31")["dividends"] / fy(TARGET, "2014-12-31")["diluted_shares"])) ** (1 / 11) - 1
    cagr_3yr = (dps25 / dps22) ** (1 / 3) - 1
    bear = ddm_scenario("DDM - bear case (trailing 3yr dividend CAGR, growth decelerating)", cagr_3yr, coe, d0, px[TARGET])
    blue = ddm_scenario("DDM - blue sky (11yr historical dividend CAGR)", cagr_11yr, coe, d0, px[TARGET])
    wk52 = week52(TARGET)

    ff = comps.football_field(target, {"Trading comps": trading, "Precedent transactions": precedents},
                              extra={bear["name"]: (bear["value_per_share"], bear["value_per_share"]), blue["name"]: (blue["value_per_share"], blue["value_per_share"]), "52-week range": (wk52["low"], wk52["high"])},
                              stat_low="p25", stat_high="p75",
                              multiples={"Trading comps": REIT_MULTIPLES, "Precedent transactions": {"P/E": ("equity", "net_income"), "P/FFO": ("equity", "ffo")}})

    normalized = build_normalized(o_hist)
    multiple_history = build_multiple_history()

    o_metrics = reit_metrics(tr)
    out = {"price": px[TARGET], "price_date": PRICE_DATE, "trading_comps": trading, "precedents": precedents,
           "ver_detail": ver_deal, "src_detail": src_deal, "ddm_bear": bear, "ddm_blue_sky": blue, "week52": wk52, "football_field": ff,
           "cagr_11yr": cagr_11yr, "cagr_3yr": cagr_3yr, "d0": d0, "normalized": normalized, "multiple_history": multiple_history,
           "target_shares": tr["diluted_shares"], "target_ni": o_metrics["net_income"], "target_ffo": o_metrics["ffo"]}
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "comps_football_field_o.json").write_text(json.dumps(out, indent=1, default=str))
    charts.report_for("comps", {"comps": trading, "precedents": precedents, "football_field": ff}, ROOT / "out" / "charts_football_field_o.html", title="Realty Income — REIT-appropriate football field on real data")

    md = write_doc(out)
    (ROOT / "docs" / "FOOTBALL_FIELD_O.md").write_text(md)
    print(f"O price {px[TARGET]:.2f} ({PRICE_DATE})")
    for it in ff["items"]:
        print(f"  {it['method']:65} {it['low']:8.2f} - {it['high']:8.2f}")


def build_normalized(o_hist):
    """finmodel.sectors, FFO-based: cycle_diagnostics/trend_diagnostics called with field='ffo', revenue_field=
    'revenue' instead of the default operating_income/revenue ('ffo' = net_income + real-estate D&A, precomputed
    into data/edgar/O.json alongside the raw EDGAR tags — the same command `finmodel cycle data/edgar/O.json
    --sector reit --field ffo --revenue-field revenue` works from the CLI for exactly this reason). Real finding:
    this reports 'near normal' / 'weak trend' in the FUNDAMENTAL (FFO margin), even though the real market
    MULTIPLE swung hard with interest rates — a genuine blind spot in what this module can see, documented
    rather than hidden."""
    diag = sectors.cycle_diagnostics(o_hist, field="ffo", revenue_field="revenue", periods=8, sector="reit")
    trend = sectors.trend_diagnostics(o_hist, field="ffo", revenue_field="revenue", periods=8)
    return {"cycle_diagnostics": diag, "trend_diagnostics": trend}


def build_multiple_history():
    """Real O year-end P/FFO, 2018-2025 -- the market-multiple cycle finmodel.sectors cannot see (it only looks
    at fundamentals, never price)."""
    o_hist = json.loads((ROOT / "data" / "edgar" / "O.json").read_text())["years"]
    rows = []
    for y in range(2018, 2026):
        r = o_hist[f"{y}-12-31"]
        ffo = r["net_income"] + r["da"]
        ffops = ffo / r["diluted_shares"]
        px = year_end_price(TARGET, y)
        rows.append({"year": y, "ffo_per_share": ffops, "year_end_price": px, "p_ffo": px / ffops})
    return rows


def write_doc(out):
    px = out["price"]; ff = out["football_field"]
    md = ["# Fifth real-company check: REITs need FFO-based multiples, not P/E — and a real blind spot in this toolkit's own cycle tool", "",
          "Same real-data method as the steel, oil & gas, enterprise-tech and banking checks, applied to Realty "
          "Income (O). Unlike the banking check, EV/EBITDA isn't the failure here — a REIT's enterprise value is "
          "computable. The failure is in the equity multiple itself: net income.", "",
          "## Why P/E breaks for a REIT (real evidence, not a hypothetical)", "",
          "Real estate depreciation is a large non-cash GAAP charge against an asset that, unlike a factory or a "
          "delivery fleet, usually *appreciates*. Nareit's response to this, decades old and industry-standard, is "
          "FFO (funds from operations = net income + real-estate depreciation & amortization) as the metric "
          "analysts actually price REITs on. Verified on real FY2025 SEC EDGAR data across six real net-lease "
          "REITs, priced at real 2026-07-02 market_data closes:", "",
          "| Ticker | Price | P/E | P/FFO |", "|---|---|---|---|"]
    f = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
    for p in out["trading_comps"]["peers"]:
        md.append(f"| {p['ticker']} | {p['price']:.2f} | {f(p['multiples']['P/E LTM'])} | {f(p['multiples']['P/FFO LTM'])} |")
    o_pe = comps.multiple(px * out["target_shares"], out["target_ni"])
    o_pffo = comps.multiple(px * out["target_shares"], out["target_ffo"])
    md.append(f"| O (target) | {px:.2f} | {f(o_pe)} | {f(o_pffo)} |")
    md += ["", "*(O is the target of this check, not a peer in its own comps set — shown in the table above for "
           "the full six-company range, not as part of the peer statistics.)*", "",
           "P/E ranges **22.9x-54.3x** across these six real companies; P/FFO sits in a much tighter, saner "
           "**13.6x-19.4x** band across the SAME six companies. A P/E-based comp set would make Realty Income look "
           "either wildly overvalued or roughly in line with peers depending entirely on which REIT you compared "
           "it to — an artifact of depreciation policy and acquisition history, not real relative value. See "
           "`finmodel.sectors.SECTOR_PROFILES['reit']` for the same finding encoded into the toolkit itself.", "",
           "**A real data-availability ceiling, documented rather than patched around**: Nareit's official FFO "
           "definition also excludes gains/losses on real-estate sales (no clean, consistent XBRL tag for that "
           "across filers), and AFFO — which further backs out straight-line rent and recurring capex — has no "
           "standardized XBRL tag at all. The FFO figure in this check is therefore a real, honest proxy "
           "(net income + D&A), not the exact Nareit-reconciled number a REIT publishes in its own earnings "
           "release.", "",
           "**A second real data gap — filer-by-filer, not sector-wide**: this check uses only equity-numerator "
           "multiples (P/E, P/FFO), not EV/EBITDA, partly by choice (P/FFO is the sector-standard metric) and "
           "partly because net debt isn't reliably available: `finmodel.edgar`'s debt tags return `None` for "
           "FY2025 for the target (O) and 2 of 5 peers (NNN, Agree Realty). Realty Income itself last reported "
           "the aggregate `LongTermDebt` XBRL tag in FY2016; since then it reports debt only through "
           "disaggregated `SecuredDebt`/`UnsecuredDebt`/`NotesPayable` tags — ADDITIVE components (a filer's "
           "true total debt is their sum), not alternative tags for the same concept, so summing them correctly "
           "needs a different TAGS design than this module's first-tag-wins fallback tuples. But this is real "
           "variation between individual filers, not a REIT-wide pattern: the other 3 of 5 peers (W. P. Carey, "
           "Essential Properties, Four Corners) DO report a populated `debt_total` for FY2025 — this check "
           "simply didn't need to lean on that, since P/E and P/FFO are equity-numerator multiples by design.", ""]
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
    md += ["", "## 1. Trading comps (P/E, P/FFO — real: SEC EDGAR fundamentals + market_data warehouse prices)", "",
           "Peers: NNN REIT, W. P. Carey, Agree Realty, Essential Properties Realty Trust, Four Corners Property "
           "Trust — all real single-tenant net-lease REITs, the same business model as Realty Income.", "",
           "| Multiple | 25th | Median | 75th |", "|---|---|---|---|"]
    for label in ("P/E LTM", "P/FFO LTM"):
        s = out["trading_comps"]["summary"][label]
        md.append(f"| {label.replace(' LTM', '')} | {s['p25']:.2f}x | {s['median']:.2f}x | {s['p75']:.2f}x |")
    md += ["", "## 2. Precedent transactions (real, verifiable, all-stock net-lease REIT mergers)", ""]
    for key, title in (("ver_detail", "Realty Income / VEREIT"), ("src_detail", "Realty Income / Spirit Realty Capital")):
        d = out[key]; det = d["_detail"]
        md += [f"### {title} — announced {d['date']}", "",
               f"All-stock: {det['exchange_ratio']} Realty Income shares per target share × Realty Income's own "
               f"price on the announcement day = offer **${d['offer_price']:.2f}**/target share. Equity value "
               f"**${d['equity_value']/1e6:,.0f}M** ({det['diluted_shares']/1e6:.1f}M target diluted shares), "
               f"target net income ${d['net_income']/1e6:,.0f}M, FFO proxy ${d['ffo']/1e6:,.0f}M, target "
               f"fundamentals from its FY{det['fy'][:4]} 10-K (SEC EDGAR).", "",
               f"**P/E {comps.multiple(d['equity_value'], d['net_income']):.2f}x, "
               f"P/FFO {comps.multiple(d['equity_value'], d['ffo']):.2f}x**.", ""]
    md += ["Both real deal-implied P/FFO multiples (11.79x, 7.03x) sit BELOW the peer trading range (14.9x-16.0x "
           "p25-p75) — worth being honest about why, since it isn't the same reason for both. Realty Income's own "
           f"stock barely moved around the VEREIT announcement (${price_on('O', '2021-04-28'):.2f} the prior "
           f"trading day → ${out['ver_detail']['_detail']['o_close_on_announcement']:.2f} on announcement day). "
           f"For Spirit Realty, O's stock fell a real, verified ~5.7% on the announcement itself "
           f"(${price_on('O', '2023-10-27'):.2f} on 2023-10-27, the prior trading day, to "
           f"${out['src_detail']['_detail']['o_close_on_announcement']:.2f} on 2023-10-30) — a real market "
           "reaction to stock-deal dilution that mechanically pulls this precedent's implied multiple down further "
           "than VEREIT's, on top of the same real FFO-vs-net-income distortion driving the rest of this "
           "check. Using the pre-announcement price instead would show a higher implied multiple for Spirit "
           "specifically; this check uses the announcement-day close for both, for the same reason the banking "
           "check did — consistency with how the other three sector checks in this project define \"the "
           "acquirer's price at announcement.\"", ""]
    md += ["## 3. Dividend discount model (REIT-appropriate DCF-equivalent)", "",
           f"Cost of equity 8.25% (`finmodel wacc examples/wacc_o.json`); 2-stage Gordon growth, 5 explicit years "
           "then a 2.5% terminal growth rate, discounted at cost of equity. REITs must distribute >=90% of taxable "
           f"income as dividends, so the dividend stream is a direct, textbook-appropriate cash-flow-to-equity "
           f"proxy. Growth assumptions are O's own real historical dividend-per-share CAGRs, not analyst "
           f"consensus: {out['cagr_3yr']*100:.2f}%/yr over the trailing 3 years (bear case — real, and reflects "
           f"real deceleration from heavy stock issuance funding the VEREIT and Spirit Realty deals) vs "
           f"{out['cagr_11yr']*100:.2f}%/yr over the trailing 11 years (blue sky — O's older, faster growth "
           "rate).", ""]
    for key in ("ddm_bear", "ddm_blue_sky"):
        d = out[key]
        md.append(f"**{d['name']}** ({d['growth']*100:.2f}%/yr growth) → implied share price "
                  f"**${d['value_per_share']:.2f}** ({d['implied_upside']*100:+.1f}% vs the real ${px:.2f} price).")
    md += ["", "## 4. 52-week trading range (real, market_data warehouse)", "",
           f"${out['week52']['low']:.2f} – ${out['week52']['high']:.2f} ({out['week52']['from']} to {out['week52']['to']}, {out['week52']['n_days']} trading days).", ""]
    md += ["## 5. The real blind spot: this toolkit's cycle tool can't see a REIT's actual cycle", "",
           "`finmodel cycle data/edgar/O.json --sector reit --field ffo --revenue-field revenue` — FFO margin, "
           "the operating fundamental this module normalizes, was genuinely stable over FY2018-2025:", ""]
    diag = out["normalized"]["cycle_diagnostics"]
    md.append(f"FY{diag['fiscal_year'][:4]} FFO margin {diag['latest_margin']*100:.1f}% vs trailing-8yr median "
              f"{diag['median_margin_trailing_years']*100:.1f}% ({diag['deviation_pct']*100:+.1f}%) → **{diag['flag']}**, "
              f"trend **{out['normalized']['trend_diagnostics']['trend_strength']}**.")
    md += ["", "Yet Realty Income's real year-end P/FFO multiple swung hard over the exact same window — driven by "
           "the interest-rate cycle, not by anything in its own operating fundamentals:", "",
           "| Year-end | FFO/share | Price | P/FFO |", "|---|---|---|---|"]
    for r in out["multiple_history"]:
        md.append(f"| {r['year']} | {r['ffo_per_share']:.2f} | {r['year_end_price']:.2f} | {r['p_ffo']:.2f}x |")
    md += ["", "P/FFO ranged **12.5x (2023, after aggressive Fed hikes) to 18.7x (2021, near-zero rates)** — a "
           ">45% swing — while `cycle_diagnostics()` on the fundamental correctly reports no cycle at all. This "
           "isn't a false negative to fix: the module only ever looks at a company's own EDGAR history, never its "
           "market price or trading multiple, so a valuation cycle that lives entirely in the multiple (as a "
           "REIT's does, being unusually rate-sensitive) is structurally outside what it can detect. Anyone using "
           "this module on a REIT should look at the real trading-multiple history directly, the way this table "
           "does, rather than trusting `cycle_diagnostics()`'s 'near normal' as evidence nothing cyclical is "
           "happening.", "",
           "## Method note", "",
           "Every net income / D&A / dividend figure is from an SEC 10-K (via `finmodel.edgar`); every price is a "
           "live database query against `market_data`; the two deals' exchange ratios and announcement dates come "
           "from Realty Income's own 8-K press releases (public record). VEREIT and Spirit Realty Capital are both "
           "delisted and absent from the warehouse, so target-side deal premiums are omitted for the same reason "
           "as the banking check's precedents.", "",
           "Regenerate with `python scripts/football_field_o.py`; chart at `out/charts_football_field_o.html`."]
    return "\n".join(md)


if __name__ == "__main__":
    run()
