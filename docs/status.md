# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9. Release re-made 2026-11-16 on the field-box fix: `tools/release.py --force` RELEASE OK,
  `release/v1.0/Ghost_Trap_EN_v1.0.zip` built and verified (BPS re-applied to the clean dump; patch sha1
  `79891f40297477763a251aedc70790d4c25e0fe6`). QA gate waived for this build by the owner (D11).
  **Release build: `build/ghost_trap_en.gba` sha1 `2f2b6ce8ea86b9b62510a20b238468ceff37fb5a`, CRC32 `A6DF99A3`**,
  frozen with its `strings.tsv` in `work/qa/roms/2f2b6ce8/`. Tour/story
  ran on `e067dd06`, pages on `3ee614ba`/`e520440d`/`667dd3c6`/`46c9659d`/`ab915aca`/`2f2b6ce8` (each later build differs only in
  reworded strings, each re-shown on its build); coverage is `tools/coverage.py` (union by id over runs with the final
  bytes).
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
  - Phase 8 QA runs (2026-11-15; details in git log): msgs 3192/3192 (`work/qa/en/msgs`, plus `msgs_final`,
    `msgs_3ee`, `msgs_667` for later rewords), tour 534/534 (`work/qa/en/tour`), story 39/39 (`work/qa/en/story`,
    `tools/story_pages.py` sheets). **`tools/pageview.py`** (+ `tools/lua/pageview.lua`) is the text-QA viewer: chains
    48 strings per boot through script 39 and shoots every page 4 frames after its page-code handler; labelled sheets
    `pages*/sheet_<group>*.png`. It leaves `status: data` strings out (insert-only `{name:0B}` stalled the chain) and
    presses A after 400 idle frames (`{clr}` waits). Runs: `pages` (3ee614ba, 98 groups), `pages_e520` (scene_00/03,
    41F18_00_00, scene_07_00), `pages_667` (scene_08_00, 41F18_02_00, 3FF00_03_01). scene_07_00 ends at 11E1DC's blank
    `{clr} {clr}` page in script 39 (the JP string has it too); its Reaper tail is shown by **`tools/lua/pageshot.lua`**
    in the real script-36 cutscene (`work/qa/en/pageshot/script_036/sheet_tail.png`). JP reference chains:
    `work/qa/jp_pages` (pageview on `work/qa/roms/jp/`, a copy of the dump with an id->address `strings.tsv`).
  - **Phase 8 gate (2026-11-15): `qa_gate.py check work/qa/en/manifest.tsv work/qa/en/verdicts` exit 0**, 638 sheets
    (story, tour, pages, pages_e520, pageshot, pages_667). Verdicts by `tools/vqa_review.py` (codex exec read-only),
    then triage in `verdicts/triage_*.tsv`: page-break notes on strings with the JP page count -> ok (D9,
    `tools/triage_breaks.py`); item-string glyph fill = script-39 viewer, identical on the JP
    (`work/qa/jp_pages/sheet_41F18_00_00_3.png`); half-size tour sheets lose the 1-px English strokes (full size clean,
    `work/qa/dbg/cmp005.png`). Fixed: 126134/1260E0/12658C reworded to the JP page count, 1067A8 `{box:02}` ->
    `{box:00}{name:02}` (D10, `batches.CODE_FIXES`). Coverage: `coverage.py --final work/qa/roms/667dd3c6/... --run
    work/qa/en/msgs work/qa/roms/en_text_19914506.gba --run work/qa/en/{tour,story,msgs_final} <e067> --run
    work/qa/en/msgs_3ee <3ee6> --run work/qa/en/msgs_667 <667d> --waive docs/text_unshown.tsv` -> 3192/3192, exit 0.
    `jp_left_build.py` on 667dd3c6: 0 runs. Graphics survey fully covered (`docs/re/graphics.md`). inkbox n/a (boxes
    left-aligned like the JP).
  - Phase 9 so far (2026-11-16): `docs/polish.md` all ticked (30 phase-6 Minors fixed, plus story-pass Minors).
    Story pass: `tools/story_chapters.py` -> 11 chapter files in `work/qa/story/chapters/` (3 cutscene chapters by
    scene table, 7 field chapters by table block, items/help), manifest `work/qa/story/manifest.tsv`;
    `tools/story_review.sh [chapters]` = codex exec read-only per chapter (re-review points it at the last
    `reports/<ch>.rN.md`). Round 1: all Critical/Important fixed (Albino confession first person, Shinfa uncontracted,
    キフ pun "sweet offering", ~40 flat George lines voiced). Round 2: 8/11 ok, rest fixed. Round 3 = confirmation.
    `tools/release.py` written (steps per pipeline §Release; coverage runs from `tools/coverage_runs.tsv`), README
    filled. `pageview.py --ids FILE` re-shoots only given strings.
  - **Story pass done (2026-11-16): `qa_gate.py check work/qa/story/manifest.tsv work/qa/story/verdicts` exit 0**
    (11/11; rounds 3-4 all ok). Reports and verdicts copied to `docs/review/story/`. Text is final: **build
    `46c9659d` (sha1 prefix), frozen in `work/qa/roms/46c9659d/`**; 153 strings changed since 667dd3c6 (list:
    `work/polish/changed_ids.txt`, = coverage.py's unshown list); `jp_left_build.py` on it: 0 runs; smoke ok.
  - **Release (2026-11-16):** visual re-check of the 153 story-pass strings on `46c9659d` (`pages_46c9`: 45 groups,
    795 pages, 76 sheets; `msgs_46c9`). Reviewer (`vqa_review.py`, chunks renamed `c46_*` so they don't overwrite the
    old `verdicts/chunk_00N.tsv`) found 25 issues: 6 page-break notes -> ok by D9 (`triage_breaks_46c9.tsv`); 2 false
    (diary line 220 px <= 224, viewer fill on item help); **17 real: 24 polish-pass rewords stored with no `{br}`**, so
    one over-wide line overflowed the box into stray glyphs. The width lint had passed them because `wrap.layout`
    wraps a `{br}`-less page before measuring, but the build inserts `en` as stored. Fixed: those 24 re-wrapped with
    `wrap.layout` (`work/polish/rewrapped_ids.txt`), new lint `test_shipped_text_is_laid_out` (stored `en` must equal
    its own layout). Build `ab915aca`: re-shot (`pages_ab91` 14 sheets all ok, checked by eye too; `msgs_ab91`),
    gate 728/728 + story 11/11, coverage 3192/3192, jp_left 0, `release.py` RELEASE OK (patch 333144 bytes).
  - Re-verified 2026-11-16 (fresh session): `release.py --force` RELEASE OK again, same sha1 `ab915aca`, CRC32
    `B7704AE0`, `check.py` 62 tests OK; nothing changed. Again 2026-11-16 (third session): same result, no open
    GitHub issues. Fourth dispatch 2026-11-16: build sha1 still `ab915aca`, `release/v1.0/` zip + bps present, no
    open issues, main = origin; nothing to do. **The pipeline is at its end state: further phase-9 dispatches are
    no-ops until the owner files a bug or asks to publish.**
  - **Player report 2026-11-16 (`rom/report/`: savestate + shot), fixed:** talking to Karol in the lounge (game
    start, script 123) flooded the field with glyphs. The field box is **176 px**, not the cutscene box's 224
    (the HUD sits right; measured in the field, `docs/re/text.md` Width gate); every QA view so far showed field
    text in the cutscene window, so no shot could catch it. `wrap.variant` now gives every string with a field slot
    the `field` budget (`tools/windows.json`), `{name:0A}` counts as the widest real item name (104 px);
    `tools/refit.py` re-laid out 1,411 strings (merged via `batches.py merge field01/03/05 --overwrite`; ~34 pages
    reworded by hand to stay on one page, `work/tl/field0*.fix.tsv`), test `test_field_strings_use_the_field_box`.
    Verified in the field: Karol's 11 pages, the 8 widest 176 px pages (`work/qa/width/field_widest`). New build
    `2f2b6ce8ea86b9b62510a20b238468ceff37fb5a`, smoke ok, `check.py` 63 OK, `jp_left_build.py` 0.
- **Next (v1.0 published):** build frozen in `work/qa/roms/2f2b6ce8/`.
  The 60 hand-reworded pages were shot in the field box, all clean (`work/qa/width/reworded`). All 1,411 changed
  ids (`work/qa/en/changed_2f2b.txt`) re-shown in game (`work/qa/en/msgs_2f2b`, 0 failed), run added to
  `tools/coverage_runs.tsv`: **coverage 3192/3192, 0 waived**. Owner ran the D11 waiver; `release.py --force`
  RELEASE OK. **Published 2026-11-16 (owner's go, D12):** repo public, description "English fan translation of
  Ghost Trap (GBA)", release https://github.com/minhnhattonthat/ghost-trap-en/releases/tag/v1.0 with the zip
  (download sha1 matches the local zip). Next: watch `gh issue list --label bug` for player reports. (`work/qa/roms/strings.tsv`, the en_text run's table,
  was overwritten by ruler builds and was restored with `tools/strings_tsv.py`; keep ad-hoc builds out of `roms/`.) Publishing only when the owner asks (`references/pipeline.md` §Publish; never run
  `gh release create` or change visibility unasked). The playable image is `build/ghost_trap_en.gba`.
- **Later, known work:** inventory warp (lead: watch writes when script 39 "を入手した" shows); FB speaker ids; FD vs
  FE difference.
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/mesen/Mesen.exe` not checked by hand (headless only); the owner
  can open it once to confirm. Not blocking. Long regens can get stopped by Claude Code for low memory (other repos'
  Mesen runs fill RAM); starting Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` avoids it. This
  has now stopped the phase-8 runs seven times (latest: the e520 pages run, 2026-11-15 night; 6 Mesen processes from
  another repo were running): the owner may want to set it, or not run other repos' tours alongside.
  Not blocking: D9 accepts ~80 sentences that run on over a JP page break (the JP does the same); if the owner wants
  them reflowed so every page ends on a clause, the list is `work/qa/issues_e520.txt` + `issues_667.txt`.
