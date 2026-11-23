"""Smoke + sanity tests for the case-study report scripts under scripts/.

The scripts read SEC fundamentals from data/edgar/*.json and closing prices from a Postgres warehouse via ``psql``.
Here ``subprocess.run`` is replaced by a deterministic fake ``psql`` and ROOT is redirected to a tmp dir (data/ is
symlinked read-only), so every script runs end to end offline and writes its report/JSON/charts under tmp_path.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = sorted(p.name for p in (REPO / "scripts").glob("*.py"))
ROOT_LINE = "ROOT = Path(__file__).resolve().parent.parent"


def fake_price(ticker: str) -> float:
    return float(10 + sum(map(ord, ticker)) % 40)


def fake_psql(cmd, **kwargs):
    assert cmd[0] == "psql"
    q = cmd[-1]
    if "min(close_price)" in q:  # 52-week range
        out = "90.5|130.25|2025-07-01|2026-07-02|252"
    elif "s.ticker in (" in q:  # peer closing prices on the pricing date
        tickers = re.search(r"s\.ticker in \(([^)]*)\)", q).group(1).replace("'", "").split(",")
        out = "\n".join(f"{t.strip()}|{fake_price(t.strip())}" for t in tickers)
    elif "close_price" in q:  # single-ticker close
        t = re.search(r"s\.ticker='([^']+)'", q).group(1)
        out = str(fake_price(t))
    else:  # global_fundamentals cross-check: no rows
        out = ""
    return subprocess.CompletedProcess(cmd, 0, stdout=out + "\n", stderr="")


def run_script(name: str, tmp_path, monkeypatch, run=fake_psql):
    path = REPO / "scripts" / name
    text = path.read_text()
    assert text.count(ROOT_LINE) == 1
    text = text.replace(ROOT_LINE, f"ROOT = Path({str(tmp_path)!r})")
    (tmp_path / "data").symlink_to(REPO / "data")
    (tmp_path / "docs").mkdir()
    (tmp_path / "out").mkdir()
    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(sys, "path", [str(REPO / "scripts"), *sys.path])  # as when run: python scripts/x.py
    monkeypatch.delitem(sys.modules, "comps_validation", raising=False)  # sibling import in football_field_stld
    g = {"__name__": "__main__", "__file__": str(path)}
    exec(compile(text, str(path), "exec"), g)  # compiled under the real filename so coverage attributes lines
    return g


@pytest.mark.parametrize("name", SCRIPTS)
def test_script_runs_offline_and_writes_its_outputs(name, tmp_path, monkeypatch, capsys):
    run_script(name, tmp_path, monkeypatch)
    docs = sorted((tmp_path / "docs").glob("*.md"))
    outs = sorted((tmp_path / "out").iterdir())
    assert docs, f"{name} wrote no markdown report"
    assert outs, f"{name} wrote no json/html output"
    for md in docs:
        assert len(md.read_text().strip()) > 200
    for js in (p for p in outs if p.suffix == ".json"):
        assert isinstance(json.loads(js.read_text()), (dict, list))
    for html in (p for p in outs if p.suffix == ".html"):
        assert "<html" in html.read_text().lower() or "<svg" in html.read_text().lower() or "<div" in html.read_text()
    assert capsys.readouterr().out.strip(), f"{name} printed nothing"


# ---------------------------------------------------------------------------------------------------------------
# Invariants on the JSON each script writes. The fake psql prices are deterministic, so the scripts' arithmetic can be
# checked against values computed independently here, not just "ran without error".
# ---------------------------------------------------------------------------------------------------------------
STAT_KEYS = ("min", "p25", "median", "p75", "max")


def walk(node):
    yield node
    if isinstance(node, dict):
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


def outputs(name, tmp_path, monkeypatch):
    run_script(name, tmp_path, monkeypatch)
    return {p.name: json.loads(p.read_text()) for p in (tmp_path / "out").glob("*.json")}


FOOTBALL = [n for n in SCRIPTS if n.startswith("football_field_")]


@pytest.mark.parametrize("name", FOOTBALL)
def test_football_field_json_invariants(name, tmp_path, monkeypatch, capsys):
    ticker = name[len("football_field_"):-3].upper()
    docs = outputs(name, tmp_path, monkeypatch)
    assert docs
    data = next(iter(docs.values()))
    assert data["price"] == fake_price(ticker)  # target priced from the (fake) warehouse, not a constant
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["price_date"])
    assert f"{fake_price(ticker):.2f}" in capsys.readouterr().out  # the console summary reports that same price
    n_peers = n_ranges = n_stats = 0
    for node in walk(data):
        if not isinstance(node, dict):
            continue
        if {"ticker", "price", "diluted_shares", "equity_value"} <= node.keys():  # a trading-comps peer
            n_peers += 1
            assert node["price"] == fake_price(node["ticker"])
            assert node["equity_value"] == pytest.approx(node["price"] * node["diluted_shares"])
            m = node.get("metrics") or {}
            mult = node.get("multiples") or {}
            if "P/B LTM" in mult and m.get("book_value"):
                assert mult["P/B LTM"] == pytest.approx(node["equity_value"] / m["book_value"])
            if "P/E LTM" in mult and m.get("net_income"):
                assert mult["P/E LTM"] == pytest.approx(node["equity_value"] / m["net_income"])
        if all(isinstance(node.get(k), (int, float)) for k in ("low", "high")):  # a valuation range
            n_ranges += 1
            assert node["low"] <= node["high"]
            if isinstance(node.get("median"), (int, float)):
                assert node["low"] <= node["median"] <= node["high"]
        if all(isinstance(node.get(k), (int, float)) for k in STAT_KEYS):  # quartile summary
            n_stats += 1
            vals = [node[k] for k in STAT_KEYS]
            assert vals == sorted(vals)
    assert n_peers >= 3 and n_ranges >= 3 and n_stats >= 1
    ff = data["football_field"]
    assert ff["current_price"] == data["price"]
    methods = [i["method"] for i in ff["items"]]
    assert len(methods) == len(set(methods)) >= 3
    wk = [i for i in ff["items"] if "52" in i["method"]]
    assert wk and wk[0]["low"] == 90.5 and wk[0]["high"] == 130.25  # the fake 52-week row, passed through intact


def test_comps_validation_outputs_are_consistent(tmp_path, monkeypatch):
    docs = outputs("comps_validation.py", tmp_path, monkeypatch)
    assert docs
    for data in docs.values():
        for node in walk(data):
            if isinstance(node, dict) and {"ticker", "price", "diluted_shares", "equity_value"} <= node.keys():
                assert node["price"] == fake_price(node["ticker"])
                assert node["equity_value"] == pytest.approx(node["price"] * node["diluted_shares"])


def test_reports_are_deterministic(tmp_path_factory, monkeypatch):
    a, b = tmp_path_factory.mktemp("a"), tmp_path_factory.mktemp("b")
    ja = outputs("football_field_usb.py", a, monkeypatch)
    jb = outputs("football_field_usb.py", b, monkeypatch)
    assert ja == jb
    assert (a / "docs" / "FOOTBALL_FIELD_USB.md").read_text() == (b / "docs" / "FOOTBALL_FIELD_USB.md").read_text()


def test_ma_case_study_deal_arithmetic(tmp_path, monkeypatch):
    deals = outputs("ma_case_study.py", tmp_path, monkeypatch)["case_study_ma.json"]
    assert len(deals) == 3
    for res in deals:
        d, e = res["deal"], res["engine"]
        premium = d["offer_price"] / d["target_undisturbed"] - 1
        assert premium > 0
        f = e["funding"]
        assert f["pct_cash"] + f["pct_debt"] + f["pct_stock"] == pytest.approx(1)
        assert f["cash"] + f["debt"] + f["stock"] == pytest.approx(e["purchase_equity_value"])
        own = e["ownership"]
        assert own["acquirer_holders"] + own["target_holders"] == pytest.approx(1)
        assert e["accretion_dilution_pct"] == pytest.approx(e["combined"]["eps"] / e["acquirer"]["eps"] - 1)
        assert (e["accretion_dilution"] > 0) == (e["accretion_dilution_pct"] > 0)
        assert res["pro_forma_static"]["revenue"] == pytest.approx(
            res["pre_acquirer"]["revenue"] + res["pre_target"]["revenue"])
        assert res["pre_acquirer"]["ebitda"] >= res["pre_acquirer"]["ebit"]  # D&A is non-negative
        assert set(res["warehouse_crosscheck"].values()) == {None}  # fake psql returns no fundamentals rows
        assert [p["fy_end"] for p in res["post"]] == sorted(p["fy_end"] for p in res["post"])
    md = (tmp_path / "docs" / "CASE_STUDY_MA.md").read_text()
    for res in deals:
        assert f"## {res['deal']['name']}" in md


def test_comps_validation_report_matches_prices(tmp_path, monkeypatch):
    run_script("comps_validation.py", tmp_path, monkeypatch)
    md = next((tmp_path / "docs").glob("*.md")).read_text()
    assert "Prices: warehouse," in md  # fake psql answered, so the fallback constants were not used
    ff = next(iter(json.loads(p.read_text()) for p in (tmp_path / "out").glob("*.json")))
    rng = next(i for n in walk(ff) if isinstance(n, dict) and isinstance(n.get("items"), list)
               for i in n["items"] if "52-week" in i["method"])
    price = fake_price("STLD")
    assert rng["low"] == pytest.approx(price * 0.75) and rng["high"] == pytest.approx(price * 1.15)
