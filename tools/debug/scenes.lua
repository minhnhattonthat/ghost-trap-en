-- Ghost Trap (GBA) scene list for tools/debug/warp.lua. RAM map and how each kind works: docs/re/debug.md.
-- Every scene boots cold, waits for the title (mode 2), then warps. Kinds:
--   title                      the title screen, with optional `after` presses
--   mode   mode=N              request game mode N from the title (3 option, 4 title intro, 5 save, 6 load)
--   script id=N                start cutscene script N (0-126, table 0x3BFD8) through the game's own cutscene mode
--   story  act=A cnt=C phase=P let the story machine (mode 8 sub-state 0) pick the scene for that story state
--   field  area=A room=R       new field session in area A (0-135), room R, then optional `after` presses
-- Families (not listed one by one): script_NNN (0-126), area_AA_rR (hex area, decimal room; rooms per area in
-- tools/debug/areas.tsv), chapter_N (story act N, first scene), chapter_Nb (second scene).
-- Optional fields: after = route string run after arrival ("6 start;60 -"); hold = frames from arrival (first
-- glyph for script/story) to the proof shot, at least the `after` presses + 30 (default 150); mash = press A
-- every N frames after the proof shot when warp runs with KEEP (default 45); sav = save fixture in work/saves/;
-- stable = frames the requested mode must hold before arrival (default 30; mode 4 passes in a few frames).

SCENES = {
  title       = { kind = "title", hold = 400, note = "title screen, PRESS START" },
  title_menu  = { kind = "title", after = "600 -;6 start;150 -", note = "NEW GAME / CONTINUE / OPTION" },
  title_intro = { kind = "mode", mode = 4, stable = 1, hold = 210, note = "title intro (castle rising into the logo)" },
  option      = { kind = "mode", mode = 3, note = "OPTION: sound test, message speed" },
  save        = { kind = "mode", mode = 5, note = "SAVE GAME yes/no" },
  save_slots  = { kind = "mode", mode = 5, after = "6 a;150 -", note = "SAVE GAME slot list (after YES)" },
  save_pick   = { kind = "mode", mode = 5, after = "6 a;200 -;6 a;100 -", note = "SAVE GAME slot 1 picked" },
  save_confirm = { kind = "mode", mode = 5, after = "6 a;200 -;6 a;100 -;6 a;100 -", note = "SAVE GAME confirm box on slot 1" },
  save_write  = { kind = "mode", mode = 5, after = "6 a;200 -;6 a;100 -;6 a;100 -;6 a;300 -", note = "saves to slot 1; regen keeps the file as work/saves/slot1.sav" },
  load        = { kind = "mode", mode = 6, note = "LOAD GAME slot list" },
  load_slot1  = { kind = "mode", mode = 6, sav = "slot1", note = "LOAD GAME with slot 1 saved (needs work/saves/slot1.sav from save_write)" },
  load_confirm = { kind = "mode", mode = 6, sav = "slot1", after = "100 -;6 a;100 -", note = "LOAD GAME confirm box on slot 1" },
  load_game   = { kind = "mode", mode = 6, sav = "slot1", after = "100 -;6 a;100 -;6 a;100 -;6 a;600 -", note = "slot 1 loaded" },
  newgame     = { kind = "title", after = "600 -;6 start;150 -;6 a;600 -", note = "NEW GAME: opening cutscene (script 2) starts" },
  opening     = { kind = "script", id = 0, note = "intro crawl before the title" },
  fainted     = { kind = "story", act = 0, cnt = 0, phase = 0, note = "faint: back at the entrance (script 3)" },
  ending      = { kind = "story", act = 10, cnt = 9, phase = 0, note = "ending (script 33)" },
  credits     = { kind = "script", id = 34, hold = 600, note = "staff roll" },
  clear_a     = { kind = "script", id = 35, note = "post-clear message A" },
  clear_b     = { kind = "script", id = 36, note = "post-clear message B" },
  copyright   = { kind = "script", id = 37, note = "copyright screen" },
  field       = { kind = "field", area = 0x5E, room = 1, note = "game start: lounge (area 5E room 1)" },
  itemmenu    = { kind = "field", area = 0x5E, room = 1, after = "6 start;120 -", note = "item menu (USE tab, help line, map panel)" },
  itemmenu_use = { kind = "field", area = 0x5E, room = 1, after = "6 start;120 -;6 a;120 -", note = "item menu: USE picked" },
  menu_drop   = { kind = "field", area = 0x5E, room = 1, after = "6 start;120 -;6 right;60 -", note = "item menu: DROP tab" },
  menu_equip  = { kind = "field", area = 0x5E, room = 1, after = "6 start;120 -;6 right;60 -;6 right;60 -", note = "item menu: EQUIP tab" },
  menu_book   = { kind = "field", area = 0x5E, room = 1, after = "6 start;120 -;6 right;60 -;6 right;60 -;6 right;60 -", note = "item menu: BOOK tab" },
  book        = { kind = "field", area = 0x5E, room = 1, after = "6 start;120 -;6 right;60 -;6 right;60 -;6 right;60 -;6 a;150 -", note = "item menu: BOOK opened" },
  menu_combine = { kind = "field", area = 0x5E, room = 1, after = "6 start;120 -;6 right;60 -;6 right;60 -;6 right;60 -;6 right;60 -", note = "item menu: COMBINE tab" },
  map         = { kind = "field", area = 0x5E, room = 1, after = "6 select;120 -", note = "Select: menu with the map panel" },
}

-- Families: resolve a name like script_034, area_5E_r1, chapter_3, chapter_3b.
function SCENE_LOOKUP(name)
  if SCENES[name] then return SCENES[name] end
  local n = name:match("^script_(%d+)$")
  -- cutscenes (0-38, and 107-108: a dialogue that types out from a black screen) fade in slowly: shoot 120 frames
  -- after the first glyph; field messages (other 39+) can close by then
  if n then
    local id = tonumber(n)
    local slow = id < 39 or id == 107 or id == 108
    return { kind = "script", id = id, hold = slow and 120 or 45 }
  end
  local a, r = name:match("^area_(%x%x)_r(%d+)$")
  if a then return { kind = "field", area = tonumber(a, 16), room = tonumber(r), hold = 90 } end
  local c, b = name:match("^chapter_(%d+)(b?)$")
  if c then
    c = tonumber(c)
    if c >= 1 and c <= 9 then
      if b == "b" then return { kind = "story", act = c, cnt = c, phase = 1 } end
      return { kind = "story", act = c, cnt = c - 1, phase = 0 }
    end
  end
  return nil
end
