"""Seventh real-company check of the CFI 'Comps, Precedents, Football Field' template — P&C insurance/reinsurance,
via Travelers Companies (TRV). Like banking, EBITDA doesn't apply here — but the root cause is different (an
investment-portfolio accounting tag contaminating D&A, not a revenue-tag mismatch), and the sector-defining real
finding is different again from every prior check: book value itself, not the trading multiple (REITs) or
earnings moving together with book value (banking's credit losses), is what's directly rate-exposed for an
insurer, because available-for-sale bond fair-value moves run through OCI (equity), not net income, under GAAP.

  Real evidence EV/EBITDA breaks here, a different root cause from banking: Chubb reports no da/ebitda tag at
  all; W.R. Berkley's own `da` tag picks up a genuinely NEGATIVE value (real, verified, FY2025) because
  `finmodel.edgar`'s preferred D&A tag for this figure (DepreciationAmortizationAndAccretionNet) bundles in bond-
  portfolio premium/discount accretion for a filer with a large investment book — nothing to do with operating
  depreciation. Same conclusion as banking (use P/B, P/TBV, P/E), different mechanism.

  The real, sector-defining finding: verified across 5 real P&C peers (SEC EDGAR FY2025) that EVERY ONE showed a
  real book-value-per-share DECLINE in FY2022 (-9% to -23%) during that year's historic bond selloff, even though
  3 of 5 stayed solidly net-income-positive. A connected trap for this sector's ROE override (field="net_income",
  revenue_field="equity", the same one banking uses): Travelers' own measured ROE ROSE in FY2022 purely because
  its book-value denominator shrank from the same AOCI hit -- not real earnings improvement. See
  finmodel.sectors.SECTOR_PROFILES['insurance'] for the full, data-driven writeup, including a real, unrelated
  bonus finding (a persistent W.R. Berkley XBRL share-count scale error) surfaced while building this check.

  What this script does -- reusing existing generic engines, no new comps/valuation code:
  Trading comps    — P/B, P/TBV and P/E (equity-numerator multiples, same finmodel.comps mapping style as the
                     banking check) for Chubb, Allstate, Progressive, Cincinnati Financial, W. R. Berkley.
  Precedent deals  — two real, verifiable, all-CASH P&C/reinsurance mergers (simpler than exchange-ratio deals):
                     AIG / Validus Holdings (2018-01-22, $68.00/share -- Validus's FY2017 net income was
                     genuinely negative, a real catastrophe-loss year, so its P/E is correctly NM) and
                     Berkshire Hathaway / Alleghany Corporation (2022-03-21, $848.02/share).
  Residual income  — the insurance-appropriate DCF-equivalent (same as banking): net income − cost of equity ×
                     book value, using finmodel.residual_income with cost of equity from
                     `finmodel wacc examples/wacc_trv.json` (8.03%). ROE scenarios come from TRV's own real,
                     genuinely trending history (see the trend-guard callback in §5 of the doc) rather than a
                     trailing-median that would misread real, sustained margin improvement as a cyclical extreme.
  52-week range    — the real trailing 252-trading-day high/low from the warehouse.

Run: python scripts/football_field_trv.py → docs/FOOTBALL_FIELD_TRV.md, out/comps_football_field_trv.json,
out/charts_football_field_trv.html"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finmodel import comps, charts, sectors  # noqa: E402
from finmodel.residual_income import residual_income  # noqa: E402
from finmodel.comps import Deal  # noqa: E402

CORE = ["CB", "ALL", "PGR", "CINF", "WRB"]
TARGET = "TRV"
PRICE_DATE = "2026-07-02"
INSURER_MULTIPLES = {"P/B": ("equity", "book_value"), "P/TBV": ("equity", "tangible_book_value"), "P/E": ("equity", "net_income")}


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


def insurer_metrics(r):
    tbv = r["equity"] - (r.get("goodwill") or 0) - (r.get("intangibles") or 0)
    return {"book_value": r["equity"], "tangible_book_value": tbv, "net_income": r["net_income"]}


def _oxford_join(items):
    items = list(items)
    if not items: return "no method"
    if len(items) == 1: return items[0]
    if len(items) == 2: return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def validus_precedent():
    """AIG / Validus Holdings: all-cash, $68.00/share, announced 2018-01-22 (source: Validus's own 8-K, exhibit
    99.1 press release, accession 0001341004-18-000039). Validus's last full fiscal year before announcement:
    FY2017 — a real catastrophe-loss year (Hurricanes Harvey/Irma/Maria), so its net income was genuinely
    negative and its P/E is correctly NM below, not a data error."""
    r = fy("VAL", "2017-12-31")
    price = 68.00
    equity_value = price * r["diluted_shares"]
    m = insurer_metrics(r)
    return {"acquirer": "American International Group, Inc.", "target": "Validus Holdings, Ltd.", "date": "2018-01-22",
            "equity_value": equity_value, "book_value": m["book_value"], "tangible_book_value": m["tangible_book_value"],
            "net_income": m["net_income"], "offer_price": price,
            "_detail": {"fy": "2017-12-31", "diluted_shares": r["diluted_shares"],
                        "source": "$68.00/share, all cash: Validus 8-K exhibit 99.1 (accession 0001341004-18-000039); Validus fundamentals: SEC EDGAR 10-K"}}


def alleghany_precedent():
    """Berkshire Hathaway / Alleghany Corporation: all-cash, $848.02/share, announced 2022-03-21 (source:
    Alleghany's own 8-K, exhibit 99.1 press release, accession 0001193125-22-080711). Alleghany's last full
    fiscal year before announcement: FY2021."""
    r = fy("Y", "2021-12-31")
    price = 848.02
    equity_value = price * r["diluted_shares"]
    m = insurer_metrics(r)
    return {"acquirer": "Berkshire Hathaway Inc.", "target": "Alleghany Corporation", "date": "2022-03-21",
            "equity_value": equity_value, "book_value": m["book_value"], "tangible_book_value": m["tangible_book_value"],
            "net_income": m["net_income"], "offer_price": price,
            "_detail": {"fy": "2021-12-31", "diluted_shares": r["diluted_shares"],
                        "source": "$848.02/share, all cash: Alleghany 8-K exhibit 99.1 (accession 0001193125-22-080711); Alleghany fundamentals: SEC EDGAR 10-K"}}


def trv_residual_income_scenario(name, roe_target, cost_of_equity, payout_ratio, book_value_0, shares, price):
    n = 5
    bv = book_value_0; ni = []; div = []
    for _ in range(n):
        ni_t = roe_target * bv; div_t = ni_t * payout_ratio
        ni.append(ni_t); div.append(div_t); bv = bv + ni_t - div_t
    res = residual_income(book_value_0, ni, div, cost_of_equity, terminal="persistence", persistence=0.5, shares=shares, price=price)
    grid = []
    for coe in (cost_of_equity - 0.005, cost_of_equity, cost_of_equity + 0.005):
        for persist in (0.3, 0.5, 0.7):
            r = residual_income(book_value_0, ni, div, coe, terminal="persistence", persistence=persist, shares=shares, price=price)
            grid.append(r["value_per_share"])
    return {"name": name, "base_value_per_share": res["value_per_share"], "low": min(grid), "high": max(grid), "roe_target": roe_target}


def run():
    px = prices(CORE + [TARGET])
    peers = []
    for t in CORE:
        r = fy(t, "2025-12-31")
        peers.append(comps.Peer(t, px[t], r["diluted_shares"], metrics=insurer_metrics(r), ticker=t))
    trading = comps.spread(peers, multiples=INSURER_MULTIPLES)

    val_deal, y_deal = validus_precedent(), alleghany_precedent()
    deals = [Deal(val_deal["acquirer"], val_deal["target"], val_deal["date"], enterprise_value=val_deal["equity_value"],
                  multiples={"P/B LTM": comps.multiple(val_deal["equity_value"], val_deal["book_value"]), "P/TBV LTM": comps.multiple(val_deal["equity_value"], val_deal["tangible_book_value"]), "P/E LTM": comps.multiple(val_deal["equity_value"], val_deal["net_income"])}),
             Deal(y_deal["acquirer"], y_deal["target"], y_deal["date"], enterprise_value=y_deal["equity_value"],
                  multiples={"P/B LTM": comps.multiple(y_deal["equity_value"], y_deal["book_value"]), "P/TBV LTM": comps.multiple(y_deal["equity_value"], y_deal["tangible_book_value"]), "P/E LTM": comps.multiple(y_deal["equity_value"], y_deal["net_income"])})]
    precedents = comps.precedents(deals)

    tr = fy(TARGET, "2025-12-31")
    target = comps.Target("The Travelers Companies, Inc.", px[TARGET], tr["diluted_shares"], metrics=insurer_metrics(tr))

    coe = 0.0803  # finmodel wacc examples/wacc_trv.json
    trv_hist = json.loads((ROOT / "data" / "edgar" / "TRV.json").read_text())["years"]
    payout = tr["dividends"] / tr["net_income"]
    # trend_diagnostics() (checked in build_normalized below) fires "strong improving" on TRV's real ROE history —
    # the same guard the software check established: a trailing-median scenario would badly understate current,
    # genuinely improved earning power, not correct it for a cyclical extreme. Base/blue-sky here use TRV's own
    # recent real levels (3yr average, and the FY2025 actual peak), not the 8yr trailing median.
    roe_recent_3yr = sum(trv_hist[f"{y}-12-31"]["net_income"] / trv_hist[f"{y}-12-31"]["equity"] for y in (2023, 2024, 2025)) / 3
    roe_2025 = tr["net_income"] / tr["equity"]
    base = trv_residual_income_scenario("Residual income - base case (trailing 3yr average ROE)", roe_target=roe_recent_3yr, cost_of_equity=coe, payout_ratio=payout, book_value_0=tr["equity"] / 1e6, shares=tr["diluted_shares"] / 1e6, price=px[TARGET])
    blue = trv_residual_income_scenario("Residual income - blue sky (FY2025 actual ROE sustained)", roe_target=roe_2025, cost_of_equity=coe, payout_ratio=payout, book_value_0=tr["equity"] / 1e6, shares=tr["diluted_shares"] / 1e6, price=px[TARGET])
    wk52 = week52(TARGET)

    ff = comps.football_field(target, {"Trading comps": trading, "Precedent transactions": precedents},
                              extra={base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"]), "52-week range": (wk52["low"], wk52["high"])},
                              stat_low="p25", stat_high="p75",
                              multiples={"Trading comps": INSURER_MULTIPLES, "Precedent transactions": {"P/B": ("equity", "book_value"), "P/TBV": ("equity", "tangible_book_value"), "P/E": ("equity", "net_income")}})

    normalized = build_normalized(trv_hist)
    bvps_history = build_bvps_history()

    out = {"price": px[TARGET], "price_date": PRICE_DATE, "trading_comps": trading, "precedents": precedents,
           "val_detail": val_deal, "y_detail": y_deal, "ri_base": base, "ri_blue_sky": blue, "week52": wk52, "football_field": ff,
           "trv_current_roe": roe_2025, "roe_recent_3yr": roe_recent_3yr, "payout": payout, "normalized": normalized, "bvps_history": bvps_history}
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "comps_football_field_trv.json").write_text(json.dumps(out, indent=1, default=str))
    charts.report_for("comps", {"comps": trading, "precedents": precedents, "football_field": ff}, ROOT / "out" / "charts_football_field_trv.html", title="Travelers — insurance-appropriate football field on real data")

    md = write_doc(out)
    (ROOT / "docs" / "FOOTBALL_FIELD_TRV.md").write_text(md)
    print(f"TRV price {px[TARGET]:.2f} ({PRICE_DATE})")
    for it in ff["items"]:
        print(f"  {it['method']:60} {it['low']:8.2f} - {it['high']:8.2f}")


def build_normalized(trv_hist):
    """finmodel.sectors on TRV's real ROE history: cycle_diagnostics/trend_diagnostics with field='net_income',
    revenue_field='equity', the same override banking established. Real finding: trend_diagnostics() correctly
    fires 'strong improving' — the trend-guard callback from the software check, now demonstrated on a totally
    different (financial-services) sector rather than a fresh mechanism."""
    diag = sectors.cycle_diagnostics(trv_hist, field="net_income", revenue_field="equity", periods=8, sector="insurance")
    trend = sectors.trend_diagnostics(trv_hist, field="net_income", revenue_field="equity", periods=8)
    return {"cycle_diagnostics": diag, "trend_diagnostics": trend}


def build_bvps_history():
    """Real BVPS (book value per share) 2021-2023 for the 5 clean peers (excludes WRB — see the doc's note on
    its own real, verified XBRL share-count scale error for these exact years) — the real, sector-wide AOCI
    finding this check is built around."""
    rows = []
    for t in ["TRV", "CB", "ALL", "PGR", "CINF"]:
        hist = json.loads((ROOT / "data" / "edgar" / f"{t}.json").read_text())["years"]
        bvps = {}
        for y in (2021, 2022, 2023):
            r = hist[f"{y}-12-31"]
            bvps[y] = r["equity"] / r["diluted_shares"]
        rows.append({"ticker": t, "bvps_2021": bvps[2021], "bvps_2022": bvps[2022], "bvps_2023": bvps[2023],
                     "decline_2022_pct": bvps[2022] / bvps[2021] - 1,
                     "net_income_2022": hist["2022-12-31"]["net_income"]})
    return rows


def write_doc(out):
    px = out["price"]; ff = out["football_field"]
    md = ["# Seventh real-company check: P&C insurers need book-value-based multiples — and book value itself is what's rate-exposed", "",
          "Same real-data method as the six prior checks, applied to Travelers (TRV). Like banking, EV/EBITDA "
          "doesn't apply — but for a different reason, and the sector-defining real finding here (book value's "
          "own rate exposure) is new, not a repeat of the banking or REIT findings.", "",
          "## Why EV/EBITDA breaks for an insurer (real evidence, a different root cause from banking)", "",
          "| Filer | FY | `da` tag picked | Value | Problem |", "|---|---|---|---|---|"]
    cb = json.loads((ROOT / "data" / "edgar" / "CB.json").read_text())["years"]["2025-12-31"]
    wrb = json.loads((ROOT / "data" / "edgar" / "WRB.json").read_text())["years"]["2025-12-31"]
    md.append(f"| Chubb Limited | 2025 | *(none populated)* | — | no `da`/`ebitda` tag at all |")
    md.append(f"| W. R. Berkley | 2025 | `DepreciationAmortizationAndAccretionNet` | -${abs(wrb['da'])/1e6:,.1f}M | NEGATIVE — this tag bundles bond-portfolio premium/discount accretion for a filer with a large investment book, not real operating depreciation |")
    md += ["", "A bank's problem was a revenue-tag mismatch; an insurer's is different — `finmodel.edgar`'s D&A "
           "tag preference picks up investment-accounting noise instead of (or in addition to) real depreciation "
           "once a filer's investment portfolio is large enough. Same conclusion either way: P/B, P/TBV and P/E "
           "(all equity-numerator, see `finmodel.comps`), never EV/EBITDA. See "
           "`finmodel.sectors.SECTOR_PROFILES['insurance']` for the same finding encoded into the toolkit.", ""]
    md += ["## The real, sector-defining finding: book value itself is rate-exposed, not the multiple or earnings", "",
           "Verified across five real P&C peers, real FY2021-2023 SEC EDGAR data (W. R. Berkley excluded from "
           "this specific table — see the note below):", "",
           "| Ticker | BVPS 2021 | BVPS 2022 | BVPS 2023 | 2022 decline | 2022 net income |", "|---|---|---|---|---|---|"]
    for r in out["bvps_history"]:
        ni_str = f"-${abs(r['net_income_2022'])/1e6:,.0f}M" if r["net_income_2022"] < 0 else f"${r['net_income_2022']/1e6:,.0f}M"
        md.append(f"| {r['ticker']} | {r['bvps_2021']:.2f} | {r['bvps_2022']:.2f} | {r['bvps_2023']:.2f} | {r['decline_2022_pct']*100:.1f}% | {ni_str} |")
    md += ["", "Every one of the five real peers shows a real book-value-per-share decline in FY2022, ranging "
           "-9.4% (Chubb) to -22.7% (Allstate) — during that year's historic bond-market selloff (the Fed's rate "
           "hikes). Three of five (Travelers, Chubb, Progressive) stayed solidly net-income-positive that same "
           "year: the business was fine, book value fell anyway. This is mechanistically different from every "
           "prior check: a REIT's operating fundamental (FFO) stayed flat while its trading MULTIPLE moved with "
           "rates; a bank's credit losses hit book value AND earnings together. An insurer's available-for-sale "
           "bond portfolio marks to fair value through OCI (equity), not net income, under GAAP — so BVPS and "
           "EPS can genuinely decouple in a way they structurally cannot for a bank's amortized-cost loan book.", "",
           "**A real, connected trap for ROE-based residual income**: Travelers' own measured ROE (net_income / "
           "equity) actually ROSE in FY2022 to 13.2%, up from 12.7% in FY2021 — not because performance improved, "
           "but because the book-value denominator shrank from the same AOCI hit. Anyone pointing "
           "`finmodel.sectors` at ROE for an insurer during or after a rate shock should check book value's own "
           "trend alongside ROE, not ROE in isolation — an 'improvement' can be a shrunken denominator, not real "
           "earnings power.", "",
           "**A real, unrelated bonus finding surfaced while building the table above**: W. R. Berkley's own "
           "`WeightedAverageNumberOfDilutedSharesOutstanding` was filed at roughly 1/1000th its real scale for "
           "FY2017-2022 (real, verified against SEC's live XBRL API — e.g. FY2022 shows `419192` where the real "
           "figure is `419,192,000`). `finmodel.edgar`'s 'latest filing wins' logic only self-heals this while "
           "the bad period still appears as a comparative column in a later 10-K — FY2023's identical error WAS "
           "corrected this way (visible in the FY2025 10-K's comparatives), but FY2017-2022 have since aged out "
           "of every subsequent filing's comparative window and remain wrong in SEC's own live data today. "
           "Excluded from the BVPS table above for exactly this reason, rather than shown wrong.", ""]
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
    md += ["", "## 1. Trading comps (P/B, P/TBV, P/E — real: SEC EDGAR fundamentals + market_data warehouse prices)", "",
           "Peers: Chubb, Allstate, Progressive, Cincinnati Financial, W. R. Berkley — real large-cap US P&C "
           "insurers.", "",
           "| Ticker | Price | P/B | P/TBV | P/E |", "|---|---|---|---|---|"]
    for p in out["trading_comps"]["peers"]:
        f = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
        md.append(f"| {p['ticker']} | {p['price']:.2f} | {f(p['multiples']['P/B LTM'])} | {f(p['multiples']['P/TBV LTM'])} | {f(p['multiples']['P/E LTM'])} |")
    md += ["", "| Multiple | 25th | Median | 75th |", "|---|---|---|---|"]
    for label in ("P/B LTM", "P/TBV LTM", "P/E LTM"):
        s = out["trading_comps"]["summary"][label]
        md.append(f"| {label.replace(' LTM', '')} | {s['p25']:.2f}x | {s['median']:.2f}x | {s['p75']:.2f}x |")
    md += ["", "## 2. Precedent transactions (real, verifiable, all-cash P&C/reinsurance mergers)", ""]
    f_mult = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
    for key, title in (("val_detail", "AIG / Validus Holdings"), ("y_detail", "Berkshire Hathaway / Alleghany Corporation")):
        d = out[key]; det = d["_detail"]
        ni_str = f"-${abs(d['net_income'])/1e6:,.0f}M" if d["net_income"] < 0 else f"${d['net_income']/1e6:,.0f}M"
        md += [f"### {title} — announced {d['date']}", "",
               f"All-cash: **${d['offer_price']:.2f}**/target share. Equity value **${d['equity_value']/1e6:,.0f}M** "
               f"({det['diluted_shares']/1e6:.1f}M target diluted shares), target book value ${d['book_value']/1e6:,.0f}M, "
               f"tangible book value ${d['tangible_book_value']/1e6:,.0f}M, target net income {ni_str}, target "
               f"fundamentals from its FY{det['fy'][:4]} 10-K (SEC EDGAR).", "",
               f"**P/B {f_mult(comps.multiple(d['equity_value'], d['book_value']))}, "
               f"P/TBV {f_mult(comps.multiple(d['equity_value'], d['tangible_book_value']))}, "
               f"P/E {f_mult(comps.multiple(d['equity_value'], d['net_income']))}**.", ""]
    md += ["Validus's negative net income isn't a data error — 2017 was a real, well-documented catastrophe-loss "
           "year for reinsurers (Hurricanes Harvey, Irma and Maria), and `comps.multiple()`'s NM-cap logic "
           "correctly reports its P/E as NM rather than a nonsensical negative multiple.", ""]
    md += ["## 3. Residual income (insurance-appropriate DCF-equivalent — same method as the banking check)", "",
           f"Cost of equity 8.03% (`finmodel wacc examples/wacc_trv.json`); a {out['payout']*100:.1f}% dividend "
           "payout ratio (TRV's own FY2025 actual — P&C insurers typically retain most earnings for underwriting "
           "capacity and buybacks, not shown here). ROE scenarios use TRV's own RECENT real levels, not a "
           "trailing 8-year median — see §4 for why that matters here specifically.", ""]
    for key in ("ri_base", "ri_blue_sky"):
        d = out[key]
        md.append(f"**{d['name']}** (ROE target {d['roe_target']*100:.1f}%, current {out['trv_current_roe']*100:.1f}%) "
                  f"→ implied share price **{d['base_value_per_share']:.2f}** (range {d['low']:.2f} – {d['high']:.2f}).")
    md += ["", "## 4. 52-week trading range (real, market_data warehouse)", "",
           f"${out['week52']['low']:.2f} – ${out['week52']['high']:.2f} ({out['week52']['from']} to {out['week52']['to']}, {out['week52']['n_days']} trading days).", ""]
    md += ["## 5. A callback, not a new finding: the trend guard from the software check, on a different sector", "",
           "`finmodel cycle data/edgar/TRV.json --sector insurance --field net_income --revenue-field equity` — "
           "ROE, not the default operating-income margin, correctly required here (same override banking uses):", ""]
    diag = out["normalized"]["cycle_diagnostics"]
    md.append(f"FY{diag['fiscal_year'][:4]} ROE {diag['latest_margin']*100:.1f}% vs trailing-8yr median "
              f"{diag['median_margin_trailing_years']*100:.1f}% ({diag['deviation_pct']*100:+.1f}%) → "
              f"**{diag['flag'].split(' — CAUTION')[0]}**.")
    trend = out["normalized"]["trend_diagnostics"]
    md += ["", f"`trend_diagnostics()` fires **{trend['trend_strength']}** (r={trend['correlation']:.2f}, "
           f"{trend['direction']}) — the same guard `docs/FOOTBALL_FIELD_CSCO.md` established: TRV's real "
           "FY2018-2025 ROE genuinely improved (11.0% → 19.1%), and a trailing-median 'normalization' would "
           "misread that real, sustained improvement as a cyclical extreme to revert away from, understating "
           "current earning power the same way it would have for Salesforce. Checked, not assumed, that this "
           "isn't just the FY2022 denominator artifact from §2: 2024-2025's ROE — the highest in the whole "
           "series — comes AFTER book value had already recovered well past its pre-2022 peak, so the broader "
           "trend is real, sustained profitability improvement (higher rates flowing through to net investment "
           "income, a harder P&C pricing market), not a shrunken-equity illusion.", "",
           "## Method note", "",
           "Every book value / tangible book value / net income figure is from an SEC 10-K (via `finmodel.edgar`); "
           "every price is a live database query against `market_data`; both deals' per-share cash prices and "
           "announcement dates come from the target's own 8-K press releases (public record). Both real "
           "precedent targets are delisted and absent from the warehouse, so target-side deal premiums are "
           "omitted for the same reason as the banking, REIT and airline checks' precedents.", "",
           "Regenerate with `python scripts/football_field_trv.py`; chart at `out/charts_football_field_trv.html`."]
    return "\n".join(md)


if __name__ == "__main__":
    run()
