from finmodel import catalog


def test_build_catalog(tmp_path):
    cat = catalog.build()
    assert cat["counts"]["cfi:cfi-login"] == 196
    assert cat["counts"]["cfi:cfi-paid"] == 127
    assert cat["counts"]["damodaran:public"] >= 55
    assert cat["counts"]["asimplemodel:public"] == 8
    srcs = {e["source"] for e in cat["entries"]}
    assert {"cfi", "damodaran", "asimplemodel", "exinfm", "macabacus"} <= srcs
    assert all(e["url"] for e in cat["entries"] if e["access"] != "cfi-paid")
    md = catalog.to_markdown(cat)
    assert "fcffginzu" in md and "Damodaran" in md


def test_fetch_skips_paid_and_login_without_auth(tmp_path):
    cat = catalog.build()
    man = catalog.fetch(cat, tmp_path, sources=["cfi"])  # no auth -> nothing attempted
    assert man == []


def test_alternatives_tags():
    from finmodel import alternatives
    assert "lbo" in alternatives.tags_for("Compact LBO Model (Complete)")
    assert {"m&a", "comps"} <= set(alternatives.tags_for("Transaction Comps and Merger Consequences"))
    r = alternatives.build()
    assert r["summary"]["paid_with_alternatives"] > 60
    lbo = next(i for i in r["items"] if i["cfi_title"] == "LBO Model")
    assert any(a["source"] in ("asimplemodel", "macabacus", "damodaran", "exinfm", "biws") for a in lbo["alternatives"])


def test_paid_templates_kb():
    from finmodel import paid_templates
    assert paid_templates.categorise("Compact LBO Model (Complete)") == "LBO"
    assert paid_templates.categorise("Trading Comps") == "Comparable companies / precedent transactions"
    r = paid_templates.build()
    assert r["summary"]["paid_titles"] == 127
    assert r["summary"]["by_category"].get("Other", 0) <= 8
    lbo = next(i for i in r["items"] if i["title"] == "LBO Model")
    assert lbo["coverage"] == "full" and lbo["analogues"]
