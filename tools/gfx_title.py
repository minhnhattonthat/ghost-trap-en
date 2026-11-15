"""gfx_title.py: the title logo without its katakana line (graphics row G1 in docs/re/graphics.md).

    python -X utf8 tools/gfx_title.py render [--rom ROM] [--pal PAL] [--out work/gfx/g1]   # before/after PNGs

The logo is BG1, 8bpp: 174 unique tiles (LZ77 `0x7D8C68`, pointer 0x20628) under a 32x32 map (LZ77 `0x7D8A10`,
pointer 0x20630; logo window = tile columns 2-28, rows 5-12, no flips). The katakana ゴーストトラップ is painted
over the lower half of the GHOST TRAP letters, so dropping it means rebuilding those letter bottoms (ruling D5: the
English logo is official, the katakana line goes).

How: a fill mask of the letters (blue fill + the white rim beside it) is read from the untouched top half; the hidden
bottoms are added as keyed spans per letter (LETTERS: stems, feet, bowls, the O mirrored from its top); then every
pixel in the repaint zone (near the katakana or near a changed mask pixel, and only where `free()` allows: rows >=
CUT plus the box around the プ handakuten) is repainted from a colour model measured on the untouched pixels: the
most common palette index for (inside depth | rim side | glow distance and side). Deterministic and stdlib-only, so
build.py runs it on every build. tests/test_gfx_title.py checks that nothing outside `free()` changes."""
import argparse
import math
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gbacomp  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"
TILES, TILES_PTR = 0x7D8C68, 0x20628
MAP = 0x7D8A10
T0X, T0Y, TW, TH = 2, 5, 27, 8      # logo window on the BG1 map, in tiles
W, H = TW * 8, TH * 8
CUT = 31                            # rows above this are never touched...
HANDAKUTEN = (24, 180, 197)         # ...except rows >= 24, x 180..196: the プ circle reaches up there
AX = 65                             # vertical mirror axis of the letters: top rim row 13 <-> bottom rim row 52
R_OUT = 6                           # glow radius
# Colour class of palette indices 0-111 (the logo uses no other), from the title's BG palette (RGB555):
# ' ' backdrop, '.' near black, b/B blue fill (B = light), r/o red / orange glow, W white, g grey (katakana).
CLASSES = (" bbbbbbbbbbbbbbb...bb.b.bbbrb.rrbrrbgrbrrbrrgbrbgrrrrgrbrgrrrbrgbgrrrBBgrroBbogoBgBoogBoggBoBogoBogooBo"
           "BWoBWooWW")


def free(y, x):
    """May the redraw repaint this logo pixel?"""
    return y >= CUT or (y >= HANDAKUTEN[0] and HANDAKUTEN[1] <= x < HANDAKUTEN[2])


def load(rom):
    """(tile block bytes, map entries, logo index image as rows of ints)."""
    tiles = gbacomp.lz77_decompress(rom, TILES)[0]
    m = struct.unpack("<1024H", gbacomp.lz77_decompress(rom, MAP)[0])
    img = [[0] * W for _ in range(H)]
    for ty in range(TH):
        for tx in range(TW):
            e = m[(T0Y + ty) * 32 + T0X + tx]
            assert not e & 0xC00, "flipped tile in the logo window"
            t = e & 0x3FF
            for y in range(8):
                img[ty * 8 + y][tx * 8:tx * 8 + 8] = tiles[t * 64 + y * 8:t * 64 + y * 8 + 8]
    return tiles, m, img


def store(tiles, m, img):
    """The tile block with the logo window's tiles replaced by img."""
    out = bytearray(tiles)
    for ty in range(TH):
        for tx in range(TW):
            t = m[(T0Y + ty) * 32 + T0X + tx] & 0x3FF
            if t == 0:          # the shared blank tile: the window must stay blank there
                assert all(img[ty * 8 + y][tx * 8 + x] == 0 for y in range(8) for x in range(8)), (tx, ty)
                continue
            for y in range(8):
                out[t * 64 + y * 8:t * 64 + y * 8 + 8] = bytes(img[ty * 8 + y][tx * 8:tx * 8 + 8])
    return bytes(out)


def near(m, y, x, test):
    return any(0 <= y + dy < H and 0 <= x + dx < W and test(m[y + dy][x + dx])
               for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)))


def fill_mask(c):
    """Blue fill plus the white rim pixels touching it."""
    return [[c[y][x] in "bB" or (c[y][x] == "W" and near(c, y, x, lambda v: v in "bB")) for x in range(W)]
            for y in range(H)]


def katakana(c):
    """Katakana pixels in the free area: grey ramp, or white inside a solid 2x2 block (letter rims are 1 px)."""
    k = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if not free(y, x):
                continue
            if c[y][x] == "g":
                k[y][x] = True
            elif c[y][x] == "W":
                k[y][x] = any(all(0 <= y + dy + a < H and 0 <= x + dx + b < W and c[y + dy + a][x + dx + b] == "W"
                                  for a in (0, 1) for b in (0, 1)) for dy in (0, -1) for dx in (0, -1))
    return k


def dilate(m, r):
    out = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if m[y][x]:
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        if dy * dy + dx * dx <= r * r + r and 0 <= y + dy < H and 0 <= x + dx < W:
                            out[y + dy][x + dx] = True
    return out


def spans(g, keys):
    """Fill rows between (y, x0, x1) keys, interpolating the ends."""
    for (ya, a0, a1), (yb, b0, b1) in zip(keys, keys[1:]):
        for y in range(ya, yb + 1):
            t = 0 if yb == ya else (y - ya) / (yb - ya)
            for x in range(round(a0 + (b0 - a0) * t), round(a1 + (b1 - a1) * t) + 1):
                g[y][x] = True


def mirror(g, top, xa, xb, y0, y1):
    """Rows y0..y1, columns xa..xb, from the top half mirrored about AX."""
    for y in range(y0, y1 + 1):
        if AX - y < CUT:
            for x in range(xa, xb + 1):
                g[y][x] = g[y][x] or top[AX - y][x]


def letters(top):
    """Mask of the letter parts under the katakana (logo pixel coordinates, read off the original's mask)."""
    g = [[False] * W for _ in range(H)]
    # G: left stroke, bottom arc, inner spur column
    spans(g, [(31, 3, 9), (40, 4, 10), (43, 5, 12), (46, 7, 14), (47, 7, 15)])
    spans(g, [(47, 7, 15), (48, 8, 25), (49, 9, 25), (50, 10, 24), (51, 11, 23), (52, 13, 20)])
    spans(g, [(31, 19, 24), (44, 19, 25), (48, 19, 25)])
    # H: stems and feet
    spans(g, [(31, 30, 35), (47, 30, 35), (48, 29, 35), (49, 28, 36), (50, 27, 36), (51, 27, 37), (52, 28, 37)])
    spans(g, [(31, 43, 48), (41, 44, 49), (47, 44, 49), (48, 44, 50), (49, 43, 51), (50, 42, 51), (52, 43, 51)])
    # O: its top half mirrored, sides joined
    mirror(g, top, 52, 79, 34, 52)
    spans(g, [(31, 53, 59), (42, 54, 59)])
    spans(g, [(31, 72, 78), (42, 70, 77)])
    # S: the spine runs on into the lower right side; bottom arc and terminal = the top ones turned round
    spans(g, [(31, 82, 96), (32, 83, 97), (33, 84, 97), (34, 87, 98), (35, 90, 98), (36, 92, 98), (44, 93, 99),
              (46, 92, 98)])
    spans(g, [(40, 82, 86), (45, 82, 87), (46, 82, 88)])
    spans(g, [(47, 82, 98), (48, 82, 97), (49, 82, 96), (50, 83, 96), (51, 86, 94), (52, 89, 91)])
    # first T: only its right edge touches the ト; restate the stem and foot so the edge pixels come back
    spans(g, [(31, 105, 110), (43, 105, 110), (44, 106, 110), (48, 106, 110), (49, 105, 111), (50, 104, 111),
              (52, 104, 111)])
    # second T: stem and foot (the foot reaches further left, as at the visible rows 49-51)
    spans(g, [(31, 131, 137), (48, 131, 137), (49, 130, 137), (50, 129, 138), (52, 128, 138)])
    # R: stem and foot, leg flaring out to x 163 at row 46 and back to 157-161 at the foot
    spans(g, [(31, 147, 152), (48, 147, 152), (49, 146, 153), (52, 146, 153)])
    spans(g, [(33, 152, 158), (35, 154, 158), (40, 156, 161), (45, 158, 163), (47, 158, 162), (49, 157, 161),
              (51, 157, 161), (52, 156, 162)])
    # A: crossbar, legs, feet
    # (the counter between the legs stays open down to row 31: the crossbar starts at row 32)
    spans(g, [(31, 169, 173), (32, 169, 181), (35, 169, 181)])
    spans(g, [(31, 175, 181), (35, 176, 182)])
    spans(g, [(35, 169, 173), (48, 169, 173), (49, 168, 174), (52, 168, 174)])
    spans(g, [(35, 176, 182), (40, 178, 182), (48, 178, 182), (49, 177, 183), (52, 177, 183)])
    # P: left stroke under the handakuten, bowl bottom into the lower stem, foot
    # (the lower stem shows at x 191-194 between the katakana and its glow; the foot at 188-196)
    spans(g, [(24, 186, 191), (28, 187, 192), (32, 188, 193), (36, 189, 194), (48, 189, 194), (49, 188, 195),
              (52, 188, 196)])
    return g


def distance(m, r):
    """Euclidean distance to the nearest True pixel, capped at r + 1."""
    pts = [(dy, dx, math.hypot(dy, dx)) for dy in range(-r, r + 1) for dx in range(-r, r + 1)]
    pts.sort(key=lambda p: p[2])
    d = [[r + 1.0] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            for dy, dx, v in pts:
                if 0 <= y + dy < H and 0 <= x + dx < W and m[y + dy][x + dx]:
                    d[y][x] = v
                    break
    return d


def feature(m, din, dout, y, x):
    """What a pixel is, for the colour model: inside depth, rim side, or glow distance (and side, near the rim)."""
    def out(yy, xx):
        return not (0 <= yy < H and 0 <= xx < W) or not m[yy][xx]
    if m[y][x]:
        if din[y][x] > 1.5:
            return ("in", min(round(din[y][x]), 4))
        gx = out(y, x + 1) - out(y, x - 1)
        gy = out(y + 1, x) - out(y - 1, x)
        return ("rim", "R" if gx > 0 else "L" if gx < 0 else "B" if gy > 0 else "T" if gy < 0 else "N")
    d = round(dout[y][x] * 2) / 2
    if d > 2.5:
        return ("out", d)
    best, side = 99, "N"
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if 0 <= y + dy < H and 0 <= x + dx < W and m[y + dy][x + dx] and dy * dy + dx * dx < best:
                best = dy * dy + dx * dx
                side = ("L" if dx > 0 else "R") if abs(dx) >= abs(dy) else ("T" if dy > 0 else "B")
    return ("out", d, side)


def blank_cells(m):
    """Logo-window cells the map leaves on tile 0 (shared blank): nothing drawn there can show."""
    return {(tx, ty) for ty in range(TH) for tx in range(TW) if m[(T0Y + ty) * 32 + T0X + tx] & 0x3FF == 0}


def redraw(img, blank=()):
    """The logo index image without the katakana line; pixels in `blank` cells are left 0."""
    assert all(v < len(CLASSES) for row in img for v in row)
    c = [[CLASSES[v] for v in row] for row in img]
    auto = fill_mask(c)
    kd = dilate(katakana(c), 1)
    top = [[auto[y][x] and y < CUT for x in range(W)] for y in range(H)]
    gen = letters(top)
    final = [[(gen[y][x] or (auto[y][x] and not kd[y][x])) if free(y, x) else auto[y][x] for x in range(W)]
             for y in range(H)]
    din = distance([[not v for v in row] for row in final], 6)
    dout = distance(final, R_OUT + 1)
    far = dilate(kd, 3)
    stats = defaultdict(Counter)
    for y in range(H):
        for x in range(W):
            # untouched pixels away from the katakana; the letter feet (rows > 50) are visible in places
            if not far[y][x] and (not free(y, x) or (y > 50 and final[y][x] == auto[y][x])):
                f = feature(final, din, dout, y, x)
                stats[f][img[y][x]] += 1
                if len(f) == 3:
                    stats[f[:2]][img[y][x]] += 1
    # most common index per feature; ties go to the lower index so the result never depends on dict order
    model = {k: min(v.items(), key=lambda kv: (-kv[1], kv[0]))[0] for k, v in stats.items()}
    changed = [[free(y, x) and final[y][x] != auto[y][x] for x in range(W)] for y in range(H)]
    zone = dilate([[kd[y][x] or changed[y][x] for x in range(W)] for y in range(H)], R_OUT + 1)
    out = [list(row) for row in img]
    for y in range(H):
        for x in range(W):
            if zone[y][x] and free(y, x):
                f = feature(final, din, dout, y, x)
                out[y][x] = 0 if f[0] == "out" and f[1] > R_OUT + 0.5 else model.get(f, model.get(f[:2], 0))
            if (x // 8, y // 8) in blank:
                out[y][x] = 0
    return out


def writes(rom):
    """[(pointer offsets, raw data)] for build.py: the new tile block (the map is unchanged)."""
    tiles, m, img = load(rom)
    return [([TILES_PTR], store(tiles, m, redraw(img, blank_cells(m))))]


def render(a):
    from PIL import Image
    p = Path(a.pal).read_bytes()
    pal = [((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31)
           for c in struct.unpack_from("<256H", p)]
    _, m, img = load(Path(a.rom).read_bytes())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, im in (("logo_jp", img), ("logo_en", redraw(img, blank_cells(m)))):
        pic = Image.new("RGB", (W, H))
        pic.putdata([pal[v] if v else (0, 0, 0) for row in im for v in row])
        pic.save(out / f"{name}.png")
        print(out / f"{name}.png")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--rom", default=str(ROM))
    r.add_argument("--pal", default=str(ROOT / "work" / "gfx" / "g1" / "dump" / "ppu_002209.pal.bin"),
                   help="BG palette dump of the title (emu.py + ppudump.lua at frame 2209 of 1500 -;6 start;700 -)")
    r.add_argument("--out", default=str(ROOT / "work" / "gfx" / "g1"))
    a = ap.parse_args(argv)
    if a.cmd == "render":
        render(a)


if __name__ == "__main__":
    main()
