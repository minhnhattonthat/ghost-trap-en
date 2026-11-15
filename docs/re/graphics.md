# Graphics text survey

Japanese (and already-English) lettering drawn as tiles rather than through the text engine. Ruling D5: translate
all Japanese graphics text. Sources: the boot/intro/first-room tour (`work/qa/tour1-3`, `work/qa/title`, routes in
the commands below), and a static sweep of every LZ77 block (`tools/gfxsweep.py`, reviewed read-only with
`tools/sweep_review.sh`).

## Japanese graphics text (to translate)

| # | Screen | Layer | Source | State |
|---|---|---|---|---|
| G1 | Title logo: katakana ゴーストトラップ under the English GHOST TRAP logo | BG1, 8bpp (BG1CNT 0x1789: char 0x8000, map 0xB800) | LZ77 `0x7D8C68` (173 tiles matched by `vramfind.py --fmt gba8`, dump `ppu_002100` from route `1500 -;6 start;700 -`; rendered: GHOST TRAP + katakana line). BG0 = castle backdrop, LZ77 `0x7D6694` (no text) | **Done (phase 8):** katakana line dropped (D5), letter bottoms rebuilt by `tools/gfx_title.py` (fill mask from the top half + keyed spans per letter, rim and glow repainted from a colour model of the untouched pixels; map `0x7D8A10` ptr 0x20630 unchanged, 174 unique tiles, no other copy in any LZ block; `build.py` appends the tiles and moves ptr 0x20628; `tests/test_gfx_title.py`: no pixel changes above row 31 except the handakuten box, no katakana left). English in cold-boot title, title menu (`work/gfx/g1/title_en_z4.png`). |

| G2+G3 | **Done (phase 8):** SAVE GAME / LOAD GAME message boxes. Not OBJ: BG1 (char 0x4000, map 0x9000, palette row 6), each message a static LZ77 32x32 tilemap over a 16x16-glyph tile set. Save: tiles G3 `0x7DD4EC` (ptr 0x212BC), maps 0x7DDA90/0x7DDC2C/0x7DDD74/0x7DDED0 (saving+wait, saved, failed, overwrite+Yes/No). Load: tiles G2 `0x7DC6A8` (ptr 0x22A34), maps 0x7DCD88/0x7DCF28/0x7DD100/0x7DD248/0x7DD38C (load+Yes/No, resume floor/Entrance Hall, loaded, no data, failed) | BG1 4bpp | `tools/gfx_save.py` typesets the English with the dialogue font (same fill 1 / outline F style), dedupes tiles, `build.py` appends the LZ blocks after the font and moves the 11 pointers. BG1 chars 0x4000-0x7FFF are free on both screens (512 tiles max) | English in game (`work/gfx/en`, compared with JP at f1620: the top-row shimmer and the plaque over the choices are the game's own) |

Old notes on G2/G3 from the sweep (superseded by the row above):

| G2 | **Seen** (warp `save_confirm`, `load_confirm`): SAVE GAME box このデータに上書きします。よろしいですか？ + はい/いいえ buttons, LOAD GAME confirm box. Save / load messages (fragments read: 上書き, 書き, 失敗, セーブ-like kana): outlined 16 px lettering | OBJ, 4bpp, 1D | LZ77 `0x7DC6A8` (0x1600 bytes) | sweep, high confidence; screen not shot yet (CONTINUE / save). Glyph tile order inside a letter is not plain 2x2 or 4x2/8x2 OBJ order: work it out from an OAM dump on the screen. |
| G3 | Same style, second message set (読み込み/セーブ variants?) | OBJ, 4bpp | LZ77 `0x7DD4EC` (0x1200) | sweep, high confidence; screen not shot yet |

Rows below "Sweep findings" are candidates until confirmed in a shot.

## Already English (no work)

- Boot legal screen (©2002 ARTOON, Eidos licence lines): already English.
- Eidos and Artoon logos.
- Title: GHOST TRAP logo, PRESS START (OBJ, LZ77 `0x7D53AC`), menu NEW GAME / CONTINUE / OPTION.
- In-game item menu (Start): command tabs USE / DROP / EQUIP / BOOK / COMBINE, HUD labels SET TRAP, NOW, MAX, compass
  N/E/S/W. The menu's help lines (えらんだアイテムを…) are text-engine strings, not graphics.

## Text-engine screens (not graphics; listed so they are not re-surveyed)

- All dialogue, the opening crawl and cutscene captions, name plates (ジョージ etc.), item-menu help lines, and the staff
  roll (scene table entry 78, 0x11C5D8) go through the font renderer (`docs/re/text.md`).

## Not yet seen (visit with the phase-2 debug tool, then add rows)

- Seen in phase 2: OPTION (English only), SAVE GAME / LOAD GAME titles, slots, NO DATA, YES/NO (English; the confirm
  boxes are G2), item-menu tabs (English). No game-over screen exists (faint = script 3).
- Still to see: BOOK pages with grimoires held (inventory warp needed), item name display, trap/combine results,
  chapter/area cards if any, ending stills and the staff-roll background (warps `ending`, `credits` exist).
- The 44 cutscene stills (pointer entries 0-43 at `0x3BF28`, custom compression, unpacked by IWRAM code at
  `0x03000614`): not covered by the LZ77 sweep. Check each still for lettering in the phase-2 scene tour.

## Sweep findings

4bpp pass (`gfxsweep.py ... --tiles 256 --page-h 600 --zoom 2`, 55 pages, 656 blocks; 9 blocks skipped as
non-tile sizes, listed in `work/sweep/index.tsv`), reviewed by `codex exec` read-only (`tools/sweep_review.sh`), then
the hits re-rendered and checked by eye:

- `0x1271C8`: the dialogue font (text engine, not graphics text).
- `0x7DC6A8`, `0x7DD4EC`: Japanese lettering -> rows G2, G3.
- `0x527288`: in-game HUD tiles (NOW, MAX, SET TRAP, WE compass): English; the reviewer's "possible Japanese" at
  the right edge looked like icons at 3x. Confirm on the HUD shot in phase 2.
- `0x763600`: large decorative pseudo-script glyphs (not Japanese kana/kanji at 3x). Confirm where it shows.
- English only: `0x527BE0` (menu tabs), `0x7D4164`/`0x7D47E0`/`0x7D4F3C` (Eidos/Artoon logos), `0x7D53AC` (PRESS START,
  NEW GAME, CONTINUE, OPTION), `0x7DE074`, `0x7DE5D4`, `0x7DE6BC` (Latin font), `0x7DE9EC`, `0x7DFD88`/`0x7DFEC8` (digits).
- The 4bpp pass misses 8bpp blocks (the title logo was not flagged), hence the 8bpp pass.

8bpp pass (`--fmt gba8 --tiles 160`, 36 pages, 632 blocks, 33 skipped as non-multiples of 64, listed in
`work/sweep8/index.tsv`), same review:

- `0x7D8C68`: title logo with the katakana line -> G1 (checked by eye).
- `0x53D49C`, `0x53DA60`, `0x53DD04`: small background signs, reviewer saw "apparent Japanese", medium/low
  confidence. **Not text (phase 8):** room-picture overlays DMA'd to VRAM 0x6008500 by the area switch at
  `0x08003E18` (case = area - 0x31, table `0x3E6C`): `0x53D49C` in areas 0x70-0x73 (pinned insect cases and a
  specimen frame on the bedroom wall, `work/gfx/g4/a70w.png`), `0x53DA60`/`0x53DD04` in area 0x74/0x75 rooms 0/1
  (framed paintings). Nothing to translate.
- English only: `0x7DFEC8` (digits), `0x7E0CE8` (GHOST TRAP, L/R=SELECT, START).
