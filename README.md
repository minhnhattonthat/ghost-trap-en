# Ghost Trap English translation

Unofficial English fan translation of **Ghost Trap** (Game Boy Advance, Artoon / Eidos Interactive KK, 2002): the
source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Dialogue, story cutscenes, field messages | Translated |
| Menus, items, item help, system messages | Translated |
| Title screen, SAVE/LOAD message boxes | Translated (redrawn graphics) |
| Name entry | None in this game |
| Staff roll, copyright screen | Already English in the original; unchanged |

Known issues: none known. See [Issues](../../issues).

## Base ROM

| | |
|---|---|
| File | `Ghost Trap (Japan).gba` (No-Intro), 8,388,608 bytes |
| SHA-1 | `00efb5ed50127f91e2a2827926cf2d4491e4b1b3` |

The patch release's README lists CRC32 and MD5 too, plus the patched ROM's hashes. Tested in MesenCE 2.2.1 from a cold
boot (old savestates carry the Japanese text and code; in-game saves work).

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, QA, release. |
| `tests/` | unittest suite, run by `tools/check.py` (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.codex/agents/`, `.opencode/agents/` | Subagent types (translator, reviewer, visual QA, playtester, graphics) for Codex and opencode; Claude Code gets them from the plugin. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/ghost-trap-en
cd ghost-trap-en
# copy your dump to: rom/Ghost Trap (Japan).gba
#   (8388608 bytes, SHA-1 00efb5ed50127f91e2a2827926cf2d4491e4b1b3; the build refuses any other dump, see rom.sha1)
python -X utf8 tools/build.py                          # -> build/ghost_trap_en.gba
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Artoon's and Eidos Interactive's and is
included only so the translation can be checked against it. Ghost Trap is (c) 2002 Artoon; this project is not
affiliated with Artoon or Eidos. Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
