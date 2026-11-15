"""msgview.py: show strings in game through the message viewer (tools/lua/msgview.lua), one cold boot each.

    python -X utf8 tools/msgview.py [--rom build/ghost_trap_en.gba] [--out work/qa/msgs] [--only REGEX]
                                    [--jobs 4] [--hold 150] [--resume] [--sheets]

For every string in build/strings.tsv (written by tools/build.py beside the ROM): warp to script 39, point its
scene-table entry at the string, and take the proof shot HOLD frames after the first glyph (warp.lua). Each run also
loads the textcover probe over the script block, so `textcover.py work/qa build/strings.tsv` counts the strings.
Out: <out>/<id>/script_039/{scene.png,log.txt}, <out>/summary.tsv, and with --sheets one contact sheet of proof
shots per pointer table (<out>/sheet_<table>_NN.png; the table is the script/ file the id lives in).
Exit 1 if any string failed to show (no SCENE_OK)."""
import argparse
import concurrent.futures as cf
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "debug"))
import font  # noqa: E402
import script  # noqa: E402
import warp  # noqa: E402
from skill import SKILL  # noqa: E402

COVER = Path(SKILL) / "scripts" / "lua" / "probes" / "textcover.lua"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", type=Path, default=ROOT / "build" / "ghost_trap_en.gba")
    ap.add_argument("--out", type=Path, default=ROOT / "work" / "qa" / "msgs")
    ap.add_argument("--only", help="regex on string ids (hex, as in script/)")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--hold", type=int, default=150, help="frames from the first glyph to the proof shot")
    ap.add_argument("--resume", action="store_true", help="skip ids that already have a proof shot")
    ap.add_argument("--sheets", action="store_true", help="only (re)write the contact sheets")
    a = ap.parse_args(argv)
    rows = [ln.split("\t") for ln in (a.rom.parent / "strings.tsv").read_text(encoding="utf-8").split("\n") if ln]
    addr = {i: int(x, 16) for i, x in rows}
    rom = a.rom.read_bytes()
    lo = min(addr.values())
    hi = struct.unpack_from("<I", rom, font.FONT_PTRS[0])[0] - 1  # the font LZ block follows the script block
    ids = [i for i in addr if not a.only or re.search(a.only, i)]
    owner = {}  # id -> script/ file stem, one sheet group per file
    for f in script.files():
        for e in script.json.loads(f.read_text(encoding="utf-8")):
            owner[e["id"]] = f.stem
    a.out.mkdir(parents=True, exist_ok=True)

    def proven(i):
        log = a.out / i / "script_039" / "log.txt"
        return log.exists() and "SCENE_OK" in log.read_text(encoding="utf-8", errors="replace")

    if not a.sheets:
        todo = [i for i in ids if not (a.resume and proven(i))]
        pvars = ["MSG=0x%X" % 0, "HOLD=%d" % a.hold, "RANGES='%X-%X'" % (lo, hi)]

        def one(i):
            v = list(pvars)
            v[0] = "MSG=0x%X" % addr[i]
            return i, warp.run_scene("script_039", a.rom, a.out / i, False, 4000, False, False,
                                     probes=[ROOT / "tools" / "lua" / "msgview.lua", COVER], pvars=v)

        with cf.ThreadPoolExecutor(a.jobs) as ex:
            for n, f in enumerate(cf.as_completed([ex.submit(one, i) for i in todo]), 1):
                i, (_, code, msg) = f.result()
                if code or n % 100 == 0:
                    print("[%d/%d] %s %s %s" % (n, len(todo), "ok " if code == 0 else "FAIL", i, msg), flush=True)
    bad = [i for i in ids if not proven(i)]
    with open(a.out / "summary.tsv", "w", encoding="utf-8", newline="\n") as f:
        f.write("id\taddress\tok\n")
        for i in ids:
            f.write("%s\t%X\t%d\n" % (i, addr[i], i not in bad))
    groups = {}
    for i in ids:
        if i not in bad:
            groups.setdefault(owner.get(i, "all"), []).append(i)
    for g, members in groups.items():
        d = a.out / "_sheets" / g
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        for i in members:
            shutil.copy(a.out / i / "script_039" / "scene.png", d / ("%s.png" % i))
        subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "sheet.py"), str(d / "*.png"),
                        "--div", "1", "--cols", "4", "--max", "24", "--out", str(a.out / ("sheet_%s.png" % g))],
                       capture_output=True)
    print("%d strings, %d failed%s" % (len(ids), len(bad), (": " + " ".join(bad[:20])) if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
