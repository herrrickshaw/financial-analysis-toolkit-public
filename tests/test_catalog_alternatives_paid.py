"""Offline tests for finmodel.catalog / alternatives / paid_templates.

Everything runs against a synthetic catalog dir under tmp_path and a faked urllib, so nothing is read from or
written to the repo's catalog/ folder and nothing touches the network.
"""
from __future__ import annotations

import hashlib
import json
import urllib.error

import pytest

from finmodel import alternatives, catalog, paid_templates

RAW = "\n".join([
    "LBO Model|Unlock|https://cfi.example/lbo",
    "",
    "Free DCF Template|Download|https://cfi.example/dcf",
    "Bare Title",  # no status / url -> treated as paid, url None
])
VERIFIED = "\n".join([
    "damodaran|fcffginzu.xlsx|https://d.example/fcffginzu.xlsx|200|2048",
    "",
    "short|line",  # fewer than 3 fields -> skipped
    "asimplemodel|Simple LBO Model.xlsx|https://a.example/lbo.xlsx|200|notanumber\r",
    "macabacus|Merger Model.xlsx|https://m.example/merger.xlsx",  # no status / size
    "biws|DCF Valuation Model.xlsx|https://b.example/dcf.xlsx|404|10",
])


@pytest.fixture
def cdir(tmp_path):
    d = tmp_path / "catalog"
    d.mkdir()
    (tmp_path / "docs").mkdir()
    (d / "cfi_dashboard_raw.txt").write_text(RAW)
    (d / "open_sources_verified.txt").write_text(VERIFIED)
    return d


# ----------------------------------------------------------------------------------------------- catalog.build
def test_build_parses_both_inputs_and_writes_outputs(cdir):
    cat = catalog.build(cdir)
    by_id = {e["id"]: e for e in cat["entries"]}
    assert len(cat["entries"]) == 3 + 4  # blank / malformed lines dropped
    lbo = by_id["cfi/LBO-Model"]
    assert (lbo["access"], lbo["url"], lbo["source"]) == ("cfi-paid", "https://cfi.example/lbo", "cfi")
    assert by_id["cfi/Free-DCF-Template"]["access"] == "cfi-login"
    bare = by_id["cfi/Bare-Title"]
    assert bare["access"] == "cfi-paid" and bare["url"] is None
    d = by_id["damodaran/fcffginzu"]
    assert (d["size"], d["verified_status"], d["access"], d["filename"]) == (2048, "200", "public", "fcffginzu.xlsx")
    assert by_id["asimplemodel/Simple-LBO-Model"]["size"] is None  # non-numeric size
    assert by_id["macabacus/Merger-Model"]["verified_status"] is None
    assert cat["counts"] == {"cfi:cfi-paid": 2, "cfi:cfi-login": 1, "damodaran:public": 1,
                             "asimplemodel:public": 1, "macabacus:public": 1, "biws:public": 1}
    assert json.loads((cdir / "catalog.json").read_text())["counts"] == cat["counts"]
    assert "## damodaran" in (cdir / "catalog.md").read_text()


def test_build_without_inputs_is_empty(tmp_path):
    cat = catalog.build(tmp_path)
    assert cat["entries"] == [] and cat["counts"] == {}


def test_load_reads_existing_json_and_builds_when_missing(cdir):
    assert not (cdir / "catalog.json").exists()
    built = catalog.load(cdir)  # builds
    assert (cdir / "catalog.json").exists()
    (cdir / "catalog.json").write_text(json.dumps({"marker": 1}))
    assert catalog.load(cdir) == {"marker": 1}  # reads, does not rebuild
    assert built["entries"]


def test_to_markdown_formats_size_and_skips_empty_sources(cdir):
    md = catalog.to_markdown(catalog.build(cdir))
    assert "| fcffginzu | public | 2 KB | 200 | https://d.example/fcffginzu.xlsx |" in md
    assert "## cfi — Corporate Finance Institute" in md
    assert "## exinfm" not in md  # no rows for that source
    assert "| Bare Title | cfi-paid |  |  |  |" in md  # url None -> blank


# ----------------------------------------------------------------------------------------------- filenames
class Hdr(dict):
    pass


@pytest.mark.parametrize("url,headers,expected", [
    ("https://x/y", {"Content-Disposition": 'attachment; filename="a%20b.xlsx"'}, "a b.xlsx"),
    ("https://x/y", {"Content-Disposition": "attachment; filename*=UTF-8''r%C3%A9sum%C3%A9.pdf"}, "résumé.pdf"),
    ("https://x/dir/file.xls?q=1", {}, "file.xls"),
    ("https://x/dir/no_ext", {"Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}, "fb.xlsx"),
    ("https://x/", {"Content-Type": "application/vnd.ms-excel"}, "fb.xls"),
    ("https://x/", {"Content-Type": "application/pdf"}, "fb.pdf"),
    ("https://x/", {"Content-Type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"}, "fb.pptx"),
    ("https://x/", {"Content-Type": "text/html"}, "fb.bin"),
    ("https://x/" + "a" * 130 + ".xlsx", {"Content-Type": "application/pdf"}, "fb.pdf"),  # over-long name ignored
])
def test_filename_from_response(url, headers, expected):
    assert catalog._filename_from_response(url, Hdr(headers), "fb") == expected


def test_filename_from_response_without_header_mapping():
    assert catalog._filename_from_response("https://x/", object(), "fb") == "fb.bin"


# ----------------------------------------------------------------------------------------------- network fakes
class FakeResp:
    def __init__(self, data=b"", headers=None, status=200):
        self._d, self.headers, self.status = data, headers or {}, status

    def read(self):
        return self._d

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_head_success_http_error_and_exception(monkeypatch):
    seen = {}

    def ok(req, timeout):
        seen["method"], seen["ua"], seen["timeout"] = req.get_method(), req.get_header("User-agent"), timeout
        return FakeResp(headers={"Content-Length": "5"}, status=200)

    monkeypatch.setattr(catalog.urllib.request, "urlopen", ok)
    status, h = catalog._head("https://x", {"X-A": "1"}, timeout=7)
    assert status == 200 and h["Content-Length"] == "5"
    assert seen == {"method": "HEAD", "ua": catalog.UA, "timeout": 7}

    def http_err(req, timeout):
        raise urllib.error.HTTPError("https://x", 403, "no", {"k": "v"}, None)

    monkeypatch.setattr(catalog.urllib.request, "urlopen", http_err)
    status, h = catalog._head("https://x", {})
    assert status == 403 and h["k"] == "v"

    def boom(req, timeout):
        raise OSError("down")

    monkeypatch.setattr(catalog.urllib.request, "urlopen", boom)
    assert catalog._head("https://x", {}) == (None, {"error": "down"})


def test_verify_only_touches_public_entries(cdir, monkeypatch):
    cat = catalog.build(cdir)
    calls = []

    def fake_head(url, headers, timeout=25):
        calls.append(url)
        if "m.example" in url:
            return None, {"error": "x"}
        if "a.example" in url:
            return 200, {"Content-Length": "oops"}  # unparsable length -> size left alone
        if "b.example" in url:
            return 200, object()  # no .get -> size untouched
        return 200, {"Content-Length": "999"}

    monkeypatch.setattr(catalog, "_head", fake_head)
    out = catalog.verify(cat)
    by_id = {e["id"]: e for e in out["entries"]}
    assert all("cfi.example" not in c for c in calls) and len(calls) == 4
    assert by_id["damodaran/fcffginzu"]["size"] == 999 and by_id["damodaran/fcffginzu"]["verified_status"] == "200"
    assert by_id["macabacus/Merger-Model"]["verified_status"] == "error"
    assert by_id["asimplemodel/Simple-LBO-Model"]["size"] is None
    assert by_id["biws/DCF-Valuation-Model"]["size"] == 10
    assert by_id["cfi/LBO-Model"]["verified_status"] is None


def test_verify_sources_filter(cdir, monkeypatch):
    cat = catalog.build(cdir)
    calls = []
    monkeypatch.setattr(catalog, "_head", lambda url, h, timeout=25: calls.append(url) or (200, {}))
    catalog.verify(cat, sources=["biws"])
    assert calls == ["https://b.example/dcf.xlsx"]


def test_fetch_downloads_public_only_and_records_manifest(cdir, tmp_path, monkeypatch):
    cat = catalog.build(cdir)
    payload = {"https://d.example/fcffginzu.xlsx": b"AAA", "https://a.example/lbo.xlsx": b"BB"}

    def urlopen(req, timeout):
        u = req.full_url
        if u in payload:
            return FakeResp(payload[u], headers={})
        if "m.example" in u:
            raise urllib.error.HTTPError(u, 500, "bad", {}, None)
        raise OSError("refused")

    monkeypatch.setattr(catalog.urllib.request, "urlopen", urlopen)
    dest = tmp_path / "dl"
    man = catalog.fetch(cat, dest, sleep=0)
    by_id = {m["id"]: m for m in man}
    assert set(by_id) == {"damodaran/fcffginzu", "asimplemodel/Simple-LBO-Model", "macabacus/Merger-Model",
                          "biws/DCF-Valuation-Model"}  # no cfi entries
    ok = by_id["damodaran/fcffginzu"]
    assert ok["ok"] and ok["bytes"] == 3 and ok["sha256"] == hashlib.sha256(b"AAA").hexdigest()
    assert (dest / "damodaran" / "fcffginzu.xlsx").read_bytes() == b"AAA"
    assert by_id["macabacus/Merger-Model"] == {"id": "macabacus/Merger-Model", "source": "macabacus",
                                               "title": "Merger Model", "url": "https://m.example/merger.xlsx",
                                               "ok": False, "error": "HTTP 500"}
    assert by_id["biws/DCF-Valuation-Model"]["error"] == "refused"
    assert json.loads((dest / "manifest.json").read_text()) == man

    # second run: successes are skipped (no overwrite), failures retried
    attempts = []

    def urlopen2(req, timeout):
        attempts.append(req.full_url)
        return FakeResp(b"Z")

    monkeypatch.setattr(catalog.urllib.request, "urlopen", urlopen2)
    man2 = catalog.fetch(cat, dest, sleep=0)
    assert sorted(attempts) == ["https://b.example/dcf.xlsx", "https://m.example/merger.xlsx"]
    assert len([m for m in man2 if m["id"] == "damodaran/fcffginzu"]) == 1

    # overwrite=True re-downloads everything
    attempts.clear()
    catalog.fetch(cat, dest, overwrite=True, sleep=0)
    assert len(attempts) == 4


def test_fetch_limit_and_sources(cdir, tmp_path, monkeypatch):
    cat = catalog.build(cdir)
    attempts = []
    monkeypatch.setattr(catalog.urllib.request, "urlopen",
                        lambda req, timeout: attempts.append(req.full_url) or FakeResp(b"x"))
    catalog.fetch(cat, tmp_path / "a", limit=2, sleep=0)
    assert len(attempts) == 2
    attempts.clear()
    catalog.fetch(cat, tmp_path / "b", sources=["biws"], sleep=0)
    assert attempts == ["https://b.example/dcf.xlsx"]


# ----------------------------------------------------------------------------------------------- alternatives
@pytest.mark.parametrize("text,expected", [
    ("Compact LBO Model (Complete)", {"lbo"}),
    ("Discounted Cash Flow NPV", {"dcf", "capital-budgeting"}),
    ("Football field chart", {"charts"}),
    ("", set()),
    ("zzzz qqqq", set()),
])
def test_tags_for(text, expected):
    assert expected <= set(alternatives.tags_for(text))
    if not expected:
        assert alternatives.tags_for(text) == []


def test_tags_for_is_case_insensitive():
    assert "lbo" in alternatives.tags_for("LEVERAGED BUYOUT")
    assert alternatives.tags_for("LBO") == alternatives.tags_for("lbo")


def test_alternatives_build_ranks_by_shared_tags_then_source_rank(tmp_path):
    ent = lambda src, title, access="public", filename=None: {  # noqa: E731
        "source": src, "title": title, "access": access, "url": f"https://{src}/{title}", "size": 1, "filename": filename}
    cat = {"generated": "2026-01-01", "entries": [
        ent("cfi", "LBO and DCF Model", "cfi-paid"),
        ent("cfi", "Free LBO", "cfi-login"),
        ent("cfi", "Unmatched Soft Skills Zzz", "cfi-paid"),
        ent("exinfm", "Simple LBO Model"),            # lbo only
        ent("asimplemodel", "Simple LBO Model"),      # lbo only, better source rank
        ent("damodaran", "LBO DCF valuation"),        # lbo + dcf -> first
        ent("biws", "Nothing relevant Zzz"),
    ]}
    (tmp_path / "catalog.json").write_text(json.dumps(cat))
    res = alternatives.build(tmp_path)
    paid = next(i for i in res["items"] if i["cfi_title"] == "LBO and DCF Model")
    assert paid["tags"] == ["dcf", "lbo"]
    order = [(a["source"], a["shared_tags"]) for a in paid["alternatives"]]
    assert order[0] == ("damodaran", ["dcf", "lbo"])
    assert [o[0] for o in order[1:]] == ["asimplemodel", "exinfm"]  # source rank breaks the tie
    free = next(i for i in res["items"] if i["cfi_title"] == "Free LBO")
    assert free["access"] == "cfi-login" and len(free["alternatives"]) == 3
    none = next(i for i in res["items"] if i["cfi_title"].startswith("Unmatched"))
    assert none["alternatives"] == []
    assert res["summary"] == {"cfi_titles": 3, "with_alternatives": 2, "paid_with_alternatives": 1, "paid_total": 2}
    assert json.loads((tmp_path / "alternatives.json").read_text()) == res
    assert (tmp_path / "alternatives.md").read_text() == alternatives.to_markdown(res)


def test_alternatives_build_caps_matches_at_eight(tmp_path):
    entries = [{"source": "cfi", "title": "LBO", "access": "cfi-paid", "url": None}]
    entries += [{"source": "exinfm", "title": f"lbo {i}", "access": "public", "url": f"u{i}", "size": None}
                for i in range(12)]
    (tmp_path / "catalog.json").write_text(json.dumps({"generated": "g", "entries": entries}))
    assert len(alternatives.build(tmp_path)["items"][0]["alternatives"]) == 8


def test_alternatives_to_markdown_sections_and_paid_only():
    res = {"summary": {"paid_with_alternatives": 1, "paid_total": 2, "with_alternatives": 2, "cfi_titles": 3},
           "items": [
               {"cfi_title": "Paid A", "access": "cfi-paid", "tags": ["lbo"],
                "alternatives": [{"source": "biws", "title": f"T{i}", "url": f"u{i}", "shared_tags": ["lbo"]}
                                 for i in range(6)]},
               {"cfi_title": "Paid B", "access": "cfi-paid", "tags": [], "alternatives": []},
               {"cfi_title": "Free C", "access": "cfi-login", "tags": ["dcf", "wacc"],
                "alternatives": [{"source": "damodaran", "title": "D", "url": "ud", "shared_tags": ["dcf", "wacc"]}]},
           ]}
    md = alternatives.to_markdown(res)
    assert "1/2 paid-only CFI titles and 2/3 titles overall" in md
    assert "- **Paid A** `lbo`" in md and "- **Paid B** `-` — no public match" in md
    assert md.count("  - biws:") == 4  # only the first four alternatives are listed
    assert "  - damodaran: [D](ud) (dcf, wacc)" in md
    assert "## Free-tier CFI titles (Download)" in md
    paid_only = alternatives.to_markdown(res, paid_only=True)
    assert "Free-tier" not in paid_only and "Free C" not in paid_only and "Paid A" in paid_only


# ----------------------------------------------------------------------------------------------- paid_templates
@pytest.mark.parametrize("title,category", [
    ("LBO Model", "LBO"),
    ("3-Statement Model Template", "3-statement / operating model"),
    ("DCF Model Template", "DCF / intrinsic valuation"),
    ("Merger Model", "M&A / merger"),
    ("Trading Comps Template", "Comparable companies / precedent transactions"),
    ("WACC Calculator", "Cost of capital & capital structure"),
    ("REIT Real Estate Model", "Real estate & project models"),
    ("Black Scholes Option Pricing", "Options, trading & derivatives"),
    ("Inventory Methods Example", "Accounting topics"),
    ("Coaching Feedback Questionnaire", "Soft skills & career"),
    ("Quantum Basket Weaving", "Other"),
    ("LBO MODEL", "LBO"),  # case-insensitive
])
def test_categorise(title, category):
    assert paid_templates.categorise(title) == category


def test_categorise_first_match_wins():
    # "dcf" (DCF category) is listed before "lbo"'s siblings but "lbo" only matches the LBO category
    assert paid_templates.categorise("LBO and DCF") == "DCF / intrinsic valuation"


def _paid_catalog(tmp_path, with_alts=True):
    d = tmp_path / "catalog"
    d.mkdir()
    (tmp_path / "docs").mkdir()
    entries = [
        {"source": "cfi", "access": "cfi-paid", "title": "LBO Model"},
        {"source": "cfi", "access": "cfi-paid", "title": "Quantum Basket Weaving"},
        {"source": "cfi", "access": "cfi-login", "title": "Free DCF"},  # not paid -> excluded
        {"source": "damodaran", "access": "public", "title": "x"},      # not cfi -> excluded
    ]
    (d / "catalog.json").write_text(json.dumps({"generated": "2026-01-02", "entries": entries}))
    if with_alts:
        alts = {"items": [{"cfi_title": "LBO Model", "alternatives": [
            {"source": "asimplemodel", "title": f"A{i}", "url": f"u{i}"} for i in range(7)]}]}
        (d / "alternatives.json").write_text(json.dumps(alts))
    return d


def test_paid_build_with_alternatives(tmp_path):
    d = _paid_catalog(tmp_path)
    out = paid_templates.build(d)
    assert [i["title"] for i in out["items"]] == ["LBO Model", "Quantum Basket Weaving"]
    lbo, other = out["items"]
    assert lbo["category"] == "LBO" and lbo["coverage"] == "full"
    assert len(lbo["analogues"]) == 5 and set(lbo["analogues"][0]) == {"source", "title", "url"}
    assert lbo["what_it_does"] and lbo["literature"] and lbo["toolkit"]
    assert (other["category"], other["coverage"], other["what_it_does"], other["analogues"]) == ("Other", "none", "", [])
    assert lbo["cfi_page"] is None and lbo["cfi_description"] == "" and lbo["cfi_sections"] == []
    s = out["summary"]
    assert (s["paid_titles"], s["with_cfi_page"], s["with_analogues"]) == (2, 0, 1)
    assert s["coverage"] == {"full": 1, "partial": 0, "n/a": 0, "none": 1}
    assert s["by_category"]["LBO"] == 1 and s["by_category"]["Other"] == 1
    assert all("match" not in v for v in out["categories"].values())
    assert json.loads((d / "paid_templates.json").read_text()) == out
    assert (tmp_path / "docs" / "PAID_TEMPLATES.md").read_text().startswith("# Paid-only CFI templates")


def test_paid_build_without_alternatives_file(tmp_path):
    out = paid_templates.build(_paid_catalog(tmp_path, with_alts=False))
    assert all(i["analogues"] == [] for i in out["items"])


def test_load_intent(tmp_path):
    assert paid_templates.load_intent(tmp_path) == {}
    (tmp_path / "analysis_intent.json").write_text(json.dumps({"categories": {"LBO": {"intent": "why"}}}))
    assert paid_templates.load_intent(tmp_path) == {"LBO": {"intent": "why"}}


def test_paid_to_markdown_renders_intent_and_title_details():
    cats = {"LBO": {"does": "d", "literature": "l", "toolkit": "t", "coverage": "full"},
            "Empty": {"does": "d2", "literature": "l2", "toolkit": "t2", "coverage": "n/a"}}
    items = [{"title": "Fancy LBO", "category": "LBO", "cfi_page": "https://p", "cfi_description": "desc",
              "cfi_sections": [f"s{i}" for i in range(7)],
              "analogues": [{"source": "biws", "title": f"A{i}", "url": f"u{i}"} for i in range(5)]},
             {"title": "Orphan", "category": "Other", "cfi_page": None, "cfi_description": "",
              "cfi_sections": [], "analogues": []}]
    out = {"summary": {"paid_titles": 2, "with_cfi_page": 1, "with_analogues": 1,
                       "coverage": {"full": 1}, "by_category": {"LBO": 1, "Other": 1}},
           "categories": cats, "items": items,
           "intent": {"LBO": {"intent": "Fund deals", "sources": [{"site": f"S{i}", "title": "T", "url": "u"}
                                                                  for i in range(10)]},
                      "Empty": {"intent": "", "sources": []}}}
    md = paid_templates.to_markdown(out)
    assert "| LBO | 1 | d | l | t (full) |" in md
    assert "### LBO\n\nFund deals" in md and "### Empty" not in md  # empty intent skipped
    assert md.count("- S") == 8  # sources capped at eight
    assert "- **Fancy LBO** — desc ([CFI page](https://p)) Sections: s0; s1; s2; s3; s4." in md
    assert "Analogues: [biws: A0](u0); [biws: A1](u1); [biws: A2](u2)." in md and "A3" not in md
    assert "### Other\n\n- **Orphan**" in md
    assert "### Empty" not in md  # category with no titles has no title section


def test_paid_to_markdown_loads_intent_from_default_dir_when_absent(monkeypatch):
    monkeypatch.setattr(paid_templates, "load_intent", lambda *a, **k: {"X": {"intent": "from loader"}})
    out = {"summary": {"paid_titles": 0, "with_cfi_page": 0, "with_analogues": 0, "coverage": {}, "by_category": {}},
           "categories": {}, "items": []}
    assert "from loader" in paid_templates.to_markdown(out)
