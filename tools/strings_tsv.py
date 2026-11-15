"""Rebuild a build's strings.tsv (id<TAB>GBA address) from its ROM's pointer slots, when the file beside a frozen
ROM was lost or overwritten (a `build.py --out DIR/x.gba` writes DIR/strings.tsv beside it).

    python -X utf8 tools/strings_tsv.py ROM [--check TSV]     prints the table; --check compares it with TSV
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import script  # noqa: E402


def table(rom):
    out = {}
    for e in script.load():
        addrs = {struct.unpack_from("<I", rom, int(s, 16))[0] for s in e["slots"]}
        if len(addrs) != 1:
            raise SystemExit(f"{e['id']}: slots disagree {sorted(map(hex, addrs))}")
        out[e["id"]] = addrs.pop()
    return out


def main(argv):
    rom = Path(argv[0]).read_bytes()
    t = table(rom)
    if "--check" in argv:
        ref = {}
        for ln in Path(argv[argv.index("--check") + 1]).read_text(encoding="utf-8").splitlines():
            if ln.strip():
                i, a = ln.split("\t")[:2]
                ref[i] = int(a, 16)
        bad = [i for i in ref if t.get(i) != ref[i]] + [i for i in t if i not in ref]
        print(f"{len(ref)} rows, {len(bad)} differ {bad[:5]}")
        return 1 if bad else 0
    sys.stdout.write("".join(f"{i}\t{a:X}\n" for i, a in t.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
