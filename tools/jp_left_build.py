"""Leftover-Japanese scan of an English build: the skill's jp_left.py over every text pointer slot.

    python -X utf8 tools/jp_left_build.py [build/ghost_trap_en.gba]     exit 0 = no Japanese a slot reaches

jp_left.py decodes with tbl/jp.tbl, but tools/font.py copied English punctuation into small-kana cells (41 '.' is
ぃ, 04 '?' is ぇ ...), so "...?" reads as ぃぃぃぇ. The scan uses jp.tbl minus every code tbl/en.tbl also maps
(written to work/qa/jp_minus_en.tbl), and work/qa/slots.txt lists every slot from script/.
The 9 `status: data` strings are not translated on purpose (staff roll, copyright, {name:0B} inserts); none is
Japanese text a slot reaches today. If one ever is, list it in work/qa/jp_known.txt and pass it on.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import script  # noqa: E402
from skill import SKILL  # noqa: E402

QA = ROOT / "work" / "qa"


def codes(path):
    out = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            out[k.strip().upper()] = (ln, v)
    return out


def main():
    built = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build" / "ghost_trap_en.gba"
    QA.mkdir(parents=True, exist_ok=True)
    en = codes(ROOT / "tbl" / "en.tbl")
    jp = codes(ROOT / "tbl" / "jp.tbl")
    keep = [ln for k, (ln, _) in jp.items() if k not in en]
    (QA / "jp_minus_en.tbl").write_text("\n".join(keep) + "\n", encoding="utf-8")
    (QA / "slots.txt").write_text("\n".join(s for e in script.load() for s in e["slots"]) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "jp_left.py"), str(built),
                        "--tbl", str(QA / "jp_minus_en.tbl"), "--slots", str(QA / "slots.txt")])
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
