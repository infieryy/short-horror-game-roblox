--!strict
-- Utility: what a player throws to find enemies. Read by the server (what it does) and the client (how it
-- looks). Times are seconds, distances studs.
-- Until there are teams, everyone but the thrower is an enemy, the target dummies too.
return {
	-- What every player carries until there is a shop, in the order the display lists it.
	Loadout = { "recon" },

	Utilities = {
		-- The recon dart. Thrown, it sticks in the first thing it meets. After a moment it pulses, and with each
		-- pulse every enemy it has a clear line to is outlined for its thrower, through walls. Everyone sees it
		-- pulse, the enemy is told they were seen, and one shot or slash knocks it out.
		recon = {
			Title = "Recon dart",
			Key = Enum.KeyCode.Q,
			-- The kit piece, and how many times as big as made it is in the game: at its true size a dart is
			-- lost on a wall across a square, and nobody could shoot it down.
			Model = "util_dart",
			Size = 1.6,
			-- A used charge comes back after Recharge.
			Charges = 2,
			Recharge = 25,
			-- Throwing: the weapon is put away for ThrowTime, the dart leaves, and the weapon is drawn again.
			ThrowTime = 0.3,
			-- Its flight: how fast it leaves, how hard it is pulled down (a quarter of what a body is, so it
			-- carries across a square), and how long it may fly before it is lost.
			Speed = 110,
			Gravity = 45,
			FlightMost = 3,
			-- Stuck: Arm until the first pulse, then Pulses of them, one every Every. Linger is how long it
			-- stays after the last.
			Arm = 0.7,
			Pulses = 3,
			Every = 1.3,
			Linger = 0.6,
			-- How far it sees, and how long someone it saw stays outlined.
			Radius = 80,
			Reveal = 1.5,
		},
	},

	-- How it looks.
	Look = {
		-- The dart's own light and the bubble of a pulse: the town's turquoise.
		Light = Color3.fromRGB(72, 196, 186),
		LightRange = 7,
		-- A pulse: a bubble at the dart that grows to PulseSize across in PulseTime and fades.
		PulseSize = 12,
		PulseTime = 0.45,
		-- Someone it saw: the colour of their outline, how see-through its inside is, and how long it takes
		-- to fade at the end.
		Enemy = Color3.fromRGB(232, 84, 76),
		Fill = 0.7,
		Fade = 0.3,
	},

	-- How it sounds (Sound/SoundConfig): thrown, stuck, and each pulse, all heard where the dart is. Seen is
	-- heard by the thrower when a pulse sees someone, Spotted by whoever it saw.
	Sounds = { Throw = "Dart Throw", Stick = "Dart Stick", Pulse = "Dart Pulse", Seen = "Dart Seen", Spotted = "Spotted" },
}
