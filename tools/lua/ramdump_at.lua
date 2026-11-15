-- Dump GBA EWRAM+IWRAM (L.dump_ram layout: 256 KB EWRAM then 32 KB IWRAM) at each frame in DUMP_AT.
--   emu.py ... --script tools/lua/ramdump_at.lua --var "DUMP_AT={60,600}"
local at = DUMP_AT or { 60 }
local want = {}
for _, f in ipairs(at) do want[f] = true end
L.on_frame(function(n)
  if want[n] then L.dump_ram(string.format("ram_%06d.bin", n)) end
end)
