"""Text lint: every shipped `en` passes tools/batches.py's checks (codes, glossary, ASCII, measured widths)."""
import unittest
from pathlib import Path

import batches
import wrap

ROM = Path(__file__).resolve().parents[1] / "rom" / "Ghost Trap (Japan).gba"


@unittest.skipUnless(ROM.exists(), "needs the ROM for font widths")
class TestShippedEnglish(unittest.TestCase):
    def test_lint_clean(self):
        terms = batches.glossary()
        bad = [f"{i}: {p}" for i, e in batches.index().items() if e.get("en")
               for p in batches.problems(e, e["en"], terms)]
        self.assertEqual(bad, [], "\n".join(bad[:40]))

    def test_shorthand_roundtrip(self):
        jp = "{box:00}{name:02}ジョージ{br}「あ{page}{box:01}い{clr}{end}"
        self.assertEqual(batches.compact(jp), "@G 「あ|@1い^$")
        self.assertEqual(batches.expand("@G Hi|@1Yo^$"), "{box:00}{name:02}George{br}Hi{page}{box:01}Yo{clr}{end}")

    def test_wrap_splits_pages_and_repeats_prefix(self):
        e = {"jp": "{box:00}{name:02}ジョージ{br}「あ{page}{end}", "slots": ["3C560"]}
        text, bad = wrap.layout(e, "{box:00}{name:02}George{br}" + "This line is long enough. " * 6 + "{page}{end}")
        self.assertEqual(bad, [])
        self.assertGreaterEqual(text.count("{name:02}George{br}"), 2)
        for body, _ in wrap.segments(text):
            self.assertLessEqual(body.count("{br}"), 2)

    def test_skeleton_ignores_added_pages(self):
        jp = "{box:00}{name:02}ジョージ{br}あ{page}{end}"
        en = "{box:00}{name:02}George{br}a{page}{box:00}{name:02}George{br}b{page}{end}"
        self.assertEqual(batches.skeleton(jp), batches.skeleton(en))
        self.assertNotEqual(batches.skeleton(jp), batches.skeleton("{box:00}{name:02}George{br}a{clr}{end}"))


if __name__ == "__main__":
    unittest.main()
