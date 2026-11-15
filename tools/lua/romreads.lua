-- Log each PC that reads cartridge ROM in frames FROM..TO, with the lowest/highest address it touched.
-- emu.py ROM --out D --route R --script tools/lua/romreads.lua --var FROM=3600 --var TO=3700
-- Optional: LO/HI limit the ROM range (default whole 32 MiB space).
local from = FROM or 0
local to = TO or 1e9
local lo = LO or 0x08000000
local hi = HI or 0x09FFFFFF
local seen = {}
L.on_read(lo, hi, function(addr, value)
  local f = L.frame
  if f < from or f > to then return end
  local pc = L.pc()
  local s = seen[pc]
  if not s then
    seen[pc] = {addr, addr, 1}
  else
    if addr < s[1] then s[1] = addr end
    if addr > s[2] then s[2] = addr end
    s[3] = s[3] + 1
  end
end)
L.on_frame(function(n)
  if n == to + 1 then
    for pc, s in pairs(seen) do
      L.log(string.format("pc %08X lo %08X hi %08X n %d", pc, s[1], s[2], s[3]))
    end
  end
end)
