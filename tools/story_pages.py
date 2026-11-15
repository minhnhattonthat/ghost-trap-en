"""story_pages.py: readable contact sheets of every cutscene page from a story run (warp.py --keep shots).

    python -X utf8 tools/story_pages.py work/qa/en/story [--only REGEX] [--max 16]

warp.py's --sheet keeps frames by whole-screen change at half size, so most text pages are dropped or unreadable.
Here a frame is a "page" when it has text ink (near-white pixels) and the next shot does not still hold all of that
ink (the page was cleared, scrolled or replaced): the last, fully typed shot of each page, from the log's SCENE_OK
frame on (no boot logos). Pages go to
<script dir>/sheet_pages.png (+ sheet_pages_2.png ...) at full size, 4 columns, 16 tiles a page, labelled by frame;
the old warp sheets (sheet.png, sheet_N.png) in that dir are removed so qa_gate.py's "*sheet*.png" glob sees only
these. Prints "<script> <pages> page frames, <n> sheets"."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill import SKILL  # noqa: E402

WHITE = 200  # every channel at least this = text ink (the dialogue font is white; pictures rarely are)


def ink(path):
    im = Image.open(path).convert("RGB")
    return frozenset(i for i, (r, g, b) in enumerate(im.get_flattened_data()) if r >= WHITE and g >= WHITE and b >= WHITE)


def pages(frames):
    masks = [ink(f) for f in frames]
    keep = []
    for i, m in enumerate(masks):
        if len(m) < 20:
            continue
        nxt = masks[i + 1] if i + 1 < len(masks) else frozenset()
        if not m <= nxt:
            keep.append(frames[i])
    return keep


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("story")
    ap.add_argument("--only", default=".")
    ap.add_argument("--max", type=int, default=16)
    a = ap.parse_args()
    for d in sorted(p for p in Path(a.story).iterdir() if p.is_dir() and re.search(a.only, p.name)):
        frames = sorted(d.glob("f[0-9]*.png"))
        log = d / "log.txt"
        m = re.search(r"SCENE_OK \S+ f(\d+)", log.read_text(errors="replace")) if log.exists() else None
        if m:  # skip the boot logos and copyright screen before the scene starts
            frames = [f for f in frames if int(f.stem[1:]) >= int(m.group(1)) - 60]
        if not frames:
            continue
        keep = pages(frames)
        for old in d.glob("sheet*.png"):
            old.unlink()
        if not keep:
            print(d.name, "0 page frames")
            continue
        r = subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "sheet.py"), *map(str, keep),
                            "--div", "1", "--cols", "4", "--max", str(a.max), "--out", str(d / "sheet_pages.png")],
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit("sheet.py failed on %s: %s" % (d.name, r.stderr))
        print(d.name, len(keep), "page frames,", len(list(d.glob("sheet_pages*.png"))), "sheets")


if __name__ == "__main__":
    main()
