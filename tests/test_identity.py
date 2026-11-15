"""Phase 3 identity build: unpack -> repack with no edits gives the dump byte for byte; the LZ77 packer roundtrips."""
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import gbacomp  # noqa: E402
import textblock  # noqa: E402
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"
FONT = 0x1271C8


class TestPacker(unittest.TestCase):
    def test_lz77_roundtrip_synthetic(self):
        for data in (b"a", b"\x00" * 5000, bytes(range(256)) * 9, b"abcabcabcabd" * 300):
            packed = gbacomp.lz77_compress(data)
            self.assertEqual(len(packed) % 4, 0)
            self.assertEqual(gbacomp.lz77_decompress(packed)[0], data)

    def test_lz77_never_uses_displacement_1(self):
        packed = gbacomp.lz77_compress(b"\x11" * 100)
        p, flags = 4, packed[4]
        # first flag byte: literal, then back-references; each must have disp >= 2
        p += 1
        for bit in range(8):
            if flags & (0x80 >> bit):
                disp = ((packed[p] & 0xF) << 8 | packed[p + 1]) + 1
                self.assertGreaterEqual(disp, 2)
                p += 2
            else:
                p += 1


@unittest.skipUnless(ROM.is_file(), "ROM not present")
class TestIdentity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig = ROM.read_bytes()
        cls.rom, cls.log = build.build(cls.orig)

    def test_identity_build_is_byte_identical(self):
        self.assertEqual(hashlib.sha1(self.rom).hexdigest(), hashlib.sha1(self.orig).hexdigest())

    def test_block_fully_covered(self):
        tbl = Table.load(ROOT / "tbl" / "jp.tbl")
        segs = textblock.unpack(self.orig, tbl)
        cur = textblock.TEXT_LO
        for kind, off, val in segs:
            if kind == "str":
                pad = -cur % 4
                self.assertEqual(self.orig[cur:cur + pad], bytes(pad))  # implicit alignment padding is zeros
                cur += pad
            self.assertEqual(off, cur)
            cur += len(val) if kind == "raw" else len(tbl.encode(val))
        self.assertEqual(cur, textblock.TEXT_HI)
        strings = sum(1 for s in segs if s[0] == "str")
        self.assertEqual(strings, 3192)  # 3191 table targets + 0x106A8C from the lone slot

    def test_writes_logged(self):
        self.assertTrue(any(ln.endswith(" script") for ln in self.log))
        self.assertEqual(sum(ln.endswith(" ptr") for ln in self.log), len(list(textblock.slots(self.orig))))

    def test_moved_strings_follow_their_pointers(self):
        # an edit that grows one early string moves every later one; every pointer must follow
        tbl = Table.load(ROOT / "tbl" / "jp.tbl")
        segs = textblock.unpack(self.orig, tbl)
        first = next(off for kind, off, _ in segs if kind == "str")
        old = dict((o, v) for k, o, v in segs if k == "str")[first]
        texts = {first: "あ" + old}
        block, moved = textblock.pack(segs, tbl, texts)
        span = textblock.TEXT_HI - textblock.TEXT_LO
        self.assertTrue(span < len(block) <= span + 4)  # one byte more, re-aligned to 4
        for target in {t for _, t in textblock.slots(self.orig)}:
            self.assertEqual(moved[target] % 4, 0)
            got = tbl.decode(block, moved[target] - textblock.TEXT_LO, maxlen=0x8000)[0]
            self.assertEqual(got, texts.get(target, tbl.decode(self.orig, target, maxlen=0x8000)[0]))

    def test_overfull_block_is_refused(self):
        tbl = Table.load(ROOT / "tbl" / "jp.tbl")
        first = next(off for kind, off, _ in textblock.unpack(self.orig, tbl) if kind == "str")
        with self.assertRaises(SystemExit):
            build.build(self.orig, {first: "あ" * 0x8000 + "{end}"})

    def test_font_block_repacks(self):
        font, _ = gbacomp.lz77_decompress(self.orig, FONT)
        self.assertEqual(gbacomp.lz77_decompress(gbacomp.lz77_compress(font))[0], font)


if __name__ == "__main__":
    unittest.main()
