--!strict
-- Every sound in the game: which recordings it is played from, how loud it is and how far it carries.
-- Read by the client, which plays them (Client/Sounds), and by the server, which goes by Far when it decides
-- who is told about a noise (a suppressed shot, a reload).
--
-- All the recordings are from Roblox's licensed library: creator "ProSoundEffects" on the Creator Store, free
-- to use in an experience. Nothing was uploaded. To change a sound, change its takes here. Take them only
-- from that creator: most other sounds on the store are lifted from other games.
--
--   Takes    the recordings. One is picked each time, never the same twice running. Each is
--              Id     the asset
--              Gain   times as loud as recorded, so that the takes of one sound are alike (they are not
--                     recorded at one level)
--              From   seconds into the recording at which to start: many have silence at their head, and a
--                     shot that sounds a twentieth of a second late feels late
--              To     seconds into the recording at which to stop
--   Volume   how loud the sound is, after Gain. Roblox plays nothing louder than 10 in all.
--   Pitch    { lowest, highest } speed it is played at, picked each time
--   Near     studs within which a sound in the world is at its full volume
--   Far      studs past which it is not heard at all
-- A sound in the player's own head (their own weapon, the display) is at its Volume, wherever they stand.
return {
	-- Everything at once.
	Master = 1,

	Sounds = {
		-- The rifle: four single shots of one automatic rifle. Heard across the town.
		["Rifle Shot"] = {
			Takes = {
				{ Id = 9114727096, Gain = 0.75 },
				{ Id = 9114727608 },
				{ Id = 9114727563 },
				{ Id = 9114727718 },
			},
			Volume = 1,
			Pitch = { 0.97, 1.03 },
			Near = 30,
			Far = 500,
		},
		-- The pistol: lighter and sharper.
		["Pistol Shot"] = {
			Takes = { { Id = 9114729355, From = 0.03 }, { Id = 9114729252, Gain = 0.83, From = 0.03 } },
			Volume = 0.85,
			Pitch = { 0.97, 1.03 },
			Near = 25,
			Far = 400,
		},
		-- Suppressed: a low thump that does not carry. The server tells nobody further off than Far.
		["Rifle Shot Quiet"] = {
			Takes = { { Id = 9119135495 }, { Id = 9119135228, Gain = 0.95 }, { Id = 9119135785, Gain = 1.1 } },
			Volume = 0.45,
			Pitch = { 0.88, 0.94 },
			Near = 10,
			Far = 70,
		},
		["Pistol Shot Quiet"] = {
			Takes = { { Id = 9119135495 }, { Id = 9119135228, Gain = 0.95 }, { Id = 9119135785, Gain = 1.1 } },
			Volume = 0.38,
			Pitch = { 1.08, 1.16 },
			Near = 8,
			Far = 55,
		},
		-- The trigger on an empty weapon.
		["Dry Fire"] = { Takes = { { Id = 9117396156, From = 0.03 } }, Volume = 1, Pitch = { 0.97, 1.03 } },

		-- A reload, piece by piece, and a weapon drawn. Heard by those close.
		["Rifle Magazine Out"] = { Takes = { { Id = 9117396464, From = 0.26 } }, Volume = 0.9, Pitch = { 0.8, 0.85 }, Near = 6, Far = 45 },
		["Rifle Magazine In"] = { Takes = { { Id = 9116347612, From = 0.2 } }, Volume = 0.3, Pitch = { 0.97, 1.03 }, Near = 6, Far = 45 },
		["Rifle Bolt"] = { Takes = { { Id = 9116357621, From = 0.02 } }, Volume = 0.5, Pitch = { 0.97, 1.03 }, Near = 6, Far = 45 },
		["Pistol Magazine Out"] = { Takes = { { Id = 9117396164, From = 0.86 } }, Volume = 1.4, Pitch = { 0.97, 1.03 }, Near = 6, Far = 40 },
		["Pistol Magazine In"] = { Takes = { { Id = 9117396464, From = 0.55 } }, Volume = 0.8, Pitch = { 1.1, 1.18 }, Near = 6, Far = 40 },
		["Rifle Draw"] = { Takes = { { Id = 9116362330 } }, Volume = 3.5, Pitch = { 0.97, 1.03 }, Near = 6, Far = 35 },
		["Pistol Draw"] = {
			Takes = { { Id = 9117396530, From = 0.01 }, { Id = 9117396574, Gain = 1.15 } },
			Volume = 1.8,
			Pitch = { 0.97, 1.03 },
			Near = 6,
			Far = 30,
		},

		-- The knife.
		["Knife Draw"] = { Takes = { { Id = 9116190478 } }, Volume = 1.5, Pitch = { 0.95, 1.05 }, Near = 5, Far = 25 },
		["Knife Swing"] = {
			Takes = { { Id = 9119750223, Gain = 6, From = 0.055 }, { Id = 9119750447, Gain = 0.5, From = 0.05 } },
			Volume = 1,
			Pitch = { 0.94, 1.06 },
			Near = 5,
			Far = 30,
		},

		-- Where a shot lands (Client/MarkConfig). Through something is a bright crack or crunch; stopped is a
		-- dull thud, and off stone now and then a ricochet. So the ear can tell them apart, like the eye.
		["Wood Through"] = {
			Takes = { { Id = 9120962232, Gain = 1.3 }, { Id = 9120962354, From = 0.055, To = 0.42 } },
			Volume = 1,
			Pitch = { 0.94, 1.06 },
			Near = 8,
			Far = 130,
		},
		["Wood Stopped"] = {
			Takes = { { Id = 9113632382, From = 0.03 }, { Id = 9113632248, Gain = 1.07, From = 0.035 } },
			Volume = 0.6,
			Pitch = { 1.1, 1.22 },
			Near = 8,
			Far = 130,
		},
		["Plaster Through"] = { Takes = { { Id = 9113632073, From = 0.09 } }, Volume = 0.6, Pitch = { 0.94, 1.08 }, Near = 8, Far = 130 },
		["Stone Stopped"] = {
			Takes = {
				{ Id = 9113632382, Gain = 0.6, From = 0.03 },
				{ Id = 9113632248, Gain = 0.65, From = 0.035 },
				{ Id = 9118168273, Gain = 1.05 },
				{ Id = 9118168585, Gain = 0.9 },
			},
			Volume = 1,
			Pitch = { 0.94, 1.06 },
			Near = 8,
			Far = 130,
		},
		["Cloth Through"] = {
			Takes = { { Id = 9113819490, From = 0.07 }, { Id = 9113818686, Gain = 0.62, From = 0.05 } },
			Volume = 0.8,
			Pitch = { 0.95, 1.1 },
			Near = 6,
			Far = 80,
		},
		-- A soft recording: as loud as it goes.
		["Leaves Through"] = { Takes = { { Id = 9114517148 } }, Volume = 10, Pitch = { 0.95, 1.1 }, Near = 6, Far = 80 },

		-- What the player is told (Cues, below). In the head.
		["Hit"] = { Takes = { { Id = 9118598470 } }, Volume = 0.7, Pitch = { 0.98, 1.02 } },
		["Headshot"] = { Takes = { { Id = 9125361323 } }, Volume = 1.6, Pitch = { 0.98, 1.02 } },
		["Kill"] = { Takes = { { Id = 9126073064, From = 0.105 } }, Volume = 3 },
		["Knife Hit"] = { Takes = { { Id = 9116197520 }, { Id = 9116197517, Gain = 2.2 } }, Volume = 0.9, Pitch = { 0.95, 1.05 } },
		["Hurt"] = { Takes = { { Id = 9113523963, From = 0.08 } }, Volume = 0.6, Pitch = { 0.95, 1.05 } },

		-- Feet (Footsteps, below).
		["Step"] = {
			Takes = {
				{ Id = 9118249165, Gain = 1.25 },
				{ Id = 9118250949, Gain = 1.2 },
				{ Id = 9118249853 },
				{ Id = 9118249166, Gain = 0.95 },
			},
			Volume = 0.7,
			Pitch = { 0.93, 1.07 },
			Near = 8,
			Far = 70,
		},
		["Land"] = { Takes = { { Id = 9118252696, From = 0.02 } }, Volume = 0.9, Pitch = { 0.76, 0.84 }, Near = 8, Far = 70 },

		-- The recon dart (Utility/UtilityConfig). Its pulse carries further than it sees.
		["Dart Throw"] = { Takes = { { Id = 9119750447, Gain = 0.5, From = 0.05 } }, Volume = 0.8, Pitch = { 1.3, 1.4 }, Near = 5, Far = 40 },
		["Dart Stick"] = { Takes = { { Id = 9113160683, From = 0.58 } }, Volume = 5, Pitch = { 0.97, 1.03 }, Near = 6, Far = 60 },
		["Dart Pulse"] = { Takes = { { Id = 9126138068 } }, Volume = 4.5, Near = 12, Far = 110 },
		["Dart Seen"] = { Takes = { { Id = 9126138070 } }, Volume = 3, Pitch = { 1.33, 1.37 } },
		["Spotted"] = { Takes = { { Id = 9126138070 } }, Volume = 4, Pitch = { 0.74, 0.76 } },
	},

	-- What the player hears when the server says: a shot of theirs landed on a body (Hit), on a head (Head),
	-- it killed (Kill, on top), their knife cut (Blade), or they were hurt.
	Cues = { Hit = "Hit", Head = "Headshot", Kill = "Kill", Blade = "Knife Hit", Hurt = "Hurt" },

	-- Footsteps (Client/Footsteps). Someone moving faster than From studs a second is heard: that is running
	-- with any weapon, and running while aiming. Walking (Shift) is at most 9.9 with the knife, and silent.
	-- A step every Stride studs; the first of a run comes First of a stride in. The player's own steps are
	-- Own times as loud. A landing is heard after a fall of LandFrom studs a second or faster.
	Footsteps = {
		Step = "Step",
		Land = "Land",
		From = 10.5,
		Stride = 4.8,
		First = 0.6,
		Own = 0.3,
		LandFrom = 12,
	},
}
