# Ghost Trap (GBA) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md, printed by `python tools/skill.py`). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 tools/build.py` -> build/ghost_trap_en.gba (checks the dump against `rom.sha1` first; written in phase 3)
- Check:    `python -X utf8 tools/check.py` (stdlib unittest over `tests/` + lint; the pre-commit hook runs this; `git config core.hooksPath tools/hooks` once per clone)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/ghost_trap_en.gba --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 tools/debug/warp.py <scene> [--rom build/ghost_trap_en.gba] [--state] [--keep --frames 6000]` -> `work/qa/warp/<scene>/scene.png`; `--list`, `--all` regenerates every scene (scenes: `tools/debug/scenes.lua`, RAM map `docs/re/debug.md`; never ask the user to play to a scene)
- Release:  `python -X utf8 tools/release.py` (patch + verify; never publish without the user; written in phase 9)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original ROM: `rom/Ghost Trap (Japan).gba` (8 MiB, game code AGVJ, EEPROM save; gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulator: this repo's own MesenCE in `tools/mesen/` (release 2.2.1, https://github.com/nesdev-org/MesenCE/releases/download/2.2.1/Mesen_2.2.1_Windows.zip; BIOS `tools/mesen/Firmware/gba_bios.bin` via `fetch_emu.py gba-bios`; gitignored; settings in `tools/emu-config/`). Savestates: `work/states/`.
- Text: `script/<table>_<nn>.json` (fields in `tools/script.py`; `tools/extract.py [--force|--check]` writes it and never clobbers `en`; build inserts every non-empty `en`). Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the agent types (translator, reviewer, visual-qa, playtester, graphics) shipped by the plugin as `translate-retro-game:<type>` (Claude Code), `.codex/agents/` (Codex) or `.opencode/agents/` (opencode), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- No pytest on this machine: tests are stdlib `unittest`, run through `tools/check.py`. The guard hook is wired in `.claude/settings.json` (the plugin's own hook did not load here).
- GBA boot needs ~1500 frames to reach the title (Nintendo, Eidos, Artoon logos, intro).

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
