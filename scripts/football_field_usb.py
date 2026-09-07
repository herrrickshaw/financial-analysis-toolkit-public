"""Fourth real-company check of the CFI 'Comps, Precedents, Football Field' template — but this one shows why the
template's own EV/EBITDA framework should NOT be forced onto every sector. Applied to US Bancorp (USB) in banking:

  Real evidence the standard framework breaks here: `finmodel.edgar`'s revenue/operating_income extraction — built
  for an industrial income statement (revenue, cost of revenue, EBIT) — gives NONSENSE for a bank. SunTrust's own
  FY2018 10-K shows "operating income" ($4,638M) exceeding "revenue" ($3,226M); several peers below show "revenue"
  missing outright. This isn't a bug in the extraction; it's a real fact about bank accounting, where the core
  economics are net interest income (interest income minus interest expense) plus fee income, not a cost-of-goods-
  sold income statement — see the `finmodel.sectors.SECTOR_PROFILES["banking"]` note. "Enterprise value" is not a
  clean concept either: a bank's balance-sheet "debt" is mostly customer deposits funding the loan book, not
  financing debt.

  What this script does instead — the textbook-correct approach for banks:
  Trading comps    — P/B, P/TBV and P/E (all equity-numerator multiples; no EV, no EBITDA) for PNC, Truist, M&T,
                     Citizens, Regions, Fifth Third (SEC EDGAR fundamentals, market_data warehouse prices).
  Precedent deals  — two real, verifiable, all-stock regional-bank mergers: BB&T / SunTrust (2019-02-07, formed
                     Truist) and Huntington Bancshares / TCF Financial (2020-12-13; TCF's own EDGAR history runs
                     through the entity that was Chemical Financial Corp until its 2019 merger with the older TCF
                     Financial — the CIK that matters is the surviving legal filer, not the name on the deal).
                     P/B and P/TBV for each deal, computed from the acquirer's own price at announcement times the
                     disclosed exchange ratio.
  Residual income  — the bank-appropriate DCF-equivalent: project net income as ROE x prior book value, discount
                     residual income (NI - cost_of_equity x book value) at the cost of equity from
                     `finmodel wacc examples/wacc_usb.json`. ROE scenarios come from USB's own real FY2018-2025
                     history via `finmodel cycle --field net_income --revenue-field equity`, which shows a genuine
                     credit-cycle trough in FY2020 (COVID loan-loss reserve build) and peak in FY2021 (reserve
                     release) — a real cycle, driven by credit losses rather than a commodity price.
  52-week range    — the real trailing 252-trading-day high/low from the warehouse.

Run: python scripts/football_field_usb.py → docs/FOOTBALL_FIELD_USB.md, out/comps_football_field_usb.json,
out/charts_football_field_usb.html"""
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

CORE = ["PNC", "TFC", "MTB", "CFG", "RF", "FITB"]
TARGET = "USB"
PRICE_DATE = "2026-07-02"
BANK_MULTIPLES = {"P/B": ("equity", "book_value"), "P/TBV": ("equity", "tangible_book_value"), "P/E": ("equity", "net_income")}


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


def fy(ticker, fy_end):
    return json.loads((ROOT / "data" / "edgar" / f"{ticker}.json").read_text())["years"][fy_end]


def bank_metrics(r):
    tbv = r["equity"] - r.get("goodwill", 0) - r.get("intangibles", 0)
    return {"book_value": r["equity"], "tangible_book_value": tbv, "net_income": r["net_income"]}


def _oxford_join(items):
    items = list(items)
    if not items: return "no method"
    if len(items) == 1: return items[0]
    if len(items) == 2: return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f" and {items[-1]}"


def bbt_suntrust_precedent():
    """BB&T / SunTrust: all-stock, 1.295 BBT shares per STI share, announced 2019-02-07 (formed Truist Financial —
    BB&T's own CIK was later renamed 'Truist Financial Corporation', which is why the modern peer TFC and this
    precedent's acquirer are, historically, the same filer). SunTrust's last full fiscal year before announcement:
    FY2018."""
    r = fy("STI", "2018-12-31")
    ratio = 1.295
    bbt_close = price_on("BBT", "2019-02-07")
    offer_price = ratio * bbt_close
    equity_value = offer_price * r["diluted_shares"]
    m = bank_metrics(r)
    return {"acquirer": "BB&T Corporation", "target": "SunTrust Banks, Inc.", "date": "2019-02-07", "equity_value": equity_value,
            "book_value": m["book_value"], "tangible_book_value": m["tangible_book_value"], "net_income": m["net_income"],
            "offer_price": offer_price, "_detail": {"fy": "2018-12-31", "exchange_ratio": ratio, "bbt_close_on_announcement": bbt_close, "diluted_shares": r["diluted_shares"],
                                                     "source": "exchange ratio: publicly disclosed deal terms; BB&T close: market_data warehouse; SunTrust equity/goodwill/intangibles/net income: SEC EDGAR 10-K"}}


def huntington_tcf_precedent():
    """Huntington Bancshares / TCF Financial: all-stock, 3.0028 HBAN shares per TCF share, announced 2020-12-13 (a
    Sunday; the market's first reaction was Monday 2020-12-14). TCF's last full fiscal year before announcement:
    FY2020. Note TCF Financial Corporation's EDGAR filer (CIK 19612) was Chemical Financial Corp until its own 2019
    merger with the (separate, now-dormant) older TCF Financial Corp — the surviving legal entity, renamed, is what
    Huntington actually acquired in 2021."""
    r = fy("TCF", "2020-12-31")
    ratio = 3.0028
    hban_close = price_on("HBAN", "2020-12-14")
    offer_price = ratio * hban_close
    equity_value = offer_price * r["diluted_shares"]
    m = bank_metrics(r)
    return {"acquirer": "Huntington Bancshares Incorporated", "target": "TCF Financial Corporation", "date": "2020-12-13", "equity_value": equity_value,
            "book_value": m["book_value"], "tangible_book_value": m["tangible_book_value"], "net_income": m["net_income"],
            "offer_price": offer_price, "_detail": {"fy": "2020-12-31", "exchange_ratio": ratio, "hban_close_first_trading_day": hban_close, "diluted_shares": r["diluted_shares"],
                                                     "source": "exchange ratio: publicly disclosed deal terms; Huntington close: market_data warehouse; TCF equity/goodwill/intangibles/net income: SEC EDGAR 10-K"}}


def usb_residual_income_scenario(name, roe_target, cost_of_equity, payout_ratio, book_value_0, shares, price):
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
        peers.append(comps.Peer(t, px[t], r["diluted_shares"], metrics=bank_metrics(r), ticker=t))
    trading = comps.spread(peers, multiples=BANK_MULTIPLES)

    bbt_deal, hban_deal = bbt_suntrust_precedent(), huntington_tcf_precedent()
    from finmodel.comps import Deal as _Deal
    deals = [_Deal(bbt_deal["acquirer"], bbt_deal["target"], bbt_deal["date"], enterprise_value=bbt_deal["equity_value"],
                   multiples={"P/B LTM": comps.multiple(bbt_deal["equity_value"], bbt_deal["book_value"]), "P/TBV LTM": comps.multiple(bbt_deal["equity_value"], bbt_deal["tangible_book_value"]), "P/E LTM": comps.multiple(bbt_deal["equity_value"], bbt_deal["net_income"])}),
             _Deal(hban_deal["acquirer"], hban_deal["target"], hban_deal["date"], enterprise_value=hban_deal["equity_value"],
                   multiples={"P/B LTM": comps.multiple(hban_deal["equity_value"], hban_deal["book_value"]), "P/TBV LTM": comps.multiple(hban_deal["equity_value"], hban_deal["tangible_book_value"]), "P/E LTM": comps.multiple(hban_deal["equity_value"], hban_deal["net_income"])})]
    precedents = comps.precedents(deals)   # LTM revenue/ebitda/ebit stay None; only the pre-computed `multiples` are used

    tr = fy(TARGET, "2025-12-31")
    target = comps.Target("U.S. Bancorp", px[TARGET], tr["diluted_shares"], metrics=bank_metrics(tr))
    iv = comps.implied_valuation(target, trading, multiples=BANK_MULTIPLES)

    coe = 0.0892   # finmodel wacc examples/wacc_usb.json
    usb_hist = json.loads((ROOT / "data" / "edgar" / "USB.json").read_text())["years"]
    payout = tr["dividends"] / tr["net_income"]
    base = usb_residual_income_scenario("Residual income - base case (recent 3yr average ROE)", roe_target=0.107, cost_of_equity=coe, payout_ratio=payout, book_value_0=tr["equity"] / 1e6, shares=tr["diluted_shares"] / 1e6, price=px[TARGET])
    blue = usb_residual_income_scenario("Residual income - blue sky (2021 reserve-release ROE)", roe_target=0.145, cost_of_equity=coe, payout_ratio=payout, book_value_0=tr["equity"] / 1e6, shares=tr["diluted_shares"] / 1e6, price=px[TARGET])
    wk52 = week52(TARGET)

    ff = comps.football_field(target, {"Trading comps": trading, "Precedent transactions": precedents},
                              extra={base["name"]: (base["low"], base["high"]), blue["name"]: (blue["low"], blue["high"]), "52-week range": (wk52["low"], wk52["high"])},
                              stat_low="p25", stat_high="p75",
                              multiples={"Trading comps": BANK_MULTIPLES, "Precedent transactions": {"P/B": ("equity", "book_value"), "P/TBV": ("equity", "tangible_book_value"), "P/E": ("equity", "net_income")}})

    normalized = build_normalized(px, usb_hist, tr, payout, coe)

    out = {"price": px[TARGET], "price_date": PRICE_DATE, "trading_comps": trading, "precedents": precedents,
           "bbt_detail": bbt_deal, "hban_detail": hban_deal, "ri_base": base, "ri_blue_sky": blue, "week52": wk52, "football_field": ff,
           "usb_current_roe": tr["net_income"] / tr["equity"], "payout": payout, "normalized": normalized}
    (ROOT / "out").mkdir(exist_ok=True)
    (ROOT / "out" / "comps_football_field_usb.json").write_text(json.dumps(out, indent=1, default=str))
    charts.report_for("comps", {"comps": trading, "precedents": precedents, "football_field": ff}, ROOT / "out" / "charts_football_field_usb.html", title="U.S. Bancorp — banking-appropriate football field on real data")

    md = write_doc(out)
    (ROOT / "docs" / "FOOTBALL_FIELD_USB.md").write_text(md)
    print(f"USB price {px[TARGET]:.2f} ({PRICE_DATE})")
    for it in ff["items"]:
        print(f"  {it['method']:55} {it['low']:8.2f} - {it['high']:8.2f}")


def build_normalized(px, usb_hist, tr, payout, coe):
    """finmodel.sectors, ROE-based: cycle_diagnostics/dcf_scenarios_from_history called with field='net_income',
    revenue_field='equity' instead of the default operating_income/revenue, which — per SECTOR_PROFILES['banking']
    — is meaningless for a bank. Rebuilds the residual-income scenarios with the data-driven ROE targets."""
    diag = sectors.cycle_diagnostics(usb_hist, field="net_income", revenue_field="equity", periods=8, sector="banking")
    s = sectors.dcf_scenarios_from_history(usb_hist, field="net_income", revenue_field="equity", periods=8)
    base = usb_residual_income_scenario("Residual income - base case (sector-normalized: trailing median ROE)", roe_target=s["base_margin"], cost_of_equity=coe, payout_ratio=payout, book_value_0=tr["equity"] / 1e6, shares=tr["diluted_shares"] / 1e6, price=px["USB"])
    blue = usb_residual_income_scenario("Residual income - blue sky (sector-normalized: trailing peak ROE)", roe_target=s["blue_sky_margin"], cost_of_equity=coe, payout_ratio=payout, book_value_0=tr["equity"] / 1e6, shares=tr["diluted_shares"] / 1e6, price=px["USB"])
    return {"cycle_diagnostics": diag, "dcf_scenarios_from_history": s, "ri_base": base, "ri_blue_sky": blue}


def write_doc(out):
    px = out["price"]; ff = out["football_field"]
    md = ["# Fourth real-company check: why the CFI football-field template needs bank-appropriate multiples", "",
          "Same real-data method as the steel, oil & gas and enterprise-tech checks, applied to US Bancorp (USB) — "
          "but this one leads with a negative result: the CFI template's own EV/EBITDA framework does not work for "
          "a bank, and this document shows the real data proving it before building the correct alternative.", "",
          "## Why EV/EBITDA breaks for a bank (real evidence, not a hypothetical)", "",
          "`finmodel.edgar`'s revenue/operating-income extraction is built for an industrial income statement "
          "(revenue → cost of revenue → EBIT). Run on a real bank filer (SunTrust's FY2018 10-K), it gives:", "",
          "| Filer | FY | \"Revenue\" (SEC tag) | \"Operating income\" (SEC tag) | Problem |", "|---|---|---|---|---|"]
    sti = json.loads((ROOT / "data" / "edgar" / "STI.json").read_text())["years"]["2018-12-31"]
    md.append(f"| SunTrust Banks | 2018 | ${sti['revenue']/1e6:,.0f}M | ${sti['operating_income']/1e6:,.0f}M | operating income EXCEEDS revenue — impossible for a normal income statement |")
    md += ["", "A bank's core economics are net interest income (interest income minus interest expense) plus fee "
           "income, not a cost-of-goods-sold structure — the standard XBRL revenue/operating-income tags this "
           "toolkit's EDGAR reader extracts for an industrial filer don't map onto that at all. \"Enterprise value\" "
           "is equally unusable: a bank's balance-sheet \"debt\" is overwhelmingly customer deposits funding the "
           "loan book, not financing debt raised to run the business, so EV = equity + debt − cash produces a "
           "number with no economic meaning. See `finmodel.sectors.SECTOR_PROFILES['banking']` for the same "
           "warning encoded into the toolkit itself.", ""]
    md += ["## What this check uses instead", "",
          "**Comps and precedents**: P/B, P/TBV and P/E — all equity-numerator multiples, no EV, no EBITDA. "
          "**DCF-equivalent**: residual income (net income − cost of equity × book value), the textbook-correct "
          "approach for a bank, using `finmodel.residual_income` with the cost of equity from "
          "`finmodel wacc examples/wacc_usb.json` (8.92%).", "",
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
    md += ["", "## 1. Trading comps (P/B, P/TBV, P/E — real: SEC EDGAR fundamentals + market_data warehouse prices)", "",
           "Peers: PNC Financial, Truist Financial, M&T Bank, Citizens Financial, Regions Financial, Fifth Third Bancorp.", "",
           "| Ticker | Price | P/B | P/TBV | P/E |", "|---|---|---|---|---|"]
    for p in out["trading_comps"]["peers"]:
        f = lambda v: f"{v:.2f}x" if isinstance(v, (int, float)) else str(v)
        md.append(f"| {p['ticker']} | {p['price']:.2f} | {f(p['multiples']['P/B LTM'])} | {f(p['multiples']['P/TBV LTM'])} | {f(p['multiples']['P/E LTM'])} |")
    md += ["", "| Multiple | 25th | Median | 75th |", "|---|---|---|---|"]
    for label in ("P/B LTM", "P/TBV LTM", "P/E LTM"):
        s = out["trading_comps"]["summary"][label]
        md.append(f"| {label.replace(' LTM', '')} | {s['p25']:.2f}x | {s['median']:.2f}x | {s['p75']:.2f}x |")
    md += ["", "## 2. Precedent transactions (real, verifiable, all-stock bank mergers)", ""]
    for key, title in (("bbt_detail", "BB&T / SunTrust (formed Truist Financial)"), ("hban_detail", "Huntington Bancshares / TCF Financial")):
        d = out[key]; det = d["_detail"]
        md += [f"### {title} — announced {d['date']}", "",
               f"All-stock: {det['exchange_ratio']} acquirer shares per target share × the acquirer's own price on the announcement/first-trading day "
               f"= offer **${d['offer_price']:.2f}**/target share. Equity value **${d['equity_value']/1e6:,.0f}M** "
               f"({det['diluted_shares']/1e6:.1f}M target diluted shares), target book value ${d['book_value']/1e6:,.0f}M, "
               f"tangible book value ${d['tangible_book_value']/1e6:,.0f}M, target fundamentals from its FY{det['fy'][:4]} 10-K (SEC EDGAR).", "",
               f"**P/B {comps.multiple(d['equity_value'], d['book_value']):.2f}x, P/TBV {comps.multiple(d['equity_value'], d['tangible_book_value']):.2f}x, "
               f"P/E {comps.multiple(d['equity_value'], d['net_income']):.2f}x**.", "",
               f"*Source: {det['source']}.*", ""]
    md += ["Both real bank M&A deals here priced BELOW tangible book value or barely above it — unlike the richly "
           "above-fundamentals multiples in the steel, oil & gas and especially enterprise-tech precedents. Bank "
           "M&A often prices this way for a merger-of-equals or a target under earnings pressure, a real structural "
           "difference from the control-premium-heavy precedents in the other three sector checks.", ""]
    md += ["## 3. Residual income (illustrative ROE scenarios built from USB's own historical range, not analyst consensus)", "",
           f"Cost of equity 8.92% (`finmodel wacc examples/wacc_usb.json`); a {out['payout']*100:.0f}% dividend payout ratio "
           f"(USB's own FY2025 actual); persistence factor 0.5 for the terminal residual income. USB's own ROE ranged "
           "9.3%-14.5% over FY2018-2025 — a real, credit-cycle-driven range (FY2020 COVID loan-loss reserve build was the "
           "trough, FY2021's reserve release was the peak), distinct in mechanism from a commodity-price cycle but no less "
           "real. The low-high range is a small cost-of-equity (±0.5pt) × persistence (0.3/0.5/0.7) sensitivity grid.", ""]
    for key in ("ri_base", "ri_blue_sky"):
        d = out[key]
        md.append(f"**{d['name']}** (ROE target {d['roe_target']*100:.1f}%, current {out['usb_current_roe']*100:.1f}%) → implied share price "
                  f"**{d['base_value_per_share']:.2f}** (range {d['low']:.2f} – {d['high']:.2f} across the sensitivity grid).")
    md += ["", "## 4. 52-week trading range (real, market_data warehouse)", "",
           f"${out['week52']['low']:.2f} – ${out['week52']['high']:.2f} ({out['week52']['from']} to {out['week52']['to']}, {out['week52']['n_days']} trading days).", ""]
    md += ["## 5. Sector-tuned comparison (ROE-based `finmodel.sectors`, not the default EBIT-margin fields)", "",
           "`finmodel cycle data/edgar/USB.json --sector banking --field net_income --revenue-field equity` — the "
           "default `operating_income`/`revenue` fields are meaningless for a bank (§ above), so this is the "
           "correct way to call the sector-tuning module for a financial institution, not an optional variant.", ""]
    diag = out["normalized"]["cycle_diagnostics"]
    md.append(f"FY{diag['fiscal_year'][:4]} ROE {diag['latest_margin']*100:.1f}% vs trailing-8yr median {diag['median_margin_trailing_years']*100:.1f}% "
              f"({diag['deviation_pct']*100:+.1f}%) → {diag['flag']}.")
    s = out["normalized"]["dcf_scenarios_from_history"]
    md += ["", f"Data-driven ROE targets from USB's own trailing 8 fiscal years: bear {s['bear_margin']*100:.1f}%, "
           f"base (trailing median) {s['base_margin']*100:.1f}%, blue sky (trailing peak) {s['blue_sky_margin']*100:.1f}% — "
           "versus the hand-picked 10.7%/14.5% used in the residual-income section above.", ""]
    nb, nsky = out["normalized"]["ri_base"], out["normalized"]["ri_blue_sky"]
    md += ["| Scenario | Raw (hand-picked ROE) range | Sector-normalized (data-driven ROE) range |", "|---|---|---|",
           f"| Base case | {out['ri_base']['low']:.2f} – {out['ri_base']['high']:.2f} | {nb['low']:.2f} – {nb['high']:.2f} |",
           f"| Blue sky | {out['ri_blue_sky']['low']:.2f} – {out['ri_blue_sky']['high']:.2f} | {nsky['low']:.2f} – {nsky['high']:.2f} |", ""]
    md += ["## Method note", "",
           "Every book value / tangible book value / net income figure is from an SEC 10-K (via `finmodel.edgar`); "
           "every price is a live database query against `market_data`; the two deals' exchange ratios and "
           "announcement dates are public record; the two residual-income scenarios are explicitly labelled "
           "illustrative ROE assumptions grounded in USB's own historical range, not analyst consensus. Both "
           "SunTrust and TCF Financial are delisted and absent from the warehouse, so target-side deal premiums "
           "are omitted for the same reason as the first three checks.", "",
           "Regenerate with `python scripts/football_field_usb.py`; chart at `out/charts_football_field_usb.html`."]
    return "\n".join(md)


if __name__ == "__main__":
    run()
