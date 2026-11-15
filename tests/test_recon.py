"""Phase 1 recon facts (docs/re/text.md) checked against the dump: table, pointer region, font block."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tbl import Table  # noqa: E402
import gbacomp  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"
PTR_LO, PTR_HI = 0x3BF28, 0x423A0
TEXT_LO, TEXT_HI = 0x100000, 0x1271C8


def text_targets(rom):
    out = set()
    for i in range(PTR_LO, PTR_HI, 4):
        v = struct.unpack_from("<I", rom, i)[0]
        if 0x08000000 + TEXT_LO <= v < 0x08000000 + TEXT_HI:
            out.add(v - 0x08000000)
    return sorted(out)


@unittest.skipUnless(ROM.is_file(), "ROM not present")
class TestRecon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()
        cls.tbl = Table.load(ROOT / "tbl" / "jp.tbl")

    def test_known_line_decodes(self):
        # opening crawl (scene table entry 44), logged from the renderer at frame 1077
        text, _ = self.tbl.decode(self.rom, 0x106B04, maxlen=20000)
        self.assertIn("その館は古く、今となっては{br}誰も成り立ちを知らなかった。", text)
        # first cutscene line, read off the screen at frame 3720
        found = any("「ゴーストハントなんて" in self.tbl.decode(self.rom, x, maxlen=20000)[0]
                    for x in text_targets(self.rom))
        self.assertTrue(found)

    def test_every_table_string_roundtrips_without_unknown_bytes(self):
        targets = text_targets(self.rom)
        self.assertEqual(len(targets), 3191)
        for x in targets:
            text, n = self.tbl.decode(self.rom, x, maxlen=20000)
            self.assertNotRegex(text, r"\[[0-9A-F]{2}\]", hex(x))
            self.assertEqual(self.tbl.encode(text), self.rom[x:x + n], hex(x))

    def test_pointer_region_holds_only_pointers(self):
        for i in range(PTR_LO, PTR_HI, 4):
            v = struct.unpack_from("<I", self.rom, i)[0]
            self.assertTrue(v == 0 or 0x08000000 <= v < 0x08800000, hex(i))

    def test_font_block(self):
        data, _ = gbacomp.lz77_decompress(self.rom, 0x1271C8)
        self.assertEqual(len(data), 0xD800)


if __name__ == "__main__":
    unittest.main()
