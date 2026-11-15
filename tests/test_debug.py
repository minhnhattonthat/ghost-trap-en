"""Static checks for the debug warp (tools/debug): scene list, families, ROM tables it relies on."""
import re
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "debug"))
sys.path.insert(0, str(ROOT / "tools"))
import warp  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"
KINDS = {"title", "mode", "script", "story", "field"}


class DebugWarp(unittest.TestCase):
    def test_named_scenes_have_known_kinds(self):
        scenes = warp.named_scenes()
        self.assertGreater(len(scenes), 20)
        for name, f in scenes.items():
            self.assertIn(f.get("kind"), KINDS, name)
            self.assertTrue(f.get("note"), name + " has no note")
            if "after" in f:
                for step in f["after"].split(";"):
                    self.assertRegex(step.strip(), r"^\d+ \S+$", name)

    def test_lookup_handles_every_family(self):
        lua = (ROOT / "tools" / "debug" / "scenes.lua").read_text(encoding="utf-8")
        for pat in (r"\^script_", r"\^area_", r"\^chapter_"):
            self.assertRegex(lua, pat)

    @unittest.skipUnless(ROM.exists(), "ROM not present")
    def test_rom_tables(self):
        rom = ROM.read_bytes()
        rooms = dict(warp.area_rooms(rom))
        self.assertEqual(len(rooms), 136)
        self.assertEqual(rooms[0x5E], 4)  # game start area: rooms 0-3 seen in the room sweep
        self.assertEqual(sum(rooms.values()), 359)
        fam = warp.family_scenes(rom)
        self.assertEqual(len(fam), 127 + 18 + 359)
        self.assertEqual(len(set(fam)), len(fam))
        for i in range(127):  # every script id the warp offers points into the script block
            p = struct.unpack_from("<I", rom, 0x3BFD8 + 4 * i)[0]
            self.assertTrue(0x08100004 <= p < 0x081271C8, "script %d -> %08X" % (i, p))

    def test_warp_lua_addresses_match_notes(self):
        lua = (ROOT / "tools" / "debug" / "warp.lua").read_text(encoding="utf-8")
        notes = (ROOT / "docs" / "re" / "debug.md").read_text(encoding="utf-8")
        for addr in re.findall(r"0x0[238][0-9A-F]{6}", lua):
            self.assertIn(addr, notes, addr + " used by warp.lua but not documented")


if __name__ == "__main__":
    unittest.main()
