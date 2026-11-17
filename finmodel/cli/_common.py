"""Shared helpers for the finmodel CLI command modules."""
from __future__ import annotations

import json
from pathlib import Path


def _load_json(p: str):
    return json.loads(Path(p).read_text())


def _dump(obj, out: str | None):
    s = json.dumps(obj, indent=1, default=str)
    if out:
        Path(out).write_text(s)
        print(f"wrote {out}")
    else:
        print(s)
