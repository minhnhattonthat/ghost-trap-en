# Skill gotchas

One line per gotcha: the skill reference it belongs in, then the fact.

- references/setup.md: `fetch_emu.py gba-bios` 404s; retrobios moved the file to `bios/Nintendo/Game Boy Advance/GBA_bios.rom` (same SHA-1 300c20df...). Fixed in the marketplace clone's `scripts/fetch_emu.py` (2026-11-15); push upstream.
- SKILL.md Step 0.2: plugin enabled in `.claude/settings.json` but not installed in `installed_plugins.json` (skill absent from the Skill list, hook not loaded); the `hooks` block in project settings with `$HOME/.claude/plugins/marketplaces/...` took effect mid-session without a reload.
- references/setup.md: no pytest on this Windows machine; the template's pre-commit `CHECK` assumes pytest. Used stdlib unittest via `tools/check.py`.
- references/emulator-qa.md §Hooks: Mesen GBA `emu.getState()` exposes registers as `cpu.r0`..`cpu.r15` (plus banked `cpu.irqRegs0`...); worth listing next to `L.pc()` so per-game hooks don't have to dump the key list first.
- references/emulator-qa.md §Hooks: `probes/ppudump.lua` with `--route-str` and no `--frames` exits 2 (needs `DUMP_AT`/`DUMP_EVERY`); the error is clear, but the usage line could say so.
- references/pipeline.md §Recon: GBA text with no Shift-JIS and no relative-search hit (font-index code page, kana in JIS order but punctuation/Latin/digits interleaved) was found fastest by `romreads.lua`-style PC/min/max logging over ROM during a typing window, then hooking the renderer's char read; a generic `probes/gba_romreads.lua` would save the hand-written one (`tools/lua/romreads.lua` here).
- references/graphics.md §Survey: GBA title/logo BGs here are 8bpp (BGxCNT bit 7); `vramfind.py --fmt gba4` gives plausible but wrong matches on 8bpp layers. Check BGxCNT in the `.io.bin` dump before choosing `--fmt`.
- references/emulator-qa.md §emu.py: without `--sav`, Mesen (portable) keeps the game's battery save in `tools/mesen/Saves/`; one `--mash` run that hit a SAVE prompt wrote a save, and every later cold boot defaulted to CONTINUE instead of NEW GAME. Debug-tool runs should always pass `--sav` (a blank 512-byte 0xFF file for GBA EEPROM here).
- references/emulator-qa.md §Hooks: two `--script` probes that read the same global (`watch.lua` and a second probe both on `WATCH_LO`) silently share the last `--var`; give per-game probes their own variable names.
- references/emulator-qa.md §emu.py: a `--mash` run with no route mashes from frame 0, so it can't be combined with a Lua warp that must reach the title untouched; set the `MASH` global from the warp script after arrival instead.
- references/emulator-qa.md §Debug tool: GBA game here: a script-id byte is overwritten by the story machine in the cutscene mode's first sub-state; swapping the id on entry to the next sub-state (exec hook) is what made "play any cutscene" work. Worth a line: hook after the picker, not before.
