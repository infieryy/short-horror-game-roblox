--!strict
-- How the marks shots leave on the town look (Client/BulletMarks).
-- A shot that went through something leaves a dark hole with a pale rim where it went in, and a wider, torn
-- one where it came out. A shot that was stopped leaves a pale chip with cracks and no hole. So the wall says
-- which it was: dark in the middle is through, pale is stopped.
return {
	-- Seconds a mark stays, and how many there are at once: past that the oldest goes first.
	Life = 60,
	Most = 90,
	-- When what a mark is on goes (a wall cracks: it is swapped for its shards), the mark waits Settle seconds
	-- for what replaces it, then looks Reach studs either side of where it was for a surface to move onto.
	Settle = 0.2,
	Reach = 0.5,
	-- Studs a mark stands off its surface, and the most that is added to it so that two marks in the same place
	-- do not flicker through each other.
	Lift = 0.02,
	LiftSpread = 0.01,
	PixelsPerStud = 220,
	-- Each mark is at most this much larger or smaller than its kind's size, and is one of this many drawings
	-- of its kind, turned any way round.
	Vary = 0.15,
	Drawings = 3,

	-- Studs across, by kind.
	Size = { ["in"] = 0.45, out = 0.7, stop = 0.5 },

	-- What flies off: a ball of dust that grows From and To that many studs across in Time seconds while it
	-- drifts Out studs from the surface and fades from Start to nothing.
	Puff = {
		Start = 0.4,
		["in"] = { From = 0.2, To = 0.7, Time = 0.2, Out = 0.35 },
		out = { From = 0.3, To = 1.3, Time = 0.28, Out = 1.1 },
		stop = { From = 0.2, To = 0.85, Time = 0.22, Out = 0.45 },
	},

	-- By what the thing is made of (PenetrationConfig.Materials), and `hard` for everything that stops every
	-- shot: stone, tiles, the ground.
	--   Hole   the dark of a hole
	--   Rim    the broken edge round a hole, and a chip: the stuff under the paint
	--   Edge   the line round a rim or a chip, so that it shows on a wall of its own colour, and the cracks
	--   Dust   what flies off
	--   Sound  what is heard there (Sound/SoundConfig): Through where a shot goes in and comes out again,
	--          Stopped where it does not
	-- A material with no Rim is not marked: a shot through leaves only shakes some loose.
	Materials = {
		plaster = {
			Hole = Color3.fromRGB(58, 38, 60),
			Rim = Color3.fromRGB(255, 220, 178),
			Edge = Color3.fromRGB(150, 80, 72),
			Dust = Color3.fromRGB(250, 214, 178),
			Sound = { Through = "Plaster Through", Stopped = "Stone Stopped" },
		},
		wood = {
			Hole = Color3.fromRGB(50, 32, 44),
			Rim = Color3.fromRGB(250, 210, 150),
			Edge = Color3.fromRGB(104, 58, 44),
			Dust = Color3.fromRGB(236, 196, 142),
			Sound = { Through = "Wood Through", Stopped = "Wood Stopped" },
		},
		cloth = {
			Hole = Color3.fromRGB(52, 38, 60),
			Rim = Color3.fromRGB(250, 236, 214),
			Edge = Color3.fromRGB(110, 86, 112),
			Dust = Color3.fromRGB(250, 236, 214),
			Sound = { Through = "Cloth Through", Stopped = "Cloth Through" },
		},
		leaves = {
			Dust = Color3.fromRGB(132, 164, 96),
			Sound = { Through = "Leaves Through", Stopped = "Leaves Through" },
		},
		hard = {
			Hole = Color3.fromRGB(58, 40, 62),
			Rim = Color3.fromRGB(250, 228, 204),
			Edge = Color3.fromRGB(122, 96, 128),
			Dust = Color3.fromRGB(244, 222, 196),
			Sound = { Through = "Stone Stopped", Stopped = "Stone Stopped" },
		},
	},
}
