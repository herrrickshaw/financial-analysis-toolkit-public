import shutil
from pathlib import Path

import pytest

from finmodel import catalog

REPO_CATALOG = Path(catalog.CATALOG_DIR)
CFI_RAW = REPO_CATALOG / "cfi_dashboard_raw.txt"
NEEDS_CFI = pytest.mark.skipif(
    not CFI_RAW.exists(),
    reason="catalog/cfi_dashboard_raw.txt (title list from your own CFI member dashboard) is not distributed "
           "with this repo; place your own copy there to run the CFI-title tests",
)


@pytest.fixture
def cat_dir(tmp_path):
    """Scratch copy of the tracked catalog inputs so builders never rewrite tracked files."""
    d = tmp_path / "catalog"
    d.mkdir()
    for f in REPO_CATALOG.iterdir():
        if f.is_file() and f.name not in ("catalog.json", "catalog.md"):
            shutil.copy(f, d / f.name)
    (tmp_path / "docs").mkdir()
    return d


def test_build_catalog_public_sources(cat_dir):
    cat = catalog.build(cat_dir)
    assert cat["counts"]["damodaran:public"] >= 55
    assert cat["counts"]["asimplemodel:public"] == 8
    srcs = {e["source"] for e in cat["entries"]}
    assert {"damodaran", "asimplemodel", "exinfm", "macabacus"} <= srcs
    assert all(e["url"] for e in cat["entries"] if e["access"] != "cfi-paid")
    md = catalog.to_markdown(cat)
    assert "fcffginzu" in md and "Damodaran" in md


@NEEDS_CFI
def test_build_catalog_cfi_titles(cat_dir):
    cat = catalog.build(cat_dir)
    assert cat["counts"]["cfi:cfi-login"] == 196
    assert cat["counts"]["cfi:cfi-paid"] == 127
    assert "cfi" in {e["source"] for e in cat["entries"]}


def test_fetch_skips_paid_and_login_without_auth(cat_dir, tmp_path):
    cat = catalog.build(cat_dir)
    man = catalog.fetch(cat, tmp_path / "dl", sources=["cfi"])  # no auth -> nothing attempted
    assert man == []


def test_alternatives_tags():
    from finmodel import alternatives
    assert "lbo" in alternatives.tags_for("Compact LBO Model (Complete)")
    assert {"m&a", "comps"} <= set(alternatives.tags_for("Transaction Comps and Merger Consequences"))


@NEEDS_CFI
def test_alternatives_build(cat_dir):
    from finmodel import alternatives
    r = alternatives.build(cat_dir)
    assert r["summary"]["paid_with_alternatives"] > 60
    lbo = next(i for i in r["items"] if i["cfi_title"] == "LBO Model")
    assert any(a["source"] in ("asimplemodel", "macabacus", "damodaran", "exinfm", "biws") for a in lbo["alternatives"])


def test_paid_templates_categorise():
    from finmodel import paid_templates
    assert paid_templates.categorise("Compact LBO Model (Complete)") == "LBO"
    assert paid_templates.categorise("Trading Comps") == "Comparable companies / precedent transactions"


@NEEDS_CFI
def test_paid_templates_kb(cat_dir):
    from finmodel import paid_templates
    r = paid_templates.build(cat_dir)
    assert r["summary"]["paid_titles"] == 127
    assert r["summary"]["by_category"].get("Other", 0) <= 8
    lbo = next(i for i in r["items"] if i["title"] == "LBO Model")
    assert lbo["coverage"] == "full" and lbo["analogues"]
