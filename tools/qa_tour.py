"""qa_tour.py: the phase-8 tour of a build, every run logging text reads for textcover.py.

    python -X utf8 tools/qa_tour.py [--rom build/ghost_trap_en.gba] [--out work/qa/en] [--skip msgs,tour,story] [--resume]

Steps (each its own output dir under --out, all with the textcover probe over this build's script block):
  msgs   tools/msgview.py: every string of build/strings.tsv through the message viewer -> msgs/
  tour   warp.py --all: every scene's proof shot and group sheets -> tour/
  story  warp.py --all --only script_000..038 --keep --sheet: each cutscene clicked through page by page -> story/,
         then tools/story_pages.py: story/<script>/sheet_pages*.png, one full-size tile per page
Then: textcover.py <out> build/strings.tsv --waive docs/text_unshown.tsv. Exit 1 if a step or the coverage fails."""
import argparse
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import font  # noqa: E402
from skill import SKILL  # noqa: E402

PY = [sys.executable, "-X", "utf8"]
COVER = str(Path(SKILL) / "scripts" / "lua" / "probes" / "textcover.lua")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", type=Path, default=ROOT / "build" / "ghost_trap_en.gba")
    # its own dir: textcover.py reads every log.txt below it, and older runs (marker build) used other layouts
    ap.add_argument("--out", type=Path, default=ROOT / "work" / "qa" / "en")
    ap.add_argument("--skip", default="", help="comma list of steps to skip")
    ap.add_argument("--resume", action="store_true", help="continue interrupted runs (skip proven ids/scenes)")
    a = ap.parse_args(argv)
    skip = set(filter(None, a.skip.split(",")))
    res = ["--resume"] if a.resume else []
    rom = a.rom.read_bytes()
    lo = min(int(ln.split("\t")[1], 16) for ln in (a.rom.parent / "strings.tsv").read_text().split("\n") if ln)
    hi = struct.unpack_from("<I", rom, font.FONT_PTRS[0])[0] - 1
    cover = ["--probe", COVER, "--var", "RANGES='%X-%X'" % (lo, hi)]
    warp = PY + [str(ROOT / "tools" / "debug" / "warp.py"), "--rom", str(a.rom)]
    steps = [
        ("msgs", PY + [str(ROOT / "tools" / "msgview.py"), "--rom", str(a.rom), "--out", str(a.out / "msgs")] + res),
        ("tour", warp + ["--all", "--out", str(a.out / "tour")] + cover + res),
        ("story", warp + ["--all"] + res + ["--only", r"^script_0([0-2]\d|3[0-8])$", "--keep", "--sheet", "--frames", "15000",
                          "--var", "MASH_EVERY=120", "--out", str(a.out / "story")] + cover),
    ]
    fails = []
    for name, cmd in steps:
        if name in skip:
            continue
        print("== %s" % name, flush=True)
        if subprocess.run(cmd).returncode:
            fails.append(name)
        if name == "story":  # warp's half-size sheets drop most pages: one full-size tile per typed-out page
            subprocess.run(PY + [str(ROOT / "tools" / "story_pages.py"), str(a.out / "story")])
    r = subprocess.run(PY + [str(Path(SKILL) / "scripts" / "textcover.py"), str(a.out), str(a.rom.parent / "strings.tsv"),
                             "--waive", str(ROOT / "docs" / "text_unshown.tsv")])
    if r.returncode:
        fails.append("textcover")
    print("failed: %s" % ", ".join(fails) if fails else "all steps ok")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
