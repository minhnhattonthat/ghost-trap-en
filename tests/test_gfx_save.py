"""SAVE/LOAD message boxes (G2, G3): tools/gfx_save.py builds tiles + maps that fit and that the build repoints."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx_save  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"


@unittest.skipUnless(ROM.exists(), "needs the original ROM")
class GfxSave(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()
        cls.new = gfx_save.english(cls.rom)

    def test_every_map_has_english_and_valid_tiles(self):
        for tb, _, maps in gfx_save.SETS.values():
            ntiles = len(self.new[tb]) // 32
            self.assertLessEqual(ntiles, gfx_save.MAX_TILES)
            self.assertEqual(self.new[tb][:32], bytes(32), "tile 0 must stay blank")
            for mb, _ in maps:
                self.assertIn(mb, gfx_save.TEXT)
                m = struct.unpack("<1024H", self.new[mb])
                ids = {e & 0x3FF for e in m}
                self.assertLess(max(ids), ntiles)
                self.assertGreater(len(ids), 1, "%X has no text" % mb)
                self.assertEqual(len(gfx_save.TEXT[mb]), len(gfx_save.bands(gfx_save.lz(self.rom, mb))))

    def test_pointers_point_at_the_originals(self):
        for tb, tp, maps in gfx_save.SETS.values():
            for off, ptrs in [(tb, [tp])] + maps:
                for p in ptrs:
                    self.assertEqual(struct.unpack_from("<I", self.rom, p)[0], 0x08000000 + off)


if __name__ == "__main__":
    unittest.main()
