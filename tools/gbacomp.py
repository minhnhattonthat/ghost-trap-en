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


def lz77_compress(data):
    """BIOS LZ77 (type 0x10), VRAM-safe (no displacement of 1, so LZ77UnCompVram's 16-bit writes work), padded to 4.

    Greedy longest match over a hash chain. Not byte-identical to the original packer: the build keeps a block's
    original bytes while its unpacked content is unchanged, and packs only edited blocks."""
    n = len(data)
    out = bytearray(b"\x10" + n.to_bytes(3, "little"))
    chains = {}
    i = 0
    while i < n:
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_len, best_disp = 0, 0
            if i + 3 <= n:
                cands = chains.get(data[i:i + 3], ())
                for j in reversed(cands[-256:]):
                    disp = i - j
                    if disp > 0x1000:
                        break
                    if disp < 2:
                        continue
                    k = 3
                    while k < 18 and i + k < n and data[j + k] == data[i + k]:
                        k += 1
                    if k > best_len:
                        best_len, best_disp = k, disp
                        if k == 18:
                            break
            step = best_len if best_len >= 3 else 1
            if best_len >= 3:
                flags |= 0x80 >> bit
                d = best_disp - 1
                out += bytes(((best_len - 3) << 4 | d >> 8, d & 0xFF))
            else:
                out.append(data[i])
            for p in range(i, i + step):
                if p + 3 <= n:
                    chains.setdefault(data[p:p + 3], []).append(p)
            i += step
        out[flag_pos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


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
