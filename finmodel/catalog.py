"""Catalog, verify and fetch financial-model template sources.

Sources
-------
- cfi           : CFI member dashboard (api.corporatefinanceinstitute.com/api/files/<uuid>) -- the SPA sends a
                  Bearer token (not a cookie); pass it via --auth / env FINMODEL_CFI_AUTH as
                  "Authorization: Bearer <token>" copied from a logged-in request in DevTools.  Items marked cfi-paid need a paid plan and are never fetched.
- damodaran     : NYU Stern spreadsheets (public, no login)
- asimplemodel  : A Simple Model free downloads (public direct links)
- exinfm        : exinfm.com free spreadsheets (public)

Downloaded files are copyrighted by their publishers: keep them in the git-ignored downloads/ folder.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parent.parent
CATALOG_DIR = ROOT / "catalog"
UA = "Mozilla/5.0 (financial-analysis-toolkit; +https://github.com/herrrickshaw)"

PUBLIC_SOURCE_META = {
    "damodaran": {"publisher": "Aswath Damodaran, NYU Stern", "home": "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/spreadsh.htm", "access": "public"},
    "asimplemodel": {"publisher": "A Simple Model", "home": "https://www.asimplemodel.com/resources/quick-references/free-downloads", "access": "public"},
    "exinfm": {"publisher": "Excellence in Financial Management (exinfm.com)", "home": "https://exinfm.com/free_spreadsheets.html", "access": "public"},
    "macabacus": {"publisher": "Macabacus (Excel add-in vendor; free demo templates)", "home": "https://macabacus.com/category/excel/templates", "access": "public"},
    "biws": {"publisher": "Breaking Into Wall Street / Mergers & Inquisitions knowledge base", "home": "https://breakingintowallstreet.com/kb/", "access": "public"},
    "cfi": {"publisher": "Corporate Finance Institute", "home": "https://corporatefinanceinstitute.com/resources/templates/", "access": "login"},
}


def _slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")


def build(catalog_dir: Path = CATALOG_DIR) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    raw = catalog_dir / "cfi_dashboard_raw.txt"
    if raw.exists():
        for line in raw.read_text().splitlines():
            if not line.strip():
                continue
            title, status, url = (line.split("|") + ["", ""])[:3]
            entries.append({"id": f"cfi/{_slug(title)}", "source": "cfi", "title": title.strip(),
                            "url": url.strip() or None,
                            "access": "cfi-login" if status.strip() == "Download" else "cfi-paid",
                            "filename": None, "size": None, "verified_status": None})
    ver = catalog_dir / "open_sources_verified.txt"
    if ver.exists():
        for line in ver.read_text().splitlines():
            if not line.strip():
                continue
            parts = line.rstrip("\r").split("|")
            if len(parts) < 3:
                continue
            src, name, url = parts[0], parts[1], parts[2]
            status = parts[3] if len(parts) > 3 else None
            size = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else None
            entries.append({"id": f"{src}/{_slug(Path(name).stem)}", "source": src, "title": Path(name).stem,
                            "url": url, "access": "public", "filename": name, "size": size,
                            "verified_status": status})
    cat = {"generated": time.strftime("%Y-%m-%d"), "sources": PUBLIC_SOURCE_META, "entries": entries,
           "counts": _counts(entries)}
    (catalog_dir / "catalog.json").write_text(json.dumps(cat, indent=1))
    (catalog_dir / "catalog.md").write_text(to_markdown(cat))
    return cat


def _counts(entries: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    c: Dict[str, int] = {}
    for e in entries:
        k = f"{e['source']}:{e['access']}"
        c[k] = c.get(k, 0) + 1
    return c


def load(catalog_dir: Path = CATALOG_DIR) -> Dict[str, Any]:
    p = catalog_dir / "catalog.json"
    if not p.exists():
        return build(catalog_dir)
    return json.loads(p.read_text())


def to_markdown(cat: Dict[str, Any]) -> str:
    out = ["# Template source catalog", "", f"Generated {cat['generated']}. Counts: `{cat['counts']}`", ""]
    for src, meta in cat["sources"].items():
        rows = [e for e in cat["entries"] if e["source"] == src]
        if not rows:
            continue
        out += [f"## {src} — {meta['publisher']}", "", f"Home: {meta['home']}  ", f"Access: {meta['access']}", "",
                "| title | access | size | status | url |", "|---|---|---|---|---|"]
        for e in rows:
            size = f"{e['size']/1024:.0f} KB" if e.get("size") else ""
            out.append(f"| {e['title']} | {e['access']} | {size} | {e.get('verified_status') or ''} | {e['url'] or ''} |")
        out.append("")
    return "\n".join(out)


def _head(url: str, headers: Dict[str, str], timeout: int = 25):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA, **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.headers
    except Exception as e:  # noqa: BLE001
        return None, {"error": str(e)}


def verify(cat: Dict[str, Any], sources: Optional[List[str]] = None, auth_header: Optional[str] = None,
           timeout: int = 25) -> Dict[str, Any]:
    hdrs = _auth_headers(auth_header)
    for e in cat["entries"]:
        if not e["url"] or (sources and e["source"] not in sources):
            continue
        if e["access"] == "cfi-login" and not hdrs:
            continue
        status, h = _head(e["url"], hdrs if e["source"] == "cfi" else {}, timeout)
        e["verified_status"] = str(status) if status else "error"
        try:
            cl = h.get("Content-Length") if hasattr(h, "get") else None
            if cl:
                e["size"] = int(cl)
        except Exception:  # noqa: BLE001
            pass
    cat["counts"] = _counts(cat["entries"])
    return cat


def _auth_headers(auth_header: Optional[str]) -> Dict[str, str]:
    auth_header = auth_header or os.environ.get("FINMODEL_CFI_AUTH")
    if not auth_header:
        return {}
    if ":" not in auth_header:
        raise ValueError('auth header must look like "Cookie: ..." or "Authorization: Bearer ..."')
    k, v = auth_header.split(":", 1)
    return {k.strip(): v.strip()}


def _filename_from_response(url: str, headers, fallback: str) -> str:
    cd = headers.get("Content-Disposition") if hasattr(headers, "get") else None
    if cd:
        m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", cd)
        if m:
            return urllib.parse.unquote(m.group(1))
    name = Path(urllib.parse.urlparse(url).path).name
    if "." in name and len(name) < 120:
        return urllib.parse.unquote(name)
    ct = (headers.get("Content-Type") or "").lower() if hasattr(headers, "get") else ""
    ext = ".xlsx" if "spreadsheetml" in ct else ".xls" if "ms-excel" in ct else ".pdf" if "pdf" in ct else ".pptx" if "presentationml" in ct else ".bin"
    return fallback + ext


def fetch(cat: Dict[str, Any], dest: Path, sources: Optional[List[str]] = None, auth_header: Optional[str] = None,
          overwrite: bool = False, sleep: float = 0.5, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Download entries into dest/<source>/.  Returns the manifest (one row per attempted entry)."""
    dest = Path(dest)
    hdrs = _auth_headers(auth_header)
    manifest_path = dest / "manifest.json"
    manifest: List[Dict[str, Any]] = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    done = {m["id"] for m in manifest if m.get("ok")}
    n = 0
    for e in cat["entries"]:
        if not e["url"] or (sources and e["source"] not in sources) or e["access"] == "cfi-paid":
            continue
        if e["access"] == "cfi-login" and not hdrs:
            continue
        if e["id"] in done and not overwrite:
            continue
        if limit is not None and n >= limit:
            break
        n += 1
        row = {"id": e["id"], "source": e["source"], "title": e["title"], "url": e["url"], "ok": False}
        req = urllib.request.Request(e["url"], headers={"User-Agent": UA, **(hdrs if e["source"] == "cfi" else {})})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
                fname = _filename_from_response(e["url"], r.headers, _slug(e["title"]))
        except urllib.error.HTTPError as ex:
            row["error"] = f"HTTP {ex.code}"
            manifest.append(row)
            continue
        except Exception as ex:  # noqa: BLE001
            row["error"] = str(ex)
            manifest.append(row)
            continue
        out_dir = dest / e["source"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / fname
        out.write_bytes(data)
        row.update({"ok": True, "path": str(out), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        manifest = [m for m in manifest if m["id"] != e["id"]] + [row]
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=1))
        time.sleep(sleep)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=1))
    return manifest


def fetch_signed(url_file: Path, dest: Path, source: str = "cfi") -> List[Dict[str, Any]]:
    """Download pre-signed URLs (one per line) into dest/<source>/, naming files from Content-Disposition.

    This is the second half of the CFI dashboard workflow: the learn.corporatefinanceinstitute.com SPA
    authenticates with a Bearer token, but a *top-level navigation* to api/files/<uuid> in a logged-in
    browser returns a 302 to a pre-signed S3 URL (resources.corporatefinanceinstitute.com, 60-second
    expiry).  Capture those URLs from the browser's network log (Claude-in-Chrome, DevTools, HAR export)
    and feed them here; no credentials are needed for the S3 leg.
    """
    dest = Path(dest); out_dir = dest / source; out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = dest / "manifest.json"
    manifest: List[Dict[str, Any]] = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    rows = []
    for line in Path(url_file).read_text().splitlines():
        url = line.strip()
        if not url or url.startswith("#"):
            continue
        key = Path(urllib.parse.urlparse(url).path).name
        row = {"id": f"{source}/{key.rsplit('.', 1)[0]}", "source": source, "title": key, "url": url.split("?")[0], "ok": False}
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read(); fname = _filename_from_response(url, r.headers, key)
        except urllib.error.HTTPError as ex:
            row["error"] = f"HTTP {ex.code}"; rows.append(row); continue
        except Exception as ex:  # noqa: BLE001
            row["error"] = str(ex); rows.append(row); continue
        out = out_dir / fname; out.write_bytes(data)
        row.update({"ok": True, "path": str(out), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        rows.append(row)
        manifest = [m for m in manifest if m["id"] != row["id"]] + [row]
    manifest_path.write_text(json.dumps(manifest, indent=1))
    return rows
