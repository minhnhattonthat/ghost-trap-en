# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool (all 534 scenes reached; 59 script proof shots to re-take with the new hold, 2026-11-15). Last build: none yet.
- **Done:**
  - Step 0 (2026-11-15): MesenCE 2.2.1 + GBA BIOS, smoke boot, guard hook, pre-commit, `rom.sha1`, rulings D1-D7.
  - Phase 1 (2026-11-15): `docs/re/text.md`, `tbl/jp.tbl`, `docs/re/graphics.md`, `tests/test_recon.py` (see git).
  - Phase 2 (2026-11-15): `tools/debug/warp.py` + `warp.lua` + `scenes.lua`, RAM map in `docs/re/debug.md`,
    `tests/test_debug.py`, `tools/debug/scripts_list.py` (`scripts.tsv`), `tools/ramdiff.py`,
    `tools/lua/{vallog,ramdump_at}.lua`. Scene kinds: title, mode (option/save/load), script N (all 127), story
    (chapters 1-9 + b, ending, faint), field (any area 0-135, any room).
  - Full `--all` regen: **534 of 534 scenes reach their target** (`work/qa/warp/summary.tsv`, 0 failed). Door
    fixes this session (docs/re/debug.md §field): rooms with an arrival dialogue (areas 09, 2C-2E, 31, 33) ignore a
    door until the text closes, so warp.lua presses A and re-arms the door; in areas 09, 2C-2E and 6E the player lands
    on the target room's exit, so warp.lua cancels the game's door check (`0x0800477E`) until the shot.
  - Proof sheets read by hand: named (30, all show their scene; `title_intro` hold raised to 210 so it shows the
    castle, re-shot), chapter (18 story scenes, ok), area sheets 4 and 10 spot-checked (rooms render; none of the
    area shots is dark by a pixel scan).
  - Script proofs: at hold 120, 14 one-line field messages (41, 42, 45, 48, 58, 59, 77, 100, 111, 113, 114,
    124-126) had closed (black shot); at 45, cutscenes 0, 2 and 34 are still fading in. `scenes.lua` now uses 120 for
    scripts 0-38 and 45 for 39+. Scripts 39-106 are re-shot at 45 (no dark shot); the regen was stopped by Claude
    Code for low memory at script 107.
- **Next (phase 2 done-when):** check free memory (needs >1 GB; `tasklist | grep -i mesen` shows other repos' runs),
  then `python -X utf8 tools/debug/warp.py --all --resume --jobs 1` re-takes the 59 missing proofs (scripts 0-38
  and 107-126; the dirs are deleted, resume skips the rest) and rebuilds the sheets. Then check no script shot is
  dark (pixel scan: under 60 pixels brighter than 40 = dark) and read `sheet_script*.png`. Then phase 3 (identity
  build).
- **Later phases, known work:** inventory warp (BOOK pages need grimoires; lead: watch writes when script 39
  "を入手した" shows); kanji readings marked guess in `tbl/jp.tbl`; 5.7 KB unreferenced strings in the script block;
  FB speaker ids; FD vs FE difference (marker build); field examine text (tables `0x3C55C`, `0x3FF00`, `0x41F18`).
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/mesen/Mesen.exe` not checked by hand (headless only); the owner
  can open it once to confirm. Not blocking. Long regens keep getting stopped by Claude Code for low memory (other
  repos' Mesen runs fill RAM); starting Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` avoids it.
