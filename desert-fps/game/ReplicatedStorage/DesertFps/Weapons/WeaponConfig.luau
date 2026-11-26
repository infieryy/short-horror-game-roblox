--!strict
-- Weapon numbers, read by the server (damage, rate, range) and the client (feel).
return {
	-- Every player carries this until loadouts exist.
	Default = "rifle",

	-- Shots the server lets through at once on top of the fire rate, to absorb network jitter.
	BurstAllowance = 2,
	-- Studs a shot may start from the shooter's head (the first-person camera sits in it).
	MaxOriginOffset = 4,

	rifle = {
		Damage = 30,
		FireInterval = 0.1, -- seconds between shots: 600 a minute
		Range = 500,

		-- Where the weapon origin (top of the grip) sits from the camera: right, up, back.
		ViewOffset = Vector3.new(0.55, -0.5, -0.9),
		-- Each shot pushes the weapon back (studs) and tips it up (degrees); Recover is how fast it settles.
		KickBack = 0.1,
		KickPitch = 1.6,
		Recover = 16,

		-- Seconds the line from the muzzle to the hit stays visible.
		TracerTime = 0.05,
		TracerWidth = 0.04,
		TracerColor = Color3.fromRGB(255, 222, 168),
	},
}
