"""Ghost Trap debug warp: boot cold and land on any scene in tools/debug/scenes.lua, with a proof shot.

    python -X utf8 tools/debug/warp.py SCENE [--rom ROM] [--out DIR] [--state] [--frames N] [--keep] [--sheet]
    python -X utf8 tools/debug/warp.py --list [--families]
    python -X utf8 tools/debug/warp.py --all [--only REGEX] [--jobs 3] [--rom ROM] [--state]   # regen every scene

One scene: work/qa/warp/<scene>/ gets scene.png (the proof shot), log.txt (SCENE_OK line) and, with --state,
work/states/<scene>.mss. --keep (with --frames) keeps running after the proof shot, mashing A where the scene asks.
--all runs every named scene and every family member (scripts 0-126, chapters 1-9 and 1b-9b, every area/room),
writes work/qa/warp/summary.tsv and contact sheets of the proof shots per group, and exits 1 if any scene failed.
The ROM defaults to the original dump; pass --rom build/ghost_trap_en.gba for the translation.
"""
import argparse
import concurrent.futures as cf
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

DEBUG = ROOT / "tools" / "debug"
ORIG = ROOT / "rom" / "Ghost Trap (Japan).gba"
AREA_TABLE, AREA_COUNT = 0x54407C, 136
SAVES = ROOT / "work" / "saves"


def posix(p):
    return str(Path(p).resolve()).replace("\\", "/")


def named_scenes():
    """Scene names and fields from scenes.lua (only the flat `name = { ... }` lines)."""
    out = {}
    for line in (DEBUG / "scenes.lua").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s+(\w+)\s*=\s*\{(.*)\},?\s*$", line)
        if m:
            fields = dict(re.findall(r"(\w+)\s*=\s*(\"[^\"]*\"|[\w.]+)", m.group(2)))
            out[m.group(1)] = {k: v.strip('"') for k, v in fields.items()}
    return out


def area_rooms(rom):
    for a in range(AREA_COUNT):
        off = AREA_TABLE + struct.unpack_from("<I", rom, AREA_TABLE + 4 * a)[0]
        yield a, struct.unpack_from("<I", rom, off + 0x34)[0]


def family_scenes(rom):
    names = ["script_%03d" % i for i in range(127)]
    names += ["chapter_%d" % c for c in range(1, 10)] + ["chapter_%db" % c for c in range(1, 10)]
    names += ["area_%02X_r%d" % (a, r) for a, n in area_rooms(rom) for r in range(n)]
    return names


def write_areas_tsv(rom):
    with open(DEBUG / "areas.tsv", "w", encoding="utf-8", newline="\n") as f:
        f.write("area\trooms\n")
        for a, n in area_rooms(rom):
            f.write("%02X\t%d\n" % (a, n))


def run_scene(scene, rom, out_root, state, frames, keep, sheet, timeout=240, probes=(), pvars=()):
    out = out_root / scene
    if out.exists():
        shutil.rmtree(out)
    meta = named_scenes().get(scene, {})
    sav = SAVES / ("%s.sav" % meta["sav"]) if "sav" in meta else SAVES / "blank.sav"
    if not sav.exists():
        if "sav" in meta:
            return scene, 4, "missing save fixture %s (run the save_write scene first)" % sav
        SAVES.mkdir(parents=True, exist_ok=True)
        sav.write_bytes(b"\xff" * 512)
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(rom), "--out", str(out),
           "--sav", str(sav), "--frames", str(frames), "--timeout", str(timeout),
           "--script", posix(DEBUG / "scenes.lua"), "--script", posix(DEBUG / "warp.lua"),
           "--var", "SCENE='%s'" % scene]
    for p in probes:
        cmd += ["--script", posix(Path(p).resolve())]
    for v in pvars:
        cmd += ["--var", v]
    if state:
        st = ROOT / "work" / "states" / ("%s.mss" % scene)
        st.parent.mkdir(parents=True, exist_ok=True)
        cmd += ["--var", "STATE_SAVE='%s'" % posix(st)]
    if keep:
        cmd += ["--var", "KEEP=1", "--shot-every", "60"]
    if sheet:
        cmd += ["--sheet"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = out / "log.txt"
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    ok = re.search(r"^SCENE_OK .*$", text, re.M)
    shot = (out / "scene.png").exists()
    if scene == "save_write" and p.returncode == 0:
        written = out / ("%s.sav" % Path(rom).stem)
        if written.exists():
            shutil.copy(written, SAVES / "slot1.sav")
    if p.returncode == 0 and ok and shot:
        return scene, 0, ok.group(0)
    err = (p.stdout + p.stderr).strip().splitlines()
    return scene, p.returncode or 1, (ok.group(0) if ok else "") + " | " + " / ".join(err[-3:])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scene", nargs="?")
    ap.add_argument("--rom", default=str(ORIG))
    ap.add_argument("--out", default=str(ROOT / "work" / "qa" / "warp"))
    ap.add_argument("--state", action="store_true", help="save work/states/<scene>.mss at the proof shot")
    ap.add_argument("--frames", type=int, default=12000)
    ap.add_argument("--keep", action="store_true", help="keep running to --frames after the proof shot (shots every 60)")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--families", action="store_true", help="with --list: also every family member")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only", help="with --all: regex on scene names")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--resume", action="store_true", help="with --all: skip scenes that already have a proof")
    ap.add_argument("--probe", action="append", default=[], help="extra Lua probe run after warp.lua (repeatable)")
    ap.add_argument("--var", action="append", default=[], help="NAME=value for the probes (repeatable)")
    a = ap.parse_args()
    rom_bytes = ORIG.read_bytes()
    out_root = Path(a.out)

    if a.list:
        for k, v in named_scenes().items():
            print("%-14s %s" % (k, v.get("note", "")))
        if a.families:
            print("\n".join(family_scenes(rom_bytes)))
        else:
            print("families: script_000..script_126, chapter_1..9 and 1b..9b, area_<hex>_r<n> (tools/debug/areas.tsv)")
        return 0

    if a.all:
        write_areas_tsv(rom_bytes)
        names = list(named_scenes()) + family_scenes(rom_bytes)
        # the save fixture first: load_confirm needs it
        names.sort(key=lambda n: (n != "save_write",))
        if a.only:
            names = [n for n in names if re.search(a.only, n)]
        if a.resume:  # keep scenes already proven by an earlier (interrupted) run
            def proven(n):
                log = out_root / n / "log.txt"
                return (out_root / n / "scene.png").exists() and log.exists() and \
                    "SCENE_OK" in log.read_text(encoding="utf-8", errors="replace")
            done = [n for n in names if proven(n)]
            names = [n for n in names if n not in done]
            print("resume: %d already proven, %d to run" % (len(done), len(names)), flush=True)
        else:
            done = []
        out_root.mkdir(parents=True, exist_ok=True)
        results = {}
        for n in done:
            text = (out_root / n / "log.txt").read_text(encoding="utf-8", errors="replace")
            results[n] = (n, 0, re.search(r"^SCENE_OK .*$", text, re.M).group(0) + " (earlier run)")
        if names and names[0] == "save_write":
            results["save_write"] = run_scene("save_write", a.rom, out_root, a.state, a.frames, False, False)
            names = names[1:]
        with cf.ThreadPoolExecutor(a.jobs) as ex:
            futs = {ex.submit(run_scene, n, a.rom, out_root, a.state, a.frames, False, False): n for n in names}
            for i, f in enumerate(cf.as_completed(futs), 1):
                s, code, msg = f.result()
                results[s] = (s, code, msg)
                print("[%d/%d] %s %s" % (i, len(names), "ok " if code == 0 else "FAIL", s), flush=True)
        order = list(named_scenes()) + family_scenes(rom_bytes)
        with open(out_root / "summary.tsv", "w", encoding="utf-8", newline="\n") as f:
            f.write("scene\texit\tdetail\n")
            for n in order:
                if n in results:
                    _, code, msg = results[n]
                    f.write("%s\t%d\t%s\n" % (n, code, msg.replace("\t", " ")))
        groups = {"named": [n for n in named_scenes() if n in results]}
        for n in results:
            g = n.split("_")[0]
            if g in ("script", "chapter", "area"):
                groups.setdefault(g, []).append(n)
        for g, ns in groups.items():
            shots = [str(out_root / n / "scene.png") for n in sorted(ns) if (out_root / n / "scene.png").exists()]
            if shots:
                sheet_dir = out_root / "_sheets" / g
                if sheet_dir.exists():
                    shutil.rmtree(sheet_dir)
                sheet_dir.mkdir(parents=True)
                for s in shots:  # sheet.py labels tiles by file name
                    shutil.copy(s, sheet_dir / (Path(s).parent.name + ".png"))
                subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "sheet.py"),
                                str(sheet_dir / "*.png"), "--div", "2", "--cols", "6", "--max", "36",
                                "--out", str(out_root / ("sheet_%s.png" % g))], capture_output=True)
        bad = [r for r in results.values() if r[1] != 0]
        print("%d scenes, %d failed" % (len(results), len(bad)))
        for s, code, msg in bad:
            print("FAIL %s exit %d %s" % (s, code, msg))
        return 1 if bad else 0

    if not a.scene:
        ap.error("give a SCENE, --list or --all")
    s, code, msg = run_scene(a.scene, a.rom, out_root, a.state, a.frames, a.keep, a.sheet, probes=a.probe,
                             pvars=a.var)
    print(("ok " if code == 0 else "FAIL ") + msg)
    print("shot: %s" % (out_root / a.scene / "scene.png"))
    return 0 if code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
