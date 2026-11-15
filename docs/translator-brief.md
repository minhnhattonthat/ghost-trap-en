# Translator brief (Ghost Trap)

Read first: `glossary.md` (rulings, style, names), `docs/synopsis.md` (story so far), `build/terms_<batch>.txt`.

## Input / output
- `python -X utf8 tools/batches.py view bNNN > work/tl/bNNN.view.txt`, then Read it: `id<TAB>JP` in shorthand, long
  strings split after each `^` onto lines indented by two spaces.
- Write `work/tl/bNNN.out.tsv` with the file-write tool, same ids, same order, same shorthand; continuation lines
  start with exactly two spaces (a blank page ` ^` is written `   ^`).
- Shorthand: `@G ` = `{box:00}{name:02}George{br}` (A Alicia, K Karol, Q/X ????, S Shinfa, B Albino, R Reaper),
  `@1` = `{box:01}`, `@0` = `{box:00}`, `|` = `{page}`, `^` = `{clr}`, `$` = `{end}`, `\` = `{br}`.
- Keep every `^`, `$`, `@..` prefix and insert (`{name:0A}` item, `{name:15}` count, `{name:01}`/`{name:07}` choice
  colours) in the JP order. Keep each `|`; you may add `|` (the wrapper also adds pages, repeating the prefix).
- Don't write `\` in dialogue or narration: `tools/wrap.py` wraps each page (224 px x 2 lines) and adds pages.
  Item help strings (table 41F18, 152 px x 3 lines) are laid out by hand: `Name\line\line^$`.
- Check until OK: `python -X utf8 tools/batches.py check bNNN`; then `merge bNNN`. Dry run one string:
  `python -X utf8 tools/wrap.py ID "text"`.

## Quality bar
- Drop 「」 after a name plate; ASCII only (no curly quotes, no ・, no …).
- Honorifics kept (Karol-san, George-san) per D1.
- Same JP line in two strings (cutscene repeats) -> the same English.
- No ordinal glued onto `{name:15}`; no a/an right before `{name:0A}`.
- Report `NEW TERM: jp -> en` in the session notes; the controller adds it to `glossary.md`.
