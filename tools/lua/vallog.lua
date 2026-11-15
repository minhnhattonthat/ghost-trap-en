-- Log every write that changes a byte in WATCH_LO..WATCH_HI (GBA), with frame, PC, address, old -> new.
--   emu.py ... --script tools/lua/vallog.lua --var WATCH_LO=0x03004A77 [--var WATCH_HI=0x03004A77] [--var MAXLOG=2000]
local lo = assert(WATCH_LO, "set --var WATCH_LO=0x...")
local hi, maxlog = WATCH_HI or lo, MAXLOG or 2000
local last, n = {}, 0
L.on_write(lo, hi, function(addr, value)
  value = value & 0xFF
  if last[addr] == value or n >= maxlog then return end
  n = n + 1
  L.log(string.format("f%d pc=%08X %08X %s -> %02X", L.frame, L.pc(), addr,
    last[addr] and string.format("%02X", last[addr]) or "??", value))
  last[addr] = value
end)
