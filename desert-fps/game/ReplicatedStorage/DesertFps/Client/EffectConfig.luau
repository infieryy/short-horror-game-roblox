--!strict
-- How shots look (Client/Effects). Everything here is made to match Valorant, from Riot's own slow-motion
-- frames of a rifle shot to the head (assets/vfx/REFERENCE.md says what each frame shows):
--   the flash    a thin-spiked star, its upright spike the tallest, in an orange glow, with a red beam across
--                the muzzle that outlives the star. About three frames.
--   the tracer   a thin pale line from the muzzle all the way to where the shot lands, there for one frame.
--   the spark    where the shot lands, at once: a small white star, then a grey puff.
--   a body hit   when the server says so: a pale core in orange, ringed with crimson blobs.
--   a head hit   a pale flame that stands up from the hit, reddens and is eaten away, with a white glint at
--                its foot. It stays on the head as the head moves.
-- The owner, on two earlier versions that were drawn from memory: "you're just making vfx up. Make it exactly
-- like valorant, minimal differences".
-- Each image is a sheet of sixteen frames drawn by assets/vfx/flipbooks.py and uploaded (Image is its asset).
-- Size is studs across a frame of the sheet, Time seconds to play it through, Glow how much it adds its light
-- to what is behind it (0 to 1), Near studs it is drawn nearer the eye than it is, so it is not sunk in what
-- it is on. Glow is kept low: the colour is in the drawing, and light added over this town's sunlit walls
-- turns any colour white (the owner on an earlier version: "too washed out ... white pale yellow").
-- Sizes are from the reference: the flash's star stands about an eighth of the screen high, a head hit about
-- two heads, a body hit about a head and a third.
return {
	Muzzle = {
		Image = 134196612509295,
		Time = 0.1,
		Glow = 0.1,
		Near = 0.25,
		-- By weapon. The star itself is about half as wide as its frame.
		Size = { rifle = 0.9, pistol = 0.75 },
		Light = { Range = 10, Brightness = 2.5, Color = Color3.fromRGB(255, 150, 70), Time = 0.05 },
		-- Suppressed: no flash, a wisp of smoke that grows From and To across and is gone in Time.
		Quiet = { From = 0.12, To = 0.4, Time = 0.16, Color = Color3.fromRGB(226, 216, 232), Start = 0.55 },
	},

	-- The line: Wide at the muzzle, Thin where it lands and Fade see-through there. A shot that lands nearer
	-- than Least has none.
	Tracer = {
		Image = 71134728944059,
		Time = 0.045,
		Glow = 0.15,
		Wide = 0.14,
		Thin = 0.05,
		Fade = 0.25,
		Least = 5,
	},

	Spark = { Image = 95683785238525, Time = 0.22, Glow = 0.2, Near = 0.4, Size = 2.2 },

	Struck = {
		body = { Image = 76832780576017, Time = 0.32, Glow = 0.05, Near = 1.2, Size = 2.4 },
		-- Foot: the hit is this far below the middle of the frame, as a share of half its height.
		head = { Image = 100954136247399, Time = 0.42, Glow = 0.1, Near = 1.2, Size = 3, Foot = 0.8 },
		-- A burst rides the part of a body nearest where it landed, if one is within this many studs.
		Reach = 1.5,
	},
}
