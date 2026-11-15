"""Title logo (G1): tools/gfx_title.py removes the katakana line and touches nothing outside its declared area."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gbacomp  # noqa: E402
import gfx_title as g  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"


@unittest.skipUnless(ROM.exists(), "needs the original ROM")
class GfxTitle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()
        cls.tiles, cls.map, cls.img = g.load(cls.rom)
        cls.new = g.redraw(cls.img)

    def test_pointer_points_at_the_original(self):
        self.assertEqual(struct.unpack_from("<I", self.rom, g.TILES_PTR)[0], 0x08000000 + g.TILES)

    def test_store_of_load_is_identity(self):
        self.assertEqual(g.store(self.tiles, self.map, self.img), self.tiles)

    def test_no_change_outside_the_free_area(self):
        bad = [(x, y) for y in range(g.H) for x in range(g.W)
               if self.new[y][x] != self.img[y][x] and not g.free(y, x)]
        self.assertEqual(bad, [])

    def test_katakana_gone(self):
        self.assertGreater(sum(g.CLASSES[v] == "g" for row in self.img for v in row), 500)
        left = [(x, y) for y in range(g.H) for x in range(g.W) if g.CLASSES[self.new[y][x]] == "g"]
        self.assertEqual(left, [])
        c = [[g.CLASSES[v] for v in row] for row in self.new]
        blocks = [(x, y) for y in range(g.H - 1) for x in range(g.W - 1) if g.free(y, x)
                  and all(c[y + a][x + b] == "W" for a in (0, 1) for b in (0, 1))]
        self.assertEqual(blocks, [], "solid white = katakana strokes (letter rims are 1 px)")

    def test_writes_is_the_whole_block_and_packs(self):
        (ptrs, raw), = g.writes(self.rom)
        self.assertEqual(ptrs, [g.TILES_PTR])
        self.assertEqual(len(raw), len(self.tiles))
        self.assertEqual(raw[:64], bytes(64), "tile 0 (blank, shared by the whole map) must stay blank")
        self.assertEqual(gbacomp.lz77_decompress(gbacomp.lz77_compress(raw), 0)[0], raw)


if __name__ == "__main__":
    unittest.main()
