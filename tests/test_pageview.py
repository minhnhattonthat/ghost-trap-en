"""pageview.py: page counting and chaining of strings for the page-by-page visual-QA run."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import pageview  # noqa: E402


class PageviewTest(unittest.TestCase):
    def test_pages_counts_page_codes_by_token(self):
        self.assertEqual(pageview.pages(bytes([0x29, 0xFD, 0x29, 0xFE])), 2)
        # a page-code value as the second byte of E0xx or as the argument of F7/FB is not a page
        self.assertEqual(pageview.pages(bytes([0xE0, 0xFD, 0xF7, 0xFE, 0xFB, 0xFD, 0x29])), 0)

    def test_chain_ends_every_string_on_a_page_and_the_chain_on_end(self):
        GBA = pageview.GBA
        rom = bytes([0x29, 0xFD, 0xFF, 0x2A, 0xFF, 0xFF])
        data, spans = pageview.chain(rom, ["a", "b", "c"], {"a": GBA, "b": GBA + 3, "c": GBA + 5})
        self.assertEqual(data, bytes([0x29, 0xFD, 0x2A, 0xFD, 0xFD, 0xFF]))
        self.assertEqual(spans, [("a", 1), ("b", 1), ("c", 1)])


if __name__ == "__main__":
    unittest.main()
