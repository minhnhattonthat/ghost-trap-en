"""Phase 5 engine spike: English glyphs, en.tbl, the relocated font, and the marker build (tools/font.py,
tools/marker.py, tbl/en.tbl; docs/re/text.md "English font", "Width gate")."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import font  # noqa: E402
import gbacomp  # noqa: E402
import marker  # noqa: E402
import script  # noqa: E402
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"
EN = Table.load(ROOT / "tbl" / "en.tbl")
JP = Table.load(ROOT / "tbl" / "jp.tbl")


def glyphs_of(data):
    """Glyph indices of an encoded string (control codes and their argument bytes skipped)."""
    out, i = [], 0
    while i < len(data):
        b = data[i]
        if b == 0xE0:
            out.append(0xE0 + data[i + 1])
            i += 2
        elif b > 0xE0:
            i += 1 + JP.ctrl.get(bytes([b]), ("", 0))[1]
        else:
            out.append(b)
            i += 1
    return out


class TestTable(unittest.TestCase):
    def test_en_tbl_is_ascii_printable(self):
        for ch in EN.enc:
            self.assertTrue(len(ch) == 1 and (32 <= ord(ch) < 127 or ch == "—"), ch)

    def test_every_en_glyph_is_below_the_script_buffer(self):
        # glyphs >= 0x1A0 sit on the script buffer at 0x0201E000 and are overwritten when a script loads
        for ch, code in EN.enc.items():
            self.assertLess(glyphs_of(code)[0], font.SAFE_END, ch)

    def test_controls_match_jp(self):
        self.assertEqual(EN.ctrl, JP.ctrl)


@unittest.skipUnless(ROM.is_file(), "ROM not present")
class TestFont(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig = ROM.read_bytes()
        cls.data = font.patched(cls.orig)
        cls.w = font.widths(cls.orig)

    def test_new_glyph_cells_are_unused_by_the_script(self):
        used = set()
        for e in script.load():
            used.update(glyphs_of(JP.encode(e["jp"])))
        for ch, (code, _, _) in font.NEW.items():
            self.assertNotIn(font.glyph_index(code), used, ch)

    def test_every_en_char_has_a_width_and_ink(self):
        for ch, code in EN.enc.items():
            g = glyphs_of(code)[0]
            self.assertGreater(self.w[g], 0, ch)
            if ch != " ":
                self.assertTrue(any(self.data[g * 128:(g + 1) * 128]), ch)

    def test_advances_are_multiples_of_4(self):
        # the renderer branches on pen x & 7 vs 4 (0x08027BD2); 6 px and odd advances misdrew in the torture shots
        for ch, code in EN.enc.items():
            self.assertEqual(self.w[glyphs_of(code)[0]] % 4, 0, ch)

    def test_staff_roll_space_keeps_8px(self):
        self.assertEqual(self.w[0x00], 8)
        self.assertEqual(self.w[glyphs_of(EN.encode(" "))[0]], font.SPACE)

    def test_glyph_ink_fits_its_advance(self):
        # ink (outline included) may touch the next glyph's first column, no further
        for ch, code in EN.enc.items():
            g = glyphs_of(code)[0]
            cols = [x for x in range(16) for y in range(16) if self._px(g, x, y)]
            if cols:
                self.assertLessEqual(max(cols), self.w[g], f"{ch!r}: ink to x={max(cols)}, advance {self.w[g]}")

    def _px(self, g, x, y):
        b = self.data[g * 128 + ((y // 8) * 2 + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2]
        return (b >> 4) if x & 1 else (b & 0xF)

    def test_english_build_carries_the_font_and_widths(self):
        rom, _ = build.build(self.orig, {0x103940: "{box:01}Hi-there; A&B/C 5%.{page}{end}"})
        ptrs = {struct.unpack_from("<I", rom, p)[0] - 0x08000000 for p in font.FONT_PTRS}
        self.assertEqual(len(ptrs), 1)
        at = ptrs.pop()
        self.assertGreaterEqual(at, build.RELOC)
        self.assertEqual(gbacomp.lz77_decompress(rom, at)[0], self.data)
        self.assertEqual(rom[font.WIDTHS:font.WIDTHS + 2 * font.GLYPHS], font.width_table(self.orig))


@unittest.skipUnless(ROM.is_file(), "ROM not present")
class TestMarker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig = ROM.read_bytes()
        cls.charw = marker.char_widths(cls.orig, EN)

    def test_every_string_marks_encodes_and_fits(self):
        for e in script.load():
            m = marker.mark(e["id"], e["jp"], self.charw)
            EN.encode(m)
            if marker.TOKEN.sub("", e["jp"]).strip(" "):  # has visible text -> carries its id
                self.assertIn(f"({e['id']})", m)
            # same control-code skeleton as the original
            self.assertEqual(marker.TOKEN.findall(m), marker.TOKEN.findall(e["jp"]), e["id"])

    def test_box_lines_fill_the_measured_width(self):
        e = next(x for x in script.load() if x["id"] == "103940")
        m = marker.mark(e["id"], e["jp"], self.charw)
        line = m.split("{br}")[0].replace("{box:01}", "")
        w = font.width_px(line, EN, self.orig)
        self.assertLessEqual(w, marker.WIDTH["{box:01}"])
        self.assertGreater(w, marker.WIDTH["{box:01}"] - 12)


if __name__ == "__main__":
    unittest.main()
