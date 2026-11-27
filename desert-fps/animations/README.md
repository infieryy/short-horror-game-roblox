# Weapon animations

Twenty animations, R15 only, 60 frames a second. Eight ("FPS ...") are for the character everyone sees.
Twelve ("FPV ...") are for the arms in front of the player's own camera; see "First person" below.

What a character's chest, head and arms do with each weapon:

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

## First person

The arms in front of the camera are a plain R15 body of their own, hung off the camera, with only the
forearms and hands showing (0.6 studs thick instead of a body's full stud), in the player's own skin and
shirt. The weapon sits in its right hand with the same grip as on the character.

| Animation | Length | Plays |
|---|---|---|
| FPV Rifle Idle, FPV Pistol Idle, FPV Knife Idle | 2.0 s, 2.0 s, 2.67 s, looping | while the weapon is in hand |
| FPV Rifle Equip, FPV Pistol Equip, FPV Knife Equip | 0.8 s, 0.5 s, 0.4 s | when it is drawn (the weapon's EquipTime) |
| FPV Rifle Fire, FPV Pistol Fire | 0.15 s, 0.13 s | on every shot |
| FPV Rifle Reload, FPV Pistol Reload | 2.5 s, 1.75 s | with the reload |
| FPV Knife Slash A, FPV Knife Slash B | 0.53 s each | on a slash, in turn: across, then back |

How they were made:
- In the same Blender file, through a camera ("FPCam") 4.1 studs up, where the player's eye is, 70 degrees
  top to bottom. The body is hidden except forearms and hands, and those are thinned to 0.6.
- Each key is a place and a tilt for the weapon in front of that camera, and the arms are solved to it. The
  chest is turned 32 degrees, as in the character's rifle hold, so the left arm reaches.
- **The owner picked the framing:** the rifle 0.55 right, 0.52 down and 1.0 ahead of the eye, the left forearm
  coming in from the bottom left to under the handguard, nearly straight.
- The style follows Valorant's: a quick draw that overshoots and settles, a reload in clear beats (tip the
  weapon, magazine out, away, a new one in with a push, rack the bolt, back), one crisp jolt per shot.
- The magazine and the bolt are not in the animation. The game moves them at set points of the reload
  (`WeaponConfig`, `View.Magazine` and `View.Bolt`): change the reload's timing and those have to follow.
- Solve the poses with no action on the armature, then key them. The solver clears the action, and keys set
  with none assigned go into a stray action.

## Uploaded

A published game can only play animations that are uploaded to Roblox. All twenty were uploaded to the
owner's account on 2026-11-27 (the owner said yes both times), and all were approved. The ids are in
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
| FPV Rifle Idle | 111039337689658 |
| FPV Rifle Equip | 85685273923057 |
| FPV Rifle Fire | 106892581186919 |
| FPV Rifle Reload | 71514583960293 |
| FPV Pistol Idle | 126691491055902 |
| FPV Pistol Equip | 108763930015179 |
| FPV Pistol Fire | 123277761668379 |
| FPV Pistol Reload | 108603579052641 |
| FPV Knife Idle | 132308344203954 |
| FPV Knife Equip | 75892368916750 |
| FPV Knife Slash A | 105972440774537 |
| FPV Knife Slash B | 90002196614241 |

To change one: export it from Blender again, load it with `build/11_import_animations.luau`, set its id to
0 in `AnimationConfig` (Studio then plays the stored sequence), and test. To upload it, save the
KeyframeSequence as a binary `.rbxm` and send it to the Open Cloud Assets API as asset type `Animation`.
The API refuses the `.rbxmx` form. An upload is a new asset with a new id; ask the owner first.
