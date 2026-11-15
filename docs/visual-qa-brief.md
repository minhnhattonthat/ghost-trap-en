# Visual-QA reviewer brief - Ghost Trap (GBA)

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- Optional: the original ROM's sheets and proof shots (`work/qa/warp/`: the phase-2 tour of the original, same scene
  names, e.g. `work/qa/warp/area_70_r0/scene.png`, `work/qa/warp/sheet_script_*.png`) and `glossary.md`.

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that.
- When something looks wrong, open the same id from `tour_jp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.
- Zoom into every Yes/No prompt, selection box, menu row and speech bubble: a few pixels of misalignment don't show
  at sheet scale. To measure one: `python -X utf8 $SKILL/scripts/inkbox.py SHOT.png x,y,w,h`.

## Judge
An `issue` is any of:
- Japanese still visible;
- text overflowing a box, clipped by a frame, or running off screen;
- text off-centre where the original centres it: an option in its selection box or cursor brackets, a label, a bubble;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok` (the controller adds the game's own below):
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp;
- anything identical in the original's sheet.
- SAVE GAME / LOAD GAME screens: the shimmer on the top row and the plaque over the choices are the original's.
- Field rooms entered by warp: the player may stand in an odd spot or inside a wall; dark rooms are dark in the
  original too (compare). The HUD labels (SET TRAP, NOW, MAX, compass) are English in the original.
- Cutscene pages are clicked through by the tour: a page caught mid-type or between two pages is fine.
- English punctuation is drawn in former small-kana cells, so "..." and "?" look slightly heavier than letters.
- `pages/sheet_*` (tools/pageview.py): every page of every string, fully typed, each tile labelled `<id> p<k>/<n>`
  (string id, page k of n). All are shown through one field-message carrier, so a black background with no room
  picture, and cutscene or menu strings in the plain field box, are normal. A sentence that continues from p1 onto
  p2 at a clause break is fine (the wrapper splits long sentences there); judge each page's own lines. A tile that
  shows only a name plate, or an empty box, is an issue only if the label's string has text on that page.
- `tour/sheet_*` (warp proof shots, half size): they prove each scene is reached and nothing gross is wrong. The
  cutscene backdrops are zigzag "warp" art, and dialogue at half size is a few pixels per glyph: both the game's
  own (compare the JP reference, `work/qa/tour_jp`). Text is judged on `pages/` and `story/` sheets, not here.
- Scripts 37-38 (copyright/licence screen played out of context): the screen-filling repeat of glyph tiles behind
  the licence lines is compared with the JP reference; the licence text itself is the original English.
- `story/*/sheet_pages*`: cutscenes clicked through in context. Tiles of the scene with no text box (the picture
  or the room between pages) are the shot picker's false positives: `ok`.

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
