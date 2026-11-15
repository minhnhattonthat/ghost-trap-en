"""Re-fit stored English to the current box budgets (tools/windows.json) as a batch for `batches.py merge`.

    python -X utf8 tools/refit.py NAME [--fix F.tsv]   -> work/tl/NAME.tsv + NAME.out.tsv, then:
    python -X utf8 tools/batches.py merge NAME --overwrite

For every string whose stored `en` differs from wrap.layout's output or fails its width check, each page with a
line over budget gets its {br} turned back into spaces, so wrap.layout re-wraps it (and adds {page}s if needed).
Pages that fit keep the author's layout. Prints before/after per string for review. Written for the field box
(184 px, narrower than the 224 px cutscene box), found from a player report on 2026-11-16.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import script  # noqa: E402
import wrap  # noqa: E402


def refit(entry):
    width, _ = wrap.variant(entry)
    out = ""
    for body, code in wrap.segments(entry["en"]):
        pre, rest = wrap.prefix(body)
        if "{br}" in rest and any(wrap.px(ln) > width for ln in rest.split("{br}")):
            rest = " ".join(ln.strip() for ln in rest.split("{br}"))
        out += pre + rest + code
    return out


def main(name, fix=None):
    """fix: TSV of `old text<TAB>new text` (hand rewrites of over-budget lines), applied before the re-fit."""
    fixes = [ln.split("\t") for ln in Path(fix).read_text(encoding="utf-8").splitlines() if ln.strip()] if fix else []
    rows, used = [], set()
    for e in script.load():
        if not e.get("en") or not e.get("slots"):
            continue
        en = e["en"]
        for old, new in fixes:
            if old in en:
                en = en.replace(old, new)
                used.add(old)
        laid, bad = wrap.layout(e, en)
        if en == e["en"] and laid == en and not any(p.startswith("line ") for p in bad):
            continue
        # laid out here: merge skips a string whose text is unchanged, and a {br}-less page re-wraps only in layout
        new = wrap.layout(e, refit(dict(e, en=en)))[0]
        rows.append((e, new))
        print(f"{e['id']}\n  old {e['en']}\n  new {new}")
    for old, _ in fixes:
        if old not in used:
            print(f"warning: fix not used: {old!r}")
    tl = ROOT / "work" / "tl"
    tl.mkdir(parents=True, exist_ok=True)
    (tl / f"{name}.tsv").write_text("".join(f"{e['id']}\t\t\t\t{e['jp']}\n" for e, _ in rows), encoding="utf-8",
                                    newline="\n")
    (tl / f"{name}.out.tsv").write_text("".join(f"{e['id']}\t{new}\n" for e, new in rows), encoding="utf-8",
                                        newline="\n")
    print(f"{len(rows)} strings -> {tl / name}.out.tsv")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    main(args[0], args[args.index("--fix") + 1] if "--fix" in args else None)
