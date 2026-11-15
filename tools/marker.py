"""Marker text for the phase-5 marker build (`build.py --marker`): every string keeps its control codes and line
structure; each text run becomes English filler at the box's measured width, the first one led by the string id.

    import marker
    text = marker.mark("10BDD4", jp, charw)   # charw: {char: advance px}, from marker.char_widths(rom, tbl)

Widths per box variant: docs/re/text.md "Width gate" (WIDTH below mirrors it). Runs of spaces only (layout padding
in the intro crawl and the staff roll) are kept as they are; leading spaces of a run are kept too.
"""
import re

TOKEN = re.compile(r"(\{\w+(?::[0-9A-Fa-f]*)?\})")
FILLER = "The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs! "
import json
from pathlib import Path

WIN = json.loads((Path(__file__).resolve().parent / "windows.json").read_text(encoding="utf-8"))
# px per line by variant (tools/windows.json): first control code of the string; "" = no {box:..} (narration);
# "help" = no {box:..} in table 41F18 (item-menu help box)
WIDTH = {"{box:00}": WIN["box"]["px"], "{box:01}": WIN["box"]["px"], "": WIN["narration"]["px"],
         "help": WIN["help"]["px"]}
NAME = "Speaker Nm"  # 80 px = WIN["name"]["px"]


def width_for(entry):
    import script
    if not entry["jp"].startswith("{box:") and script.table_of(int(entry["slots"][0], 16)) == "41F18":
        return WIDTH["help"]
    return None


def char_widths(rom, tbl):
    import font
    w = font.widths(rom)
    out = {}
    for ch, code in tbl.enc.items():
        g = code[0] if len(code) == 1 else 0xE0 + code[1]
        if g < len(w):
            out[ch] = w[g]
    return out


def fill(lead, px, charw):
    """`lead` then filler, cut so the line is at most px wide."""
    out, used, i = lead, sum(charw[c] for c in lead), 0
    while True:
        c = FILLER[i % len(FILLER)]
        if used + charw[c] > px:
            return out.rstrip()
        out, used, i = out + c, used + charw[c], i + 1


def mark(sid, jp, charw, width=None):
    parts = TOKEN.split(jp)
    first = next((p for p in parts if p.startswith("{box:")), "")
    px = width or WIDTH.get(first, WIDTH[""])
    out, tagged, after_name = [], False, False
    for p in parts:
        if not p:
            continue
        if TOKEN.fullmatch(p):
            # {box:00}{name:NN} opens a name plate; {name:NN} elsewhere inserts a variable (item, count)
            if p.startswith("{name:") and out and out[-1] == "{box:00}":
                after_name = True
            out.append(p)
            if p in ("{br}", "{page}", "{clr}"):
                after_name = False
            continue
        if not p.strip(" "):
            out.append("[00]" * len(p))  # layout spaces keep the original 8 px space (en.tbl's is 4 px)
            continue
        if after_name:
            out.append(NAME)
            continue
        nlead = len(p) - len(p.lstrip(" "))
        lead = f"({sid})" if not tagged else ""  # the font has ( ) but no [ ]
        tagged = True
        out.append("[00]" * nlead + fill(lead, max(px - 8 * nlead, sum(charw[c] for c in lead)), charw))
    return "".join(out)
