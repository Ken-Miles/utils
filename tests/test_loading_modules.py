# tests/test_import_all_files.py
from pathlib import Path
import subprocess
import sys
import pytest

SRC = Path(__file__).resolve().parents[1] / "src"

def to_dotted(path: Path) -> str:
    # make dotted module path relative to SRC, strip .py
    rel = path.relative_to(SRC).with_suffix("")
    return ".".join(rel.parts)

# Collect all python modules under src/
FILES = sorted(p for p in SRC.rglob("*.py"))
# Also test packages (directories) by importing their package name, not just files
# Include __init__.py targets and plain .py modules
MODULES = [to_dotted(p) for p in FILES]

@pytest.mark.parametrize("modname", MODULES, ids=MODULES)
def test_imports_as_temp_package(modname: str):
    """
    Import each module under a temporary package so relative imports (from .foo) work.
    Any failure surfaces as a pytest failure with traceback.
    """
    code = r"""
import sys, types, importlib, pathlib
root = pathlib.Path(sys.argv[1])      # SRC folder
modname = sys.argv[2]                 # dotted path like "utils.helpers" or "file1"

# Create a transient top-level package whose __path__ points at SRC.
PKG = "_autopkg_"
pkg = types.ModuleType(PKG)
pkg.__path__ = [str(root)]
sys.modules[PKG] = pkg

# Import the target as a submodule of that package.
# This makes relative imports inside your modules resolve (e.g., from .utils import x).
fullname = f"{PKG}.{modname}"
importlib.import_module(fullname)
"""
    try:
        subprocess.run(
            [sys.executable, "-c", code, str(SRC), modname],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Import failed for {modname}:\n{e.stderr}")
