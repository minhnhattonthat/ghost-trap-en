-- Ghost Trap: log every glyph the text renderer (0x08027924) draws.
-- At 0x0802795E r4 = pointer to the current character byte (already past the 2-byte prefix when r3 = 0xE0).
-- Log line: "t <frame> <ptr> <r3> <bytes from ptr-1, 8>"
local function reg(s, n)
  return s["cpu.r" .. n] or s[string.format("cpu.r[%d]", n)]
end
local dumped = false
L.on_exec(0x0802795E, 0x0802795E, function()
  local s = emu.getState()
  if not dumped then
    dumped = true
    local keys = {}
    for k, _ in pairs(s) do if k:find("^cpu") then keys[#keys + 1] = k end end
    table.sort(keys)
    L.log("keys " .. table.concat(keys, " "))
  end
  local p, r3 = reg(s, 4), reg(s, 3)
  if not p then return end
  local t = {}
  for i = -1, 6 do t[#t + 1] = string.format("%02X", emu.read(p + i, emu.memType.gbaMemory)) end
  L.log(string.format("t %d %08X %02X %s font %08X", L.frame, p, r3, table.concat(t, " "), reg(s, 10)))
end)
