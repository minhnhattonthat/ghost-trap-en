"""pageview.py: every page of every string, fully typed, on labelled contact sheets (phase-8 visual QA).

    python -X utf8 tools/pageview.py [--rom build/ghost_trap_en.gba] [--out work/qa/en/pages] [--only REGEX]
                                     [--group 24] [--jobs 2] [--resume] [--sheets]

msgview.py takes one shot a fixed time after the first glyph, so most of its shots show a page still typing. Here
the strings of build/strings.tsv (read from --rom, so the bytes are the final build's) are chained, per script/
file and --group strings at a time, into one message each: a string's {end} becomes {page} (or is dropped after
its own {page}/{clr}), the last string keeps its {end}. The chains are appended to a QA-only copy of the ROM
(<out>/_qa.gba); each chain is shown through script 39's scene-table slot (tools/lua/msgview.lua) and
tools/lua/pageview.lua shoots every page a few frames after its {page}/{clr} handler runs (pages do not wait for a
button there). Page n of the chain maps to its string by counting page codes per string.
Out: <out>/<group>/script_039/{p0001.png..,log.txt}, <out>/_tiles/<group>/<id>_<k>.png, and contact sheets
<out>/sheet_<group>.png (16 tiles, 4 columns, full size, each tile labelled "<id> p<k>").
Prints each string with no page shot (no glyph drawn, or a stalled run); exit 1 if a run failed or stalled."""
import argparse
import concurrent.futures as cf
import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools" / "debug"))
import script  # noqa: E402
import warp  # noqa: E402

GBA = 0x08000000
PAGE, CLR, END = 0xFD, 0xFE, 0xFF
LUA = ROOT / "tools" / "lua"
LABEL = 12  # px label strip above each tile


def body(rom, addr):
    off = addr - GBA
    return rom[off:rom.index(END, off)]  # without the {end}


def pages(b):
    """Page codes in a string body, by token (E0xx kanji, F7 nn {box}, FB nn {name} take 2 bytes; tbl/jp.tbl)."""
    k = n = 0
    while k < len(b):
        c = b[k]
        if c in (PAGE, CLR):
            n += 1
        k += 2 if c in (0xE0, 0xF7, 0xFB) else 1
    return n


def chain(rom, ids, addr):
    """Bytes of one chained message and each string's (id, page count), in order."""
    out, spans = bytearray(), []
    for i in ids:
        b = bytearray(body(rom, addr[i]))
        if pages(b) == 0 or b[-1] not in (PAGE, CLR):
            b.append(PAGE)
        out += b
        spans.append((i, pages(b)))
    out.append(END)
    return bytes(out), spans


def groups(ids, size):
    """Chains of up to `size` strings per script/ file. `status: data` strings are left out: insert-only
    {name:0B} strings (the item-name insert stalls a chain in script 39) and text the original already has in
    English (staff roll, copyright screen); the story run shows those."""
    owner, data = {}, set()
    for f in script.files():
        for e in script.json.loads(f.read_text(encoding="utf-8")):
            owner[e["id"]] = f.stem
            if e.get("status") == "data":
                data.add(e["id"])
    by = {}
    for i in ids:
        if i not in data:
            by.setdefault(owner.get(i, "all"), []).append(i)
    out = {}
    for g, members in by.items():
        for k in range(0, len(members), size):
            out["%s_%02d" % (g, k // size)] = members[k:k + size]
    return out


def sheets(tiles, dest_stem, per=16, cols=4):
    """tiles: [(label, png path)] -> dest_stem.png, dest_stem_2.png ..."""
    made = []
    for s in range(0, len(tiles), per):
        part = tiles[s:s + per]
        rows = (len(part) + cols - 1) // cols
        w, h = 240, 160 + LABEL
        sheet = Image.new("RGB", (cols * w + (cols - 1) * 2, rows * h + (rows - 1) * 2), (90, 0, 90))
        d = ImageDraw.Draw(sheet)
        for k, (label, p) in enumerate(part):
            x, y = (k % cols) * (w + 2), (k // cols) * (h + 2)
            d.rectangle([x, y, x + w - 1, y + LABEL - 1], fill=(255, 255, 160))
            d.text((x + 2, y), label, fill=(0, 0, 0))
            sheet.paste(Image.open(p).convert("RGB").resize((240, 160)), (x, y + LABEL))
        name = dest_stem.parent / ("%s%s.png" % (dest_stem.name, "" if s == 0 else "_%d" % (s // per + 1)))
        sheet.save(name)
        made.append(name)
    return made


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", type=Path, default=ROOT / "build" / "ghost_trap_en.gba")
    ap.add_argument("--out", type=Path, default=ROOT / "work" / "qa" / "en" / "pages")
    ap.add_argument("--only", help="regex on group names (<script file>_<nn>)")
    ap.add_argument("--group", type=int, default=24)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--resume", action="store_true", help="skip groups whose log says PAGES_DONE")
    ap.add_argument("--sheets", action="store_true", help="only (re)write tiles and sheets from existing runs")
    a = ap.parse_args(argv)
    rows = [ln.split("\t") for ln in (a.rom.parent / "strings.tsv").read_text(encoding="utf-8").split("\n") if ln]
    addr = {i: int(x, 16) for i, x in rows}
    rom = a.rom.read_bytes()
    grp = groups(list(addr), a.group)
    if a.only:
        grp = {g: m for g, m in grp.items() if re.search(a.only, g)}
    a.out.mkdir(parents=True, exist_ok=True)

    qa = bytearray(rom)
    base = {}
    spans = {}
    for g in sorted(grp):
        while len(qa) % 4:
            qa.append(0)
        data, sp = chain(rom, grp[g], addr)
        base[g] = GBA + len(qa)
        spans[g] = sp
        qa += data
    if len(qa) > 0x2000000:
        sys.exit("QA ROM over 32 MiB")
    qa_rom = a.out / "_qa.gba"
    qa_rom.write_bytes(bytes(qa))

    def logpath(g):
        return a.out / g / "script_039" / "log.txt"

    def logtext(g):
        p = logpath(g)
        return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

    def one(g):
        expect = sum(c for _, c in spans[g])
        pv = ["MSG=0x%X" % base[g], "HOLD=999999", "LO=0x%X" % base[g], "EXPECT=%d" % expect]
        frames = 4000 + 1500 * expect
        return g, warp.run_scene("script_039", qa_rom, a.out / g, False, frames, False, False, timeout=1800,
                                 probes=[LUA / "msgview.lua", LUA / "pageview.lua"], pvars=pv)

    if not a.sheets:
        todo = [g for g in sorted(grp) if not (a.resume and "PAGES_DONE" in logtext(g))]
        with cf.ThreadPoolExecutor(a.jobs) as ex:
            for n, f in enumerate(cf.as_completed([ex.submit(one, g) for g in todo]), 1):
                g, (_, code, msg) = f.result()
                state = "ok " if "PAGES_DONE" in logtext(g) else "FAIL"
                print("[%d/%d] %s %s %s" % (n, len(todo), state, g, "" if state == "ok " else msg), flush=True)

    bad, missing, total = [], [], 0
    for g in sorted(grp):
        text = logtext(g)
        if "PAGES_DONE" not in text:
            bad.append(g)
        d = a.out / "_tiles" / g
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        owner = [(i, k) for i, c in spans[g] for k in range(1, c + 1)]  # page n of the chain -> (string, page)
        tiles, shown = [], set()
        for m in re.finditer(r"^PAGE (\d+) f\d+", text, re.M):
            n = int(m.group(1))
            if n > len(owner):
                continue
            sid, k = owner[n - 1]
            dst = d / ("%s_%d.png" % (sid, k))
            shutil.copy(a.out / g / "script_039" / ("p%04d.png" % n), dst)
            tiles.append(("%s p%d/%d" % (sid, k, dict(spans[g])[sid]), dst))
            shown.add(sid)
        total += len(tiles)
        missing += [i for i, _ in spans[g] if i not in shown]
        for old in a.out.glob("sheet_%s*.png" % g):
            old.unlink()
        if tiles:
            sheets(tiles, a.out / ("sheet_%s" % g))
    with open(a.out / "missing.tsv", "w", encoding="utf-8", newline="\n") as f:
        for i in missing:
            f.write("%s\n" % i)
    print("%d groups, %d pages, %d failed groups%s, %d strings with no page (missing.tsv)" % (
        len(grp), total, len(bad), (": " + " ".join(bad[:20])) if bad else "", len(missing)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
