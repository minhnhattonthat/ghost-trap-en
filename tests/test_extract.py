"""Phase 4 extraction: script/ roundtrips to the original bytes, covers the whole script block, and build.py inserts
from it; extract.py never clobbers en."""
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import extract  # noqa: E402
import script  # noqa: E402
import textblock  # noqa: E402
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"


class TestMerge(unittest.TestCase):
    def test_merge_keeps_en_and_flags_changed_jp(self):
        fresh = {"a.json": [{"id": "1", "slots": [], "jp": "new", "en": "", "status": "todo", "notes": ""},
                            {"id": "2", "slots": [], "jp": "same", "en": "", "status": "todo", "notes": ""}]}
        old = [{"id": "1", "jp": "old", "en": "Hi", "status": "done", "notes": "n"},
               {"id": "2", "jp": "same", "en": "Yo", "status": "draft", "notes": ""}]
        changed = extract.merge(fresh, old)
        a, b = fresh["a.json"]
        self.assertEqual((a["en"], a["status"], a["notes"]), ("Hi", "recheck", "n"))
        self.assertEqual((b["en"], b["status"]), ("Yo", "draft"))
        self.assertEqual(changed, ["1"])

    def test_extract_refuses_without_force(self):
        if not script.files():
            self.skipTest("script/ not extracted")
        with self.assertRaises(SystemExit):
            extract.main([])


@unittest.skipUnless(ROM.is_file(), "ROM not present")
class TestScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM.read_bytes()
        cls.tbl = Table.load(ROOT / "tbl" / "jp.tbl")
        cls.entries = script.load()

    def test_fields(self):
        for e in self.entries:
            self.assertEqual(tuple(e), script.FIELDS, e["id"])

    def test_roundtrip_every_string(self):
        """encode(jp) is exactly the original bytes at the id, through the {end} (FF)."""
        self.assertEqual(len(self.entries), 3192)
        for e in self.entries:
            off = int(e["id"], 16)
            raw = self.tbl.encode(e["jp"])
            self.assertEqual(raw, self.rom[off:off + len(raw)], e["id"])
            self.assertEqual(raw[-1], 0xFF, e["id"])
            self.assertEqual(self.tbl.decode(self.rom, off, maxlen=0x8000)[1], len(raw), e["id"])
            self.assertNotRegex(e["jp"], r"\[[0-9A-F]{2}\]", f"{e['id']}: unknown byte")

    def test_every_slot_listed_once_and_points_at_its_entry(self):
        listed = {}
        for e in self.entries:
            for s in e["slots"]:
                self.assertNotIn(s, listed)
                listed[s] = e["id"]
        rom_slots = {f"{s:05X}": f"{t:06X}" for s, t in textblock.slots(self.rom)}
        self.assertEqual(listed, rom_slots)
        self.assertEqual(len(rom_slots), 5741)

    def test_matches_fresh_extraction(self):
        fresh = extract.extract(self.rom, self.tbl)
        self.assertEqual({f.name for f in script.files()}, set(fresh))
        key = lambda es: [(e["id"], e["slots"], e["jp"]) for e in es]  # noqa: E731
        self.assertEqual(key(self.entries), key([e for f in script.files() for e in fresh[f.name]]))

    def test_block_coverage_only_known_raw_runs(self):
        """Every byte of 0x100000-0x1271C8 is a string, its 4-alignment padding, the header or a listed dead run."""
        raws = [(off, len(v)) for kind, off, v in textblock.unpack(self.rom, self.tbl) if kind == "raw"]
        tail = raws.pop()
        self.assertEqual(tail[0] + tail[1], textblock.TEXT_HI)
        self.assertLess(tail[1], 4)
        self.assertEqual([o for o, _ in raws], [textblock.HEADER, *textblock.DEAD])
        self.assertEqual(self.rom[textblock.HEADER:textblock.HEADER + 4], b"AGBD")

    def test_dead_runs_have_no_pointer(self):
        """No u32 anywhere in the ROM points at the start of a string inside a dead run."""
        segs = {off: v for kind, off, v in textblock.unpack(self.rom, self.tbl) if kind == "raw"}
        for d in textblock.DEAD:
            run, p = segs[d], 0
            while p < len(run):
                while p < len(run) and run[p] == 0:
                    p += 1
                if p >= len(run):
                    break
                start = d + p
                ptr = struct.pack("<I", textblock.GBA + start)
                hits, i = [], self.rom.find(ptr)
                while i != -1:
                    hits.append(i)
                    i = self.rom.find(ptr, i + 1)
                # 0x4C5824 is inside graphics data (0x4xxxxx), not a pointer table
                self.assertEqual([h for h in hits if h < 0x100000], [], f"{start:X}")
                p += self.tbl.decode(self.rom, start, maxlen=0x8000)[1]

    def test_build_inserts_en_and_repoints(self):
        target = next(e for e in self.entries if len(e["slots"]) > 1 and len(self.tbl.encode(e["jp"])) > 24)
        over = {int(target["id"], 16): "{box:01}Hello there{page}{end}"}
        rom, _ = build.build(self.rom, over)
        en = build.table("en")
        for s in target["slots"]:
            p = struct.unpack_from("<I", rom, int(s, 16))[0] - textblock.GBA
            self.assertEqual(en.decode(rom, p)[0], over[int(target["id"], 16)])
            self.assertEqual(p % 4, 0)
        other = next(e for e in reversed(self.entries) if e["id"] != target["id"])
        p = struct.unpack_from("<I", rom, int(other["slots"][0], 16))[0] - textblock.GBA
        self.assertEqual(self.tbl.decode(rom, p, maxlen=0x8000)[0], other["jp"])


if __name__ == "__main__":
    unittest.main()
