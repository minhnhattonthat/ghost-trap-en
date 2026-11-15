# Glossary - Ghost Trap

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Johannes-san). Name order: Western (given name first).
- Romanisation source: official English names where they exist, else an earlier fan patch, else Hepburn without macrons.
- Credits: English.
- Register / flavour: <set in phase 6 from the script>. Sound effects: <set in phase 6>.
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening.

## Limits (measured, phase 5; tools/windows.json, docs/re/text.md "Width gate")
- Dialogue / field box: 2 lines per page, 224 px per line. Name plate: 80 px. Narration: 2 lines, 224 px.
  Item help box: 3 lines, 152 px. Item names: 152 px (also inserted into box lines by {name:0A}).
- Widths (tools/font.py): most letters and digits 8 px; I i j l , . ' : ; ! - and space 4 px; — 12 px; ~ 16 px.
  About 28-34 characters per box line. Characters available: A-Z a-z 0-9 space ! ? , . : ; ' " ( ) - — & / % ~ #.
- Keep every {page} and {clr} where the Japanese has them ({clr} also advances the cutscene picture); add pages with
  {page} only inside a run that has no picture change.

## Style rules
- Punctuation map: 「」 -> "...", 『』 -> '...', ・・・ -> ..., ！？ -> !?, <more>.
- <voice notes per character, or point to docs/style-reference.md>

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|

## Decisions from earlier batches
- <batch> <JP> -> <EN> (reason)
