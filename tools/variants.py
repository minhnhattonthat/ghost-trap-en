"""Survey the script's box variants: per variant (first control code of the string, by table), how many strings,
the most lines on one page, and the widest Japanese line in px. Feeds the width gate (docs/re/text.md).

    python -X utf8 tools/variants.py [--examples 2]
"""
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import font  # noqa: E402
import script  # noqa: E402
from tbl import Table  # noqa: E402

TOKEN = re.compile(r"(\{\w+(?::[0-9A-Fa-f]*)?\})")


def pages(text):
    """[[line, ...], ...] split on {page}/{clr}; lines split on {br}; other control codes stay in the line."""
    out = []
    for pg in re.split(r"\{page\}|\{clr\}", text):
        out.append(pg.split("{br}"))
    return out


def variant(e):
    m = re.match(r"(\{box:\w+\}(?:\{name:\w+\})?)", e["jp"])
    v = m[1] if m else "none"
    if v.startswith("{box:00}"):
        v = "{box:00}{name}"
    return f"{script.table_of(int(e['slots'][0], 16))} {v}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--examples", type=int, default=1)
    a = ap.parse_args()
    jp = Table.load(ROOT / "tbl" / "jp.tbl")
    rom = (ROOT / "rom" / "Ghost Trap (Japan).gba").read_bytes()
    stats = defaultdict(lambda: {"n": 0, "lines": 0, "px": 0, "ex": []})
    for e in script.load():
        s = stats[variant(e)]
        s["n"] += 1
        for pg in pages(e["jp"]):
            body = [ln for ln in pg if not re.fullmatch(r"(\{[^}]*\})*", ln)]
            s["lines"] = max(s["lines"], len(body))
            for ln in pg:
                plain = TOKEN.sub("", ln)
                if plain:
                    s["px"] = max(s["px"], font.width_px(plain, jp, rom))
        if len(s["ex"]) < a.examples:
            s["ex"].append(f"{e['id']} {e['jp'][:60]}")
    for k, s in sorted(stats.items()):
        print(f"{k:28} n={s['n']:5} max lines/page={s['lines']:3} widest JP line={s['px']:4} px")
        for x in s["ex"]:
            print(f"    {x}")


if __name__ == "__main__":
    main()
