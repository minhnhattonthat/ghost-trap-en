-- Message viewer: show any string through the game's own script path (text coverage and visual QA, phase 8).
-- Run after warp.lua on a script scene; points that script's scene-table entry at MSG before the game reads it:
--   warp.py script_039 --rom build/ghost_trap_en.gba --probe tools/lua/msgview.lua --var MSG=0x08801234
-- MSG = the string's address in this build (build/strings.tsv). tools/msgview.py runs it over many strings.
-- Scene table 0x3BF28: entries 44-170 are scripts 0-126 (docs/re/text.md "Pointers").
local carrier = CARRIER or 39
local slot = 0x3BF28 + (44 + carrier) * 4
local v = MSG
for i = 0, 3 do
  emu.write(slot + i, (v >> (8 * i)) & 0xFF, emu.memType.gbaPrgRom)
end
L.log(string.format("MSGVIEW slot %X -> %08X (script %d)", slot, v, carrier))
