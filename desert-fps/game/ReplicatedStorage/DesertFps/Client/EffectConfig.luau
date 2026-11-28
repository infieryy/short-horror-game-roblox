--!strict
-- How shots look (Client/Effects). Everything here is made to match Valorant, from Riot's own pictures: its
-- muzzle flash concept sheet, three slow-motion clips and eight stills (assets/vfx/REFERENCE.md says what each
-- shows). Valorant's effects are flat, hard-edged clusters of long tapered blades in colour bands, yellow in
-- the middle, orange, red at the tips:
--   the flash    a cluster of blades with one thin blade standing far above the rest, a thick level beam, and
--                a flat orange light behind. About three frames; the blades leave the middle as it goes.
--   the tracer   a strong yellow line from the muzzle all the way to where the shot lands, for one frame.
--   the spark    where the shot lands, at once: a small hard white star, then a pale puff.
--   a body hit   when the server says so: a compact burst with a hot middle and a jagged red rim.
--   a head hit   a pale fan thrown up from the hit, edged orange with a red light round it, a white star on
--                the hit itself. It narrows to a streak. It stays on the head as the head moves.
-- The owner, on the versions before this one: "you're just making vfx up. Make it exactly like valorant,
-- minimal differences", then "The VFX is still really bad. Redraw the flipbooks from scratch ... use multiple
-- valorant references".
-- Each image is a sheet of sixteen frames drawn by assets/vfx/flipbooks.py and uploaded. Image is its asset's
-- number; to try a sheet in Studio before uploading it, copy it into Studio's content folder and give its
-- address instead ("rbxasset://claude_fx/fx_muzzle.png").
-- Size is studs across a frame of the sheet, Time seconds to play it through, Glow how much it adds its light
-- to what is behind it (0 to 1), Near studs it is drawn nearer the eye than it is, so it is not sunk in what
-- it is on. Glow is kept low: the colour is in the drawing, and light added over this town's sunlit walls
-- turns any colour white (the owner on an earlier version: "too washed out ... white pale yellow").
return {
	Muzzle = {
		Image = 113323198339887,
		Time = 0.1,
		Glow = 0.1,
		Near = 0.25,
		-- By weapon. The cluster of blades is about half as wide as its frame; the beam runs to its edge.
		Size = { rifle = 1.2, pistol = 1 },
		Light = { Range = 10, Brightness = 2.5, Color = Color3.fromRGB(255, 150, 70), Time = 0.05 },
		-- Suppressed: no flash, a wisp of smoke that grows From and To across and is gone in Time.
		Quiet = { From = 0.12, To = 0.4, Time = 0.16, Color = Color3.fromRGB(226, 216, 232), Start = 0.55 },
	},

	-- The line: Wide at the muzzle, Thin where it lands and Fade see-through there. A shot that lands nearer
	-- than Least has none.
	Tracer = {
		Image = 75872092952618,
		Time = 0.045,
		Glow = 0.2,
		Wide = 0.13,
		Thin = 0.09,
		Fade = 0.1,
		Least = 5,
	},

	Spark = { Image = 107694068321201, Time = 0.22, Glow = 0.15, Near = 0.4, Size = 1.6 },

	Struck = {
		-- The owner, on the body hit at 2 across: "make the body shot vfx smaller".
		body = { Image = 77151486929998, Time = 0.2, Glow = 0.05, Near = 1.2, Size = 1.4 },
		-- Foot: the hit is this far below the middle of the frame, as a share of half its height.
		-- Clear: how see-through the whole burst is, 0 to 1 (the owner: "a bit more transparent (slightly)").
		head = { Image = 116958428878519, Time = 0.26, Glow = 0.05, Near = 1.2, Size = 2.5, Foot = 0.5, Clear = 0.2 },
		-- A burst rides the part of a body nearest where it landed, if one is within this many studs.
		Reach = 1.5,
	},
}
