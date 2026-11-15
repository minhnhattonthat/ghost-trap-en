"""check.py: the repo's one-command check (the pre-commit hook runs it). Exit 0 only when every test passes.

Runs every tests/test_*.py with stdlib unittest (no pytest needed). Tests that need the ROM skip themselves when
rom/ is absent, so a fresh clone still passes. Text lint joins here once script/ exists.

    python -X utf8 tools/check.py"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "tests")]
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py", top_level_dir=str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() and result.testsRun else 1)
