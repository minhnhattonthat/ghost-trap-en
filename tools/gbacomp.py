"""GBA BIOS LZ77 (type 0x10) decompression and a scanner for compressed blocks.

python -X utf8 tools/gbacomp.py scan ROM [--min 64]   -> offset, packed size, unpacked size per block
"""
import sys


def lz77_decompress(data, off=0):
    """Return (bytes, end_offset). Raises ValueError on malformed input."""
    if data[off] != 0x10:
        raise ValueError("not LZ77")
    size = int.from_bytes(data[off + 1:off + 4], "little")
    if size == 0:
        raise ValueError("zero size")
    out = bytearray()
    p = off + 4
    n = len(data)
    while len(out) < size:
        if p >= n:
            raise ValueError("ran off end")
        flags = data[p]
        p += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                if p + 1 >= n:
                    raise ValueError("ran off end")
                b1, b2 = data[p], data[p + 1]
                p += 2
                length = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                if disp > len(out):
                    raise ValueError("bad back-reference")
                for _ in range(length):
                    out.append(out[-disp])
            else:
                if p >= n:
                    raise ValueError("ran off end")
                out.append(data[p])
                p += 1
    return bytes(out[:size]), p


def scan(rom, min_size=64, max_size=0x40000):
    """Yield (offset, end, unpacked) for plausible LZ77 blocks at 4-byte alignment."""
    for off in range(0, len(rom) - 4, 4):
        if rom[off] != 0x10:
            continue
        size = int.from_bytes(rom[off + 1:off + 4], "little")
        if size < min_size or size > max_size:
            continue
        try:
            out, end = lz77_decompress(rom, off)
        except ValueError:
            continue
        yield off, end, out


def main(argv):
    if len(argv) < 2 or argv[0] != "scan":
        print(__doc__)
        return 2
    rom = open(argv[1], "rb").read()
    mn = int(argv[argv.index("--min") + 1]) if "--min" in argv else 64
    for off, end, out in scan(rom, mn):
        print(f"{off:07x} {end - off:6x} {len(out):6x}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
