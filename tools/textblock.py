"""Unpack and repack the script block (docs/re/text.md): strings back to back at 0x100000-0x1271C8, reached only
from the pointer region 0x3BF28-0x423A0 plus the lone slot at 0x423A0.

    from textblock import unpack, pack
    segs = unpack(rom, tbl)            # [("raw", off, bytes) | ("str", off, text)] covering the whole block in order
    block, moved = pack(segs, tbl)     # bytes for the block, {old string offset: new offset}

Raw segments (the AGBD header, unreferenced runs, padding) are kept byte for byte, so unpack -> pack with no edits
gives the original block: the identity build (tests/test_identity.py)."""
import struct

PTR_LO, PTR_HI = 0x3BF28, 0x423A0
EXTRA_SLOTS = (0x423A0,)  # one text pointer after the region, before the Thumb code pointers
TEXT_LO, TEXT_HI = 0x100000, 0x1271C8
GBA = 0x08000000
HEADER = 0x100000  # "AGBD", 4 bytes
# Unreferenced runs (dead, kept byte for byte; docs/re/text.md "Dead runs"): no pointer anywhere in the ROM reaches
# them, six are older copies of referenced strings, and the staff-roll copy at 0x11E67A is never read when the
# credits play (tools/lua/textreads.lua).
DEAD = (0x1064CE, 0x10EE11, 0x1166DA, 0x116786, 0x11AAB0, 0x11E67A, 0x120B12, 0x12230C)


def slots(rom):
    """Yield (slot offset, target offset) for every text pointer slot."""
    for off in (*range(PTR_LO, PTR_HI, 4), *EXTRA_SLOTS):
        v = struct.unpack_from("<I", rom, off)[0]
        if GBA + TEXT_LO <= v < GBA + TEXT_HI:
            yield off, v - GBA


def unpack(rom, tbl):
    """Strings start 4-aligned; the 0-3 zero bytes after each one are alignment padding, left implicit (pack
    re-aligns). Anything else between strings (the header, the dead runs in DEAD) is a raw segment."""
    targets = sorted({t for _, t in slots(rom)})
    segs, cur = [], TEXT_LO
    for t in targets:
        if t < cur:
            raise ValueError(f"string {t:#x} starts inside the previous one (ends {cur:#x})")
        gap = bytes(rom[cur:t])
        if gap and not (cur % 4 and t - cur < 4 and not any(gap)):
            segs.append(("raw", cur, gap))
        text, used = tbl.decode(rom, t, maxlen=0x8000)
        segs.append(("str", t, text))
        cur = t + used
    if cur > TEXT_HI:
        raise ValueError(f"last string runs past the block end ({cur:#x})")
    if cur < TEXT_HI:
        segs.append(("raw", cur, bytes(rom[cur:TEXT_HI])))
    return segs


def pack(segs, tbl, texts=None, enc=None):
    """texts: optional {string offset: replacement text}, encoded with `enc` (default tbl); the rest re-encode with
    tbl. Every string starts 4-aligned (zero padding before it, as in the original).
    Returns (block bytes, {old offset: new offset})."""
    out, moved, texts = bytearray(), {}, texts or {}
    for kind, off, val in segs:
        if kind == "raw":
            out += val
        else:
            out += bytes(-(TEXT_LO + len(out)) % 4)
            moved[off] = TEXT_LO + len(out)
            out += (enc or tbl).encode(texts[off]) if off in texts else tbl.encode(val)
    return bytes(out), moved
