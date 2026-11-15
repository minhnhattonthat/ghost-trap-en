"""Lay out English for the box it shows in, and check it against the measured budgets (tools/windows.json).

    import wrap
    text, problems = wrap.layout(entry, en)      # en as authored -> the string build.py inserts, plus problems
    python -X utf8 tools/wrap.py ID "text"       # dry run: print the laid-out lines with their px widths

Authoring rules (docs/translator-brief.md):
- A page is the text between {page} / {clr} / {end}. Keep every {clr}, {end}, {box:..}, variable insert
  ({name:0A} item, {name:15} count, {name:01}/{name:07} choice colours) where the Japanese has them.
- Dialogue pages keep their prefix `{box:00}{name:NN}Speaker{br}`; the speaker plate is 80 px.
- A page body with no {br} is wrapped here (greedy, on spaces); if it needs more lines than the box has, it is split
  into extra pages joined by {page} (box pages repeat their prefix). A body with {br} is the author's layout and is
  only checked. Item-help strings (table 41F18) are always laid out by hand: name{br}line{br}line.
Widths: tools/font.py advances; {name:0A} counts as the widest item name, {name:15} as two digits.
"""
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
WIN = json.loads((ROOT / "tools" / "windows.json").read_text(encoding="utf-8"))
TOKEN = re.compile(r"(\{\w+(?::[0-9A-Fa-f]*)?\})")
PAGE = ("{page}", "{clr}", "{end}")
INSERT_PX = {"{name:0A}": WIN["item_name"]["px"], "{name:15}": 16, "{name:01}": 0, "{name:07}": 0, "{name:0B}": 0}


@lru_cache(maxsize=1)
def charw():
    import build
    import marker
    rom = build.ROM.read_bytes()
    w = marker.char_widths(rom, build.table("en"))
    return {c: px for c, px in w.items() if len(c) == 1}


SCENE = 0x3BFD8  # script pointer table (127 u32): scripts 0-38 play as cutscenes (mode 8), 39+ in the field
CUTSCENES = 39


def in_field(entry):
    """True if any slot shows the string in the field box (narrower than the cutscene box: the HUD sits right)."""
    for s in entry["slots"]:
        s = int(s, 16)
        if not (SCENE <= s < SCENE + 4 * CUTSCENES):
            return True
    return False


def variant(entry):
    """(px per line, lines per page) for the string's box."""
    import script
    if not entry["jp"].startswith("{box:") and script.table_of(int(entry["slots"][0], 16)) == "41F18":
        return WIN["help"]["px"], WIN["help"]["lines"]
    if in_field(entry):
        return WIN["field"]["px"], WIN["field"]["lines"]
    return WIN["box"]["px"], WIN["box"]["lines"]


ITEM_NAMES = (0x4214C, 0x42294)  # slots of the item description strings; their first line is the item name


@lru_cache(maxsize=1)
def item_name_px():
    """Widest English item name, which is what {name:0A} draws (the 152 px item-name budget if none is translated):
    "Picked up {name:0A}" has to fit the 184 px field box with the real names, not the budget."""
    import script
    widths = [px(re.split(r"\{br\}|\{page\}|\{end\}", e["en"])[0]) for e in script.load()
              if e.get("en") and any(ITEM_NAMES[0] <= int(s, 16) <= ITEM_NAMES[1] for s in e["slots"])]
    return max(widths, default=WIN["item_name"]["px"])


def px(text):
    w, total = charw(), 0
    for part in TOKEN.split(text):
        if part == "{name:0A}":
            total += item_name_px()
        elif TOKEN.fullmatch(part):
            total += INSERT_PX.get(part, 0)
        else:
            total += sum(w.get(c, 8) for c in part)
    return total


def segments(text):
    """[(body, page code)]; the last code may be '' when the string has no {end}."""
    out, cur = [], ""
    for part in TOKEN.split(text):
        if part in PAGE:
            out.append((cur, part))
            cur = ""
        else:
            cur += part
    if cur:
        out.append((cur, ""))
    return out


def prefix(body):
    """Split `{box:NN}{name:NN}Speaker{br}` (or `{box:NN}`) off a page body."""
    m = re.match(r"(\{box:[0-9A-F]{2}\}(?:\{name:[0-9A-F]{2}\}[^{]*\{br\})?)", body)
    return (m.group(1), body[m.end():]) if m else ("", body)


def wrap_body(body, width):
    words, lines, cur = body.split(" "), [], ""
    for wd in words:
        cand = f"{cur} {wd}" if cur else wd
        if cur and px(cand) > width:
            lines.append(cur)
            cur = wd
        else:
            cur = cand
    lines.append(cur)
    return lines


def balance(lines, width):
    """Two lines: move the break so the longer line is as short as possible (no one-word orphan)."""
    if len(lines) != 2:
        return lines
    words = " ".join(lines).split(" ")
    best = lines
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if px(a) <= width and px(b) <= width and max(px(a), px(b)) < max(px(best[0]), px(best[1])):
            best = [a, b]
    return best


def paginate(body, width, nlines):
    """Pages of at most nlines lines, broken between sentences where possible, each page balanced."""
    chunks = [c for c in re.split(r"(?<=[.!?\"')])\s+", body) if c]
    pages, cur = [], ""
    for c in chunks:
        cand = f"{cur} {c}" if cur else c
        if cur and len(wrap_body(cand, width)) > nlines:
            pages.append(cur)
            cur = c
        else:
            cur = cand
    pages.append(cur)
    out = []
    for p in pages:
        for part in split_long(p, width, nlines):
            out.append(balance(wrap_body(part, width), width))
    return out


@lru_cache(maxsize=4096)
def split_long(text, width, nlines):
    """One sentence too long for a page: split it into as few pages as it needs, at the break that keeps the
    pages even and prefers a clause boundary (comma, dash, ellipsis), so no page is a one-word stub."""
    lines = wrap_body(text, width)
    if len(lines) <= nlines:
        return [text]
    words = text.split(" ")
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if len(wrap_body(a, width)) > nlines:
            break
        rest = split_long(b, width, nlines)
        clause = a[-1] in ",;:-" or a.endswith("...")
        score = (len(rest), -min(len(a), len(rest[0])) - (12 if clause else 0))
        if best is None or score < best[0]:
            best = (score, [a] + rest)
    return best[1] if best else [text]


STUB = 10  # a page wrap.py adds must hold at least this many characters ("running." at 8 read as a stub)
LAST_MIN = 6  # the last line of a multi-line page (an orphaned word reads as a layout bug)


def stubs(text):
    """Pages that continue a sentence from the page before (it ends without . ! ? or a quote) yet hold under
    STUB characters: what a mid-clause page split looks like to the player."""
    bad, prev = [], None
    for body, _ in segments(text):
        # {clr} clears the box too (cutscene narration), so each cleared part is its own page on screen
        for part in prefix(body)[1].split("{clr}"):
            plain = TOKEN.sub("", part.replace("{br}", " ")).strip()
            if prev and plain and len(plain) < STUB and not re.search(r"[.!?\"')~]$", prev):
                bad.append(f"stub page {plain!r} continues {prev[-30:]!r}")
            if plain:
                prev = plain
    return bad


def layout(entry, en):
    width, nlines = variant(entry)
    help_box = width == WIN["help"]["px"]
    out, bad = "", []
    for body, code in segments(en):
        pre, rest = prefix(body)
        if "{name:" in pre:
            name = re.sub(r"\{[^}]*\}", "", pre)
            if px(name) > WIN["name"]["px"]:
                bad.append(f"speaker {name!r} is {px(name)} px > {WIN['name']['px']}")
        if "{br}" in rest or help_box or not rest.strip():
            lines = rest.split("{br}")
            pages = [lines]
        else:
            pages = paginate(rest.strip(), width, nlines)
        for i, pg in enumerate(pages):
            for ln in pg:
                if px(ln) > width:
                    bad.append(f"line {ln!r} is {px(ln)} px > {width}")
            if len(pg) > nlines:
                bad.append(f"{len(pg)} lines on a page > {nlines}: {pg!r}")
            last = TOKEN.sub("", pg[-1]).strip()
            if len(pg) > 1 and re.search(r"[A-Za-z]", last) and len(last) < LAST_MIN:
                bad.append(f"stub last line {last!r} (under {LAST_MIN} characters): {pg!r}")
            out += ("{page}" if i else "") + (pre if (i == 0 or pre.startswith("{box")) else "") + "{br}".join(pg)
        out += code
    return out, bad + stubs(out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import script
    ent = {e["id"]: e for e in script.load()}[sys.argv[1]]
    text, problems = layout(ent, sys.argv[2])
    for body, code in segments(text):
        for ln in body.split("{br}"):
            print(f"{px(re.sub(r'^.*\}', '', ln) if ln.startswith('{box') else ln):4d}  {ln}")
        print(f"      {code}")
    print("\n".join(problems) or "OK")
