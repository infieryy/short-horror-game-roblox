--!strict
-- How shots look (Client/Effects): the flash at the muzzle, the tracer, what flies off a wall, and what a hit
-- on a body looks like. The reference is Valorant: a small sharp burst of a flash out of the barrel that is
-- gone in two frames, a tracer that is a short streak racing to where the shot lands and not a line drawn all
-- the way, and a hit that bursts into angular shards, more of them and with a flash for a head.
-- The colours are orange and red, saturated. The owner on the first version, which was white-hot with a
-- yellow edge: "too washed out ... I need it to be more pop! with orange effects like valorant", "smaller",
-- and for the head "orange and red in the core rather than white". Everything is drawn from
-- tapered beams and a little light: no picture was made or uploaded for it.
-- Lengths are studs, times seconds, speeds studs a second. A { low, high } pair is picked from each time.
-- Glow is how much a thing adds its light to what is behind it (0 to 1): hot things glow, and things with a
-- colour of their own do not, or the town's sunlit walls wash that colour out to white.
return {
	-- The flash at the muzzle: a burst out of the barrel. Spikes lean forward round a longer one straight
	-- ahead, each orange outside (Edge) and amber inside (Hot), from a small core at the barrel's end, with a
	-- light that reaches the walls near by. It stays on the barrel while it shows.
	Muzzle = {
		Time = 0.05,
		Spikes = { 4, 5 },
		Long = { 0.3, 0.55 },
		Wide = { 0.13, 0.2 },
		-- How far forward the side spikes lean: 0 is straight out to the sides, 1 is halfway to straight ahead.
		Sweep = 0.9,
		Forward = { 0.6, 0.95 },
		ForwardWide = 0.22,
		-- The amber inside of a spike is this share of its width.
		Inner = 0.5,
		Core = 0.15,
		Glow = 0.25,
		Hot = Color3.fromRGB(255, 182, 48),
		Edge = Color3.fromRGB(255, 92, 16),
		Light = { Range = 10, Brightness = 2.5, Color = Color3.fromRGB(255, 150, 70) },
		-- Suppressed: no flash, a wisp of smoke that grows From and To across and is gone in Time.
		Quiet = { From = 0.12, To = 0.4, Time = 0.16, Color = Color3.fromRGB(226, 216, 232), Start = 0.55 },
		-- By weapon: how big its flash is.
		Size = { rifle = 1, pistol = 0.75 },
	},

	-- The tracer: a streak Long that leaves the muzzle at Speed and ends where the shot does. Its head is Hot
	-- and Wide, its tail thin and clear. A shot that lands nearer than Least has none.
	Tracer = {
		Speed = 1100,
		Long = 14,
		Wide = 0.15,
		Least = 5,
		Glow = 0.25,
		Hot = Color3.fromRGB(255, 190, 70),
		Tail = Color3.fromRGB(255, 104, 22),
	},

	-- What flies off where a shot lands on the town, by the mark it leaves (Client/BulletMarks): Count
	-- sparks, each a streak Long and Wide that leaves at Speed within Cone degrees of straight out, falls at
	-- Gravity and is gone in Life.
	Sparks = {
		["in"] = { Count = { 2, 3 }, Speed = { 14, 24 }, Life = { 0.1, 0.16 } },
		out = { Count = { 3, 5 }, Speed = { 18, 34 }, Life = { 0.12, 0.2 } },
		stop = { Count = { 4, 6 }, Speed = { 20, 40 }, Life = { 0.12, 0.22 } },
		Long = { 0.25, 0.55 },
		Wide = 0.04,
		Cone = 65,
		Gravity = 60,
		Glow = 0.25,
		-- A spark off stone or plaster is hot; off anything else it is a chip of the stuff (MarkConfig's Chip).
		Hot = Color3.fromRGB(255, 160, 48),
	},

	-- A hit on a body: shards that burst from where the shot landed, back along the shot and outwards, red.
	-- A hit to the head is more of them, faster, orange with red edges, round a flash of the same colours
	-- Flash times the size of a muzzle's.
	Struck = {
		body = {
			Count = { 5, 7 },
			Speed = { 10, 20 },
			Life = { 0.18, 0.28 },
			Long = { 0.35, 0.6 },
			Wide = { 0.16, 0.26 },
			Glow = 0.05,
			Hot = Color3.fromRGB(240, 58, 48),
			Edge = Color3.fromRGB(168, 22, 38),
		},
		head = {
			Count = { 9, 12 },
			Speed = { 14, 30 },
			Life = { 0.22, 0.36 },
			Long = { 0.45, 0.85 },
			Wide = { 0.2, 0.34 },
			Glow = 0.15,
			Hot = Color3.fromRGB(255, 140, 28),
			Edge = Color3.fromRGB(226, 36, 28),
			Flash = 1.5,
		},
		-- Wide, so that most of them fly across the shooter's view and not straight at it, where a shard
		-- seen end on is a dot.
		Cone = 115,
		Gravity = 34,
	},
}
