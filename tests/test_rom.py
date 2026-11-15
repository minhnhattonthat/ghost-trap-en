"""The pinned dump: rom.sha1 is filled in and, when the ROM is present, matches it."""
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pinned():
    for line in (ROOT / "rom.sha1").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            sha, name = line.split(None, 1)
            return sha, ROOT / name.strip().lstrip("*")
    raise AssertionError("rom.sha1 has no entry")


class TestRom(unittest.TestCase):
    def test_sha1_line_is_filled(self):
        sha, path = pinned()
        self.assertRegex(sha, r"^[0-9a-f]{40}$")
        self.assertNotIn("<", str(path))

    def test_dump_matches(self):
        sha, path = pinned()
        if not path.is_file():
            self.skipTest("ROM not present")
        self.assertEqual(hashlib.sha1(path.read_bytes()).hexdigest(), sha)


if __name__ == "__main__":
    unittest.main()
