# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool (next; phase 1 recon done 2026-11-15). Last build: none yet.
- **Done:**
  - Step 0 (2026-11-15): MesenCE 2.2.1 + GBA BIOS, smoke boot, guard hook, pre-commit, `rom.sha1`, rulings D1-D7.
  - Phase 1 (2026-11-15): `docs/re/text.md` (encoding = font index, `E0 xx` second page; control codes F7/FB/FC/FD/FE/FF
    from the interpreter at 0x08027148; all text pointers in ROM 0x3BF28-0x423A0; script block 0x100004-0x1271C5,
    3191 strings, roundtrip exact; font LZ77 0x1271C8; free-space candidates 0xF9ABC-0x100000 and the ROM end),
    `tbl/jp.tbl` (kana/Latin/digits verified, kanji first pass), `docs/re/graphics.md` (title katakana logo G1, save
    message sprites G2/G3; LZ77 sweep 4bpp + 8bpp reviewed), `tests/test_recon.py`. No earlier fan patch exists
    (web search, 2026-11-15).
  - Tools: `tools/gbacomp.py` (LZ77), `tools/fontsheet.py`, `tools/gfxsweep.py` + `tools/sweep_review.sh`,
    `tools/lua/textlog.lua` (logs every glyph the renderer draws), `tools/lua/romreads.lua`.
- **Next (phase 2):** debug tool in `tools/debug/` (warp by scene id). Leads: the scene table at 0x3BF28 (entries
  44-170 are scripts); the script is copied to EWRAM 0x0201E000 before drawing; the renderer's work struct holds the
  text pointer at +0x250 (`sb` in 0x08027924). Find the room/scene id in RAM (ramsearch while walking between rooms)
  and the cutscene trigger. Then shoot the screens graphics.md lists as "Not yet seen" (OPTION, CONTINUE/save, BOOK,
  map, game over, endings, cutscene stills) and confirm G2/G3.
- **Later phases, known work:** kanji readings marked guess in `tbl/jp.tbl` (E017 E085 E0BA E0BC never used; confirm
  the rest against context in phase 4); 5.7 KB of unreferenced strings in the script block (find readers in phase 4);
  FB speaker ids; FD vs FE difference (marker build).
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/mesen/Mesen.exe` not checked by hand (headless only); the owner
  can open it once to confirm. Not blocking.
