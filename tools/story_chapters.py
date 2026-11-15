"""Write the story-pass chapter files (references/translation.md §Review) into work/qa/story/chapters/.

    python -X utf8 tools/story_chapters.py [--out DIR]

One file per chapter, strings in table order (the scene table is the cutscene order, scripts 0-38; field tables
are grouped by area block). Each string: `>> id | file` then one line per page, `JP  speaker: text` and
`EN  speaker: text` with box/name codes folded into the speaker. `status: data` strings (staff roll, copyright,
insert-only) are left out. After writing, run:
    python -X utf8 $SKILL/scripts/qa_gate.py init work/qa/story/manifest.tsv work/qa/story/chapters --glob "*.txt"
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import script  # noqa: E402

CHAPTERS = [
    ("01_story_prologue_to_books", ["scene_00", "scene_01", "scene_02"]),
    ("02_story_middle", ["scene_03", "scene_04", "scene_05"]),
    ("03_story_late_to_ending", ["scene_06", "scene_07", "scene_08", "scene_09", "scene_10"]),
    ("04_field_advice_and_hall", ["3C1D4_00", "3C1D4_01", "3C55C_00", "3C55C_01", "3C55C_02"]),
    ("05_field_3C55C_a", ["3C55C_03", "3C55C_04", "3C55C_05", "3C55C_06", "3C55C_07"]),
    ("06_field_3C55C_b", ["3C55C_08", "3C55C_09", "3C55C_10", "3C55C_11", "3C55C_12"]),
    ("07_field_3C55C_c", ["3C55C_13", "3C55C_14", "3C55C_15", "3C55C_16", "3C55C_17"]),
    ("08_field_3FF00_a", ["3FEB0_00", "3FF00_00", "3FF00_01", "3FF00_02", "3FF00_03", "3FF00_04"]),
    ("09_field_3FF00_b", ["3FF00_05", "3FF00_06", "3FF00_07", "3FF00_08", "3FF00_09"]),
    ("10_field_3FF00_c", ["3FF00_10", "3FF00_11", "3FF00_12", "3FF00_13", "423A0_00"]),
    ("11_items_and_help", ["41F18_00", "41F18_01", "41F18_02", "41F18_03"]),
]
PAGE = re.compile(r"\{(?:page|clr|end)\}")
SPEAKER = re.compile(r"^\{box:00\}\{name:[0-9A-F]{2}\}([^{]*)\{br\}")


def pages(text):
    out = []
    for body in PAGE.split(text):
        m = SPEAKER.match(body)
        who = ""
        if m:
            who, body = m.group(1) + ": ", body[m.end():]
        body = re.sub(r"\{br\}\s*", " ", body)
        body = re.sub(r"\{box:[0-9A-F]{2}\}", "", body).strip()
        if body:
            out.append(who + body)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "story" / "chapters"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    listed = {f for _, fs in CHAPTERS for f in fs}
    missing = [f.stem for f in script.files() if f.stem not in listed]
    if missing:
        sys.exit(f"script files in no chapter: {missing}")
    for name, stems in CHAPTERS:
        lines = []
        for stem in stems:
            for e in json.loads((script.SCRIPT / f"{stem}.json").read_text(encoding="utf-8")):
                if e["status"] == "data" or not e["en"]:
                    continue
                lines.append(f">> {e['id']} | {stem}")
                lines += [f"JP  {p}" for p in pages(e["jp"])]
                lines += [f"EN  {p}" for p in pages(e["en"])]
                lines.append("")
        (out / f"{name}.txt").write_text("\n".join(lines), encoding="utf-8")
        print(f"{name}.txt  {sum(1 for x in lines if x.startswith('>>'))} strings")


if __name__ == "__main__":
    main()
