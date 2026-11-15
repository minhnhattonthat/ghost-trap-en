"""English font additions for the 16x16 font (docs/re/text.md "Font", "English font").

    import font
    data = font.patched(rom)          # decompressed font (0xD800 bytes) with the English glyphs drawn in
    widths = font.widths(rom)         # {glyph code: advance px}, ROM width table plus the English advances
    font.width_px("Hello.", tbl)      # pixel width of one line of tbl-encodable text

The font already has proportional A-Z a-z 0-9 and Western punctuation (the staff-roll cells E0C0-E0C9). The
glyphs below are drawn into cells no string uses (six kanji, checked by tests/test_font.py), in the font's own
style: fill colour 1 with an 8-neighbour outline in colour F, cap height rows 3-11, baseline row 11.
"""
import functools
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gbacomp  # noqa: E402

FONT_LZ = 0x1271C8          # LZ77 block, 0x3628 bytes, then 32 zero bytes
FONT_PTRS = (0x1FB88, 0x267D0)  # the only two u32 literals 0x081271C8 in the ROM
WIDTHS = 0x3BBD0            # u16 per glyph 0x000-0x1AB; high byte = advance px
GLYPHS = 0x1AC
FILL, LINE = 0x1, 0xF

# char: (tbl code, advance, fill rows from row 3 down; '#' = fill, x from column 1)
NEW = {
    "-": ("E054", 4, ["", "", "", "", "##"]),
    "—": ("E077", 12, ["", "", "", "", "#########"]),
    ";": ("E085", 5, ["", "", "", "", " #", " #", "", "", " #", " #", " #", "#"]),
    "&": ("E090", 8, [" ##", "#  #", "#  #", " ##", "# # #", "#  #", "#  #", "#  ##", " ## #"]),
    "/": ("E0A8", 8, ["    #", "    #", "   #", "   #", "  #", "  #", " #", " #", "#"]),
    "%": ("E0AA", 8, ["##  #", "##  #", "   #", "   #", "  #", " #", " #", "#  ##", "#  ##"]),
}


# Glyphs 0x1A0-0x1AF lie at EWRAM 0x0201E000+, the script buffer: loading any script overwrites them (verified: RAM
# dump at frame 1400 differs from the font there, original ROM too). So the staff-roll punctuation is copied into
# small-kana cells, which English text never needs: {dest code: source glyph}. Not into the Japanese punctuation
# cells 01-0A: there 、 and 」 (01, 08) drew with no advance or not at all (torture shot work/qa/width/t, phase 5),
# so the renderer special-cases them.
COPY = {
    "3F": 0x1A4,  # ぁ -> ,
    "41": 0x1A5,  # ぃ -> .
    "43": 0x1A9,  # ぅ -> :
    "45": 0x1A2,  # ぇ -> "
    "47": 0x1A6,  # ぉ -> '
    "8F": 0x1A0,  # ァ -> (
    "91": 0x1A1,  # ィ -> )
}
SAFE_END = 0x1A0  # first glyph the script buffer overwrites


def glyph_index(code):
    """'E054' -> 0x134; '0B' -> 0x0B."""
    b = bytes.fromhex(code)
    return b[0] if len(b) == 1 else 0xE0 + b[1]


def _put(buf, g, x, y, v):
    i = g * 128 + ((y // 8) * 2 + x // 8) * 32 + (y % 8) * 4 + (x % 8) // 2
    buf[i] = (buf[i] & 0x0F) | (v << 4) if x & 1 else (buf[i] & 0xF0) | v


def draw(buf, g, rows):
    """Clear glyph g and draw `rows` (fill pattern) with its outline."""
    buf[g * 128:(g + 1) * 128] = bytes(128)
    fill = {(x + 1, y + 3) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "#"}
    for x, y in fill:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                p = (x + dx, y + dy)
                if p not in fill and 0 <= p[0] < 16 and 0 <= p[1] < 16:
                    _put(buf, g, *p, LINE)
    for x, y in fill:
        _put(buf, g, x, y, FILL)


def original(rom):
    data, _ = gbacomp.lz77_decompress(rom, FONT_LZ)
    return data


def patched(rom):
    buf = bytearray(original(rom))
    for code, src in COPY.items():
        g = glyph_index(code)
        buf[g * 128:(g + 1) * 128] = buf[src * 128:(src + 1) * 128]
    for _, (code, _, rows) in NEW.items():
        draw(buf, glyph_index(code), rows)
    buf[SPACE_CELL * 128:(SPACE_CELL + 1) * 128] = bytes(128)
    return bytes(buf)


# English word space: its own blank cell (ゥ 93), 4 px. Code 00 stays the 8 px space: the staff roll (already
# English, left in its original bytes) is laid out in fixed 8 px columns with it.
SPACE_CELL, SPACE = 0x93, 4
# ASCII glyph cells whose advance TIGHT recomputes: ? ! ~, the COPY cells, A-Z a-z, 0-9
TIGHT_CELLS = [0x04, 0x05, 0x06, *range(0x0B, 0x3F), *range(0xD0, 0xDA)]
# advance = ink width (outline included) rounded up to a multiple of 4. The renderer places a glyph by pen x & 7
# with a branch on < 4 / >= 4 (0x08027BD2), and every original advance is 4, 8, 12 or 16: odd advances dropped
# glyphs and 6 px ones drew the next glyph 6 px left in the torture shots (docs/re/text.md "English font").
TIGHT = True


def ink_right(data, g):
    """Last column with any pixel in glyph g, or -1 if blank."""
    best = -1
    for t in (0, 1, 2, 3):
        for y in range(8):
            for x in range(8):
                b = data[g * 128 + t * 32 + y * 4 + x // 2]
                if (b >> 4) if x & 1 else (b & 0xF):
                    best = max(best, x + 8 * (t & 1))
    return best


def width_table(rom, tight=None):
    """The width table bytes with the English advances (same size and place as the original)."""
    tight = TIGHT if tight is None else tight
    t = bytearray(rom[WIDTHS:WIDTHS + 2 * GLYPHS])
    for code, src in COPY.items():
        g = glyph_index(code)
        t[2 * g:2 * g + 2] = t[2 * src:2 * src + 2]
    for _, (code, adv, _) in NEW.items():
        struct.pack_into("<H", t, 2 * glyph_index(code), adv << 8)
    if tight:
        data = patched(rom)
        for g in TIGHT_CELLS + [glyph_index(c) for c in COPY] + [glyph_index(c) for c, _, _ in NEW.values()]:
            struct.pack_into("<H", t, 2 * g, ((ink_right(data, g) + 4) & ~3) << 8)  # multiples of 4 (TIGHT)
    struct.pack_into("<H", t, 2 * SPACE_CELL, SPACE << 8)
    return bytes(t)


@functools.lru_cache(maxsize=4)
def widths(rom, tight=None):
    t = width_table(rom, tight)
    return {g: t[2 * g + 1] for g in range(GLYPHS)}


def width_px(text, tbl, rom):
    """Advance sum of one line (no {br}); control codes count 0."""
    w, data, i = widths(rom), tbl.encode(text), 0
    total = 0
    while i < len(data):
        b = data[i]
        if b == 0xE0:
            total += w[0xE0 + data[i + 1]]
            i += 2
        elif b >= 0xE1:  # control code + its argument bytes
            i += 1 + tbl.ctrl.get(bytes([b]), ("", 0))[1]
        else:
            total += w[b]
            i += 1
    return total
