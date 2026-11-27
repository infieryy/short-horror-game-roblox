# Weapon animations

What a character's chest, head and arms do with each weapon. Eight animations, R15 only, 60 frames a second:

| Animation | Length | Loops | Plays |
|---|---|---|---|
| FPS Rifle Hold | 2.0 s | yes | while the rifle is in hand |
| FPS Rifle Fire | 0.15 s | no | on every shot |
| FPS Rifle Reload | 2.5 s | no | with the reload (the same length) |
| FPS Pistol Hold | 2.0 s | yes | while the pistol is in hand |
| FPS Pistol Fire | 0.13 s | no | on every shot |
| FPS Pistol Reload | 1.75 s | no | with the reload |
| FPS Knife Hold | 2.67 s | yes | while the knife is in hand |
| FPS Knife Slash | 0.53 s | no | on every slash |

They move the chest, head and arms only. The hips and legs are left out of the files, so a character goes
on walking underneath.

## Files

- `fps_*.rbxmx`: the animations as Roblox KeyframeSequences. `build/11_import_animations.luau` loads them
  into the place.
- `fps_*.rbxm`: the same, in the binary format the upload takes.
- `Desert FPS Weapons (work).blend`: the Blender file they were made in, with every animation in it.
  A copy, and one `.blend` per animation, is in the kit: `Desktop/Roblox Animation Kit/Packs/Desert FPS Weapons/`.

## How they were made

With the owner's "Roblox Animation Kit" (its rig, its reference animations, its export add-on), in Blender 4.5.

- The weapon models (`assets/out/<weapon>/<weapon>.obj`) were put in the rig's right hand exactly as Roblox
  holds a Tool: at the hand's grip point, turned by the Tool's grip.
- **Rifle and pistol:** the weapon is placed where it should be (level, pointing forward) and the arms are
  solved to it: the right hand on the grip, the left on the handguard or wrapped round the pistol. The
  shoulders start from the kit's fighter guard. A blocky R15 arm cannot reach a rifle's handguard with the
  chest square on, so the chest is turned 32 degrees to the right and the head turned back.
- **Knife:** the hold is the kit's "Combat Idle" guard and the slash its "Punch Right", from the chest up.
  The blow lands 8 frames in instead of 13, because the game decides the hit at the click.
- How each weapon sits in the hand is worked out from its hold pose and written to `WeaponConfig` (`Hand`).
  Change a hold and that number has to be worked out again.

## Uploaded

A published game can only play animations that are uploaded to Roblox. All eight were uploaded to the
owner's account on 2026-11-27 (the owner said yes), and all were approved. The ids are in
`AnimationConfig.Ids`:

| Animation | Asset id |
|---|---|
| FPS Rifle Hold | 83028381190337 |
| FPS Rifle Fire | 96286693108659 |
| FPS Rifle Reload | 124740467076400 |
| FPS Pistol Hold | 108605858556304 |
| FPS Pistol Fire | 137279406699731 |
| FPS Pistol Reload | 126204687311857 |
| FPS Knife Hold | 108323231141444 |
| FPS Knife Slash | 78142187319149 |

To change one: export it from Blender again, load it with `build/11_import_animations.luau`, set its id to
0 in `AnimationConfig` (Studio then plays the stored sequence), and test. To upload it, save the
KeyframeSequence as a binary `.rbxm` and send it to the Open Cloud Assets API as asset type `Animation`.
The API refuses the `.rbxmx` form. An upload is a new asset with a new id; ask the owner first.
