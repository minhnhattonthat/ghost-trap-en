# Glossary - Ghost Trap

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.
`tools/batches.py check` enforces the tables (a JP term present -> its EN form must appear; Avoid spellings fail).

## Rulings (asked of the user once; options and reasons in docs/decisions.md)
- Honorifics: kept, hyphenated (Johannes-san). Name order: Western (given name first).
- Romanisation source: official English names where they exist, else an earlier fan patch, else Hepburn without macrons.
  Ghost Trap had no English release and no earlier patch: names are Hepburn, or the obvious Western name a katakana
  name transcribes (ジョージ George, アリシア Alicia), or the real-world source (Babylonian month names, alchemy terms).
- Credits: English.
- Register / flavour (D8): casual, modern American English for the cast; George is a cocky young ghost hunter who
  narrates in first person ("I"); spooky, slightly wry narration. Sound effects: English onomatopoeia ("Bang!",
  "Creak..."). Hiragana-heavy JP (the game writes for kids) -> plain words, short sentences, no archaic spelling.
- Abbreviations: full names and terms everywhere, prefer engine changes over shortening.

## Limits (measured, phase 5; tools/windows.json, docs/re/text.md "Width gate")
- Dialogue / field box: 2 lines per page, 224 px per line. Name plate: 80 px. Narration: 2 lines, 224 px.
  Item help box: 3 lines, 152 px. Item names: 152 px (also inserted into box lines by {name:0A}).
- Widths (tools/font.py): most letters and digits 8 px; I i j l , . ' : ; ! - and space 4 px; — 12 px; ~ 16 px.
  About 28-34 characters per box line. Characters available: A-Z a-z 0-9 space ! ? , . : ; ' " ( ) - — & / % ~ #.
- Keep every {page} and {clr} where the Japanese has them ({clr} also advances the cutscene picture); add pages with
  {page} only inside a run that has no picture change. `tools/wrap.py` wraps page bodies and adds the pages.

## Style rules
- Punctuation map: 「」 after a name plate -> dropped (the plate marks speech); 「」 inside narration -> "...";
  『』 -> '...' for titles/names, "..." for quoted speech; ・・・ / … -> ... ; ！？ -> ?! ; ～ -> ~ only for a
  drawled sound, else dropped; （） -> ( ). One space after . ! ? when a sentence follows on the same line.
- George (ジョージ, オレ): brash, sarcastic, talks to himself a lot while examining things ("Huh.", "Seriously?").
  Alicia (アリシア): his childhood friend, sharp-tongued, sceptical of ghost hunting. Karol (カロル): a nervous
  tourist who came to gawk at the haunted house; polite (です/ます) -> politer, hesitant English.
  ???? (？？？？): an unseen voice; keep it fragmentary and eerie.
- Field examine text ({box:01}, 3C55C/3FF00): short, wry observations; vary the stock openers ("There's a...",
  "A ... sits here.") instead of repeating one form.

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ジョージ | George | 80px | hero, ghost hunter, narrator (オレ = I) | |
| アリシア | Alicia | 80px | George's childhood friend | Alisha |
| カロル | Karol | 80px | a man who came to see the ghost house | Carol |
| アリギエリ | Alighieri | | the late artist who owned the mansion (氏 = Mr. Alighieri) | |
| シンファ | Shinfa | 80px | | |
| アルビノ | Albino | 80px | | |
| 死のつかい | Reaper | 80px | name plate; in prose "messenger of death" | |
| アトラハシス | Atrahasis | | | |
| アンジェリカ | Angelica | | | |
| グレゴリ | Gregori | | | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ゴーストハウス | ghost house | | the haunted mansion's nickname | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| ゴースト | ghost | | | |
| ゴーストハント | ghost hunting | | | |
| ひょうい | possess | | possession / possessed; ghost possessing George; ひょうい時間 = possession time | |
| ガラクタ | junk | | | |
| ワナ | trap | | | |
| タリスマン | Talisman | | | |
| アミュレット | Amulet | | | |
| エルダー | Elder | | エルダーのえだ = Elder Branch | |
| バーベイン | Vervain | | herb | |
| フラックス | Flax | | herb | |
| カモミール | Chamomile | | herb | |
| エリクシール | Elixir | | | |
| アタノール | Athanor | | alchemist's furnace | |
| マグネトロン | Magnetron | | | |
| サプレッサー | Suppressor | | | |
| クリティカル | Critical | | | |
| ゴーストセンサー | Ghost Sensor | | | |
| センサー | sensor | | | |
| トランシーバー | transceiver | | | |
| ジュークボックス | jukebox | | | |
| 魔道書 | grimoire | | | |
| ニサン / ニサンの書 | Nisan | | Babylonian month; ～の書 = Book of Nisan | |
| アイヤル | Iyyar | | | |
| シマヌ | Simanu | | | |
| ドゥウズ | Duuzu | | | |
| アブ | Abu | | | |
| ウルル | Ululu | | | |
| テシュリトゥ | Teshritu | | | |
| アラフシャム | Arahsham | | | |
| キスリム | Kislim | | | |

## Decisions from earlier batches
- (none yet)
