# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 5. Engine spike and marker build (phase 4 extract done 2026-11-15). Last build: 2026-11-15, from
  `script/` with no `en` yet, sha1 `00efb5ed50127f91e2a2827926cf2d4491e4b1b3` (= the dump), smoke ok.
- **Done:**
  - Step 0 (2026-11-15): MesenCE 2.2.1 + GBA BIOS, smoke boot, guard hook, pre-commit, `rom.sha1`, rulings D1-D7.
  - Phase 1 (2026-11-15): `docs/re/text.md`, `tbl/jp.tbl`, `docs/re/graphics.md`, `tests/test_recon.py` (see git).
  - Phase 2 (2026-11-15): `tools/debug/warp.py` + `warp.lua` + `scenes.lua`, RAM map in `docs/re/debug.md`,
    `tests/test_debug.py`, `tools/debug/scripts_list.py` (`scripts.tsv`), `tools/ramdiff.py`,
    `tools/lua/{vallog,ramdump_at}.lua`. Scene kinds: title, mode (option/save/load), script N (all 127), story
    (chapters 1-9 + b, ending, faint), field (any area 0-135, any room). `--all`: **534 of 534 scenes reach their
    target** (`work/qa/warp/summary.tsv`). Proof sheets read by hand: named, chapter, area (spot-checked, none dark),
    and all 4 `sheet_script*.png` pages (every script shows its text; pixel scan finds no dark shot). Script holds:
    120 frames for cutscenes 0-38 and 107-108 (a dialogue typed out from black), 45 for the other field messages.
  - Phase 3 (2026-11-15): `tools/build.py` (check dump -> unpack script block -> repack -> rewrite 5741 text
    pointers -> `build/writes.log` -> `romdiff.py` with `tools/allowed_ranges.txt`), `tools/textblock.py`
    (unpack/pack, raw segments kept byte for byte), `gbacomp.lz77_compress` (VRAM-safe, disp >= 2; the build keeps
    original LZ bytes for unchanged blocks). `tests/test_identity.py`: build == dump (sha1), block fully covered (3192
    strings), every pointer follows a grown string, overfull block refused, LZ77 roundtrip incl. the font.
    The script block has **no slack**: phase 7 must relocate it (free space past 0x800000, see `docs/re/text.md`).
  - Phase 4 (2026-11-15): `script/<table>_<nn>.json` (51 files, 3192 strings, 5741 slots; fields in
    `tools/script.py`), `tools/extract.py` (`--force` keeps en/status/notes, flags `recheck`; `--check`), `build.py`
    reads `script/` (`--lang`, encoder `tbl/<lang>.tbl` else `jp.tbl`), `textblock.pack` re-aligns strings to 4.
    `tests/test_extract.py`: every `jp` re-encodes to the original bytes, every slot listed once, block = header +
    strings + padding + the 8 dead runs (`textblock.DEAD`, evidence in `docs/re/text.md`), build inserts and
    repoints. Kanji all verified (`tools/kanjicheck.py`); fixed E0BA 木, E0BC 低. `warp.py --probe/--var` runs extra
    Lua; `tools/lua/textreads.lua` logs script-block reads (staff-roll copy proven unread).
- **Next (phase 5 done-when):** marker build (every string -> `[id]` + filler at full box width; a `build.py
  --marker` mode), boot + tour it with the warp tool (scripts, chapters, field examine, menus), find non-text
  strings (mark `"status": "data"` or similar in `script/`), decide FD vs FE. Engine spike: the engine already has a
  VWF width table (`0x3BBD0`) and ASCII A-Z/a-z glyphs (8 px); needs English punctuation (ASCII `! ? ' , . -` are not
  in the font; only fullwidth ！？、。) -> add glyphs to the font (LZ at `0x1271C8`, 432 cells, repack with
  `gbacomp.lz77_compress`; relocate if larger) and their widths. Glyph torture line. Width gate: measure px and lines
  per box variant (`{box:00}` name plate, `{box:01}` plain, staff roll, menus, item names) from zoomed shots. The
  script block has no slack: relocate it past 0x800000 (or into `0xF9ABC` + end) before English grows it.
- **Later phases, known work:** inventory warp (BOOK pages need grimoires; lead: watch writes when script 39
  "を入手した" shows); FB speaker ids; FD vs FE difference (marker build); field examine text (tables `0x3C55C`,
  `0x3FF00`, `0x41F18`).
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/mesen/Mesen.exe` not checked by hand (headless only); the owner
  can open it once to confirm. Not blocking. Long regens can get stopped by Claude Code for low memory (other repos'
  Mesen runs fill RAM); starting Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` avoids it.
