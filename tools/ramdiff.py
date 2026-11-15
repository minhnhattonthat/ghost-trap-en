"""Find GBA RAM bytes that follow a pattern across L.dump_ram dumps (EWRAM 256 KB then IWRAM 32 KB).

    python tools/ramdiff.py PATTERN DUMP1 DUMP2 ... [--iwram] [--max 80]

PATTERN has one letter per dump; dumps with the same letter must hold the same byte, different letters a
different byte (e.g. AAAAB: a room id that changed only in the last dump; ABCD: a counter that differs in each).
Prints address:value per dump.
"""
import argparse


def addr(i):
    return 0x02000000 + i if i < 0x40000 else 0x03000000 + i - 0x40000


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pattern")
    p.add_argument("dumps", nargs="+")
    p.add_argument("--iwram", action="store_true", help="IWRAM only")
    p.add_argument("--max", type=int, default=80)
    a = p.parse_args()
    assert len(a.pattern) == len(a.dumps), "one pattern letter per dump"
    fs = [open(f, "rb").read() for f in a.dumps]
    n = min(len(f) for f in fs)
    start = 0x40000 if a.iwram else 0
    hits = []
    for i in range(start, n):
        vals = {}
        ok = True
        for letter, f in zip(a.pattern, fs):
            v = f[i]
            if letter in vals:
                if vals[letter] != v:
                    ok = False
                    break
            else:
                if v in vals.values():
                    ok = False
                    break
                vals[letter] = v
        if ok:
            hits.append(i)
    print(len(hits), "hits")
    for i in hits[: a.max]:
        print("%08X %s" % (addr(i), " ".join("%02X" % f[i] for f in fs)))


if __name__ == "__main__":
    main()
