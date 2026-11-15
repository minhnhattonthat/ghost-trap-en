# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1. Research and recon (next; Step 0 setup done). Last build: none yet.
- **Done:** Step 0 (2026-11-15): MesenCE 2.2.1 + GBA BIOS in `tools/mesen/`; original ROM smoke-boots and reaches the title menu (NEW GAME / CONTINUE / OPTION) via `tools/routes/boot.txt`; Lua probe logs (`tools/lua/probe_hello.lua`); guard hook blocks the `sed -i` canary; pre-commit rejects a failing test; `rom.sha1` pinned; `tools/check.py` (unittest) passes; rulings D1-D7 recorded.
- **Next:** Phase 1 recon: earlier patches/docs, text encoding (likely Shift-JIS; check), pointer tables, compression (LZ77/Huffman), control codes, free space; graphics-text survey (title logo has a katakana subtitle, menu text on title is already English).
- **Open bugs:** none.
- **Waiting on the user:** GUI keyboard input in `tools/mesen/Mesen.exe` not checked by hand (headless only); the owner can open it once to confirm. Not blocking.
