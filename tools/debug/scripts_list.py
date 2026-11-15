"""List the 127 cutscene scripts (table 0x3BFD8, index = byte 0x03004A77): id, ROM address, length, opening text.

    python -X utf8 tools/debug/scripts_list.py [--chars 60] [--tsv tools/debug/scripts.tsv]
"""
import argparse
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"
SCRIPT_TABLE = 0x3BFD8
COUNT = 127


def scripts(rom):
    for i in range(COUNT):
        p = struct.unpack_from("<I", rom, SCRIPT_TABLE + 4 * i)[0]
        yield i, (p & 0x1FFFFFF) if p else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chars", type=int, default=60)
    ap.add_argument("--tsv")
    a = ap.parse_args()
    rom = ROM.read_bytes()
    tbl = Table.load(ROOT / "tbl" / "jp.tbl")
    rows = []
    for i, off in scripts(rom):
        if off is None:
            rows.append((i, "-", 0, ""))
            continue
        text, n = tbl.decode(rom, off, maxlen=20000)
        flat = re.sub(r"\{[^}]*\}|\s+", " ", text)
        flat = re.sub(" +", " ", flat).strip()
        rows.append((i, "%06X" % off, n, flat[: a.chars]))
    for r in rows:
        print("%3d %s %5d %s" % r)
    if a.tsv:
        with open(a.tsv, "w", encoding="utf-8", newline="\n") as f:
            f.write("id\trom\tbytes\topening\n")
            for r in rows:
                f.write("%d\t%s\t%d\t%s\n" % r)


if __name__ == "__main__":
    main()
