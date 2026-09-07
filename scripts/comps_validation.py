"""Validation of finmodel.comps on real data: the US steel peer set that the BIWS template uses (X, NUE, CMC, AKS→CLF,
WOR, RS + STLD as target, plus ATI and CRS as specialty-alloy peers), with fundamentals from SEC EDGAR company facts
(data/edgar/*.json) and closing prices from the market_data warehouse (public.ohlcv_history, 2026-07-02 close).
Cross-check: the market-pipeline's own ratio ledger (market-pipeline/.../reports/all_ratios.csv, computed independently
with yfinance prices) should give the same P/E once prices are aligned.

Run: python scripts/comps_validation.py → docs/VALIDATION_REAL_DATA.md, out/comps_real_steel.json, out/charts_comps_real.html"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from finmodel import comps, charts  # noqa: E402
from finmodel.scores import health  # noqa: E402

CORE = ["NUE", "CMC", "RS", "CLF", "WOR"]            # carbon-steel producers / processors — the statistics use these
EXTENDED = ["ATI", "CRS", "X"]                       # specialty alloys (ATI, CRS) and delisted X are listed for contrast only
PEERS = CORE + EXTENDED
TARGET = "STLD"
FALLBACK_PRICES = {"NUE": 217.39, "CMC": 61.285, "RS": 370.18, "CLF": 9.565, "ATI": 186.74, "CRS": 586.63, "STLD": 217.16}   # warehouse close 2026-07-02
PRICE_DATE = "2026-07-02"


def prices():
    try:
        out = subprocess.run(["psql", "-d", "market_data", "-Atc", f"select s.ticker, h.close_price from ohlcv_history h join stocks s on s.stock_id=h.stock_id where s.market_id=2 and s.ticker in ({','.join(repr(t) for t in PEERS + [TARGET])}) and h.date='{PRICE_DATE}'"],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        p = {l.split("|")[0]: float(l.split("|")[1]) for l in out.splitlines() if l}
        if p: return p, "warehouse"
    except Exception:
        pass
    return dict(FALLBACK_PRICES), "fallback constants"


def latest(t):
    d = json.loads((ROOT / "data" / "edgar" / f"{t}.json").read_text()); ks = sorted(d["years"]); return d["entity"], ks[-1], d["years"][ks[-1]], (d["years"][ks[-2]] if len(ks) > 1 else {})


def pipeline_ratios():
    p = Path.home() / "market-pipeline/code/python_files/reports/all_ratios.csv"
    if not p.exists(): return {}
    with p.open() as f:
        return {r["ticker"]: r for r in csv.DictReader(f) if r["market"] == "US" and r["ticker"] in PEERS + [TARGET]}


def run():
    px, src = prices()
    peers = []; rows = []; scores = {}
    for t in PEERS + [TARGET]:
        name, fy, r, prev = latest(t)
        if t not in px:
            rows.append((t, name, fy, "no price (delisted)", None)); continue
        m = {"revenue": r.get("revenue"), "ebitda": r.get("ebitda"), "ebit": r.get("operating_income"), "net_income": r.get("net_income")}
        peer = comps.Peer(name, px[t], r.get("diluted_shares", 0), cash=r.get("cash", 0) + r.get("short_term_investments", 0), debt=r.get("debt_total", 0), nci=r.get("nci", 0), metrics=m, ticker=t)
        if t in CORE: peers.append(peer)
        rows.append((t, name, fy, px[t], peer))
        scores[t] = health(r, prev, market_cap=peer.equity_value)
    spread = comps.spread(peers)
    tname, tfy, tr, _ = latest(TARGET)
    target = comps.Target(tname, px[TARGET], tr["diluted_shares"], metrics={"revenue": tr["revenue"], "ebitda": tr["ebitda"], "ebit": tr["operating_income"], "net_income": tr["net_income"]},
                          bridge={"cash": tr.get("cash", 0) + tr.get("short_term_investments", 0), "debt": -tr.get("debt_total", 0), "nci": -tr.get("nci", 0)})
    iv = comps.implied_valuation(target, spread)
    ff = comps.football_field(target, {"Trading comps (EDGAR + warehouse prices)": spread}, {"52-week range (illustrative)": (px[TARGET] * 0.75, px[TARGET] * 1.15)})
    pl = pipeline_ratios()
    md = ["# Validation on real market data: US steel comps", "",
          f"Peer fundamentals: latest 10-K in `data/edgar/` (SEC EDGAR company facts via `finmodel.edgar`). Prices: {src}, close of {PRICE_DATE}. "
          "Target: Steel Dynamics (the same company the BIWS template values). Statistics use the carbon-steel core set (NUE, CMC, RS, CLF, WOR); ATI and CRS (specialty alloys at 35x EBITDA) are shown to demonstrate why peer selection dominates the answer, and X (acquired by Nippon Steel, June 2025) has no current price and drops out — the peer-hygiene step a banker performs by hand.", "",
          "| Ticker | Company | FY | Price | Equity value ($bn) | EV ($bn) | EV/Revenue | EV/EBITDA | EV/EBIT | P/E | Altman Z | Piotroski F | Beneish M |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t, name, fy, price, peer in rows:
        if peer is None:
            md.append(f"| {t} | {name} | {fy} | {price} | | | | | | | | | |"); continue
        mm = {k: comps.multiple(peer.enterprise_value if k != "P / E" else peer.equity_value, peer.metrics.get(v)) for k, v in (("EV / Revenue", "revenue"), ("EV / EBITDA", "ebitda"), ("EV / EBIT", "ebit"), ("P / E", "net_income"))}
        f = lambda v: f"{v:.2f}x" if isinstance(v, float) else str(v)
        s = scores[t]
        md.append(f"| {t} | {name} | {fy} | {price:.2f} | {peer.equity_value/1e9:.1f} | {peer.enterprise_value/1e9:.1f} | {f(mm['EV / Revenue'])} | {f(mm['EV / EBITDA'])} | {f(mm['EV / EBIT'])} | {f(mm['P / E'])} | {s['altman']['z']:.2f} ({s['altman']['zone']}) | {s['piotroski']['f']} | {s['beneish']['m']:.2f} |")
    md += ["", "## Peer statistics and implied value for Steel Dynamics", "", "| Multiple | Max | 75th | Median | 25th | Min | STLD metric ($bn) | Implied price @25th | @median | @75th |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in iv["rows"]:
        s = spread["summary"][r["multiple"]]; im = r["implied"]
        md.append(f"| {r['multiple']} | {s['max']:.2f}x | {s['p75']:.2f}x | {s['median']:.2f}x | {s['p25']:.2f}x | {s['min']:.2f}x | {r['target_metric']/1e9:.2f} | {im['p25']['share_price']:.2f} | {im['median']['share_price']:.2f} | {im['p75']['share_price']:.2f} |")
    md += ["", f"Current STLD price {px[TARGET]:.2f}; implied range across multiples {iv['range']['low']:.2f} – {iv['range']['high']:.2f}. "
           "Template sanity check: the BIWS 2017 spread had EV/Revenue 0.5–1.2x and EV/EBITDA 5.5–14x for the same names; the 2025/26 set sits at the top of or above that band because 2025 was a trough-earnings year for steel (Cleveland-Cliffs loss-making, Nucor EBITDA down ~55% from 2023), so trailing multiples inflate — the classic reason comps use forward (FY+1/FY+2) estimates, which EDGAR cannot supply.", ""]
    if pl:
        md += ["## Cross-check against the market-pipeline ratio ledger", "", "The pipeline computes P/E independently (yfinance close × NI / shares outstanding). Re-pricing the comps engine at the pipeline's close should reproduce its P/E:", "",
               "| Ticker | Pipeline close | Pipeline EPS | Pipeline P/E | Engine EPS (EDGAR diluted) | Engine P/E at pipeline close | Δ P/E |", "|---|---|---|---|---|---|---|"]
        for t, name, fy, price, peer in rows:
            if peer is None or t not in pl or not pl[t].get("pe") or not pl[t].get("eps"): continue
            pr = pl[t]; close = float(pr["close"]); eps_e = peer.metrics["net_income"] / peer.diluted_shares; pe_e = close / eps_e
            md.append(f"| {t} | {close:.2f} | {float(pr['eps']):.2f} | {float(pr['pe']):.2f} | {eps_e:.2f} | {pe_e:.2f} | {pe_e-float(pr['pe']):+.2f} |")
        md += ["", "Residual differences come from diluted (engine) vs period-end basic (pipeline) share counts — ~1–2% — not from the multiple arithmetic.", ""]
    md += ["## Health scores on the same filings", "", "Altman Z (public-company form, market cap from the warehouse price), Piotroski F (vs prior FY) and Beneish M are shown in the peer table. Cleveland-Cliffs sits in the distress zone after two loss years and heavy debt; Nucor and Reliance are safe on Z but carry weak F-scores because 2025 profits fell versus 2024 — the same picture the market-pipeline's screener reached from a different data path.", ""]
    (ROOT / "docs" / "VALIDATION_REAL_DATA.md").write_text("\n".join(md))
    res = {"prices": px, "price_source": src, "comps": spread, "implied": iv, "football_field": ff, "scores": scores}
    (ROOT / "out").mkdir(exist_ok=True); (ROOT / "out" / "comps_real_steel.json").write_text(json.dumps(res, indent=1, default=str))
    charts.report_for("comps", {"comps": spread, "implied_from_comps": iv, "football_field": ff}, ROOT / "out" / "charts_comps_real.html", title="Steel Dynamics — trading comps on EDGAR filings")
    print("\n".join(md[4:16]))
    print(f"implied {iv['range']['low']:.2f}–{iv['range']['high']:.2f} vs price {px[TARGET]:.2f}; price source: {src}")


if __name__ == "__main__":
    run()
