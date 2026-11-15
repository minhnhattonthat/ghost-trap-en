"""release.py: build, gate and package a release (references/pipeline.md §Release). Stops at the first failure.

    python -X utf8 tools/release.py [--version 1.0] [--force]

Steps: build (tools/build.py, no --marker/--qa/--loose) -> tests (tools/check.py) -> smoke boot (emu.py --smoke) ->
jp_left_build.py -> qa_gate.py check on every work/qa/**/manifest.tsv (verdicts dir beside it: visual tour and story
pass) -> coverage.py over tools/coverage_runs.tsv (textcover per run layout; waivers docs/text_unshown.tsv) -> no
unticked line in docs/polish.md -> no template placeholder in README.md -> debug tool off (below) -> BPS patch ->
re-apply to the clean original and compare -> zip (patch + README.txt only).

Debug tool off: the debug tool (tools/debug/warp.py) is Lua run by the emulator and never patched into the ROM; the
release ROM is the plain build, and this script checks it is byte-identical to a second plain build and contains no
QA-only marker text.

Out: release/v<version>/Ghost_Trap_EN_v<version>.bps, README.txt, Ghost_Trap_EN_v<version>.zip. The playable image
stays in build/ghost_trap_en.gba. Refuses to overwrite an existing version's files without --force.
"""
import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402
from tbl import Table  # noqa: E402

PY = [sys.executable, "-X", "utf8"]
ORIG = ROOT / "rom" / "Ghost Trap (Japan).gba"
BUILT = ROOT / "build" / "ghost_trap_en.gba"


def step(name, args, **kw):
    print(f"== {name}: {' '.join(str(a) for a in args)}", flush=True)
    r = subprocess.run([str(a) for a in args], cwd=ROOT, **kw)
    if r.returncode:
        sys.exit(f"RELEASE STOPPED at {name}: exit {r.returncode}")
    return r


def hashes(data):
    return {"crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08X}", "md5": hashlib.md5(data).hexdigest(),
            "sha1": hashlib.sha1(data).hexdigest(), "size": len(data)}


README = """Ghost Trap - English translation patch v{version}
===================================================

Unofficial English fan translation of Ghost Trap (Game Boy Advance, Artoon / Eidos Interactive KK, 2002).
Project page and source: https://github.com/minhnhattonthat/ghost-trap-en

What is translated
------------------
- Dialogue, story cutscenes, field messages: translated
- Menus, items, item help, system messages: translated
- Title screen, SAVE/LOAD message boxes: translated (redrawn graphics)
- Staff roll and copyright screen: already English in the original, unchanged
- Name entry: none in this game

How to patch
------------
1. Get your own dump of the Japanese cartridge. It must match:
     No-Intro name: Ghost Trap (Japan).gba
     Size:   {o[size]} bytes
     CRC32:  {o[crc32]}
     MD5:    {o[md5]}
     SHA-1:  {o[sha1]}
2. Apply {patch} with a BPS patcher: Flips, beat, or https://www.marcrobledo.com/RomPatcher.js/
3. The patched ROM should have:
     CRC32:  {p[crc32]}
     SHA-1:  {p[sha1]}

Playing
-------
Tested in MesenCE 2.2.1. Start from a cold boot: savestates made with the Japanese ROM carry its text and code.
In-game saves (EEPROM) work across the patch.

Known issues: none known. Report bugs at https://github.com/minhnhattonthat/ghost-trap-en/issues

Credits
-------
Translation, hacking and QA: minhnhattonthat, with extensive AI assistance (Claude by Anthropic).
Ghost Trap is (c) 2002 Artoon, published by Eidos Interactive KK. This is an unofficial fan work, not affiliated
with them. Do not share or ask for pre-patched ROMs.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--force", action="store_true", help="overwrite an existing release/v<version>/")
    a = ap.parse_args()
    out = ROOT / "release" / f"v{a.version}"
    stem = f"Ghost_Trap_EN_v{a.version}"
    patch, zpath, readme = out / f"{stem}.bps", out / f"{stem}.zip", out / "README.txt"
    if any(p.exists() for p in (patch, zpath, readme)) and not a.force:
        sys.exit(f"{out} already holds release files; pass --force to overwrite")

    step("build", PY + ["tools/build.py"])
    rom = BUILT.read_bytes()
    step("tests", PY + ["tools/check.py"])
    step("smoke", PY + [Path(SKILL) / "scripts" / "emu.py", BUILT, "--out", "work/qa/release_smoke", "--route",
                        "tools/routes/boot.txt", "--smoke"])
    step("jp_left", PY + ["tools/jp_left_build.py", BUILT])
    manifests = sorted((ROOT / "work" / "qa").rglob("manifest.tsv"))
    if not manifests:
        sys.exit("RELEASE STOPPED: no work/qa/**/manifest.tsv")
    for m in manifests:
        step(f"qa_gate {m.parent.relative_to(ROOT).as_posix()}",
             PY + [Path(SKILL) / "scripts" / "qa_gate.py", "check", m, m.parent / "verdicts"])
    runs = []
    for ln in (ROOT / "tools" / "coverage_runs.tsv").read_text(encoding="utf-8").splitlines():
        if ln.strip() and not ln.startswith("#"):
            logdir, run_rom = ln.split("\t")
            runs += ["--run", logdir, run_rom]
    step("coverage", PY + ["tools/coverage.py", "--final", BUILT] + runs + ["--waive", "docs/text_unshown.tsv"])

    unticked = [ln for ln in (ROOT / "docs" / "polish.md").read_text(encoding="utf-8").splitlines()
                if ln.startswith("- [ ]")]
    if unticked:
        sys.exit(f"RELEASE STOPPED: {len(unticked)} unticked line(s) in docs/polish.md")
    placeholders = re.findall(r"<(?:Game title|platform|publisher|year|repo|file|size|sha1|game|ext)>|<[A-Z][a-z]+ /",
                              (ROOT / "README.md").read_text(encoding="utf-8"))
    if placeholders:
        sys.exit(f"RELEASE STOPPED: template placeholders in README.md: {sorted(set(placeholders))}")

    print("== debug tool off: second plain build must match; no marker text", flush=True)
    with tempfile.TemporaryDirectory() as td:
        again = Path(td) / "again.gba"
        step("rebuild", PY + ["tools/build.py", "--out", again])
        if again.read_bytes() != rom:
            sys.exit("RELEASE STOPPED: build/ghost_trap_en.gba differs from a fresh plain build")
    en = Table.load(ROOT / "tbl" / "en.tbl")
    hexd = b"".join(re.escape(en.encode(c)) for c in "0123456789ABCDEF")
    marker = re.escape(en.encode("(")) + b"[" + hexd + b"]{6}" + re.escape(en.encode(")"))
    if re.search(marker, rom):
        sys.exit("RELEASE STOPPED: marker text '(id)' found in the release ROM")

    out.mkdir(parents=True, exist_ok=True)
    step("patch", PY + ["tools/bps.py", "make", ORIG, BUILT, patch])
    with tempfile.TemporaryDirectory() as td:
        check = Path(td) / "check.gba"
        step("re-apply", PY + ["tools/bps.py", "apply", ORIG, patch, check])
        if check.read_bytes() != rom:
            sys.exit("RELEASE STOPPED: re-applied patch does not reproduce build/ghost_trap_en.gba")
    o, p = hashes(ORIG.read_bytes()), hashes(rom)
    readme.write_text(README.format(version=a.version, o=o, p=p, patch=patch.name), encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(patch, patch.name)
        z.write(readme, "README.txt")
    print(f"RELEASE OK: {zpath.relative_to(ROOT).as_posix()}  patched CRC32 {p['crc32']} SHA-1 {p['sha1']}")


if __name__ == "__main__":
    main()
