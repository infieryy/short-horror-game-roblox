# What Valorant's shot effects look like

Written from Riot's own material, looked at frame by frame on 2026-11-28 (twice: the second time after the
owner said of the first drawing "The VFX is still really bad. Redraw the flipbooks from scratch ... use
multiple valorant references"). The sheets in `out/` are drawn to this by `flipbooks.py`. None of Riot's
pictures are kept in the repo.

## Sources

1. **Riot, "How the VALORANT Arsenal was built"** (playvalorant.com/en-us/news/dev/how-the-valorant-arsenal-was-built).
   Its picture `muzzle-flash-concepts.jpg` is the concept sheet for every gun's flash, each drawn twice: as
   the holder sees it and as others see it. White on grey, so it is shape only.
2. **Riot, "The State of Hit Registration"** (playvalorant.com/en-us/news/dev/the-state-of-hit-registration).
   Three slow-motion clips at 30 ms a frame and eight stills, all of one rifle, first person, on an orange
   brick wall:
   - clip 1 (60 frames): a head shot. Frames 33 to 36 are the flash, 33 to 35 the landing, 36 to 43 the
     head hit.
   - clip 2 (31 frames): a miss past the head. Frames 18 to 20 the flash, 18 to 22 the landing.
   - clip 3 (54 frames): a body shot at range. Frame 25 the flash, 26 to 28 the body hit.
   - stills: the flash and tracer at full size; the head hit's first frame; the body hit twice.
3. **RealTimeVFX forum, "Stylised Weapon VFX - Khaotic's Sketchbook"** (realtimevfx.com/t/27017): a
   breakdown of the pistol's flash, with four in-game frames, and the black-and-white mask of a burst.
4. **PC Gamer, "Here's how to read Valorant's hit effects following the latest patch"**: which effect means
   what, and that Riot made the head hit smaller in patch 1.07.

YouTube would not play without a sign-in (tried again the second time), so nothing here is from video.

## The style, which the first drawing missed

Everything is **flat, hard-edged and angular**. A shape is a cluster of long tapered blades (thin kites:
a point at the tail, widest a quarter of the way along, a long taper), every blade a different length and
width, never an even star. Colour is in flat bands: pale yellow in the middle, yellow, orange, red at the
tips. Nothing is a gradient. Light is a separate flat disc behind the shape. The forum's mask shows the same
thing: nested blades, each band a step of grey.

## The flash

- Concept sheet: each gun has its own silhouette. The rifles: a cluster of blades with one thin blade
  standing far above the rest, and a long level blade forward.
- Clip 1 frame 33, clip 2 frame 18: the cluster, pale yellow in a big middle, blades going orange then red;
  a tall thin blade straight up; a thick level beam, pale down its middle, running forward three or four
  times the cluster's width; a wide flat orange light behind, about twice the cluster.
- Frame 34: the same, a little smaller.
- Frame 35: the blades have left the middle and are orange; the beam is thin and orange.
- Frame 36: four or five salmon blades to the forward side, and a thin pale arc in the air.
- The forum, on the pistol: "a unique shape ... rather than a perfect star pattern"; "the horizontal 'beam'
  section of the muzzle pushes more toward red"; the "explosion dies slightly before beam".

## The tracer

A strong yellow line from the muzzle all the way to where the shot lands, pale down its very middle, orange
at its edges, the same width all along, there for one frame (clip 1 frame 33, the still).

## Where the shot lands

- First frame: a small hard white star of five or so uneven points, about half a head across.
- Next two or three frames: a pale, half see-through puff about a head across, the star's middle still in
  it, opening and going.

## The hit on a head (clip 1 frames 36 to 43, and the still at six times its size)

It is not a flame. It is a pale fan thrown **up** from the hit:

- 36: pointed at its foot (just under the hit), widening to shoulders that flick out into a short spike
  each side, a tall broad spike in the middle. Flat pale yellow, a thin orange line round it, a tight vivid
  red light hugging that, a flat salmon patch behind. About two heads tall, a little over one wide.
- 37: wider. A white jagged star now sits on the hit itself, with dark red blades behind it to each side.
- 38 to 39: taller; the star and the red blades stay.
- 40 to 41: the fan narrows; the star is still there.
- 42: a thin pale streak; the patch is still there.
- 43: a faint stain and a few specks.

It stays on the head as the head moves (PC Gamer, on patch 1.07, which also made it smaller because at range
it hid the head).

## The hit on a body (clip 3 frames 26 to 28, two stills)

A compact burst about a head across: a blown-out pale middle, orange round it, a jagged red rim, a red light
behind. Three frames, then it breaks up. **The dark squares round it in the stills are Riot's debug
crosshair, not the effect**: the first drawing took them for crimson blobs and drew a ring of balls.

## What was not found

- A wall being hit, close up. The sheets use the landing star and puff for it.
- The flash as other players see it, in the game (the concept sheet has its shapes). The game here uses the
  holder's sheet for both.
- A suppressed shot.
