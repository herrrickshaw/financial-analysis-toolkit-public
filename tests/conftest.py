import json, sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
EX = ROOT / "examples"

CFI_DIRS = [
    Path.home() / "Library/CloudStorage/GoogleDrive-tdrickshaw@gmail.com/My Drive",
    Path.home() / "Library/CloudStorage/Dropbox",
    ROOT / "downloads" / "cfi",
]


def cfi_file(name: str):
    for d in CFI_DIRS:
        p = d / name
        if p.exists():
            return p
    return None


@pytest.fixture
def three_statement_inputs():
    return json.loads((EX / "cfi_three_statement.json").read_text())


@pytest.fixture
def dcf_inputs():
    return json.loads((EX / "cfi_dcf.json").read_text())


@pytest.fixture
def projection_inputs():
    return json.loads((EX / "projection_demo.json").read_text())
