"""Render the Ghost Trap 16x16 4bpp font (LZ77 at ROM 0x1271C8) as labelled sheets.

python -X utf8 tools/fontsheet.py ROM OUTDIR [--per 128] [--zoom 3]
Each glyph = 128 bytes = four 8x8 GBA 4bpp tiles in order TL, TR, BL, BR (verified by eye on the sheet).
Labels are the text code: 00-DF single byte, E0 xx for glyph 0xE0+xx.
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gbacomp  # noqa: E402

FONT_LZ = 0x1271C8
GLYPH = 128


def glyph_image(data, g):
    im = Image.new("L", (16, 16), 0)
    px = im.load()
    base = g * GLYPH
    for t, (tx, ty) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
        for y in range(8):
            for x in range(8):
                b = data[base + t * 32 + y * 4 + x // 2]
                v = (b >> 4) if x & 1 else (b & 0xF)
                px[tx + x, ty + y] = min(255, v * 17)
    return im


def label(g):
    return f"{g:02X}" if g < 0xE0 else f"E0{g - 0xE0:02X}"


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    rom = open(argv[0], "rb").read()
    out = argv[1]
    per = int(argv[argv.index("--per") + 1]) if "--per" in argv else 128
    zoom = int(argv[argv.index("--zoom") + 1]) if "--zoom" in argv else 3
    data, _ = gbacomp.lz77_decompress(rom, FONT_LZ)
    n = len(data) // GLYPH
    os.makedirs(out, exist_ok=True)
    cols = 16
    cw, ch = 16 * zoom + 8, 16 * zoom + 16
    for start in range(0, n, per):
        cnt = min(per, n - start)
        rows = (cnt + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cw, rows * ch), (40, 40, 60))
        dr = ImageDraw.Draw(sheet)
        for i in range(cnt):
            g = start + i
            x, y = (i % cols) * cw, (i // cols) * ch
            im = glyph_image(data, g).resize((16 * zoom, 16 * zoom), Image.NEAREST).convert("RGB")
            sheet.paste(im, (x + 4, y + 14))
            dr.text((x + 4, y + 1), label(g), fill=(255, 220, 0))
        path = os.path.join(out, f"font_{start:03X}.png")
        sheet.save(path)
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
