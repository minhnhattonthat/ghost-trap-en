"""Phase 7: the all-English build, made here from script/ (never a stale build/ file), passes the ROM-level checks
of the skill's references/pipeline.md §Checks."""
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import font  # noqa: E402
import romdiff  # noqa: E402
import script  # noqa: E402
import textblock  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"
GBA = textblock.GBA


def allowed_ranges():
    out = []
    for ln in (ROOT / "tools" / "allowed_ranges.txt").read_text(encoding="utf-8").splitlines():
        ln = ln.split("#")[0].strip()
        if ln:
            lo, _, hi = ln.partition("-")
            out.append((int(lo, 16), int(hi or lo, 16)))
    return out


@unittest.skipUnless(ROM.is_file(), "ROM not present")
class TestEnglishBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig = ROM.read_bytes()
        cls.entries = script.load()
        cls.texts = script.texts(cls.entries, "en")
        cls.rom, cls.log = build.build(cls.orig, cls.texts)
        cls.en = build.table("en")

    def test_every_change_is_a_logged_write_inside_the_allowed_ranges(self):
        writes = []
        for ln in self.log:
            off, old, new, who = ln.split(None, 3)
            writes.append((int(off, 16), bytes.fromhex(old), bytes.fromhex(new), who))
        errs, _ = romdiff.check(self.orig, self.rom, set(), writes)  # no blanket ranges: every byte has a write
        self.assertEqual(errs, [], "\n".join(errs[:20]))
        ranges = allowed_ranges()
        for off, old, _, who in writes:
            end = off + len(old) - 1
            self.assertTrue(any(lo <= off and end <= hi for lo, hi in ranges), f"{who} {off:X}-{end:X}")

    def test_size_within_eeprom_limit(self):
        self.assertLessEqual(len(self.rom), build.ROM_MAX)
        self.assertEqual(len(self.rom) % 0x10000, 0)

    def test_every_string_with_english_is_written_and_every_slot_reaches_it(self):
        n = 0
        for e in self.entries:
            if not e.get("en"):
                continue
            n += 1
            for s in e["slots"]:
                p = struct.unpack_from("<I", self.rom, int(s, 16))[0] - GBA
                self.assertGreaterEqual(p, build.RELOC, e["id"])
                self.assertEqual(p % 4, 0, e["id"])
                self.assertEqual(self.en.decode(self.rom, p, maxlen=0x8000)[0], e["en"], f"{e['id']} slot {s}")
        self.assertEqual(n, len(self.texts))
        self.assertEqual(n, 3183)

    def test_untranslated_strings_keep_their_bytes(self):
        jp = build.table("jp")
        for e in self.entries:
            if e.get("en"):
                continue
            p = struct.unpack_from("<I", self.rom, int(e["slots"][0], 16))[0] - GBA
            self.assertEqual(jp.decode(self.rom, p, maxlen=0x8000)[0], e["jp"], e["id"])

    def test_no_reader_left_on_the_old_block(self):
        """No u32 in code and tables (below 0xE0000) still points at a moved string, the old header or the old font.
        Above that, matches are sound/graphics data (checked by hand 2026-11-15: e.g. 0xE5D78 is 8-bit samples)."""
        keys = {t for _, t in textblock.slots(self.orig)} | {textblock.HEADER, textblock.HEADER + 4, 0x1271C8}
        stale = []
        for off in range(0, 0xE0000, 4):
            v = struct.unpack_from("<I", self.rom, off)[0]
            if v >> 24 == 0x08 and v - GBA in keys:
                stale.append(f"{off:X}->{v:08X}")
        self.assertEqual(stale, [])
        for p in font.FONT_PTRS:
            at = struct.unpack_from("<I", self.rom, p)[0] - GBA
            self.assertGreaterEqual(at, build.RELOC)
            self.assertEqual(self.rom[at], 0x10)  # LZ77 header

    def test_no_japanese_in_english_text(self):
        bad = [e["id"] for e in self.entries if e.get("en") and re.search(r"[぀-ヿ一-鿿　-〿＀-￯]", e["en"])]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
