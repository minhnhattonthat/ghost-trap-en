"""build.py: build build/ghost_trap_en.gba from the original dump.

    python -X utf8 tools/build.py [--out build/ghost_trap_en.gba]

Steps: check the dump against rom.sha1; unpack the script block (tools/textblock.py); repack it with every non-empty
`en` from script/ (tools/script.py; none yet, so the output is byte-identical to the dump: tests/test_identity.py);
rewrite the text pointers; log every write to
build/writes.log and run romdiff.py over it with tools/allowed_ranges.txt. Exit 1 if any step fails."""
import argparse
import hashlib
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402
import font  # noqa: E402
import gbacomp  # noqa: E402
import gfx_save  # noqa: E402
import marker  # noqa: E402
import script  # noqa: E402
import textblock  # noqa: E402
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"
OUT = ROOT / "build" / "ghost_trap_en.gba"


class Writer:
    """ROM buffer that logs every write as `OFFSET ORIG_HEX NEW_HEX writer` for romdiff.py --writes."""

    def __init__(self, orig):
        self.orig, self.rom, self.log = bytes(orig), bytearray(orig), []

    def write(self, off, data, who):
        end = off + len(data)
        if end > len(self.rom):
            self.rom += b"\xff" * (end - len(self.rom))
        old = self.orig[off:end].ljust(len(data), b"\xff")
        self.rom[off:end] = data
        self.log.append(f"{off:X} {old.hex()} {bytes(data).hex()} {who}")


def table(lang):
    """Encoder for `lang`: tbl/<lang>.tbl once it exists, else tbl/jp.tbl (its A-Z/a-z cells encode plain ASCII)."""
    p = ROOT / "tbl" / f"{lang}.tbl"
    return Table.load(p if p.exists() else ROOT / "tbl" / "jp.tbl")


RELOC = 0x800000      # English builds: script block, then the font, past the original 8 MiB
ROM_MAX = 0x1000000   # EEPROM save: stay at or below 16 MiB


def build(orig, texts=None, lang="en", layout=None):
    """Return (rom bytes, write log lines). texts: {string offset: text} overrides (script/ via script.texts).
    layout: a dict to fill with {original string offset: ROM offset in this build} (build/strings.tsv).
    No overrides: the identity build (== the dump). Any override: the English layout (docs/re/text.md
    "English layout"): script block at RELOC without the dead runs, old block blanked (header kept), the font with
    the English glyphs (tools/font.py) LZ-packed after it and both font pointers moved, English advances in the
    width table, ROM padded to a 64 KiB multiple."""
    jp = Table.load(ROOT / "tbl" / "jp.tbl")
    w = Writer(orig)
    segs = textblock.unpack(orig, jp)
    if not texts:
        block, moved = textblock.pack(segs, jp)
        w.write(textblock.TEXT_LO, block, "script")
    else:
        block, moved = textblock.pack(segs, jp, texts, enc=table(lang), base=RELOC, raw=False)
        w.write(RELOC, block, "script")
        w.write(textblock.HEADER + 4, bytes(textblock.TEXT_HI - textblock.HEADER - 4), "blank-old-script")
        lz = gbacomp.lz77_compress(font.patched(orig))
        at = RELOC + len(block) + (-len(block) % 4)
        w.write(at, lz, "font")
        for p in font.FONT_PTRS:
            w.write(p, struct.pack("<I", textblock.GBA + at), "font-ptr")
        w.write(font.WIDTHS, font.width_table(orig), "widths")
        end = at + len(lz)
        for ptrs, raw in gfx_save.writes(orig):  # graphics text G2/G3: new LZ blocks after the font, repointed
            end += -end % 4
            blk = gbacomp.lz77_compress(raw)
            w.write(end, blk, "gfx")
            for p in ptrs:
                w.write(p, struct.pack("<I", textblock.GBA + end), "gfx-ptr")
            end += len(blk)
        if end % 0x10000:
            w.write(end, b"\xff" * (-end % 0x10000), "pad")
        if len(w.rom) > ROM_MAX:
            raise SystemExit(f"ROM is {len(w.rom):#x} bytes, over the 16 MiB EEPROM limit")
    for slot, target in textblock.slots(orig):
        w.write(slot, struct.pack("<I", textblock.GBA + moved[target]), "ptr")
    if layout is not None:
        layout.update(moved)
    return bytes(w.rom), w.log


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--lang", default="en", help="script/ field to insert (default en)")
    ap.add_argument("--marker", action="store_true",
                    help="every string without `en` -> (id) + filler at box width (tools/marker.py)")
    ap.add_argument("--qa", action="append", default=[], metavar="ID=TEXT",
                    help="override one string (hex id as in script/) with TEXT (en.tbl), after --marker; repeatable")
    ap.add_argument("--loose", action="store_true", help="original 8 px advances instead of font.TIGHT (comparison)")
    a = ap.parse_args(argv)
    if a.loose:
        font.TIGHT = False
    check_rom.check()
    orig = ROM.read_bytes()
    entries = script.load()
    over = script.texts(entries, a.lang)
    if a.marker:
        charw = marker.char_widths(orig, table(a.lang))
        for e in entries:
            if e["status"] == "data":  # not text (variable inserts) or already English: original bytes
                continue
            over.setdefault(int(e["id"], 16), marker.mark(e["id"], e["jp"], charw, marker.width_for(e)))
    for q in a.qa:
        sid, _, text = q.partition("=")
        over[int(sid, 16)] = text
    layout = {}
    rom, log = build(orig, over, a.lang, layout)
    print(f"{len(over)} strings from script/ ({a.lang}{', marker' if a.marker else ''}"
          f"{f', {len(a.qa)} --qa' if a.qa else ''})")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(rom)
    # textcover.py input: id = original offset (script/ ids), address = where this build's game reads it
    ids = sorted(int(e["id"], 16) for e in entries)
    (a.out.parent / "strings.tsv").write_text(
        "".join(f"{i:X}\t{textblock.GBA + layout[i]:X}\n" for i in ids), encoding="utf-8", newline="\n")
    wlog = a.out.parent / "writes.log"
    wlog.write_text("\n".join(log) + "\n", encoding="utf-8")
    ranges = [ln.split("#")[0].strip() for ln in (ROOT / "tools" / "allowed_ranges.txt").read_text().splitlines()]
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "romdiff.py"), str(ROM), str(a.out),
                        *[x for x in ranges if x], "--writes", str(wlog)])
    if r.returncode:
        sys.exit("romdiff failed")
    same = rom == orig
    print(f"{a.out}  {len(rom)} bytes  sha1 {hashlib.sha1(rom).hexdigest()}"
          f"{'  (identical to the dump)' if same else ''}")


if __name__ == "__main__":
    main()
