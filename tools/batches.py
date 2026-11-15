"""Translation batches (docs/translator-brief.md): split untranslated text, check translator output, merge it back.

    python -X utf8 tools/batches.py split [--size 3500]   work/tl/bNNN.tsv and build/terms_bNNN.txt for untranslated JP
    python -X utf8 tools/batches.py check [bNNN ...]      a batch's .out.tsv; with no batch, all shipped English (for check.py)
    python -X utf8 tools/batches.py merge bNNN ... [--overwrite]   check, then write the English into script/

From the skill's assets/batches.py, ADAPTER fitted to Ghost Trap ({codes}, pixel widths via tools/wrap.py).
Batch TSV: id, speaker, form, limit, JP. Output: work/tl/bNNN.out.tsv, id<TAB>English, every id once, same order.
merge stores the English laid out by wrap.layout ({br} and any added {page} filled in), status done.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TL = ROOT / "work/tl"
SCRIPT = ROOT / "script"
GLOSSARY = ROOT / "glossary.md"
MAX_ENTRIES = 150

# ---- ADAPTER: this game's text format ----
TOKEN = re.compile(r"\{\w+(?::[0-9A-Fa-f]*)?\}")  # control codes and variable inserts; must survive translation
# {br} is placed by tools/wrap.py; {page} may be added; {box}/{name:NN} speaker prefixes repeat on added pages.
FREE = {"{br}", "{page}"}
VARIABLE = r"\{name:(?:0A|15)\}"  # an item name or count the game draws
HONORIFICS = {"さん": "-san", "くん": "-kun", "ちゃん": "-chan", "先生": "-sensei"}  # glossary ruling D1
ENCODABLE = set(" !\"%&'()+,-./0123456789:;?ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#~")


def docs():
    """(path, doc, entries) per script file; entries hold id, jp, en, and optionally speaker, box, max, dup."""
    for path in sorted(SCRIPT.rglob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        yield path, doc, doc["entries"] if isinstance(doc, dict) else doc


def needs_english(entry):
    """Empty JP isn't "untranslated": it would be re-queued forever. `data` strings are never translated."""
    return bool(entry.get("jp")) and not entry.get("en") and entry.get("status") != "data"


def group_of(entry):
    """Entries with the same value stay in one batch: fragments of one sentence, split around a drawn number."""
    return entry.get("dup") or entry["id"]


def limit_label(entry):
    import wrap
    w, n = wrap.variant(entry)
    return f"{w}px x{n}"


def skeleton(text):
    """Order of the codes that must survive: {clr}/{end}, inserts, and the speaker/box run (repeats collapsed)."""
    t = [x for x in TOKEN.findall(text) if x not in FREE]
    units, i = [], 0
    while i < len(t):
        if t[i].startswith("{box:") and i + 1 < len(t) and t[i + 1].startswith("{name:") and t[i + 1] not in INSERTS:
            u, i = t[i] + t[i + 1], i + 2
        else:
            u, i = t[i], i + 1
        if not (u.startswith("{box:") and units and units[-1] == u):  # a prefix repeated on an added page
            units.append(u)
    return units


INSERTS = {"{name:0A}", "{name:15}", "{name:01}", "{name:07}", "{name:0B}"}
SPEAKERS = {"ジョージ": "George", "カロル": "Karol", "アリシア": "Alicia", "？？？？": "????", "シンファ": "Shinfa",
            "アルビノ": "Albino", "死のつかい": "Reaper"}  # glossary.md Characters


# Shorthand for reading batches (`view`) and writing .out.tsv: expanded before check/merge.
PLATES = {"G": ("02", "ジョージ", "George"), "A": ("03", "アリシア", "Alicia"), "K": ("04", "カロル", "Karol"),
          "Q": ("05", "？？？？", "????"), "S": ("06", "シンファ", "Shinfa"), "B": ("06", "アルビノ", "Albino"),
          "R": ("06", "死のつかい", "Reaper"), "X": ("07", "？？？？", "????")}
CODES = [("|", "{page}"), ("^", "{clr}"), ("$", "{end}"), ("\\", "{br}"), ("@1", "{box:01}"), ("@0", "{box:00}")]


def compact(jp):
    for k, (nn, ja, _) in PLATES.items():
        jp = jp.replace("{box:00}{name:%s}%s{br}" % (nn, ja), f"@{k} ")
    for short, code in CODES:
        jp = jp.replace(code, short)
    return jp


def expand(en):
    en = re.sub(r"@([GAKQSBRX]) ?", lambda m: "{box:00}{name:%s}%s{br}" % (PLATES[m.group(1)][0], PLATES[m.group(1)][2]), en)
    for short, code in CODES:
        en = en.replace(short, code)
    return en


def width_problems(entry, en):
    import wrap
    return wrap.layout(entry, en)[1]


def encodable(char):
    return char in ENCODABLE
# ---- end of ADAPTER ----


def kind(char):
    if "぀" <= char <= "ゟ":
        return "hiragana"
    if "゠" <= char <= "ヿ":
        return "katakana"
    if "一" <= char <= "鿿" or char == "々":
        return "kanji"
    return "other"


def has_term(jp, term):
    """term occurs as a whole kana or kanji run: ミン isn't in タイミング, くも isn't in ぼくも."""
    for m in re.finditer(re.escape(term), jp):
        a, b = m.start(), m.end()
        if (a == 0 or kind(jp[a - 1]) != kind(term[0])) and (b == len(jp) or kind(jp[b]) != kind(term[-1])):
            return True
    return False


def glossary():
    """[(JP forms, EN forms, avoid forms)] from glossary.md's | JP | EN | max | notes | Avoid | tables."""
    rows = []
    if not GLOSSARY.exists():
        return rows
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 2 and cells[0] not in ("JP", "") and not set(cells[0]) <= set("-: "):
            avoid = [x.strip() for x in cells[4].split("/") if x.strip()] if len(cells) > 4 else []
            rows.append(([x.strip() for x in cells[0].split("/")], [x.strip() for x in cells[1].split("/")], avoid))
    return rows


def problems(entry, en, terms):
    """Every rule, on one line of English."""
    jp = entry["jp"]
    if not en.strip():
        return ["empty English"]
    out = []
    plain = TOKEN.sub("", en)
    if bad := sorted({c for c in plain if not encodable(c) and c != "\n"}):
        out.append(f"unencodable characters {bad}")
    if re.search(r"\\u[0-9a-fA-F]{4}", en) or "\t" in en:
        out.append("escape sequence or tab in the English")
    want, have = skeleton(jp), skeleton(en)
    if want != have:
        k = next((i for i, (a, b) in enumerate(zip(want, have)) if a != b), min(len(want), len(have)))
        out.append(f"control codes differ at unit {k}: JP {want[max(0, k - 1):k + 3]} EN {have[max(0, k - 1):k + 3]}")
    if en.count("{page}") < jp.count("{page}"):
        out.append(f"{{page}} count {en.count('{page}')} < JP {jp.count('{page}')}")
    for m in re.finditer(r"\{name:([0-9A-F]{2})\}([^{]*)\{br\}", jp):
        if m.group(1) not in ("0A", "15", "01", "07", "0B") and SPEAKERS.get(m.group(2)):
            if not re.search(re.escape("{name:" + m.group(1) + "}" + SPEAKERS[m.group(2)] + "{br}"), en):
                out.append(f"speaker {m.group(2)} must read {SPEAKERS[m.group(2)]!r}")
    if re.search(VARIABLE + r"(st|nd|rd|th)\b", en):
        out.append('ordinal suffix after a variable (write "No. [var]")')
    jp_plain = TOKEN.sub("", jp)
    for jps, ens, avoid in terms:
        if any(has_term(jp_plain, j) for j in jps) and not any(e.lower() in en.lower() for e in ens):
            out.append(f"glossary: {jps[0]} -> {ens[0]}")
        out += [f"glossary Avoid: {a}" for a in avoid if re.search(rf"\b{re.escape(a)}\b", en)]
    for jp_form, en_form in HONORIFICS.items():
        if jp_form in jp_plain and en_form.lower() not in en.lower():
            out.append(f"honorific {jp_form} needs {en_form}")
    return out + width_problems(entry, en)


def index():
    return {e["id"]: e for _, _, entries in docs() for e in entries}


def read_tsv(path):
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def existing():
    return sorted(TL.glob("b[0-9][0-9][0-9].tsv"))


def split(size):
    """Numbers on from the last batch and leaves out ids already batched, so a repeat run can't duplicate work."""
    TL.mkdir(parents=True, exist_ok=True)
    (ROOT / "build").mkdir(exist_ok=True)
    taken = {r[0] for p in existing() for r in read_tsv(p)}
    n = max((int(p.stem[1:]) for p in existing()), default=0)
    groups = {}
    for _, _, entries in docs():
        for e in entries:
            if needs_english(e) and e["id"] not in taken:
                groups.setdefault(group_of(e), []).append(e)
    batches, cur, chars = [], [], 0
    for group in groups.values():
        c = sum(len(TOKEN.sub("", e["jp"])) for e in group)
        if cur and (chars + c > size or len(cur) + len(group) > MAX_ENTRIES):
            batches.append(cur)
            cur, chars = [], 0
        cur += group
        chars += c
    if cur:
        batches.append(cur)
    terms = glossary()
    for batch in batches:
        n += 1
        name = f"b{n:03d}"
        path = TL / f"{name}.tsv"
        if path.exists():
            sys.exit(f"{path} already exists")
        rows = [f"{e['id']}\t{e.get('speaker', '')}\t{e.get('box', '')}\t{limit_label(e)}\t{e['jp']}" for e in batch]
        path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        jps = " ".join(TOKEN.sub("", e["jp"]) for e in batch)
        used = [(j, ens[0]) for jpl, ens, _ in terms for j in jpl if has_term(jps, j)]
        (ROOT / f"build/terms_{name}.txt").write_text("".join(f"{j}\t{e}\n" for j, e in used)
                                                      or "(no glossary terms in this batch)\n", encoding="utf-8", newline="\n")
    print(f"{len(batches)} new batches in {TL}, {len(taken)} ids already batched")


def check_batch(batch, entries, terms):
    want = [r[0] for r in read_tsv(TL / f"{batch}.tsv")]
    raw = []  # a line starting with a space continues the row above (long strings split at {clr} for reading)
    for line in (TL / f"{batch}.out.tsv").read_text(encoding="utf-8").splitlines():
        if line.startswith("  ") and raw:
            raw[-1] += line[2:]
        elif line.strip():
            raw.append(line)
    rows = [(r.split("\t")[0], expand("\t".join(r.split("\t")[1:]).strip())) for r in raw]
    bad = []
    if [r[0] for r in rows] != want:
        got = [r[0] for r in rows]
        dup = sorted(i for i, c in Counter(got).items() if c > 1)
        bad.append(f"ids differ: missing {sorted(set(want) - set(got))[:8]} extra {sorted(set(got) - set(want))[:8]} "
                   f"duplicate {dup[:8]} (order must match too)")
    for eid, en in rows:
        if eid in entries:
            bad += [f"{eid}: {p}" for p in problems(entries[eid], en, terms)]
    return bad, dict(rows)


def merge(new, overwrite):
    """Refuses to replace different English unless told to, before anything is written."""
    if not overwrite:
        for _, _, entries in docs():
            for e in entries:
                if e["id"] in new and e.get("en") and e["en"] != new[e["id"]]:
                    sys.exit(f"{e['id']} would lose {e['en']!r}: pass --overwrite if that is meant")
    changed = 0
    for path, doc, entries in docs():
        touched = False
        for e in entries:
            if e["id"] in new and e.get("en") != new[e["id"]]:
                e["en"], e["status"] = new[e["id"]], "done"
                if e.get("slots"):
                    import wrap
                    e["en"] = wrap.layout(e, e["en"])[0]
                touched = True
                changed += 1
        if touched:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"merged: {changed} entries changed")


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "split":
        return split(int(args[args.index("--size") + 1]) if "--size" in args else 3500)
    if cmd == "view":  # the batch in shorthand: id, JP (see PLATES / CODES)
        for r in read_tsv(TL / f"{args[0]}.tsv"):
            print(f"{r[0]}\t" + compact(r[4]).replace("^", "^\n  "))
        return 0
    overwrite = "--overwrite" in args
    names = [a for a in args if a != "--overwrite"]
    entries, terms = index(), glossary()
    if cmd == "check" and not names:
        bad = [f"{i}: {p}: {e['en']!r}" for i, e in entries.items() if e.get("en") for p in problems(e, e["en"], terms)]
        print(f"{len(entries)} entries, {len(bad)} problems")
        print("\n".join(bad[:200]))
        return 1 if bad else 0
    if cmd not in ("check", "merge") or not names:
        sys.exit(__doc__)
    new, failed = {}, 0
    for batch in names:
        bad, rows = check_batch(batch, entries, terms)
        new.update(rows)
        failed += bool(bad)
        print(f"{batch}: " + ("OK" if not bad else f"{len(bad)} problems"))
        for line in bad:
            print("  " + line)
    if failed:
        return 1
    if cmd == "merge":
        merge(new, overwrite)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(ROOT / "tools"))
    sys.exit(main(sys.argv[1:]))
