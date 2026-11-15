# Skill gotchas

One line per gotcha: the skill reference it belongs in, then the fact.

- references/setup.md: `fetch_emu.py gba-bios` 404s; retrobios moved the file to `bios/Nintendo/Game Boy Advance/GBA_bios.rom` (same SHA-1 300c20df...). Fixed in the marketplace clone's `scripts/fetch_emu.py` (2026-11-15); push upstream.
- SKILL.md Step 0.2: plugin enabled in `.claude/settings.json` but not installed in `installed_plugins.json` (skill absent from the Skill list, hook not loaded); the `hooks` block in project settings with `$HOME/.claude/plugins/marketplaces/...` took effect mid-session without a reload.
- references/setup.md: no pytest on this Windows machine; the template's pre-commit `CHECK` assumes pytest. Used stdlib unittest via `tools/check.py`.
- references/emulator-qa.md §Hooks: Mesen GBA `emu.getState()` exposes registers as `cpu.r0`..`cpu.r15` (plus banked `cpu.irqRegs0`...); worth listing next to `L.pc()` so per-game hooks don't have to dump the key list first.
- references/emulator-qa.md §Hooks: `probes/ppudump.lua` with `--route-str` and no `--frames` exits 2 (needs `DUMP_AT`/`DUMP_EVERY`); the error is clear, but the usage line could say so.
- references/pipeline.md §Recon: GBA text with no Shift-JIS and no relative-search hit (font-index code page, kana in JIS order but punctuation/Latin/digits interleaved) was found fastest by `romreads.lua`-style PC/min/max logging over ROM during a typing window, then hooking the renderer's char read; a generic `probes/gba_romreads.lua` would save the hand-written one (`tools/lua/romreads.lua` here).
- references/graphics.md §Survey: GBA title/logo BGs here are 8bpp (BGxCNT bit 7); `vramfind.py --fmt gba4` gives plausible but wrong matches on 8bpp layers. Check BGxCNT in the `.io.bin` dump before choosing `--fmt`.
