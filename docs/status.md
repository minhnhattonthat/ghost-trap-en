# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator: in progress (phase 7 done 2026-11-15; its review had no Critical/Important).
  **QA build: `build/ghost_trap_en.gba` sha1 `e067dd06da642c19398d69d338f84a3a1e9c9d96`** (G1+G2+G3 graphics, Yes/No
  layout fix), frozen with its `strings.tsv` in `work/qa/roms/e067dd06/` (tour + story ran on that copy). The msgs
  run (strings 1135-3192) ran on the text-only `19914506…`, frozen in `work/qa/roms/en_text_19914506.gba` with its
  `strings.tsv` beside it; layouts differ (Yes/No strings grew), so coverage is `tools/coverage.py` (union by id,
  a run counts only for strings with the same bytes as the final build), not plain textcover.
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
    Pad" -> "Control Pad" in 5 strings + glossary). The lint now reads its charset from `tbl/en.tbl` (see below).
  - Phase 6 review fixes (2026-11-15, `.harness/reviews/ghost-trap-en-phase6.md`): `wrap.split_long` splits an
    over-long sentence into even pages at a clause break (was: sliced every 2 lines -> one-word stub pages);
    `wrap.stubs` lint (a page continuing a sentence with < 8 chars) + 5 stub pages reworded (101974 106B04 x2
    1090C8 10B734); voice table in `glossary.md` (George/Alicia/Karol/Shinfa/Albino/Reaper, JP marker -> English
    device), Albino re-voiced (11DB88, 11E1DC); `batches.ENCODABLE` read from `tbl/en.tbl`; 2 gotchas logged.
  - Phase 7 (2026-11-15): lint adds stub last line (< 6 chars on a multi-line page; 3 item-help strings reworded:
    10EF98 10EED8 10ED84) and leading blanks == JP (15 strings had lost the JP's leading space: the TSV strip; the
    choice boxes 10F05C/10F06C ` {name:01}Yes` keep the cursor's room; `check_batch` now restores it).
    `tests/test_english_build.py` builds the all-English ROM in memory: every changed byte is a logged write inside
    the allowed ranges (romdiff.check with no blanket ranges), <= 16 MiB, all 3183 strings decode at every slot,
    untranslated strings keep their bytes, no u32 in code/tables (< 0xE0000) still points at the old block, header
    or font, no Japanese in any `en`. `tools/jp_left_build.py`: jp_left.py over every slot with jp.tbl minus the
    en.tbl cells (English punctuation sits in small-kana cells, so plain jp.tbl reports "...?" as ぃぃぃぇ): 0 runs.
  - Phase 8 so far (2026-11-15): **G2/G3 done**: the SAVE/LOAD message boxes are BG1 tilemaps (not OBJ), now
    English via `tools/gfx_save.py` (dialogue font, appended + repointed by `build.py`; `tests/test_gfx_save.py`;
    details in `docs/re/graphics.md`). **Text coverage tooling**: `build.py` writes `build/strings.tsv`;
    `tools/lua/msgview.lua` + `tools/msgview.py` show any string through script 39's scene-table slot (one cold boot,
    ~5 s, textcover probe on); `tools/qa_tour.py` runs msgs (all strings) + tour (`warp.py --all`) + story (cutscenes
    0-38 clicked through, `--keep --sheet`) into `work/qa/en/`, then `textcover.py`. `warp.py --all` now passes
    `--probe/--var/--keep/--sheet`. `tools/lua/rompages.lua`: ROM pages read per frame (finds BIOS LZ sources).
  - Phase 8 this session (2026-11-15): **G1 done** (`tools/gfx_title.py`: katakana line dropped, letter bottoms
    rebuilt from a mask + colour model, `tests/test_gfx_title.py`; title/menu shots in `work/gfx/g1/`). **G4 = not
    text** (room pictures, `docs/re/graphics.md`). **Item-menu Yes/No** fixed: the question strings (10EEFC 10EF18
    10EF50) carry their own Yes/No row and the cursor redraws 10F05C/10F06C over it without clearing, so all five
    now share one layout `  Yes       No` (Yes/No at the x of はい/いいえ; lint test
    `test_choice_rows_share_one_layout`; lead-blank lint now "no fewer than the JP"). Checked in game by
    `play.py` (DROP -> Throw this away?, cursor both ways: `work/play/yesno3`, JP `work/play/yesno_jp`). Not a
    centred box (left-aligned like the JP), so inkbox doesn't apply. `tools/vqa_review.py` (codex exec verdicts per
    qa_gate chunk) written, not yet run.
- **Next (phase 8 done-when), in order:**
  1. Msgs run on the frozen text build (`work/qa/en_msgs_resume.log`, out `work/qa/en/msgs`): if it stopped, resume
     with `python -X utf8 tools/msgview.py --resume --jobs 2 --rom <repo>/work/qa/roms/en_text_19914506.gba --out
     work/qa/en/msgs`. Then show the 5 changed Yes/No strings on the final build:
     `msgview.py --only "10EEFC|10EF18|10EF50|10F05C|10F06C" --rom <repo>/work/qa/roms/e067dd06/ghost_trap_en.gba
     --out work/qa/en/msgs_final` (or waive them citing `work/play/yesno3`).
  2. Tour + story (`qa_tour.py --skip msgs --rom <repo>/work/qa/roms/e067dd06/ghost_trap_en.gba --out work/qa/en`,
     log `work/qa/en_tour.log`). Then look at the 44 cutscene stills in the story sheets for lettering.
  3. Coverage: `python -X utf8 tools/coverage.py --final work/qa/roms/e067dd06/ghost_trap_en.gba --run
     work/qa/en/msgs work/qa/roms/en_text_19914506.gba --run work/qa/en/tour work/qa/roms/e067dd06/ghost_trap_en.gba
     --run work/qa/en/story work/qa/roms/e067dd06/ghost_trap_en.gba [--run work/qa/en/msgs_final ...] --waive
     docs/text_unshown.tsv` exit 0; reasoned waivers for insert-only `status: data` ids. Answers b024 too.
  4. `qa_gate.py init work/qa/en/manifest.tsv work/qa/en --build work/qa/roms/e067dd06/ghost_trap_en.gba --glob
     "*sheet*.png"`, `todo ... --out-dir work/qa/chunks`, `tools/vqa_review.py work/qa/en/manifest.tsv
     work/qa/chunks/chunk_*.txt`, fix issues, `qa_gate.py check` exit 0. Copy the QA build to `build/` if it differs.
  5. inkbox on the save/load confirm boxes (warp `save_confirm`, `load_confirm`); confirm on a long dialogue the
     extra `{page}` wrap.py adds.
- **Later phases, known work:** inventory warp (BOOK pages need grimoires; lead: watch writes when script 39
  "を入手した" shows); FB speaker ids; FD vs FE difference (marker build); field examine text (tables `0x3C55C`,
  `0x3FF00`, `0x41F18`).
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/mesen/Mesen.exe` not checked by hand (headless only); the owner
  can open it once to confirm. Not blocking. Long regens can get stopped by Claude Code for low memory (other repos'
  Mesen runs fill RAM); starting Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` avoids it.
