--!strict
-- Health, armor and hits, read by the server (which decides them) and the client (which shows them).
return {
	Health = 100,
	-- Armor is a second bar that takes damage before health does.
	Armor = { none = 0, light = 25, heavy = 50 },

	-- The parts of a character a shot can land on, and what each counts as (WeaponConfig damage is by these).
	Zones = {
		Head = "head",
		UpperTorso = "body",
		LowerTorso = "body",
		LeftUpperArm = "body",
		LeftLowerArm = "body",
		LeftHand = "body",
		RightUpperArm = "body",
		RightLowerArm = "body",
		RightHand = "body",
		LeftUpperLeg = "legs",
		LeftLowerLeg = "legs",
		LeftFoot = "legs",
		RightUpperLeg = "legs",
		RightLowerLeg = "legs",
		RightFoot = "legs",
	},
	-- Studs a hit box is larger than its part on every side.
	HitMargin = 0.1,
	-- A knife reaches wider than a bullet.
	MeleeMargin = 1,

	-- The shooter sees everyone else a little in the past. The server keeps where each character's parts were
	-- for Keep seconds, and a shot counts if it hits where its target was at any moment in the last Reach.
	Rewind = { Keep = 0.6, Reach = 0.35 },

	-- Walking (Shift): this share of the weapon's run speed.
	WalkFactor = 0.55,

	-- Seconds from dying to standing at the spawn again, while there are no rounds.
	RespawnSeconds = 3,
}
