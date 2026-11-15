# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool (built and spot-checked; full regen interrupted by low memory, 2026-11-15). Last build: none yet.
- **Done:**
  - Step 0 (2026-11-15): MesenCE 2.2.1 + GBA BIOS, smoke boot, guard hook, pre-commit, `rom.sha1`, rulings D1-D7.
  - Phase 1 (2026-11-15): `docs/re/text.md`, `tbl/jp.tbl`, `docs/re/graphics.md`, `tests/test_recon.py` (see git).
  - Phase 2 so far (2026-11-15): `tools/debug/warp.py` + `warp.lua` + `scenes.lua`, RAM map in `docs/re/debug.md`,
    `tests/test_debug.py`, `tools/debug/scripts_list.py` (labels the 127 scripts; `scripts.tsv`), `tools/ramdiff.py`,
    `tools/lua/{vallog,ramdump_at}.lua`. Scene kinds: title, mode (option/save/load), script N (all 127 cutscene
    ids via the game's cutscene mode), story (chapters 1-9 + b, ending, faint), field (any area 0-135, any room).
    Proven by hand: title, title_menu, newgame, option, save, save_pick, save_confirm, save_write (writes
    `work/saves/slot1.sav`), load, load_slot1, load_confirm, load_game, field, book, menu_combine, map, ending,
    credits, fainted, chapter_3, opening, script_010/039, area_00_r0, area_00_r1, area_11_r4, area_5E_r3.
    `--all` run reached 52 of 533 scenes ok (scripts 0-23 and the named scenes it got to) before Claude Code
    killed it for low system memory (other repos' Mesen runs held ~3 GB). Its one failure, `title_intro`, is fixed
    in code (`stable = 1`) but not re-run.
- **Next (phase 2 done-when):** run `python -X utf8 tools/debug/warp.py --all --resume --jobs 2` when memory allows
  (each Mesen ~0.5-1 GB; check `tasklist | grep -i mesen` first), fix any FAIL in `work/qa/warp/summary.tsv`,
  then read `work/qa/warp/sheet_*.png` (named, script, chapter, area) and confirm each proof shot shows its scene.
  Then phase 3 (identity build).
- **Later phases, known work:** inventory warp (BOOK pages need grimoires; lead: watch writes when script 39
  "を入手した" shows); kanji readings marked guess in `tbl/jp.tbl`; 5.7 KB unreferenced strings in the script block;
  FB speaker ids; FD vs FE difference (marker build); field examine text (tables `0x3C55C`, `0x3FF00`, `0x41F18`).
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/mesen/Mesen.exe` not checked by hand (headless only); the owner
  can open it once to confirm. Not blocking. The phase-2 regen was stopped by Claude Code for low memory and must not
  be restarted unasked: say when to run it (`--resume --jobs 2`). Not blocking for a fresh worker.
