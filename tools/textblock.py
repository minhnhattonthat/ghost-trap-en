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


def slots(rom):
    """Yield (slot offset, target offset) for every text pointer slot."""
    for off in (*range(PTR_LO, PTR_HI, 4), *EXTRA_SLOTS):
        v = struct.unpack_from("<I", rom, off)[0]
        if GBA + TEXT_LO <= v < GBA + TEXT_HI:
            yield off, v - GBA


def unpack(rom, tbl):
    targets = sorted({t for _, t in slots(rom)})
    segs, cur = [], TEXT_LO
    for t in targets:
        if t < cur:
            raise ValueError(f"string {t:#x} starts inside the previous one (ends {cur:#x})")
        if t > cur:
            segs.append(("raw", cur, bytes(rom[cur:t])))
        text, used = tbl.decode(rom, t, maxlen=0x8000)
        segs.append(("str", t, text))
        cur = t + used
    if cur > TEXT_HI:
        raise ValueError(f"last string runs past the block end ({cur:#x})")
    if cur < TEXT_HI:
        segs.append(("raw", cur, bytes(rom[cur:TEXT_HI])))
    return segs


def pack(segs, tbl, texts=None):
    """texts: optional {string offset: replacement text}. Returns (block bytes, {old offset: new offset})."""
    out, moved = bytearray(), {}
    for kind, off, val in segs:
        if kind == "raw":
            out += val
        else:
            moved[off] = TEXT_LO + len(out)
            out += tbl.encode((texts or {}).get(off, val))
    return bytes(out), moved
