--!strict
-- What a shot goes through, and what that costs it.
-- A shot starts with all its force (1). Going through something takes Loss of it for every stud of thickness,
-- divided by the weapon's Pierce (WeaponConfig): the rifle's is 1, the pistol's under a half, so the pistol
-- loses twice as much in the same plank and is stopped by half the thickness. What is left is the share of
-- its damage the shot still does, to a body or to the next thing in its way. A shot that would come out with
-- less than Least left does not come out.
--
-- With these numbers the rifle goes through:
--   cloth, a market stall, a door (0.3 studs of wood)      and keeps nine tenths or more
--   a barrel, a counter, a crate (3 studs of wood)          and keeps a quarter to two thirds
--   one house wall (1 stud of plaster)                      and keeps 0.45: a shot to the head does 72
--   a door frame (1.3 studs of plaster)                     and keeps 0.3
-- and is stopped by a corner post (1.6 studs), a second wall, a floor, a roof and the town wall.
-- The pistol goes through cloth, stalls and doors, and nothing thicker.
return {
	Least = 0.15,
	-- A shot goes through this many things at most.
	Most = 8,

	Materials = {
		cloth = { Loss = 0.06 }, -- and leaves: a tree's crown is no cover
		wood = { Loss = 0.25 }, -- and fired clay: pots, vases
		plaster = { Loss = 0.55 }, -- the houses' walls
	},

	-- What each kit piece is made of. A piece is looked up by its name, then by the part of its name before the
	-- first "_" (wall2_shutter under wall2). Anything not listed stops every shot: floors, roofs, stairs, the
	-- ground, the town wall, the well.
	Pieces = {
		awning = "cloth",
		cloth = "cloth",
		banner = "cloth",
		rug = "cloth",
		rack = "cloth",
		bolts = "cloth",
		bougainvillea = "cloth",
		baskets = "cloth",
		divan = "cloth",
		tree = "cloth",
		cypress = "cloth",
		palm = "cloth",
		potted = "cloth",

		door = "wood",
		door2 = "wood",
		crate = "wood",
		stack = "wood",
		barrel = "wood",
		stall = "wood",
		counter = "wood",
		shelf = "wood",
		plank = "wood",
		ladder = "wood",
		pergola = "wood",
		cart = "wood",
		loom = "wood",
		tea = "wood",
		sign = "wood",
		lantern = "wood",
		pot = "wood",
		vase = "wood",
		sacks = "wood",

		wall = "plaster",
		wall2 = "plaster",
		corner = "plaster",
		corner2 = "plaster",
		pillar = "plaster",
		parapet = "plaster",
	},
}
