--!strict
-- How shots look (Client/Effects): the flash at the muzzle, the tracer, what flies off a wall, and what a hit
-- on a body looks like. The reference is Valorant: a small sharp star of a flash that is gone in two frames,
-- a tracer that is a short streak racing to where the shot lands and not a line drawn all the way, and a hit
-- that bursts into angular shards, larger and white-hot with a flash for a head. Everything is drawn from
-- tapered beams and a little light: no picture was made or uploaded for it.
-- Lengths are studs, times seconds, speeds studs a second. A { low, high } pair is picked from each time.
return {
	-- The flash at the muzzle: spikes out to the sides and a longer one forward, round a small bright core,
	-- with a light that reaches the walls near by. Mine is how big the player's own is beside everyone else's:
	-- it sits a stud from the eye and must not hide what is being shot at.
	Muzzle = {
		Time = 0.05,
		Spikes = { 4, 5 },
		Long = { 0.5, 0.9 },
		Wide = { 0.16, 0.26 },
		Forward = { 1.2, 1.8 },
		ForwardWide = 0.3,
		Core = 0.28,
		Hot = Color3.fromRGB(255, 250, 226),
		Edge = Color3.fromRGB(255, 170, 60),
		Light = { Range = 12, Brightness = 3, Color = Color3.fromRGB(255, 206, 140) },
		Mine = 0.55,
		-- Suppressed: no flash, a wisp of smoke that grows From and To across and is gone in Time.
		Quiet = { From = 0.15, To = 0.55, Time = 0.16, Color = Color3.fromRGB(226, 216, 232), Start = 0.55 },
		-- By weapon: how big its flash is.
		Size = { rifle = 1, pistol = 0.7 },
	},

	-- The tracer: a streak Long that leaves the muzzle at Speed and ends where the shot does. Its head is Hot
	-- and Wide, its tail thin and clear. A shot that lands nearer than Least has none.
	Tracer = {
		Speed = 1100,
		Long = 14,
		Wide = 0.09,
		Least = 5,
		Hot = Color3.fromRGB(255, 244, 206),
		Tail = Color3.fromRGB(255, 188, 92),
	},

	-- What flies off where a shot lands on the town, by the mark it leaves (Client/BulletMarks): Count
	-- sparks, each a streak Long and Wide that leaves at Speed within Cone degrees of straight out, falls at
	-- Gravity and is gone in Life.
	Sparks = {
		["in"] = { Count = { 2, 3 }, Speed = { 14, 24 }, Life = { 0.1, 0.16 } },
		out = { Count = { 3, 5 }, Speed = { 18, 34 }, Life = { 0.12, 0.2 } },
		stop = { Count = { 4, 6 }, Speed = { 20, 40 }, Life = { 0.12, 0.22 } },
		Long = { 0.35, 0.8 },
		Wide = 0.05,
		Cone = 65,
		Gravity = 60,
		-- A spark off stone or plaster is hot; off anything else it is a chip of the stuff (MarkConfig's Rim).
		Hot = Color3.fromRGB(255, 226, 150),
	},

	-- A hit on a body: shards that burst from where the shot landed, back along the shot and outwards. A hit
	-- to the head is more of them, faster, white-hot, with a star of a flash Flash across.
	Struck = {
		body = {
			Count = { 6, 8 },
			Speed = { 10, 22 },
			Life = { 0.2, 0.32 },
			Long = { 0.45, 0.8 },
			Wide = { 0.16, 0.26 },
			Hot = Color3.fromRGB(255, 120, 96),
			Edge = Color3.fromRGB(214, 52, 58),
		},
		head = {
			Count = { 10, 13 },
			Speed = { 16, 34 },
			Life = { 0.24, 0.4 },
			Long = { 0.6, 1.1 },
			Wide = { 0.18, 0.3 },
			Hot = Color3.fromRGB(255, 252, 232),
			Edge = Color3.fromRGB(255, 196, 84),
			Flash = 1.5,
		},
		Cone = 80,
		Gravity = 34,
	},
}
