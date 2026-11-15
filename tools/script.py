"""The repo's text format: script/<table>_<nn>.json, written by tools/extract.py, read by tools/build.py.

Each file is a JSON list (indent=1, ensure_ascii=False) of entries:
    {"id": "10F2A4",            string offset in the original ROM (hex); stable, the key everywhere
     "slots": ["3C560", ...],   every pointer slot (ROM offset, hex) that reaches this string, in all tables
     "jp": "...",               decoded original (tbl/jp.tbl), byte-exact: encode(jp) == the original bytes
     "en": "",                  translation; empty = keep the original
     "status": "todo",          todo | draft | done | recheck (jp changed under an existing translation)
     "notes": ""}
A string reached from several tables lives in the file of the table whose slot comes first in ROM order.
Tables (docs/re/text.md): scene 0x3BF28, 3C1D4, 3C55C, 3FEB0, 3FF00, 41F18, 423A0 (the lone slot).

    from script import load, texts
    entries = load()                 # [entry, ...] over every file, file order
    over = texts(entries, "en")      # {string offset: text} for entries with a non-empty `en`
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "script"
TABLES = [("scene", 0x3BF28), ("3C1D4", 0x3C1D4), ("3C55C", 0x3C55C), ("3FEB0", 0x3FEB0), ("3FF00", 0x3FF00),
          ("41F18", 0x41F18), ("423A0", 0x423A0)]
FIELDS = ("id", "slots", "jp", "en", "status", "notes")


def table_of(slot):
    name = None
    for n, start in TABLES:
        if slot >= start:
            name = n
    return name


def files(root=SCRIPT):
    return sorted(Path(root).glob("*.json"))


def load(root=SCRIPT):
    out = []
    for f in files(root):
        out += json.loads(f.read_text(encoding="utf-8"))
    return out


def dump(entries):
    """JSON text for one file: indent=1, ensure_ascii=False, trailing newline."""
    return json.dumps(entries, indent=1, ensure_ascii=False) + "\n"


def texts(entries, lang="en"):
    return {int(e["id"], 16): e[lang] for e in entries if e.get(lang)}
