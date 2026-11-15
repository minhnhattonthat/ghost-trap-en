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

    def test_shipped_text_is_laid_out(self):
        # wrap.layout wraps a {br}-less page before measuring it, so the width lint passes text the build then
        # inserts unwrapped: one over-wide line runs off the box and floods it with stray glyphs (24 polish-pass
        # rewords, phase 9). The stored `en` must already be its own layout.
        bad = [i for i, e in batches.index().items() if e.get("en") and e.get("status") != "data"
               and wrap.layout(e, e["en"])[0] != e["en"]]
        self.assertEqual(bad, [], "re-wrap with wrap.layout: " + " ".join(bad[:40]))

    def test_field_strings_use_the_field_box(self):
        # the field box is 184 px (the HUD sits right), the cutscene box 224: Karol's lounge talk (script 123, slot
        # 3C1C4) was linted at 224 and its 212 px first line flooded the field with glyphs (player report 2026-11-16)
        ent = batches.index()
        field, box = wrap.WIN["field"]["px"], wrap.WIN["box"]["px"]
        self.assertEqual(wrap.variant(ent["1109AC"])[0], field)                   # scene script 123: field
        self.assertEqual(wrap.variant(dict(ent["1109AC"], slots=["3C054"]))[0], box)  # scene script 31: cutscene
        self.assertEqual(wrap.variant(dict(ent["1109AC"], slots=["3C054", "3C1C4"]))[0], field)  # shared: tighter
        self.assertEqual(wrap.variant(dict(ent["1109AC"], slots=["3C55C"]))[0], field)  # field tables
        self.assertLessEqual(wrap.item_name_px(), wrap.WIN["item_name"]["px"])

    def test_choice_rows_share_one_layout(self):
        # the item-menu cursor redraws 10F05C/10F06C over the question's own Yes/No row without clearing it:
        # any other spacing leaves two copies on screen ("YYes No No")
        import re
        rows = {i: re.search(r"(?:^|\{br\})( *\{name:0[17]\}Yes *\{name:0[17]\}No)\{clr\}", e["en"])
                for i, e in batches.index().items() if re.search(r"\{name:0[17]\}はい", e["jp"]) and e.get("en")}
        self.assertTrue(rows and all(rows.values()), rows)
        layouts = {re.sub(r"\{name:0[17]\}", "{c}", m.group(1)) for m in rows.values()}
        self.assertEqual(len(layouts), 1, layouts)

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

    def test_long_sentence_splits_without_stub(self):
        e = {"jp": "あ{clr}{end}", "slots": ["106B04"]}
        en = "Not even records from a century ago said a thing about it at all, so nobody knew where it came from."
        text, bad = wrap.layout(e, en + "{clr}{end}")
        self.assertEqual(bad, [])
        pages = [b for b, _ in wrap.segments(text) if b]
        self.assertGreaterEqual(len(pages), 2)
        self.assertTrue(all(len(p.replace("{br}", " ")) >= wrap.STUB for p in pages), pages)

    def test_stub_lint(self):
        self.assertTrue(wrap.stubs("said a thing about{page}it.{page}{end}"))
        self.assertFalse(wrap.stubs("It was dark.{page}Ah!{page}{end}"))
        # a {clr} clears the box like a page: a fragment before it is a stub too
        self.assertTrue(wrap.stubs("she was already{page}running.{clr}I followed her.{end}"))
        self.assertTrue(wrap.stubs("she was already{clr}running.{clr}I followed her.{end}"))

    def test_charset_is_the_table(self):
        self.assertNotIn("+", batches.ENCODABLE)
        self.assertIn(" ", batches.ENCODABLE)
        self.assertIn("z", batches.ENCODABLE)
        from tbl import Table
        en = Table.load(Path(__file__).resolve().parents[1] / "tbl" / "en.tbl")
        for c in sorted(batches.ENCODABLE):
            en.encode(c)

    def test_skeleton_ignores_added_pages(self):
        jp = "{box:00}{name:02}ジョージ{br}あ{page}{end}"
        en = "{box:00}{name:02}George{br}a{page}{box:00}{name:02}George{br}b{page}{end}"
        self.assertEqual(batches.skeleton(jp), batches.skeleton(en))
        self.assertNotEqual(batches.skeleton(jp), batches.skeleton("{box:00}{name:02}George{br}a{clr}{end}"))


if __name__ == "__main__":
    unittest.main()
