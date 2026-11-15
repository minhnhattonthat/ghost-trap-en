# Skill gotchas

One line per gotcha: the skill reference it belongs in, then the fact.

- references/setup.md: `fetch_emu.py gba-bios` 404s; retrobios moved the file to `bios/Nintendo/Game Boy Advance/GBA_bios.rom` (same SHA-1 300c20df...). Fixed in the marketplace clone's `scripts/fetch_emu.py` (2026-11-15); push upstream.
- SKILL.md Step 0.2: plugin enabled in `.claude/settings.json` but not installed in `installed_plugins.json` (skill absent from the Skill list, hook not loaded); the `hooks` block in project settings with `$HOME/.claude/plugins/marketplaces/...` took effect mid-session without a reload.
- references/setup.md: no pytest on this Windows machine; the template's pre-commit `CHECK` assumes pytest. Used stdlib unittest via `tools/check.py`.
