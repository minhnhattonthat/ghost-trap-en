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


def build(orig, texts=None, lang="en"):
    """Return (rom bytes, write log lines). texts: {string offset: text} overrides (script/ via script.texts)."""
    jp = Table.load(ROOT / "tbl" / "jp.tbl")
    w = Writer(orig)
    segs = textblock.unpack(orig, jp)
    block, moved = textblock.pack(segs, jp, texts, enc=table(lang))
    span = textblock.TEXT_HI - textblock.TEXT_LO
    if len(block) > span:
        raise SystemExit(f"script block is {len(block)} bytes, {len(block) - span} over its {span}-byte home")
    w.write(textblock.TEXT_LO, block, "script")
    for slot, target in textblock.slots(orig):
        w.write(slot, struct.pack("<I", textblock.GBA + moved[target]), "ptr")
    return bytes(w.rom), w.log


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--lang", default="en", help="script/ field to insert (default en)")
    a = ap.parse_args(argv)
    check_rom.check()
    orig = ROM.read_bytes()
    over = script.texts(script.load(), a.lang)
    rom, log = build(orig, over, a.lang)
    print(f"{len(over)} strings from script/ ({a.lang})")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_bytes(rom)
    wlog = a.out.parent / "writes.log"
    wlog.write_text("\n".join(log) + "\n", encoding="utf-8")
    ranges = [ln.split("#")[0].strip() for ln in (ROOT / "tools" / "allowed_ranges.txt").read_text().splitlines()]
    r = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "romdiff.py"), str(ROM), str(a.out),
                        *[x for x in ranges if x], "--writes", str(wlog)])
    if r.returncode:
        sys.exit("romdiff failed")
    same = rom == orig
    print(f"{a.out.relative_to(ROOT)}  {len(rom)} bytes  sha1 {hashlib.sha1(rom).hexdigest()}"
          f"{'  (identical to the dump)' if same else ''}")


if __name__ == "__main__":
    main()
