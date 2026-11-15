-- Log which bytes of the script block the game reads, as merged address ranges (TEXTREAD lo hi), every 300 frames.
-- warp.py SCENE --keep --frames N --probe tools/lua/textreads.lua    (then tools/textreads.py maps them to strings)
-- Optional LO/HI override the block (default 0x08100000-0x081271C7).
local lo = LO or 0x08100000
local hi = HI or 0x081271C7
local new = {}
local any = false
L.on_read(lo, hi, function(addr, value)
  if not new[addr] then new[addr] = true; any = true end
end)
local function flush()
  if not any then return end
  local list = {}
  for a in pairs(new) do list[#list + 1] = a end
  table.sort(list)
  local s, p = list[1], list[1]
  for i = 2, #list do
    local a = list[i]
    if a ~= p + 1 then
      L.log(string.format("TEXTREAD %08X %08X", s, p))
      s = a
    end
    p = a
  end
  L.log(string.format("TEXTREAD %08X %08X", s, p))
  new, any = {}, false
end
L.on_frame(function(n)
  if n % 300 == 0 then flush() end
end)
