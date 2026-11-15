# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6. Translate in progress (b025-b027 merged, 28 batches to go). Last builds: 2026-11-15,
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
    31 batches split into `work/tl/b001-b031.tsv` (gitignored; ~95k JP chars without codes). **Merged: b025, b026,
    b027** (25 cutscene strings, scripts 0-20ish). Pilot in-game: script_001 renders clean
    (`work/qa/pilot/s1`).
- **Next (phase 6 done-when):** translate b028-b031 (rest of the cutscenes, extend `docs/synopsis.md` as you go),
  then b001-b024 (field text 3C55C/3FF00, items 41F18, menus) with `docs/translator-brief.md`; `batches.py check`
  OK + merge per batch; commit after each few batches. Plugin translator/reviewer agent types are NOT available in
  this harness (and the Orca brief forbids helpers): translate in the main thread, review yourself in a fresh
  read-only pass at the end (pairs file, Critical/Important fixed, Minors -> `docs/polish.md`). If `work/tl/` is
  missing (fresh clone), `batches.py split` regenerates batches for untranslated ids only. The extra `{page}` in a
  box run is used by wrap.py; confirm in-game on a long dialogue during phase 8.
- **Later phases, known work:** inventory warp (BOOK pages need grimoires; lead: watch writes when script 39
  "を入手した" shows); FB speaker ids; FD vs FE difference (marker build); field examine text (tables `0x3C55C`,
  `0x3FF00`, `0x41F18`).
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/mesen/Mesen.exe` not checked by hand (headless only); the owner
  can open it once to confirm. Not blocking. Long regens can get stopped by Claude Code for low memory (other repos'
  Mesen runs fill RAM); starting Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` avoids it.
