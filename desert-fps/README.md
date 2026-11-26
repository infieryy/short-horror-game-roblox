# Desert FPS

Stylized tactical FPS for Roblox. 1v1 / 2v2 duels.

## Game notes
- Stylized visuals (painterly anime watercolor)
- Buy guns, attachments, utility and armor
- 1v1, 2v2, duels
- Interactive environment (doors, breakable windows, destructible cover)
- Streaks / events
- Utility to gain an edge
- Tactical shooter
- Big map

## Map 1: Desert Village
One big walled village split into duel zones. Each round picks one zone and closes the rest (barriers / storm wall), so fights stay tight but the map feels big.

Zones (from `reference/concept/01-aerial-master.webp`):
- Gate
- Market Square (well)
- Cistern (underground)
- Dye Works
- Tea House
- Courtyard House
- Rooftops / Watchtower

### Style rules
- Walls: one colour family (peach, apricot, salmon pink, pale orange)
- Turquoise accent band at the bottom of ground-floor walls
- Flat base colour + few soft strokes, each one value step lighter/darker
- No painted shadows; lavender where light can't reach, never gray
- Fully matte, no shine
- Lighting: Future, lavender-blue OutdoorAmbient, sun slightly dimmed

## Reference
| Folder | Contents |
|---|---|
| `reference/concept` | Master aerial view + market street-level view |
| `reference/zones` | Eye-level target for each duel zone |
| `reference/kit` | Modular pieces: walls, doors, windows, beam ends, parapets, ladders, stairs, awnings |
| `reference/props` | Crates, barrels, pots, sacks, stall, cart, well, lantern, rug, spices |
| `reference/sky` | Background panorama, sky (not yet seamless), sandstorm |

Reference images are targets only. Final models and textures are built by code.

## Next steps
1. Grid plan (8-stud cells): zones, spawns, cover, routes, sightlines
2. Graybox script in Studio + playtest
3. Kit modeling, stroke-painted textures, lighting, set dressing, sky/map edge
