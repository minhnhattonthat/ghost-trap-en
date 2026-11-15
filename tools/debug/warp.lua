-- Ghost Trap (GBA) debug warp: boot cold, reach the title, then put the game in scene SCENE (tools/debug/scenes.lua).
-- Run through tools/debug/warp.py (it passes scenes.lua first). Globals:
--   SCENE='name'        required (a SCENES key or a family name: script_034, area_5E_r1, chapter_3, chapter_3b)
--   STATE_SAVE='abs'    save a Mesen state at the proof shot (the warp's arrival + hold)
--   KEEP=1              keep running after the proof shot (until emu.py --frames), pressing A every `mash`
--                       (default 45) frames to click through the scene
--   LIMIT=N             fail if the scene is not reached by frame N (default 9000)
-- Log lines: "TITLE f<n>", "WARP f<n> ...", "SCENE_OK <name> f<n> <detail>", "SHOT scene.png f<n>".
-- RAM map and the reasoning: docs/re/debug.md.
local M = emu.memType.gbaMemory
local MODE, NEXT, SUB = 0x03003100, 0x03003102, 0x03003104
local PHASE, SCRIPT = 0x03004A75, 0x03004A77
local ACT, CNT, FLAG_D, MAINGAME = 0x03004A8A, 0x03004A8C, 0x03004A8D, 0x03004A8E
local ROOM, AREA = 0x03003715, 0x03003719
local CUT_SUB1 = 0x08024340   -- mode 8 sub-state 1 entry: the story machine has chosen the script
local FLOOR_LOAD = 0x080038A0 -- floor loader, after it stored the area id at 0x03003719
local GLYPH = 0x0802795E      -- text renderer reads a character

local name = assert(SCENE, "set --var \"SCENE='name'\"")
local sc = SCENE_LOOKUP and SCENE_LOOKUP(name)
if not sc then error("unknown scene " .. name .. " (tools/debug/scenes.lua)") end
local limit = LIMIT or 9000
local hold = sc.hold or 150

local function r8(a) return emu.read(a, M) end
local function r16(a) return emu.read16(a, M, false) end
local function w8(a, v) emu.write(a, v, M) end
local function w16(a, v) emu.write16(a, v, M) end

local stage = "boot"        -- boot -> title -> warped -> arrived -> done
local titleRun, warpAt, arriveAt, stable = 0, nil, nil, 0
local swapped, glyphAt, storyScript, doored = false, nil, nil, false

local function arrive(detail)
  if stage ~= "warped" then return end
  stage = "arrived"
  arriveAt = L.frame
  L.log(string.format("SCENE_OK %s f%d %s", name, L.frame, detail or ""))
  if sc.after then
    local total = 0
    for step in sc.after:gmatch("[^;]+") do
      local n, spec = step:match("^%s*(%d+)%s+(%S+)%s*$")
      L.press(spec, tonumber(n))
      total = total + tonumber(n)
    end
    if hold < total + 30 then hold = total + 30 end
  end
end

-- cutscene: swap the script id once the story machine has run (it overwrites 0x03004A77 in sub-state 0)
L.on_exec(CUT_SUB1, CUT_SUB1, function()
  if stage ~= "warped" or sc.kind ~= "script" or swapped then return end
  if r8(SCRIPT) ~= 2 then return end
  w8(SCRIPT, sc.id)
  swapped = true
  L.log(string.format("WARP f%d script 2 -> %d", L.frame, sc.id))
end)

-- field: replace the area id the floor loader just stored, and the room the room loader will use
L.on_exec(FLOOR_LOAD, FLOOR_LOAD, function()
  if stage ~= "warped" or sc.kind ~= "field" then return end
  w8(AREA, sc.area)
end)

-- story: note which script the story machine picks
L.on_write(SCRIPT, SCRIPT, function(_, v)
  if stage == "warped" and sc.kind == "story" then storyScript = v & 0xFF end
end)

L.on_exec(GLYPH, GLYPH, function()
  if stage ~= "warped" or glyphAt then return end
  if (sc.kind == "script" and swapped) or sc.kind == "story" then glyphAt = L.frame end
end)

local function warp()
  stage = "warped"
  warpAt = L.frame
  local k = sc.kind
  if k == "title" then
    arrive("mode 2")
  elseif k == "mode" then
    w16(NEXT, sc.mode)
    L.log(string.format("WARP f%d mode %d", L.frame, sc.mode))
  elseif k == "script" or k == "field" then
    -- not-yet-started game (0x03004A8E = 0, act != 0): script 0-2 plays it (act 1); any other id goes to the field
    w8(MAINGAME, 0); w8(FLAG_D, 0); w8(ACT, 1); w8(PHASE, 0)
    w8(SCRIPT, k == "script" and 2 or 0xFE)
    w16(NEXT, 8)
    L.log(string.format("WARP f%d %s", L.frame, k == "script" and ("script " .. sc.id)
      or string.format("area %02X room %d", sc.area, sc.room or 0)))
  elseif k == "story" then
    w8(MAINGAME, 1); w8(FLAG_D, 0); w8(ACT, sc.act); w8(CNT, sc.cnt or 0); w8(PHASE, sc.phase or 0)
    w16(NEXT, 8)
    L.log(string.format("WARP f%d story act %d cnt %d phase %d", L.frame, sc.act, sc.cnt or 0, sc.phase or 0))
  else
    error("bad scene kind " .. tostring(k))
  end
end

L.on_frame(function(n)
  local mode = r16(MODE)
  if stage == "boot" then
    if mode == 2 then
      titleRun = titleRun + 1
      if titleRun == 60 then stage = "title"; L.log("TITLE f" .. n) end
    else
      titleRun = 0
      -- skip logos and the intro crawl: start every 90 frames until the title shows
      if n > 300 and n % 90 == 0 and r16(NEXT) ~= 2 then L.press("start", 6) end
    end
  end
  if stage == "title" then warp() end
  if stage == "warped" then
    local k = sc.kind
    if k == "mode" and mode == sc.mode then
      stable = stable + 1
      if stable == (sc.stable or 30) then arrive("mode " .. mode) end
    elseif k == "script" and glyphAt then
      if r8(SCRIPT) ~= sc.id or mode ~= 8 then L.fail(string.format("script %d not playing (script %d mode %d)", sc.id, r8(SCRIPT), mode)) end
      arrive(string.format("script %d, first glyph f%d", sc.id, glyphAt))
    elseif k == "field" and mode == 9 and r8(AREA) == sc.area then
      -- the floor loader picks the room from the player's position; another room is reached by a fake door
      stable = stable + 1
      if stable == 60 then
        if r8(ROOM) == (sc.room or 0) then
          arrive(string.format("area %02X room %d%s", sc.area, sc.room or 0, doored and " (door)" or ""))
        elseif not doored then
          doored = true
          w8(0x03003716, sc.room or 0)
          w8(0x03003710, 1)
          stable = 0
          L.log(string.format("WARP f%d door to room %d", n, sc.room or 0))
        end
      end
    elseif k == "story" and (glyphAt or ((mode == 9 or mode == 5) and n - warpAt > 30)) then
      arrive(string.format("story picked script %s, mode %d", storyScript and string.format("%d", storyScript) or "-", mode))
    end
    if n > limit then
      L.fail(string.format("scene %s not reached by frame %d (mode %d script %d area %02X room %d)", name, n, mode,
        r8(SCRIPT), r8(AREA), r8(ROOM)))
    end
  elseif stage == "boot" and n > limit then
    L.fail("title not reached by frame " .. n)
  end
  if stage == "arrived" and n == arriveAt + hold then
    L.shot("scene.png")
    L.log(string.format("SHOT scene.png f%d mode %d script %d area %02X room %d act %d", n, mode, r8(SCRIPT),
      r8(AREA), r8(ROOM), r8(ACT)))
    stage = "done"
    if KEEP then MASH = sc.mash or 45 end  -- click through the rest of the scene
    if STATE_SAVE then
      L.save_state(STATE_SAVE, function() if not KEEP then L.finish(0) end end)
    elseif not KEEP then
      L.finish(0)
    end
  end
end)
