-- Page viewer: one proof shot per page of a chained message (tools/pageview.py), phase-8 visual QA.
-- Run after warp.lua (script_039, HOLD huge so warp never stops the run) and msgview.lua (MSG = the chain):
--   LO       CPU address of the chain in the QA ROM (the engine's pre-pass reads it: pages count from then on)
--   EXPECT   number of page codes ({page}/{clr}) in the chain
--   DELAY    frames from the page code's handler to the shot (default 4)
--   IDLE     frames with no page code before pressing A (default 400; a {clr} can wait for a button)
-- Shown through script 39, a page does not wait for a button: the FD/FE handler (0x080272B8, jump table
-- 0x0802717C) runs right after the page's last glyph, the glyph is on screen 2-3 frames later, and the box is
-- cleared about 6 frames after the handler (work/qa/dbg/fd.png, 2026-11-15). So the shot is taken DELAY frames
-- after each handler run: p<NNNN>.png, logged "PAGE <n> f<frame>". "PAGES_DONE <n>" after the EXPECT-th page;
-- "PAGES_STALL" if no page code runs for 3000 frames.
local HANDLER = 0x080272B8
local delay = DELAY or 4
local started, n, due, lastAt, done = false, 0, {}, nil, false

L.on_read(LO, LO, function()
  if not started then
    started = true
    lastAt = L.frame
    L.log(string.format("CHAIN f%d", L.frame))
  end
end)

L.on_exec(HANDLER, HANDLER, function()
  if not started or done then return end
  due[#due + 1] = L.frame + delay
  lastAt = L.frame
end)

L.on_frame(function(f)
  if done or not started then return end
  while due[1] and due[1] <= f do
    table.remove(due, 1)
    n = n + 1
    L.shot(string.format("p%04d.png", n))
    if n == 1 then L.shot("scene.png") end
    L.log(string.format("PAGE %d f%d", n, f))
    if n == EXPECT then
      done = true
      L.log("PAGES_DONE " .. n)
      L.finish(0)
      return
    end
  end
  -- a {clr} in cutscene and item-help strings waits for a button even here: press A when no page code has run
  -- for IDLE frames (far past the previous page's shot, so the press never lands before a shot)
  local idle = IDLE or 400
  if f - lastAt >= idle and (f - lastAt) % idle == 0 then
    L.press("a", 6)
  end
  if f - lastAt > 3000 then
    done = true
    L.log(string.format("PAGES_STALL f%d after %d pages", f, n))
    L.finish(0)
  end
end)
