# Handoff: picking this up in a session on the PC

Everything so far was made in a cloud session that cannot reach Roblox Studio. This note is for a Claude session running on the PC that has Studio.

## Where things stand
| Area | State | Where |
|---|---|---|
| Game notes and style rules | written | `README.md` |
| Concept art (20 images) | done | `reference/` |
| Grid plan: 7 duel zones, fairness checks | done, not playtested | `plan/PLAN.md`, `plan/out/plan.json` |
| Asset pipeline and pilot pieces | done, never imported into Roblox | `assets/README.md`, `assets/out/` |

Pilot pieces in `assets/out/<piece>/`: `wall_plain`, `wall_window`, `wall_door`, `door`, `crate`, `barrel`, `rifle`, `pistol`, `knife`, `smoke`. Each folder has the whole mesh, a low-detail mesh, one 1024 px texture, and either breakable shards (`chunks/` + `.break.json`) or separate parts (`parts/` + `.parts.json`).

## Decisions already made
- Roblox tactical FPS, 1v1 and 2v2 duels. One big desert village split into duel zones; each round uses one zone.
- Painted anime-watercolour look. Every asset is a recipe (code builds the model and paints the texture). No generated models or textures.
- Scale: 1 unit = 1 stud. Walls are 8 x 12 x 1 studs. Guns share one scale (an 880 mm rifle is 3.3 studs).
- Walls and doors break into jagged pre-cut shards; crates and barrels shatter into debris.
- Weapons are not breakable. They are modular: separate parts, sockets for attachments, joints for rigging.
- Phone-friendly: 1024 px textures and low-detail meshes.

## First jobs in Studio, in order
1. **Import test.** Bring in `wall_plain`, `crate` and `rifle` (`.fbx`, exported at scale 0.01, or `.obj` at 1:1). Check that one wall is 8 x 12 studs and the rifle is 3.3 studs long. Fix the export scale in `assets/build.py` if not.
2. **Matte look.** Apply each piece's texture as a SurfaceAppearance colour map with full roughness and no metalness. Compare with `assets/out/preview.png`.
3. **Lighting.** Future lighting, lavender-blue OutdoorAmbient, warm lavender Ambient, sun slightly dimmed (see the style rules in `README.md`).
4. **Graybox.** Build the zones from `plan/out/plan.json` as grey parts with spawns and zone barriers, and playtest the timings.
5. **Break test.** Assemble one wall from its shards using `wall_plain.break.json` and remove the shards within a blast radius.

## Not verified anywhere yet
- Scale, axes and the matte look inside Roblox.
- The break data and the gun sockets and joints in use.
- Zone timings with real players or bots.

## Rebuilding assets
Only needed to change a piece. On any machine with Python:

```bash
pip install bpy pillow numpy
```

```bash
python3 desert-fps/assets/run.py
```
