-- Page shots in a real story run (warp.py script_NNN --keep --frames N --probe tools/lua/pageshot.lua):
-- one shot DELAY frames (default 4) after every {page}/{clr} handler run, so each page is fully typed.
-- Used where pageview.lua's script-39 chain cannot go: 11E1DC ends its script-39 message at its blank
-- "{clr} {clr}" page before the Reaper lines, which the real cutscene (script 36) shows over a portrait.
-- Out: g<NNNN>.png (n-th page code, from the first frame on), logged "GPAGE <n> f<frame>".
local HANDLER = 0x080272B8
local delay = DELAY or 4
local n, due = 0, {}

L.on_exec(HANDLER, HANDLER, function()
  due[#due + 1] = L.frame + delay
end)

L.on_frame(function(f)
  while due[1] and due[1] <= f do
    table.remove(due, 1)
    n = n + 1
    L.shot(string.format("g%04d.png", n))
    L.log(string.format("GPAGE %d f%d", n, f))
  end
end)
