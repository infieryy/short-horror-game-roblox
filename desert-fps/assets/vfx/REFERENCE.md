# What Valorant's shot effects look like

Written from Riot's own material, looked at frame by frame on 2026-11-28. The sheets in `out/` are drawn to
this. None of Riot's pictures are kept here.

## Sources

- Riot, "The State of Hit Registration" (playvalorant.com/en-us/news/dev/the-state-of-hit-registration). Its
  first animated clip is a slow-motion rifle shot to the head of a strafing enemy, in first person, against an
  orange brick wall: 60 frames, 30 ms apart. Frames 33 to 43 are the shot. Its stills show the same hit burst
  large, and a body hit on a crouching enemy.
- RealTimeVFX forum, "Stylised Weapon VFX - Khaotic's Sketchbook" (realtimevfx.com/t/27017): a hobbyist's
  breakdown of Valorant's pistol flash, with three in-game frames and notes.
- PC Gamer, "Here's how to read Valorant's hit effects following the latest patch": which effect means what.

YouTube would have been the obvious source (slow-motion spray clips exist) but it would not play without a
sign-in, so nothing here is from video.

## The shot, frame by frame (Riot's clip)

| Frame | Muzzle | Tracer | Where the shot lands |
|---|---|---|---|
| 33 | A star at the muzzle: pale yellow middle, thin orange spikes of uneven length, the upright one much the tallest. A soft orange glow round it | A thin line from the muzzle all the way to the head: pale yellow, orange at its edges, a little thicker at the muzzle | A small white star at the line's end |
| 34 | The glow is at its widest (three star-widths), orange. The star keeps its tall upright spike. A thin red-orange beam lies level across the muzzle, far longer to the left | Gone | A grey, half see-through puff with the white star in its middle |
| 35 | Star and glow smaller; the beam shorter | | The puff spreads and thins; the star is small |
| 36 | A few small orange spikes, no glow | | The **hit burst** appears, a moment after the shot (it waits for the server): see below |

Notes from the forum breakdown, on the pistol: the burst is "a unique shape ... rather than a perfect star
pattern"; "the horizontal 'beam' section of the muzzle pushes more toward red"; the flash "is brighter in the
emissive and lighter in value in the center"; the "explosion dies slightly before beam". Its three frames show
a pale yellow middle, orange round it, and thin red spikes whose tips fade.

## The hit on a head (frames 36 to 43)

- 36: whole at once. A flame standing on the hit point: a tall middle tongue with a shorter one flaring from
  each shoulder, tapering to a point at its foot. Pale yellow, nearly white in the middle, a thin orange edge,
  a soft red glow outside. About twice as tall as a head. A faint thin white ring beside it.
- 37: a little larger.
- 38 to 39: it stretches upward and turns orange. A white four-pointed glint sits at its foot.
- 40 to 41: holes eat it into a hooked wisp; it is salmon, then pink. The glint is still there.
- 42: a thin sliver and a few bits drifting up. The glint is gone.
- 43: a few orange specks.

It stays where the head was hit and moves with the head (PC Gamer, on patch 1.07). Riot made it smaller in that
patch because at long range it hid the head.

## The hit on a body (Riot's still)

A round burst about one and a third heads across: a pale yellow middle, orange round it, and six or so dark
crimson blobs round the rim. No frames of how it ends were found: the sheet has the blobs drift out and
shrink, which is a guess.

## What was not found

- A wall being hit, close up. The sheets use the landing spark for it, which Riot describes as showing "where
  your shots land".
- The flash and tracer as other players see them. Riot says the first-person and third-person flashes were
  made to differ; the game here uses the same sheet for both.
- A suppressed shot.
