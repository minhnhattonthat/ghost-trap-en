# Debug warp: RAM map and how each scene kind works

Tool: `tools/debug/warp.py` (wrapper) + `tools/debug/warp.lua` (Mesen) + `tools/debug/scenes.lua` (scene list).
Every scene boots cold with a blank save, waits for the title, pokes RAM, and lets the game's own code load the
scene. No savestate or user save is needed. All addresses below were found on the original dump (`rom.sha1`).

```
python -X utf8 tools/debug/warp.py SCENE [--rom build/ghost_trap_en.gba] [--state] [--keep --frames 6000]
python -X utf8 tools/debug/warp.py --list [--families]
python -X utf8 tools/debug/warp.py --all [--only REGEX] [--jobs 4] [--state]
```

## RAM map (verified by poking and watching the screen)

| Address | Size | Meaning |
|---|---|---|
| `0x03003100` | u16 | game mode (current). 1 logos, 2 title + main menu, 3 OPTION, 4 title intro, 5 SAVE GAME, 6 LOAD GAME, 7 title transition, 8 cutscene/story, 9 field. Handlers: table `0x080F729C` |
| `0x03003102` | u16 | requested mode; the main loop (`0x08000284`) switches when it differs and clears the sub-state |
| `0x03003104` | u16 | sub-state of the current mode (mode 8: table `0x08039860`; sub-state 0 is the story machine) |
| `0x03004A75` | u8 | cutscene phase (0 before a story scene, 1 after; read by the story machine) |
| `0x03004A77` | u8 | script id: index into the script pointer table at ROM `0x3BFD8` (127 entries; text loaded at `0x080268F4`) |
| `0x03004A80` | 0x200 | persistent story block = the save file (EEPROM 512 B: bytes 0-1 checksum, 2-9 `backupok`, then this block from +0x0A) |
| `0x03004A8A` | u8 | act 0-10 (story machine switch `0x080238D4`): 0 faint/return, 1-9 acts, 10 ending |
| `0x03004A8C` | u8 | story counter inside the act |
| `0x03004A8D` | u8 | flag; non-zero skips the act switch (left 0 by the warp) |
| `0x03004A8E` | u8 | 0 = game not started (opening scripts 0-2), 1 = main game (act switch), 2/3 = scripts 30/31 |
| `0x03003710` | u8 | door taken this frame (1); the field then loads room `[0x03003716]` |
| `0x03003715` | u8 | current room in the area |
| `0x03003716` | u8 | room to load (door target, or the room the floor loader found under the player) |
| `0x03003719` | u8 | current area 0-135 (ROM table `0x0854407C`, offsets relative to it; block copied to IWRAM `0x03001900`, 0x17FF bytes; room count = u32 at block +0x34, room pointers from +0x38) |
| `0x030037AF` | u8 | cell index into the EWRAM area grid `0x02030000` (u16 cells, low byte = area id) |

Code points the warp hooks: `0x08024340` (mode 8 sub-state 1 entry: the script id is final), `0x080038A0` (floor
loader, right after it stored the area id), `0x0802795E` (text renderer reads a character: "text is on screen").

## Story machine (mode 8, sub-state 0, `0x08023890`)

With `0x03004A8E = 1`, act A picks a script from the counter and phase (measured for acts 0-10, counters 0-9):

| Act | counter, phase -> script |
|---|---|
| 0 | any -> 3 (faint: "back at the entrance") |
| 1-8 | A-1, 0 -> 2A+2; A, 1 -> 2A+3 (scripts 4-19) |
| 9 | 8, 0 -> 28; 9, 1 -> 29 |
| 10 | any, 0 -> 33 (ending) |

Other combinations give script `0xFF`: phase 0 goes to SAVE GAME (mode 5), phase 1 to the field (mode 9).
With `0x03004A8E = 0` and act != 0, scripts 0-2 play (new game), any other id goes straight to the field.
After a cutscene ends the game goes to SAVE GAME (mode 5), then the field.

## Scene kinds (scenes.lua)

- **title**: wait until mode 2 has held for 60 frames (Start is pressed every 90 frames before that to skip the
  logos and the intro crawl). PRESS START accepts input ~450 frames later, hence `600 -` before menu presses.
- **mode N**: request mode N from the title. SAVE GAME needs four A presses to write (YES, slot, box, confirm);
  LOAD GAME two (box, confirm). `save_write` produces `work/saves/slot1.sav`, which the `load_*` scenes boot with.
- **script N**: from the title set act 1, 0x8E = 0, script 2 and request mode 8 (the new-game path); on entry to
  sub-state 1 swap the id 2 -> N. Arrival = first glyph drawn while script N plays. Proven so far for scripts
  0-23, 34, 37 and 39 (39+ are field messages; they show in the cutscene window); the rest wait for `--all`.
- **story act/cnt/phase**: set the story block and request mode 8; the game picks the scene. `chapter_N` = act N,
  counter N-1, phase 0 (the act's first story scene); `chapter_Nb` = the second.
- **field area/room**: same new-game path with script `0xFE` (goes to the field); the floor-loader hook replaces the
  area id. The floor loader picks the room from the player's position (`0x08003A2C`), so a room other than that one
  is reached with a fake door (`0x03003716` = room, `0x03003710` = 1) once the area has loaded.

## Limits and leads

- Inventory is the new-game one: BOOK opens empty, no grimoire pages. Item/book warps need the inventory layout
  (next lead: watch writes when an item is picked up, script 39 "を入手した").
- Field rooms are entered at the floor loader's default spot or a fake door; the player can stand in an odd place.
- Field text (examine messages, pointer tables `0x3C55C`, `0x3FF00`, `0x41F18`) is reached by playing in a room;
  the area warps get there, triggering each message is phase-8 work (text coverage).
- Mode 4 is the title intro, not a game-over screen. There is no game over: running out of life plays the faint
  scene (act 0, script 3).
