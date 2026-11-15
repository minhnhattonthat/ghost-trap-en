# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool (built; full regen at 379/533 proofs, stopped twice by low memory, 2026-11-15). Last build: none yet.
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
  - Second `--all --resume --jobs 1` run (2026-11-15, log `work/qa/warp_all.log`) got to 328 of the 475 remaining
    (area_4C_r1) before Claude Code killed it for low memory again (free RAM 0.3 GB, other repos' Mesens).
    379 scenes now have a `scene.png`. 9 FAIL, all field rooms reached by the fake door: area_09_r2, 2C_r2, 2D_r2,
    2E_r1, 31_r0, 31_r2, 33_r0, 33_r2, 33_r3. Each lands in the wrong room (`lua_error.txt`: mode 9, right area,
    room 1, or room 2 for 2E_r1), so `0x03003716` alone doesn't pick the target room in those areas. Leads: the door
    may index a link table rather than a room id (watch the writes to `0x03003716`/`ROOM` on a real door in area 33),
    or retry the door from the room it landed in (warp.lua only tries one door: `not doored`).
- **Next (phase 2 done-when):** first check free memory (`(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory`,
  needs >2 GB) and `tasklist | grep -i mesen`; then `python -X utf8 tools/debug/warp.py --all --resume --jobs 1`
  for the last 147 scenes (area_4D onward; resume skips the done ones, so delete the 9 failed dirs first to rerun
  them after the fix). Fix the door failures above, then read `work/qa/warp/sheet_*.png` (named, script, chapter,
  area) and confirm each proof shot shows its scene. Then phase 3 (identity build).
- **Later phases, known work:** inventory warp (BOOK pages need grimoires; lead: watch writes when script 39
  "を入手した" shows); kanji readings marked guess in `tbl/jp.tbl`; 5.7 KB unreferenced strings in the script block;
  FB speaker ids; FD vs FE difference (marker build); field examine text (tables `0x3C55C`, `0x3FF00`, `0x41F18`).
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/mesen/Mesen.exe` not checked by hand (headless only); the owner
  can open it once to confirm. Not blocking. The phase-2 regen was stopped by Claude Code for low memory twice: it
  needs a time when other repos' Mesen runs are not filling RAM (or Claude Code started with
  `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1`). A fresh worker can resume it once free RAM is over 2 GB.
