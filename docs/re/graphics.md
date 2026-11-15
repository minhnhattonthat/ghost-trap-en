# Graphics text survey

Japanese (and already-English) lettering drawn as tiles rather than through the text engine. Ruling D5: translate
all Japanese graphics text. Sources: the boot/intro/first-room tour (`work/qa/tour1-3`, `work/qa/title`, routes in
the commands below), and a static sweep of every LZ77 block (`tools/gfxsweep.py`, reviewed read-only with
`tools/sweep_review.sh`).

## Japanese graphics text (to translate)

| # | Screen | Layer | Source | State |
|---|---|---|---|---|
| G1 | Title logo: katakana ゴーストトラップ under the English GHOST TRAP logo | BG1, 8bpp (BG1CNT 0x1789: char 0x8000, map 0xB800) | LZ77 `0x7D8C68` (173 tiles matched by `vramfind.py --fmt gba8`, dump `ppu_002100` from route `1500 -;6 start;700 -`; rendered: GHOST TRAP + katakana line). BG0 = castle backdrop, LZ77 `0x7D6694` (no text) | verified tiles; map + palette source not traced yet. Keep the English logo, replace the katakana line with English or drop it (D5: the English logo is official). |

| G2 | Save / load messages (fragments read: 上書き, 書き, 失敗, セーブ-like kana): outlined 16 px lettering | OBJ, 4bpp, 1D | LZ77 `0x7DC6A8` (0x1600 bytes) | sweep, high confidence; screen not shot yet (CONTINUE / save). Glyph tile order inside a letter is not plain 2x2 or 4x2/8x2 OBJ order: work it out from an OAM dump on the screen. |
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

- OPTION screen, CONTINUE / save-slot screen, BOOK (notebook) pages, map screen, item name display, trap/combine
  results, game over, ending(s), any chapter or area cards, "to be continued"/end cards.
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
- `0x53D49C`, `0x53DA80`, `0x53DD04`: small background signs, reviewer saw "apparent Japanese", medium/low
  confidence; at 2x they look like plaques/frames. Candidate G4: confirm in the room where they show (phase 2 tour).
- English only: `0x7DFEC8` (digits), `0x7E0CE8` (GHOST TRAP, L/R=SELECT, START).
