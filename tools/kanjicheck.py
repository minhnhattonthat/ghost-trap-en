"""Kanji check sheet: each font glyph beside the character tbl/jp.tbl gives it (drawn in MS Gothic), to confirm
readings by eye (docs/re/text.md, Encoding).

    python -X utf8 tools/kanjicheck.py OUT.png [--from E00A] [--to E0BF] [--cols 8] [--zoom 4]

Cell: code label, the game glyph (white on dark, zoomed), the table's character (black on white, same size), and
how many script/ strings use the code."""
import argparse
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fontsheet  # noqa: E402
import gbacomp  # noqa: E402
import script  # noqa: E402
from tbl import Table  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"
SYSFONT = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "msgothic.ttc"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--from", dest="lo", default="E00A")
    ap.add_argument("--to", dest="hi", default="E0BF")
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--zoom", type=int, default=4)
    a = ap.parse_args(argv)
    tbl = Table.load(ROOT / "tbl" / "jp.tbl")
    data, _ = gbacomp.lz77_decompress(ROM.read_bytes(), fontsheet.FONT_LZ)
    lo, hi = int(a.lo, 16), int(a.hi, 16)
    codes = [c for c in range(lo, hi + 1)]
    jp = [e["jp"] for e in script.load()] if script.files() else []
    z = a.zoom
    gs = 16 * z
    cw, ch = gs * 2 + 24, gs + 22
    rows = -(-len(codes) // a.cols)
    sheet = Image.new("RGB", (cw * a.cols, ch * rows), (200, 200, 200))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(SYSFONT), gs - 4)
    small = ImageFont.truetype(str(SYSFONT), 14)
    for i, c in enumerate(codes):
        x, y = (i % a.cols) * cw, (i // a.cols) * ch
        key = c.to_bytes(2 if c > 0xFF else 1, "big")
        ch_ = tbl.dec.get(key, "?")
        g = (c & 0xFF) + 0xE0 if c > 0xFF else c
        im = fontsheet.glyph_image(data, g).resize((gs, gs), Image.NEAREST)
        sheet.paste(Image.merge("RGB", (im, im, im)), (x + 4, y + 18))
        d.rectangle((x + gs + 10, y + 18, x + 2 * gs + 10, y + 18 + gs), fill=(255, 255, 255))
        d.text((x + gs + 12, y + 20), ch_, font=font, fill=(0, 0, 0))
        n = sum(ch_ in s for s in jp)
        d.text((x + 4, y + 2), f"{c:X} n={n}", font=small, fill=(0, 0, 160))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out)
    print(a.out, len(codes), "codes")


if __name__ == "__main__":
    main()
