"""coverage.py: text coverage over several tour runs made on different builds (textcover.py takes one layout).

    python -X utf8 tools/coverage.py --final ROM --run LOGDIR ROM [--run LOGDIR ROM ...] [--waive docs/text_unshown.tsv]

Each ROM has its build's strings.tsv beside it (tools/build.py writes it; freeze a copy with the ROM before a long
run, e.g. work/qa/roms/<sha8>/). A string of the final build counts as shown when some run's logs (TEXT lines from
the textcover probe, read below LOGDIR) read its first byte at that run's address AND the string's bytes up to the
end code are the same in that run's ROM as in the final ROM: a string edited after a run must be shown again.
Prints each string never shown; exit 1 if any isn't waived (waiver = "id<TAB>reason", as for textcover.py)."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill import SKILL  # noqa: E402

sys.path.insert(0, str(Path(SKILL) / "scripts"))
import textcover  # noqa: E402

GBA = 0x08000000
END = 0xFF  # {end}


def table(rom_path):
    return {r[0]: int(r[1], 16) for r in textcover.read_rows(Path(rom_path).parent / "strings.tsv")}


def body(rom, addr):
    off = addr - GBA
    end = rom.index(END, off)
    return rom[off:end + 1]


def report(final, runs, waive=None):
    fin_rom = Path(final).read_bytes()
    fin = table(final)
    shown = set()
    for logdir, rom_path in runs:
        rom, tab, seen = Path(rom_path).read_bytes(), table(rom_path), textcover.shown(logdir, 0xFFFFFFFF)
        n = 0
        for i, a in tab.items():
            if a in seen and i in fin and body(rom, a) == body(fin_rom, fin[i]):
                shown.add(i)
                n += 1
        print(f"{logdir}: {n} strings shown (same bytes as the final build)")
    waived = {r[0]: r[1].strip() for r in textcover.read_rows(waive) if len(r) > 1 and r[1].strip()} if waive else {}
    missing = [i for i in fin if i not in shown]
    bad = [i for i in missing if i not in waived]
    for i in bad:
        print(f"NEVER SHOWN  {i}  {fin[i]:X}")
    print(f"{len(fin) - len(missing)}/{len(fin)} strings shown, {len(missing) - len(bad)} waived, {len(bad)} failing")
    return 1 if bad or not fin else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--final", required=True)
    ap.add_argument("--run", nargs=2, action="append", required=True, metavar=("LOGDIR", "ROM"))
    ap.add_argument("--waive")
    a = ap.parse_args(argv)
    return report(a.final, a.run, a.waive)


if __name__ == "__main__":
    sys.exit(main())
