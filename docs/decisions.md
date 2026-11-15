# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

Rulings D1-D7 came from the owner's standing answers for one-shot runs (injected by the Orca coordinator brief).

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-15 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western name order (given name first). Owner's standing answer. |
| D2 | 2026-11-15 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist, else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-11-15 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-15 | Abbreviations | engine work first (default), abbreviate | Engine work first (skill default; not overridden by the owner). Abbreviate only as a flagged last resort. |
| D5 | 2026-11-15 | Graphics text left in Japanese | none (default), list | Translate all of it (titles, menus, banners, cards); leave the original Japanese logo only if it has no official English version. |
| D6 | 2026-11-15 | Specs and plans | need approval, pre-approved | Pre-approved: keep going through checkpoints, report at the end. |
| D7 | 2026-11-15 | Existing saves / savestates | user supplies, none | None provided; build the debug tool as usual. |
| D8 | 2026-11-15 | Register, flavour, sound effects, quote style | formal / casual; keep 「」 as quotes / drop after name plates | Casual modern American English, George narrates as "I", spooky-wry narration; English onomatopoeia; 「」 dropped after a name plate (saves width, the plate marks speech), "..." in narration. Set by the agent (pre-approved run, D6). |
| D9 | 2026-11-15 | Sentences that run on over a page break | reflow every string so pages end on clause breaks / accept where the break is the JP's | Accept where the string keeps the JP page count (the break is a JP `{page}`/`{clr}`, which also steps cutscene pictures; the JP runs sentences on the same way); reword where we added the page (126134, 12658C) or a page is a stub. ~80 reviewer notes of this kind are in `work/qa/issues_e520.txt`/`issues_667.txt` if the owner wants a reflow pass. Set by the agent (pre-approved run, D6). |
| D10 | 2026-11-15 | 1067A8 `{box:02}` (only string using it) | keep / show as box 00 + name plate 02 | Box 00 + plate 02: box 02 draws the name with overlapping glyphs, in the JP too (`work/qa/dbg/cmp1067.png`). Exempted in `tools/batches.py` CODE_FIXES. Set by the agent. |
| D11 | 2026-11-16 | Visual gate after the field-box fix (1,411 strings re-laid out, ~700 sheets to re-review) | full re-shoot + visual-QA agents / hotfix waiver + spot-check | Waiver + spot-check (owner): every changed string re-shown in game for coverage, the hand-reworded strings and a field sample checked by eye; the width limit was measured in the field. |
| D12 | 2026-11-16 | Publishing v1.0 | public repo + GitHub release / release but keep private | Public (owner): description "English fan translation of Ghost Trap (GBA)", push main, GitHub release v1.0 with the patch zip. |
