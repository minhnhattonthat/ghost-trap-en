# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 4. Extract (phase 3 identity build done 2026-11-15). Last build: 2026-11-15, identity,
  sha1 `00efb5ed50127f91e2a2827926cf2d4491e4b1b3` (= the dump), smoke ok.
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
- **Next (phase 4 done-when):** pick the `script/` format (JSON per scene/table, `indent=1`, `ensure_ascii=False`;
  id = string offset; record which slots/tables reach each string), write `tools/extract.py` (never clobbers `en`),
  make `build.py` read `script/`, roundtrip test (every `jp` re-encodes to the original bytes) and coverage test
  (block fully covered; decide the 9 unreferenced runs in `docs/re/text.md`: find readers or mark dead). Confirm the
  guessed kanji readings in `tbl/jp.tbl` from zoomed glyph sheets (`tools/fontsheet.py`) against script lines.
- **Later phases, known work:** inventory warp (BOOK pages need grimoires; lead: watch writes when script 39
  "を入手した" shows); FB speaker ids; FD vs FE difference (marker build); field examine text (tables `0x3C55C`,
  `0x3FF00`, `0x41F18`).
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/mesen/Mesen.exe` not checked by hand (headless only); the owner
  can open it once to confirm. Not blocking. Long regens can get stopped by Claude Code for low memory (other repos'
  Mesen runs fill RAM); starting Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` avoids it.
