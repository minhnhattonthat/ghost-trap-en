"""extract.py: dump every string of the script block into script/*.json (format: tools/script.py).

    python -X utf8 tools/extract.py            # writes script/ only if it has no .json yet
    python -X utf8 tools/extract.py --force    # re-extract jp/slots; keeps en/status/notes by id (never clobbers en)
    python -X utf8 tools/extract.py --check    # exit 1 if script/ differs from a fresh extraction (jp/slots/ids)

With --force, an entry whose jp changed while it has an en gets status "recheck" and is listed. Strings are grouped
by owning table (first slot in ROM order), in slot order, and split into files of at most 100 entries or ~6000
characters of jp."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import script  # noqa: E402
import textblock  # noqa: E402
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"
MAX_N, MAX_CHARS = 100, 6000


def extract(rom, tbl):
    """Return {file name: [entry, ...]} for the whole script block."""
    strings = {off: text for kind, off, text in textblock.unpack(rom, tbl) if kind == "str"}
    slots = {}
    for slot, target in textblock.slots(rom):
        slots.setdefault(target, []).append(slot)
    order = sorted(strings, key=lambda t: min(slots[t]))
    groups = {}
    for t in order:
        groups.setdefault(script.table_of(min(slots[t])), []).append(
            {"id": f"{t:06X}", "slots": [f"{s:05X}" for s in sorted(slots[t])], "jp": strings[t], "en": "",
             "status": "todo", "notes": ""})
    out = {}
    for name, _ in script.TABLES:
        chunk, size, n = [], 0, 0
        for e in groups.get(name, []):
            if chunk and (len(chunk) >= MAX_N or size + len(e["jp"]) > MAX_CHARS):
                out[f"{name}_{n:02d}.json"], chunk, size, n = chunk, [], 0, n + 1
            chunk.append(e)
            size += len(e["jp"])
        if chunk:
            out[f"{name}_{n:02d}.json"] = chunk
    return out


def merge(fresh, old_entries):
    """Carry en/status/notes over by id. Returns the ids whose jp changed under an existing translation."""
    old = {e["id"]: e for e in old_entries}
    changed = []
    for entries in fresh.values():
        for e in entries:
            o = old.get(e["id"])
            if not o:
                continue
            for k in ("en", "status", "notes"):
                e[k] = o.get(k, e[k])
            if o["jp"] != e["jp"] and e["en"]:
                e["status"] = "recheck"
                changed.append(e["id"])
    return changed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", type=Path, default=script.SCRIPT)
    a = ap.parse_args(argv)
    tbl = Table.load(ROOT / "tbl" / "jp.tbl")
    fresh = extract(ROM.read_bytes(), tbl)
    existing = script.files(a.out)
    if a.check:
        old = {e["id"]: (e["jp"], e["slots"]) for e in script.load(a.out)}
        new = {e["id"]: (e["jp"], e["slots"]) for es in fresh.values() for e in es}
        bad = sorted(set(old) ^ set(new)) + sorted(i for i in set(old) & set(new) if old[i] != new[i])
        names = {f.name for f in existing} == set(fresh)
        print(f"{len(new)} strings; {len(bad)} differ{'' if names else '; file set differs'}")
        return 1 if bad or not names else 0
    if existing and not a.force:
        sys.exit(f"{a.out} already has {len(existing)} files; --force re-extracts and keeps en/status/notes")
    changed = merge(fresh, script.load(a.out)) if existing else []
    a.out.mkdir(parents=True, exist_ok=True)
    for f in existing:
        if f.name not in fresh:
            f.unlink()
    for name, entries in fresh.items():
        p = a.out / name
        text = script.dump(entries)
        if not p.exists() or p.read_text(encoding="utf-8") != text:
            p.write_text(text, encoding="utf-8", newline="\n")
    n = sum(map(len, fresh.values()))
    print(f"{n} strings in {len(fresh)} files under {a.out}")
    for i in changed:
        print(f"recheck {i}: jp changed under an existing translation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
