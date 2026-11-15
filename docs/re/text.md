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
- **Kanji (E00A-E0BF): verified** (phase 4). E014-E0B3 are sorted by on'yomi in gojuon order (永 英 遠 … 霊 話);
  E00A-E013 and E0B4-E0BF are later additions in no order. All 182 checked twice: glyph beside the table character
  (`tools/kanjicheck.py OUT.png --from E00A --to E0BF`, 4 pages), and up to 3 script contexts per code. Fixed then:
  E0BA 木 (was 未: 木のハコ, カラの木ばこ), E0BC 低 (was 催: せの低いたな). Unused by any string, read off the glyph
  only: E054 識, E077 相, E085 団, E090 内, E0A8 幽, E0AA 容. No duplicate values in `tbl/jp.tbl`.
- Text is horizontal, 16x16 glyphs, with a per-glyph width table (VWF already in the engine).

## Font (verified)

- LZ77 (BIOS type 0x10) at ROM `0x1271C8`, 0xD800 bytes unpacked = 432 glyphs x 128 bytes, 16x16 4bpp, four 8x8 tiles
  TL TR BL BR. Decompressed to EWRAM `0x02011000` (page 2 at `0x02018000`). Outlined white glyphs.
  Verified: RAM dump at frame 1400 matches the decompressed block; `tools/fontsheet.py` renders it labelled.
- Width table: ROM `0x3BBD0`, u16 per glyph code (0x000-0x1AF), read at `0x0802796A`: low byte & 0x3F = left offset (?),
  high byte = advance in px (8 ASCII/punct, 16 kana/kanji, 12 small kana, 4 E0CA/E0CB, …). Guess for the low byte.

## English font (phase 5, verified in the marker build)

- The font already has proportional A-Z a-z 0-9 (8 px, I i j l 4 px) and Western punctuation in E0C0-E0C9
  (`( ) " + , . ' ◎ ™ :`, staff roll). **But glyphs 0x1A0-0x1AF (E0C0-E0CF) lie on the script buffer at EWRAM
  `0x0201E000`**: the font is 0xD800 bytes from `0x02011000`, the buffer starts at offset 0xD000, so loading any
  script overwrites them (RAM dump at frame 1400 differs from the font exactly there, on the original ROM too). In
  dialogue they draw as noise. Only glyphs below 0x1A0 are usable (`font.SAFE_END`, `tests/test_font.py`).
- **Advances must be multiples of 4** (verified): the renderer (`0x08027924`) builds each glyph row as 64 bits,
  trims `low6(width) * 4` bits off the left (`0x0802AACC`, a 64-bit right shift; all 0 here), then places it by
  `pen & 7` with a branch on `< 4` / `>= 4` at `0x08027BD2`. Every original advance is 4, 8, 12 or 16. Torture shots:
  odd advances (7, 3) dropped and merged glyphs; 6 px advances drew the following glyph 6 px left.
- **Codes 01 、 and 08 」 are special-cased**: placed there, `,` took no advance and `'` drew nothing. So no English
  glyph lives in 01-0A except `? ! ~` (04 05 06), which the torture line shows are plain.
- `tools/font.py` (applied by every English build): copies `, . : " ' ( )` from the staff-roll cells into the small
  kana cells ぁぃぅぇぉァィ (3F 41 43 45 47 8F 91); draws `- — ; & / %` into six kanji cells no string uses (E054 識,
  E077 相, E085 団, E090 内, E0A8 幽, E0AA 容); English word space = its own blank cell ゥ 93, 4 px. Code 00 stays the
  8 px space: the staff roll (already English, kept as original bytes) is laid out in fixed 8 px columns.
  `~` is 06 ー (a wave dash, 16 px), `#` is E009 (fullwidth). Advances (`font.TIGHT`): ink width rounded up to 4,
  so 8 for most letters/digits, 4 for `I i j l , . ' : ; ! -` and space, 12 for `—`.
  "The quick brown fox jumps over the lazy dog." = 304 px (336 at the original 8 px space).
- Encoder: `tbl/en.tbl` (ASCII only; anything else in `en` fails the build). `font.width_px(text, tbl, rom)` measures
  a line with the English advances. Torture line (every en.tbl character, double spaces) renders correctly:
  `work/qa/width/t220/script_040`, `work/qa/width/t/script_041` (`tests/test_font.py` covers cells and advances).

## English layout (phase 5, `tools/build.py`)

Any build with at least one override (en, `--marker`, `--qa`) uses this layout; with none it is the identity build.
- Script block packed at `0x800000` without the dead runs and the AGBD header; every slot in the pointer region
  repointed. The old block `0x100004-0x1271C8` is zeroed (header kept), so a stale read shows blank, not Japanese.
- Font: the patched font LZ-packed after the script block (our packer is 184 bytes larger than the original, and only
  32 bytes follow the original block); both u32 literals `0x081271C8` (`0x1FB88`, `0x267D0`) repointed.
- Width table `0x3BBD0` rewritten in place (same size). ROM padded with 0xFF to a 64 KiB multiple, at most 16 MiB
  (EEPROM). Marker build: 0x870000 bytes.

## Width gate (phase 5, measured)

Measured with ruler builds (`build.py --qa ID=TEXT`, digits 8 px each) shot through `warp.py script_NNN --var HOLD=N`.
An over-long line does not wrap or clip: its tiles spill into the BG and paint the whole screen with the glyph.

Machine-readable copy: `tools/windows.json` (marker build and the phase-7 lint read it).

| Variant | Where | Lines/page | px per line | Shot |
|---|---|---|---|---|
| `{box:01}` plain box | field messages, cutscenes | 2 | 224 (28 digits ok, 29 corrupt; 27 digits + `ll` = 224 ok) | `work/qa/width/w28`, `w29`, `x1` script_040 |
| `{box:00}{name:NN}` name plate | dialogue | name + 2 (a 3rd line corrupts) | name 80 (10 W ok, 11 corrupt); lines 224 | `n10`, `n11`, `l3` script_005 |
| narration (scene table, no `{box}`) | opening crawl, cutscene captions | 2 | 224 (28 ok, 29 corrupt) | `v28`, `v29` script_002 |
| item help (41F18, no `{box}`) | item menu help, item descriptions | 3 | 152 (19 ok, 20 corrupt) | `h19`, `h20` itemmenu |
| item name | first line of the item descriptions (slots `0x4214C-0x42294`); `{name:0A}` inserts it into box lines (script 39 showed `(10F07…`) | 1 | 152, and its box line must fit 224 | marker tour script_039 |
| staff roll `11C5D8`, copyright `11E004` | already English, `status: data` | - | original 8 px columns | - |

Field messages (scripts 39+) close by themselves a few seconds after typing ends: shoot them with `HOLD` 150-220.

## Variable inserts and page codes (phase 5)

- `FB nn` after `{box:00}` is the speaker plate (name text follows inline). Elsewhere it inserts a variable:
  `{name:0A}` item name, `{name:15}` count (script 39 `…を{br}{name:15}コ入手した`), `{name:0B}` alone in seven
  41F18 strings (`status: data`), `{name:01}` / `{name:07}` colour the はい/いいえ choices.
- **FD `{page}` vs FE `{clr}`** (verified, `work/qa/fdfe`): both wait for a button and clear the box; FE also sets
  work+0x23C, and in a cutscene the picture fades to black and moves to its next still. Translations must keep
  every FD/FE exactly where the Japanese has it (the cutscene timeline counts them).

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
`FE`. FD vs FE and the FB inserts: "Variable inserts and page codes" above.

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
- Every string starts 4-aligned; the 0-3 bytes after each are zero padding (`textblock.pack` re-aligns).
- **Dead runs (verified unreferenced, kept byte for byte, not extracted):** `0x1064CE` (242), `0x10EE11` (123),
  `0x1166DA` (86), `0x116786` (34), `0x11AAB0` (32), `0x11E67A` (4074), `0x120B12` (894), `0x12230C` (108); listed
  in `textblock.DEAD`. (`0x106A8C`, once on this list, is the lone slot at `0x423A0` and is extracted.) Evidence:
  no u32 anywhere in the ROM points at any string start inside them (one hit, `0x4C5824`, is inside graphics data);
  the renderer reads text only through the pointer tables; 6 of the 8 runs are older copies of referenced strings
  (field-examine lines, inventory-box prompts); `0x11E67A` is a second staff roll, and a ROM-read probe over the
  whole credits (`warp.py credits --keep --frames 15000 --probe tools/lua/textreads.lua`) reads `0x11C5D8-0x11DB87`
  (the referenced roll, start to end) and nothing in it. Phase 8 text coverage is the backstop.
- **Repo text format:** `script/<table>_<nn>.json` (`tools/script.py` documents the fields; `tools/extract.py` writes
  it, `--check` compares, never clobbers `en`). 3192 strings, 5741 slots, 51 files.
- Longest string: 0x11C5D8 (5551 bytes), the staff roll (scene table entry 78), mostly space padding.
- Script is loaded into an EWRAM buffer at `0x0201E000` (2-byte header `00 0F` + string) before drawing.
- Other candidates (not text, noted so nobody re-checks): `0x2B8EA`, `0x394EB`, `0x4247C`, `0x42560` are code
  order tables / tile maps; `0x3BA74`/`0x3B99C` are window tile maps.

## Free space (candidates, not proven)

- `0xF9ABC-0x100000`: 25,924 bytes of 0x00 just before the script block.
- `0x7E8B85-0x800000`: ~95 KB of 0x00/0xFF at the ROM end.
- Past 8 MiB: the ROM can grow to 16 MiB (EEPROM save; keep it at or below 16 MiB, IPS/BPS).
- Relocating the whole script past 0x800000 needs only the table region above repointed (no in-code pointers found).
  The dead runs (~5.6 KB) can be dropped when it moves.
- The block itself has no slack: the last string ends 0x1271C5 and the font LZ block starts 0x1271C8 (verified by
  `tests/test_identity.py`, which repacks it with `tools/textblock.py`). Any growth needs relocation.

## Other compression

- 681 BIOS LZ77 blocks (`python -X utf8 tools/gbacomp.py scan ROM`), mostly graphics; none holds text.
- Cutscene pictures use a custom format (header `00 00 00 40` + sizes, e.g. 0x435BC), unpacked by IWRAM code at
  `0x03000614-0x03000830`. Not needed for text.
