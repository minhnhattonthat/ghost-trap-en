"""Print a batch's ids whose JP already has an English translation elsewhere (same JP -> same English).

Usage: python -X utf8 tools/prefill.py bNNN               (list the prefill)
       python -X utf8 tools/prefill.py --todo bNNN        (view lines still to translate -> write bNNN.new)
       python -X utf8 tools/prefill.py --assemble bNNN    (prefill + bNNN.new -> bNNN.out.tsv, batch order)
Reads work/tl/*.tsv (batch JP) and work/tl/*.out.tsv (shorthand English); prints `id<TAB>english` lines in the
shorthand used by out.tsv (continuation lines indented by two spaces), ready to paste.
"""
import sys
from pathlib import Path

TL = Path(__file__).resolve().parent.parent / "work" / "tl"


def jp_of(batch):
    rows = {}
    for line in (TL / f"{batch}.tsv").read_text(encoding="utf-8").splitlines():
        if line.strip():
            cols = line.split("\t")
            rows[cols[0]] = cols[-1]
    return rows


def out_of(batch):
    rows, cur = {}, None
    path = TL / f"{batch}.out.tsv"
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("  "):
            rows[cur] += "\n" + line
        elif line.strip():
            cur, text = line.split("\t", 1)
            rows[cur] = text
    return rows


def todo(batch):
    """Print the view lines (work/tl/bNNN.view.txt) of ids with no prefill, to translate into bNNN.new."""
    filled = prefilled(batch)
    jp, seen = jp_of(batch), set()
    keep = False
    for line in (TL / f"{batch}.view.txt").read_text(encoding="utf-8").splitlines():
        if not line.startswith("  ") and line.strip():
            i = line.split("\t", 1)[0]
            keep = i not in filled and jp[i] not in seen  # a repeat inside the batch is filled by --assemble
            seen.add(jp[i])
        if keep:
            print(line)
    print(f"# {len(jp_of(batch)) - len(filled)} to translate", file=sys.stderr)


def assemble(batch):
    """Write bNNN.out.tsv in batch order from the prefill plus bNNN.new (hand-translated ids)."""
    rows = prefilled(batch)
    rows.update(out_of_path(TL / f"{batch}.new"))
    jp = jp_of(batch)
    by_jp = {jp[i]: text for i, text in rows.items() if i in jp}
    rows.update({i: by_jp[j] for i, j in jp.items() if i not in rows and j in by_jp})  # repeats inside the batch
    missing = [i for i in jp_of(batch) if i not in rows]
    if missing:
        sys.exit(f"missing: {missing}")
    text = "".join(f"{i}\t{rows[i]}\n" for i in jp_of(batch))
    (TL / f"{batch}.out.tsv").write_text(text, encoding="utf-8")
    print(f"{batch}.out.tsv: {len(rows)} ids")


def out_of_path(path):
    rows, cur = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("  "):
            rows[cur] += "\n" + line
        elif line.strip():
            cur, text = line.split("\t", 1)
            rows[cur] = text
    return rows


def prefilled(batch):
    known = {}
    for path in sorted(TL.glob("b[0-9][0-9][0-9].tsv")):
        name = path.stem
        if name == batch:
            continue
        jp, en = jp_of(name), out_of(name)
        for i, text in en.items():
            if i in jp:
                known.setdefault(jp[i], text)
    return {i: known[jp] for i, jp in jp_of(batch).items() if jp in known}


def main(batch):
    known = {}
    for path in sorted(TL.glob("b[0-9][0-9][0-9].tsv")):
        name = path.stem
        if name == batch:
            continue
        jp, en = jp_of(name), out_of(name)
        for i, text in en.items():
            if i in jp:
                known.setdefault(jp[i], text)
    hits = 0
    for i, jp in jp_of(batch).items():
        if jp in known:
            print(f"{i}\t{known[jp]}")
            hits += 1
    print(f"# {hits} of {len(jp_of(batch))} prefilled", file=sys.stderr)


if __name__ == "__main__":
    mode = {"--todo": todo, "--assemble": assemble}.get(sys.argv[1])
    mode(sys.argv[2]) if mode else main(sys.argv[1])
