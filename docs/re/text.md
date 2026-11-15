# Text engine, encoding, pointers

Dump: `rom.sha1` (AGVJ, 8 MiB). Tools: `tbl/jp.tbl`, `tools/textlog.lua` (in `tools/lua/`), `tools/lua/romreads.lua`,
`tools/fontsheet.py`, `tools/gbacomp.py`.

## Encoding (verified)

- One byte per glyph, code = font glyph index. `E0 xx` = glyph `0xE0 + xx` (second page, mostly kanji).
  No Shift-JIS anywhere: relative search over the ROM, every LZ77 block and RAM found nothing.
- **Verified** by hooking the glyph renderer (`0x08027924`, character read at `0x0802795E`, `r4` = text pointer;
  `tools/lua/textlog.lua`) on the first cutscene, line 「ゴーストハントなんて… = `07 A2 06 A7 B6 BD …` (A2 ゴ, 06 ー,
  A7 ス, B6 ト), and by decoding every string in the pointer tables: 3191 strings, roundtrip byte-exact, 0 unknown bytes.
- Layout of `tbl/jp.tbl` (font order, not JIS):
  `00` space (8 px) · `01-0A` 、。・？！ー「」『』 · `0B-24` A-Z · `25-3E` a-z · `3F-8E` hiragana ぁ…ろ わ を ん (JIS order, no ゎゐゑ)
  · `8F-CF` katakana ァ…メ · `D0-D9` 0-9 · `DA-DF` モャヤュユョ · `E000-E007` ヨラリルレロワン · `E008` … · `E009` ＃
  · `E00A-E0BF` 182 kanji · `E0C0-E0C9` （）”＋，．’◎™： · `E0CA/E0CB` blank 4 px (narrow space, staff roll).
  No ヮヰヱヲヴ glyphs.
- **Kanji (E00A-E0BF): partly guessed.** E014-E0B3 are sorted by on'yomi in gojuon order (永 英 遠 … 霊 話), which
  backs the reading; E00A-E013 and E0B4-E0BF are later additions in no order. Fixed from script context: 古 (古い), 印
  (封印), 因 (原因), 科 (科学), 礼 (礼を言わせて), 残 (何も残っていない). Never seen in any string (reading unconfirmed): E017 塩, E085 団,
  E0BA 未, E0BC 催. Phase 4: read zoomed glyph sheets against script lines and confirm the rest.
- Text is horizontal, 16x16 glyphs, with a per-glyph width table (VWF already in the engine).

## Font (verified)

- LZ77 (BIOS type 0x10) at ROM `0x1271C8`, 0xD800 bytes unpacked = 432 glyphs x 128 bytes, 16x16 4bpp, four 8x8 tiles
  TL TR BL BR. Decompressed to EWRAM `0x02011000` (page 2 at `0x02018000`). Outlined white glyphs.
  Verified: RAM dump at frame 1400 matches the decompressed block; `tools/fontsheet.py` renders it labelled.
- Width table: ROM `0x3BBD0`, u16 per glyph code (0x000-0x1AF), read at `0x0802796A`: low byte & 0x3F = left offset (?),
  high byte = advance in px (8 ASCII/punct, 16 kana/kanji, 12 small kana, 4 E0CA/E0CB, …). Guess for the low byte.

## Control codes (verified from the interpreter at `0x08027148`, jump table `0x0802717C` for E0-FE)

| Code | Args | Meaning |
|---|---|---|
| `F7 01` | 1 | open a window without a name plate |
| `F7 00` | 1 | open a window with a name plate; followed by `FB nn` |
| `FB nn` | 1 | name plate / speaker style (`nn` stored at work+0x238): 02 ジョージ, 03 アリシア?, 04 カロル?, 05 ????, 06 … |
| `FC` | 0 | line break (also ends the name plate: `FB 02 ジョージ FC 「…`) |
| `FD` | 0 | wait for button, next page |
| `FE` | 0 | wait/clear variant (same handler as FD; sets work+0x23C) |
| `FF` | 0 | end of string (after FD/FE, or alone) |

`F7`/`FB` are in `tbl` as `{box:NN}` / `{name:NN}`; the bytes after `00 FE 00 FE` at scene starts are plain space +
`FE`. Unknown: the exact visual difference between FD and FE (to confirm in the marker build).

## Pointers (verified)

- GBA u32 `0x08000000|off`, 4-byte aligned. All text pointers sit in one data region, ROM `0x3BF28-0x423A0`
  (10.4 KB): 44 image/palette pointers (`0x0877xxxx-0x087Dxxxx`, entries 0-43 of the first table), 5740 text
  pointers, 646 zeros, nothing else. 3191 unique targets (strings are shared: one string, many slots).
- Sub-tables inside that region (start addresses from the zero runs; owners not traced yet): `0x3BF28` scenes (171
  entries; 44-170 text), `0x3C1D4`, `0x3C55C` (largest, 3383 slots), `0x3FEB0`, `0x3FF00` (1754), `0x41F18` (291).
  `0x423A0` holds one more text pointer (`0x08106A8C`) followed by Thumb code pointers (`0x08028995…`).
- No pointer lands inside another string. Strings are back to back in one block.
- ~120 single "pointers" elsewhere in the ROM (`0x2B9B4`, `0x3026C`, …) are values in code/graphics that happen to
  fall in range; **not** pointers. Do not repoint outside the region above.

## Text ranges

- Script block: ROM `0x100000-0x1271C8` (starts with ASCII `AGBD` at 0x100000; first string 0x100004; last string ends
  0x1271C5; the font LZ block follows at 0x1271C8). 149,866 bytes are reached from the tables.
- Unreferenced gaps with text (5,713 bytes, 9 runs): `0x1064CE` (242), `0x106A8C` (120, referenced from `0x423A0`),
  `0x10EE11`, `0x1166DA`, `0x116786`, `0x11AAB0`, `0x11E67A` (4074, mostly zeros), `0x120B12` (894), `0x12230C`.
  Phase 4: find their readers (literal pools in code) or mark them dead.
- Longest string: 0x11C5D8 (5551 bytes), the staff roll (scene table entry 78), mostly space padding.
- Script is loaded into an EWRAM buffer at `0x0201E000` (2-byte header `00 0F` + string) before drawing.
- Other candidates (not text, noted so nobody re-checks): `0x2B8EA`, `0x394EB`, `0x4247C`, `0x42560` are code
  order tables / tile maps; `0x3BA74`/`0x3B99C` are window tile maps.

## Free space (candidates, not proven)

- `0xF9ABC-0x100000`: 25,924 bytes of 0x00 just before the script block.
- `0x7E8B85-0x800000`: ~95 KB of 0x00/0xFF at the ROM end.
- Past 8 MiB: the ROM can grow to 16 MiB (EEPROM save; keep it at or below 16 MiB, IPS/BPS).
- Relocating the whole script past 0x800000 needs only the table region above repointed (no in-code pointers found).

## Other compression

- 681 BIOS LZ77 blocks (`python -X utf8 tools/gbacomp.py scan ROM`), mostly graphics; none holds text.
- Cutscene pictures use a custom format (header `00 00 00 40` + sizes, e.g. 0x435BC), unpacked by IWRAM code at
  `0x03000614-0x03000830`. Not needed for text.
