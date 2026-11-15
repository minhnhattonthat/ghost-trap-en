"""gfx_save.py: the SAVE GAME / LOAD GAME message boxes (graphics rows G2, G3 in docs/re/graphics.md).

    python -X utf8 tools/gfx_save.py render [--rom ROM] [--out work/gfx/save]   # each message as a PNG

Each message is a 32x32 BG1 tilemap (LZ77, 0x800 bytes) over one 4bpp tile block loaded at BG1 char base 0x4000:
save screen tiles G3 `0x7DD4EC` (pointer 0x212BC) with maps 0x7DDA90 0x7DDC2C 0x7DDD74 0x7DDED0; load screen tiles
G2 `0x7DC6A8` (pointer 0x22A34) with maps 0x7DCD88 0x7DCF28 0x7DD100 0x7DD248 0x7DD38C. The maps' pointers are listed
in SETS. Palette: BG palette row 6 (map entries 0x6xxx), taken from a dump of the save screen."""
import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gbacomp  # noqa: E402

ROM = ROOT / "rom" / "Ghost Trap (Japan).gba"
GBA = 0x08000000
# name: (tile block, its pointer, [(map block, [map pointers]), ...])
SETS = {
    "save": (0x7DD4EC, 0x212BC, [(0x7DDA90, [0x22008]), (0x7DDC2C, [0x22030]), (0x7DDD74, [0x22058]),
                                 (0x7DDED0, [0x22080])]),
    "load": (0x7DC6A8, 0x22A34, [(0x7DCD88, [0x230B0]), (0x7DCF28, [0x230D8]), (0x7DD100, [0x23100]),
                                 (0x7DD248, [0x23128]), (0x7DD38C, [0x23150])]),
}


def lz(rom, off):
    return gbacomp.lz77_decompress(rom, off)[0]


def palette(dump):
    p = Path(dump).read_bytes()
    out = []
    for i in range(16):
        c = struct.unpack_from("<H", p, (6 * 16 + i) * 2)[0]
        out.append(((c & 31) * 8, ((c >> 5) & 31) * 8, ((c >> 10) & 31) * 8))
    return out


def tile_px(tiles, n):
    """8x8 list of colour indices of 4bpp tile n."""
    b = tiles[n * 32:(n + 1) * 32]
    return [[(b[y * 4 + x // 2] >> 4) if x & 1 else (b[y * 4 + x // 2] & 15) for x in range(8)] for y in range(8)]


def compose(tiles, mapdata):
    """Index image (256x160 as rows of ints) of a map over tiles; flips honoured."""
    img = [[0] * 256 for _ in range(160)]
    m = struct.unpack("<1024H", mapdata)
    for r in range(20):
        for c in range(32):
            e = m[r * 32 + c]
            t = e & 0x3FF
            if not t:
                continue
            px = tile_px(tiles, t)
            for y in range(8):
                for x in range(8):
                    sx = 7 - x if e & 0x400 else x
                    sy = 7 - y if e & 0x800 else y
                    img[r * 8 + y][c * 8 + x] = px[sy][sx]
    return img


# English per map, one entry per text band of the original (2 tile rows, in order top to bottom); the band's
# first column is kept. Choices keep their place: the hand cursor (OBJ) points at the band.
TEXT = {
    0x7DDA90: ["Saving the data.", "Please wait."],
    0x7DDC2C: ["The data was saved."],
    0x7DDD74: ["The data could not", "be saved."],
    0x7DDED0: ["Overwrite this data.", "Is that all right?", "Yes", "No"],
    0x7DCD88: ["Load this data.", "Is that all right?", "Yes", "No"],
    0x7DCF28: ["Where do you want", "to start again?", "The floor you saved on", "The Entrance Hall"],
    0x7DD100: ["The data was loaded."],
    0x7DD248: ["There is no data."],
    0x7DD38C: ["The data could not", "be loaded."],
}
RIGHT = 28 * 8          # box interior ends at tile column 28 (frame map 0x7DC590)
MAX_TILES = 512         # BG1 chars 0x4000-0x7FFF; BG2 chars start at 0x8000 (VRAM dumps of both screens)
PAL_BITS = 0x6000


def bands(mapdata):
    """[(first col, top row)] of each 2-row text band of an original map."""
    m = struct.unpack("<1024H", mapdata)
    rows = [r for r in range(20) if any(m[r * 32 + c] & 0x3FF for c in range(32))]
    out, r = [], 0
    while r < len(rows):
        top = rows[r]
        cols = [c for c in range(32) for rr in (top, top + 1) if m[rr * 32 + c] & 0x3FF]
        out.append((min(cols), top))
        r += 2 if r + 1 < len(rows) and rows[r + 1] == top + 1 else 1
    return out


def typeset(rom, lines, starts):
    """Index canvas 256x160 with `lines` in the dialogue font (fill 1, outline F) at each band start."""
    import font
    from tbl import Table
    tbl = Table.load(ROOT / "tbl" / "en.tbl")
    data = font.patched(rom)
    canvas = [[0] * 256 for _ in range(160)]
    for text, (col, row) in zip(lines, starts):
        x = col * 8
        for ch in text:
            if ch == " ":
                x += 4
                continue
            code = tbl.encode(ch)
            g = code[0] if code[0] != 0xE0 else 0xE0 + code[1]
            right = font.ink_right(data, g)
            for y in range(16):
                for gx in range(right + 1):
                    t = (y // 8) * 2 + gx // 8
                    b = data[g * 128 + t * 32 + (y % 8) * 4 + (gx % 8) // 2]
                    v = (b >> 4) if gx & 1 else (b & 0xF)
                    if v and not (v == font.LINE and canvas[row * 8 + y][x + gx] == font.FILL):
                        canvas[row * 8 + y][x + gx] = v
            x += right  # outlines share a column
        if x > RIGHT:
            raise SystemExit("%r is %d px past the box" % (text, x - RIGHT))
    return canvas


def english(rom):
    """{tile block offset: new 4bpp tiles, map offset: new map} for every set; tile 0 stays blank."""
    out = {}
    for name, (tb, _, maps) in SETS.items():
        tiles, index = [bytes(32)], {bytes(32): 0}
        for mb, _ in maps:
            orig = lz(rom, mb)
            canvas = typeset(rom, TEXT[mb], bands(orig))
            m = []
            for r in range(32):
                for c in range(32):
                    if r >= 20:
                        m.append(0)
                        continue
                    px = [canvas[r * 8 + y][c * 8 + x] for y in range(8) for x in range(8)]
                    t = bytes(px[i] | px[i + 1] << 4 for i in range(0, 64, 2))
                    if t not in index:
                        index[t] = len(tiles)
                        tiles.append(t)
                    m.append(PAL_BITS | index[t] if index[t] else 0)
            out[mb] = struct.pack("<1024H", *m)
        if len(tiles) > MAX_TILES:
            raise SystemExit("%s: %d tiles, over %d" % (name, len(tiles), MAX_TILES))
        out[tb] = b"".join(tiles)
    return out


def writes(rom):
    """[(pointer offsets, raw data)] for build.py: each block is LZ-packed, appended and its pointers moved."""
    new = english(rom)
    out = []
    for tb, tp, maps in SETS.values():
        out.append(([tp], new[tb]))
        out += [(ptrs, new[mb]) for mb, ptrs in maps]
    return out


def render(a):
    from PIL import Image
    rom = Path(a.rom).read_bytes()
    pal = palette(a.pal)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    new = english(rom) if a.english else {}
    for name, (tb, _, maps) in SETS.items():
        tiles = new.get(tb) or lz(rom, tb)
        for i, (mb, _) in enumerate(maps):
            img = compose(tiles, new.get(mb) or lz(rom, mb))
            im = Image.new("RGB", (256, 160))
            im.putdata([pal[v] if v else (40, 40, 120) for row in img for v in row])
            p = out / ("%s_%d_%X.png" % (name, i, mb))
            im.resize((512, 320), Image.NEAREST).save(p)
            print(p)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("--rom", default=str(ROM))
    r.add_argument("--pal", default=str(ROOT / "work" / "gfx" / "dump" / "save_confirm" / "ppu_001640.pal.bin"))
    r.add_argument("--out", default=str(ROOT / "work" / "gfx" / "save"))
    r.add_argument("--english", action="store_true", help="the English messages instead of the original")
    a = ap.parse_args(argv)
    if a.cmd == "render":
        render(a)


if __name__ == "__main__":
    main()
