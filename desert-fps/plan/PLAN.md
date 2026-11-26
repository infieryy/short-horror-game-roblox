# Desert Village: grid plan (v1)

![Town overview](out/town-overview.png)

## Layout
- **Grid:** 1 cell = 8 studs. Each zone is 28 x 28 cells (224 studs).
- **Town:** 3 x 3 districts plus a ring road and the town wall, 92 x 92 cells (736 studs across).
- **Rounds:** each round uses one duel zone. The streets into the other zones are closed with barriers (a storm wall or gates).
- **Fairness:** each zone's bottom half is the top half rotated 180°. Spawn A and spawn B get exactly the same routes, cover and timings. Decoration can still differ between the two halves.

| | West | Middle | East |
|---|---|---|---|
| **North** | Rooftops | Tea House | Caravan Yard (reserve) |
| **Middle** | Courtyard House | Market Square | Dye Works |
| **South** | Gate | Potters' Row (reserve) | Cistern (underground) |

The two reserve districts are placeholder housing blocks for now. Either can become an 8th or 9th zone later.

## Fairness checks
`planner.py` measures every zone with Roblox default movement: walk at 16 studs/s, climb ladders at about 11 studs/s.

| Check | Target | What it means |
|---|---|---|
| Meet time | 6-10 s | Earliest moment both teams can stand on the same spot |
| First sight | at least 3.5 s | Earliest moment a player from each team can see the other at eye level. This rules out spawn-to-spawn sightlines. |
| Longest sightline | at most 200 studs | Keeps long-range fights within reach of non-sniper weapons |
| Lanes | at least 3 | Separate routes from spawn A to spawn B |
| Reachable | all cells | No sealed-off pockets |

## Results

| Zone | Spawns | Meet | First sight | Longest sightline (studs) | Lane times A→B (s, * = uses roofs) | Low / high cover cells |
|---|---|---|---|---|---|---|
| Market Square | N / S | 7.33 s | 4.12 s | 192 | 14.45 / 14.74 / 20.04 | 2 / 44 |
| Tea House | W / E | 6.91 s | 4.41 s | 152 | 13.74 / 14.04 / 23.56* | 10 / 10 |
| Courtyard House | N / S | 7.41 s | 3.91 s | 190 | 14.36 / 24.45 / 24.45 | 8 / 28 |
| Dye Works | W / E | 6.00 s | 3.91 s | 192 | 11.91 / 12.62 / 14.54 | 2 / 12 |
| Cistern | N / S | 7.74 s | 4.21 s | 192 | 14.99 / 15.28 / 20.33 | 8 / 14 |
| Gate | N / S | 8.41 s | 6.41 s | 193 | 16.33 / 16.62 / 18.40 | 16 / 20 |
| Rooftops | W / E | 6.00 s | 4.21 s | 186 | 11.91 / 20.21* / 19.97* | 0 / 14 |

All 7 zones pass all checks.

## Zones

### Market Square
![Market](out/zone-market.png)

- An open plaza around the well, with a ring of stalls.
- A spice hall on one flank for close-quarters fights.
- A ladder to a 2-story roof that overlooks the plaza.
- This is the most exposed zone, with lots of high cover.

### Tea House
![Tea House](out/zone-teahouse.png)

- A big hall in the middle, split by a long counter. The doors are offset so you can't see straight through.
- A ring street runs around the hall.
- Stairs lead up to a raised terrace that connects to the hall roof, which gives a slower route over the roofs.

### Courtyard House
![Courtyard](out/zone-courtyard.png)

- A courtyard with a tree and a planter, surrounded by arcade wings full of doorways.
- Stairs and a ladder up to the gallery roof.
- Zig-zag side streets on both flanks.

### Dye Works
![Dye Works](out/zone-dyeworks.png)

- A workshop interior, a yard of dye vats, and rows of hanging cloth.
- The cloth can be walked through but blocks sight, so it's good for utility plays and ambushes.
- A roof terrace reached by stairs and a ladder.

### Cistern (underground)
![Cistern](out/zone-cistern.png)

- A hall of staggered pillars.
- Two shallow water channels that slow you down, with dry bridges across them.
- A well shaft in the middle.
- Spawns come down stairwells.

### Gate
![Gate](out/zone-gate.png)

- An inner wall splits the zone. The main gate is in the middle, with a side gate near each end.
- Stairs lead up to the wall-walk.
- Wagons in front of the gate block direct sight through it.

### Rooftops
![Rooftops](out/zone-rooftops.png)

- House blocks with walkable roofs, joined by plank bridges and ladders.
- Narrow alleys underneath.
- A central watchtower with a ladder.
- Two of the three lanes use the roofs.

## How to change a zone
1. Edit the zone's 14 rows in `zones.py`. You only draw the top half; the legend is at the top of the file.
2. Run:

   ```bash
   python3 planner.py
   ```

3. Look at `out/zone-<name>.png`. The red line is the earliest sight contact, the dashed line is the longest sightline, and the coloured lines are the lanes.

`out/plan.json` holds every zone as a full grid. The graybox builder will read it.

## Known limits of v1
- **Sightlines are only checked at eye level on the ground.** Roof-to-street and tower sightlines are not measured yet; check them in the graybox.
- **Heights are simplified.** One story is 12 studs, and roofs only connect to roofs of the same height. Parapets and dome shapes are not modelled.
- **Walls inside a cell are thin walls on the cell's edges.** The graybox builder will turn them into real walls with door and window gaps.
- **Timings are estimates.** Bot or friend playtests in the graybox are the real check.

## Next step
Build a Roblox Studio graybox from `out/plan.json`:
- grey parts for buildings, walls, cover and stairs
- barriers that open and close zones
- spawn points
- a zone picker for testing
