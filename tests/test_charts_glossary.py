import json
from pathlib import Path
from finmodel import charts, three_statement as ts, dcf, lbo, merger, projection

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "examples"


def _load(n): return json.loads((EX / n).read_text())


def test_chart_reports_render(tmp_path):
    r3 = ts.from_dict(_load("cfi_three_statement.json")).to_dict()
    inp = dcf.DCFInputs(**dcf.clean(_load("cfi_dcf.json"))); rd = dcf.run(inp)
    rd["sensitivity"] = dcf.sensitivity(inp, [0.10, 0.12, 0.14], [0.02, 0.03, 0.04])
    results = {"three_statement": r3, "dcf": rd, "lbo": lbo.from_dict(_load("lbo_asm.json")),
               "merger": merger.from_dict(_load("merger_biws.json")), "projection": projection.from_dict(_load("projection_demo.json"))}
    for eng, res in results.items():
        p = charts.report_for(eng, res, tmp_path / f"{eng}.html")
        html = p.read_text()
        n_cards = html.count('<div class="card">'); n_svg = html.count("<svg ")
        assert n_cards >= len(charts.CATALOG[eng]["charts"]) - 1, eng      # tiles are not a card
        assert n_svg == n_cards and "<title>" in html and "data-theme" in html, eng
        assert "NaN" not in html and ">nan<" not in html and "\"nan\"" not in html, eng


def test_chart_primitives():
    s = charts.column_chart(["a", "b"], {"x": [1, -2], "y": [3, 4]}, stacked=True)
    assert s.startswith("<svg") and s.count('class="mark"') == 4
    w = charts.waterfall([("start", 100), ("up", 20), ("down", -30), ("end", 90)], totals=(0, 3))
    assert w.count('class="mark"') == 4
    h = charts.heatmap(["r1", "r2"], ["c1", "c2"], [[0.1, -0.1], [0.2, 0.0]], diverging_center=0.0)
    assert h.count('<rect class="mark"') == 4
    assert charts._fmt(0.1234, "pct") == "12.3%" and charts._fmt(1234567) == "1.2M"


def test_range_bars_wraps_long_labels_without_overflow():
    short = charts.range_bars([("Trading comps", 10, 20), ("52-week range", 5, 40)])
    assert '<tspan' not in short and short.count('<text class="t"') == 2   # short labels: one line each, no wrap needed
    long_label = "DCF - base case (margin recovers toward FY2024 level)"
    r = charts.range_bars([(long_label, 10, 20), ("Precedent transactions", 5, 15)])
    import re
    label_x = [float(m) for m in re.findall(r'<text class="t" x="(-?[\d.]+)"', r)]
    svg_w = int(re.search(r'viewBox="0 0 (\d+)', r).group(1))
    assert label_x and all(0 <= x < svg_w for x in label_x)   # no label anchor sits off-canvas
    assert r.count('<text class="t" x=') > 2   # the long label wrapped onto a second line, adding a text node
    assert charts._wrap_label("short", 20) == ["short"]
    assert charts._wrap_label("a rather long label that needs wrapping onto two lines", 20) == ["a rather long label", "that needs wrapping…"]


def test_glossary_data():
    g = json.loads((ROOT / "data/glossary.json").read_text())
    terms = {e["term"].lower() for e in g["entries"]}
    assert len(g["entries"]) >= 170 and len(g["gaap_vs_ifrs"]) >= 15
    for t in ("ebitda", "goodwill", "balance sheet", "cash sweep", "working capital", "accretion / dilution"):
        assert t in terms, t
    lease = next(e for e in g["entries"] if e["term"].startswith("Leases"))
    assert "IFRS 16" in lease["gaap_vs_ifrs"]
    assert all(e["definition"] for e in g["entries"])
