-- Log which ROM pages (0x100 bytes) are read between FROM and TO, with the first PC: finds LZ sources the BIOS
-- decompresses (watch.lua logs one line per PC, so a second block read by the same BIOS loop is hidden there).
--   warp.py SCENE --probe tools/lua/rompages.lua --var FROM=1516 --var TO=1516 [--var LO=0x08700000 --var HI=0x087FFFFF]
local lo, hi = LO or 0x08000000, HI or 0x08FFFFFF
local from, to = FROM or 0, TO or math.huge
local seen = {}
L.on_read(lo, hi, function(addr, value)
  if L.frame < from or L.frame > to then return end
  local page = addr & ~0xFF
  if seen[page] then return end
  seen[page] = true
  L.log(string.format("ROMREAD f%d page %08X first %08X pc %08X", L.frame, page, addr, L.pc()))
end)
