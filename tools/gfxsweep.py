"""Static graphics-text sweep: render every BIOS LZ77 block as 4bpp tiles into labelled pages.

python -X utf8 tools/gfxsweep.py ROM OUTDIR [--tiles 512] [--cols 32] [--page-h 1100] [--fmt gba4|gba8] [--zoom 2]
Every block gets a label row (ROM offset, unpacked size, tiles shown). Blocks whose size is not a multiple of 32
(not tile data) are listed as skipped with the reason, never dropped silently. index.tsv maps page -> blocks.
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gbacomp  # noqa: E402


def tile4(data, off):
    im = Image.new("L", (8, 8))
    px = im.load()
    for y in range(8):
        for x in range(8):
            b = data[off + y * 4 + x // 2]
            px[x, y] = ((b >> 4) if x & 1 else (b & 0xF)) * 17
    return im


def tile8(data, off):
    im = Image.frombytes("L", (8, 8), bytes(data[off:off + 64]))
    return im


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    opt = lambda k, dflt: type(dflt)(argv[argv.index(k) + 1]) if k in argv else dflt  # noqa: E731
    rom = open(argv[0], "rb").read()
    out = argv[1]
    max_tiles, cols, page_h, fmt = opt("--tiles", 512), opt("--cols", 32), opt("--page-h", 1100), opt("--fmt", "gba4")
    tsz = 32 if fmt == "gba4" else 64
    os.makedirs(out, exist_ok=True)
    blocks, skipped = [], []
    for off, end, data in gbacomp.scan(rom, 64):
        if len(data) % tsz:
            skipped.append((off, len(data), f"size not a multiple of {tsz}"))
            continue
        blocks.append((off, data))
    pages, cur, h = [], [], 0
    for off, data in blocks:
        n = min(len(data) // tsz, max_tiles)
        bh = 12 + ((n + cols - 1) // cols) * 8
        if cur and h + bh > page_h:
            pages.append(cur)
            cur, h = [], 0
        cur.append((off, data, n, bh))
        h += bh
    if cur:
        pages.append(cur)
    idx = open(os.path.join(out, "index.tsv"), "w", encoding="utf-8")
    for p, page in enumerate(pages):
        H = sum(b[3] for b in page)
        im = Image.new("RGB", (cols * 8, H), (60, 0, 60))
        dr = ImageDraw.Draw(im)
        y = 0
        for off, data, n, bh in page:
            dr.text((1, y), f"{off:06X} {len(data):X}" + (f" (first {n})" if n < len(data) // tsz else ""),
                    fill=(255, 220, 0))
            for i in range(n):
                t = tile4(data, i * 32) if fmt == "gba4" else tile8(data, i * 64)
                im.paste(t.convert("RGB"), ((i % cols) * 8, y + 12 + (i // cols) * 8))
            idx.write(f"p{p:02d}\t{off:06X}\t{len(data):X}\t{n}\n")
            y += bh
        z = opt("--zoom", 1)
        if z > 1:
            im = im.resize((im.width * z, im.height * z), Image.NEAREST)
        im.save(os.path.join(out, f"p{p:02d}.png"))
    for off, size, why in skipped:
        print(f"skipped {off:06X} {size:X}: {why}")
        idx.write(f"skipped\t{off:06X}\t{size:X}\t{why}\n")
    print(f"{len(blocks)} blocks on {len(pages)} pages, {len(skipped)} skipped -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
