# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 7. Insert, fit, check: next (phase 6 done 2026-11-15: all 31 batches merged, 3183 strings `done` + 9
  `data`, review clean). Last builds: 2026-11-15,
  `build/ghost_trap_en.gba` with b025 only, sha1 `0176c388…`, script_001 checked in-game; `build/marker.gba` (`build.py --marker`)
  sha1 `0f58afea14d823a0ac7f944525888ca85ec1876e`, 0x870000 bytes, smoke ok.
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
  - Phase 5 (2026-11-15): English layout in `build.py` (any override -> script block at 0x800000 without dead runs,
    old block zeroed, patched font LZ after it with both pointers moved, width table rewritten; identity build
    unchanged). `tools/font.py` (punctuation copied into small-kana cells, `- — ; & / %` drawn into unused kanji,
    4 px space cell 93, advances = multiples of 4: the renderer needs that), `tbl/en.tbl` (ASCII only),
    `tools/marker.py` + `build.py --marker` / `--qa ID=TEXT` / `--loose`, `tools/windows.json` (measured budgets),
    `tools/variants.py`, `warp.lua` `HOLD`/`MASH_EVERY` vars, `tests/test_font.py`. Marker tour (`work/qa/marker`,
    named scenes + all 127 scripts): 157/157 reached, every box shows its id, no corruption; save/load confirm boxes
    stay Japanese = graphics G2/G3 (known). Width gate: box 224 px x 2 lines, name plate 80, narration 224 x 2, item
    help 152 x 3, item names 152 (docs/re/text.md "Width gate"). Torture line clean. FE = FD + cutscene picture step.
    `status: data`: staff roll, copyright screen (already English), seven `{name:0B}` insert-only strings.
  - Phase 6 so far (2026-11-15): `tools/batches.py` (split/view/check/merge; shorthand `@G |^$\`, codes skeleton,
    px widths), `tools/wrap.py` (wraps page bodies to 224 px x 2, packs pages on sentence breaks, balances lines,
    adds `{page}` + repeats the speaker prefix), `tests/test_batches.py` (lint of every shipped `en` gates commits),
    `docs/translator-brief.md` (the workflow; read it), `docs/synopsis.md`, glossary rulings + D8 (register, quotes).
    31 batches split into `work/tl/b001-b031.tsv` (gitignored; ~95k JP chars without codes). **Merged: b001-b005,
    b025-b031** (all cutscenes through the ending and post-credits skits; `docs/synopsis.md` covers the whole
    story). Pilot in-game: script_001 renders clean (`work/qa/pilot/s1`).
  - `tools/prefill.py` (2026-11-15): field text repeats a lot (half of b003-b005 were repeats). Per batch:
    `batches.py view bNNN > work/tl/bNNN.view.txt`, `prefill.py --todo bNNN > work/tl/bNNN.todo.txt` (only ids
    with no translation yet, in-batch repeats dropped), translate those into `work/tl/bNNN.new` (same out.tsv
    format), `prefill.py --assemble bNNN` (prefill + .new + in-batch repeats -> bNNN.out.tsv), `check`, `merge`.
    Near-identical JP (違う/ちがう) is not matched: reuse the earlier English by hand.
  - Phase 6 finished (2026-11-15): b006-b024 translated in the main thread (items/menus b023 first so names were
    fixed before field notes used them; item names + stat-line wording in `glossary.md`). Review: `codex exec`
    read-only over 4 pairs files (`work/qa/review/run.sh`, reports in `docs/review/`): 3 Critical + ~20 Important,
    all fixed directly in `script/*.json` (knife "reacting to" the sensor, bust not mirror stand, item-name
    capitals Knife/Matches/Oil/Black Stone, Alighieri-san x2, Talisman line 1090C8, puns 100E6C/1233C8/11DB88,
    BOOK1 location, Encyclopedia, BOOK#00 help); re-review of the fixed ids: "No Critical/Important issues".
    30 Minors in `docs/polish.md` (release blocks until ticked). Note: after hand edits in `script/`,
    `batches.py merge` refuses to overwrite them (good); edit JSON directly for later fixes (quotes are `\"`).
  - First all-English build (2026-11-15): `build/ghost_trap_en.gba` sha1 `63591450c2f9150cc7139ec57b6321ed19f71312`,
    3183 strings, romdiff identical outside allowed ranges. It first failed on `+` (not in the font; "+Control
    Pad" -> "Control Pad" in 5 strings + glossary). Gap: `batches.py check`/lint don't test encodability against
    `tbl/en.tbl`; add that test in phase 7.
- **Next (phase 7 done-when):** build green: `python -X utf8 tools/build.py` with all English, width/overflow lint
  clean, control codes matched, `romdiff.py` no writes outside `tools/allowed_ranges.txt`; smoke boot. Then phase 8
  in-game QA (warp `--all`, visual QA; the extra `{page}` wrap.py adds in a box run: confirm on a long dialogue).
  b024 is an older duplicate script (alternate field/cutscene lines); check in phase 8 whether the game reads it.
- **Later phases, known work:** inventory warp (BOOK pages need grimoires; lead: watch writes when script 39
  "を入手した" shows); FB speaker ids; FD vs FE difference (marker build); field examine text (tables `0x3C55C`,
  `0x3FF00`, `0x41F18`).
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/mesen/Mesen.exe` not checked by hand (headless only); the owner
  can open it once to confirm. Not blocking. Long regens can get stopped by Claude Code for low memory (other repos'
  Mesen runs fill RAM); starting Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` avoids it.
