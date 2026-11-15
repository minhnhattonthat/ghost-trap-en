"""triage_breaks.py: verdict lines for visual-QA page-break issues (phase 8).

    awk -F'\\t' '$2=="issue"{print $1" | "$3}' work/qa/en/verdicts/chunk_*.tsv > work/qa/issues.txt
    python -X utf8 tools/triage_breaks.py work/qa/issues.txt work/qa/en/verdicts/triage_breaks.tsv

A reviewer note about a page break, on strings that all keep the JP page count, gets "ok": every break there is a JP
{page}/{clr}, kept by the glossary rule (decisions.md D9). Ids in FIXED (reworded since) get "fixed". Prints the
issues it leaves for hand triage (anything else, or a string with more pages than the JP)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import script  # noqa: E402

PG = re.compile(r"\{page\}|\{clr\}")
BREAK = re.compile(r"split|break|stub|dangl|separat|stranded|isolated|clause|across|alone|onto a separate", re.I)
s = {}
for f in script.files():
    for e in script.json.loads(f.read_text(encoding="utf-8")):
        s[e["id"]] = e
FIXED = {"12658C", "126134", "1260E0"}
out, left = [], []
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "work/qa/issues_e520.txt"
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "work/qa/en/verdicts/triage_breaks.tsv"
for ln in SRC.read_text(encoding="utf-8").splitlines():
    sheet, note = ln.split(" | ", 1)
    ids = sorted(set(i for i in re.findall(r"\b1[0-2][0-9A-F]{4}\b", note) if i in s))
    same = ids and all(len(PG.findall(s[i]["jp"])) == len(PG.findall(s[i].get("en") or "")) for i in ids)
    if set(ids) & FIXED:
        out.append("%s\tfixed\t%s reworded to the JP page count, each page a whole clause (build 667dd3c6); re-shown "
                   "in ../pages_667 sheets" % (sheet, " ".join(sorted(set(ids) & FIXED))))
    elif BREAK.search(note) and same and "garbage" not in note and "fused" not in note:
        out.append("%s\tok\tpage breaks are the JP's own {page}/{clr} (%s keep the JP page count; glossary: keep every "
                   "JP page, a sentence may run on over them as in the JP); no stub page" % (sheet, " ".join(ids)))
    else:
        left.append(ln)
DST.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print(len(out), "ok lines written;", len(left), "left:")
print("\n".join(left))
