"""vqa_review.py: read-only visual-QA verdicts for qa_gate.py chunks, by `codex exec` (no nested Claude workers here).

    python -X utf8 tools/vqa_review.py work/qa/en/manifest.tsv work/qa/chunks/chunk_*.txt [--batch 6] [--jobs 2]

For each chunk file (paths, one per line, from `qa_gate.py todo ... --out-dir`), sends the sheets to
`codex exec -s read-only` in batches of --batch images, with the judging rules of docs/visual-qa-brief.md, and
writes work/qa/en/verdicts/<chunk>.tsv (`id<TAB>ok|issue<TAB>note`, ids from the manifest). The raw answers go to
work/qa/en/verdicts/raw/<chunk>_<n>.txt. A sheet the reviewer skipped is retried once alone; still missing ->
listed on stderr and left without a verdict (qa_gate.py check keeps failing on it). Issues are for the controller to
fix and re-check (`verdicts/recheck_<n>.tsv`), never waived here."""
import argparse
import concurrent.futures as cf
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "visual-qa-brief.md"


def rules():
    text = BRIEF.read_text(encoding="utf-8")
    return text[text.index("## Judge"):text.index("## Verdicts")].strip()


PROMPT = """You are a read-only visual-QA reviewer for a Japanese-to-English fan translation of a GBA game (Ghost Trap).
Each attached image is a contact sheet (or a proof shot) from the English build's QA tour: tiles are emulator
screenshots (240x160 each, possibly scaled), labelled with frame or scene names. Read every image whole, and look
closely at every text box, menu, Yes/No row and name plate.

{rules}

Answer with exactly one line per image, in attachment order, and nothing else:
<id><TAB>ok|issue<TAB><what and where: tile, the text, what is wrong; for ok a short note of what it shows>
Use a real tab character. The ids, in attachment order:
{ids}
Do not run any commands."""


def ask(ids_paths, raw):
    args = ["codex", "exec", "--skip-git-repo-check", "-s", "read-only"]
    for _, p in ids_paths:
        args += ["-i", str(p)]
    prompt = PROMPT.format(rules=rules(), ids="\n".join(i for i, _ in ids_paths))
    r = subprocess.run(args + ["--", prompt], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=ROOT, timeout=1800)
    raw.write_text(r.stdout + "\n--- stderr ---\n" + r.stderr, encoding="utf-8")
    out = {}
    want = {i for i, _ in ids_paths}
    for line in r.stdout.splitlines():
        m = re.match(r"^\s*`?([^\t`]+?)`?\s*\t\s*(ok|issue)\s*\t\s*(.*)$", line)
        if m and m.group(1) in want:
            out[m.group(1)] = (m.group(2), m.group(3).replace("\t", " ").strip())
    return out


def review(chunk, ids, vdir, batch):
    paths = [Path(p.strip()) for p in chunk.read_text(encoding="utf-8").splitlines() if p.strip()]
    items = [(ids[str(p.resolve())], p) for p in paths]
    got = {}
    for n in range(0, len(items), batch):
        got.update(ask(items[n:n + batch], vdir / "raw" / f"{chunk.stem}_{n // batch}.txt"))
    for i, p in items:
        if i not in got:
            got.update(ask([(i, p)], vdir / "raw" / f"{chunk.stem}_retry_{re.sub(r'[^\\w]+', '_', i)}.txt"))
    lines = [f"{i}\t{got[i][0]}\t{got[i][1]}" for i, _ in items if i in got]
    (vdir / f"{chunk.stem}.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    missing = [i for i, _ in items if i not in got]
    issues = [ln for ln in lines if "\tissue\t" in ln]
    return chunk.name, len(lines), missing, issues


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest", type=Path)
    ap.add_argument("chunks", nargs="+", type=Path)
    ap.add_argument("--batch", type=int, default=6)
    ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args(argv)
    ids = {}
    for line in a.manifest.read_text(encoding="utf-8").splitlines():
        cells = line.split("\t")
        if len(cells) >= 2 and not line.startswith("#"):
            ids[str((ROOT / cells[1]).resolve()) if not Path(cells[1]).is_absolute() else str(Path(cells[1]).resolve())] = cells[0]
    vdir = a.manifest.parent / "verdicts"
    (vdir / "raw").mkdir(parents=True, exist_ok=True)
    bad = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for name, n, missing, issues in ex.map(lambda c: review(c, ids, vdir, a.batch), a.chunks):
            print(f"{name}: {n} verdicts, {len(issues)} issues, {len(missing)} missing", flush=True)
            for ln in issues:
                print("  ISSUE " + ln, flush=True)
            for i in missing:
                print("  MISSING " + i, file=sys.stderr, flush=True)
            bad += len(missing)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
