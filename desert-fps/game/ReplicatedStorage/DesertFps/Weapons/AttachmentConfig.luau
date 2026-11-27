--!strict
-- What can be put on a weapon, and what each thing does to it.
-- An attachment goes on one socket of a weapon's model: muzzle, optic, underbarrel, side or magazine. `Fits` lists
-- the weapons it goes on, and for each what it changes in that weapon's numbers (WeaponConfig):
--   Scale  { ["Recoil.Sway"] = 0.7 }   the number is multiplied
--   Add    { Magazine = 10 }           the number has this added
--   Set    { ["Aim.Zoom"] = 2 }        the value is replaced (a table on the way is made if the weapon has none)
--   Size   1.4                         its model is that many times as big on this weapon as it was made
-- Model is the kit piece that shows on the weapon (assets/recipes/attach.py). An attachment with no piece of
-- its own has Stretch: the weapon's own part of the socket's name is made that many times as long.
-- Everything is free until there is a shop. Changing what is on the weapon in hand draws it again.
return {
	-- The sockets, in the order the loadout shows them.
	Sockets = { "muzzle", "optic", "underbarrel", "side", "magazine" },

	-- A laser's light (Client/LaserSight): a dot where the weapon points and a thin beam to it from the laser,
	-- which everyone sees. The dot: how big it is for each stud it is from the eye, and at least; Range is how
	-- far the light carries. The beam: how wide it is at the laser, how wide at its far end for each stud that
	-- end is from the eye, how see-through it is near and far, and Glow, how much it adds its light to what
	-- is behind it instead of covering it (all the way, it washes out to white over the town's bright walls).
	Laser = {
		Color = Color3.fromRGB(255, 40, 32),
		PerStud = 0.004,
		Least = 0.03,
		Range = 300,
		Beam = { Width = 0.016, PerStud = 0.0018, Near = 0.05, Far = 0.4, Glow = 0.3 },
	},

	Attachments = {
		-- Nobody else sees where the shots come from. The price is damage at long range: past 150 studs the
		-- rifle's shot to the head no longer kills through heavy armor.
		suppressor = {
			Title = "Suppressor",
			About = "Enemies see no tracer. Less damage at long range.",
			Socket = "muzzle",
			Model = "att_suppressor",
			Fits = {
				rifle = { Set = { Silent = true, Falloff = { { 150, 0.9 } } } },
				pistol = { Set = { Silent = true, Falloff = { { 70, 0.85 } } } },
			},
		},
		compensator = {
			Title = "Compensator",
			About = "A spray climbs less, and swings a little more.",
			Socket = "muzzle",
			Model = "att_compensator",
			Fits = {
				rifle = { Scale = { ["Recoil.Rise"] = 0.78, ["Recoil.Sway"] = 1.15 } },
			},
		},
		-- An optic is looked through, not over: the point brought to the eye is the middle of its window
		-- (SightDrop 0), nearer than the iron sights so the window is worth looking through, and the screen
		-- shows the optic's red cross there instead of the crosshair (View.Reticle).
		reddot = {
			Title = "Red dot",
			About = "Quicker to aim, and tighter. Lets the pistol aim.",
			Socket = "optic",
			Model = "att_reddot",
			Fits = {
				rifle = {
					Scale = { ["Aim.Time"] = 0.75, ["Aim.Spread"] = 0.85 },
					Set = { ["View.SightDistance"] = 0.6, ["View.SightDrop"] = 0, ["View.Reticle"] = true },
				},
				pistol = {
					Set = {
						Aim = { Zoom = 1.15, Spread = 0.8, Recoil = 0.9, Speed = 0.85, Time = 0.14 },
						["View.SightDistance"] = 0.7,
						["View.SightDrop"] = 0,
						["View.Reticle"] = true,
					},
				},
			},
		},
		-- Raised all the way, a scope fills the screen: black, but for a round window (View.Scope, drawn by
		-- the display; HudConfig.Scope says how).
		scope = {
			Title = "2x scope",
			About = "Twice as close. Slow to raise, slow to walk with.",
			Socket = "optic",
			Model = "att_scope",
			Fits = {
				rifle = {
					Scale = { ["Aim.Time"] = 1.5, ["Aim.Speed"] = 0.8, ["Aim.Spread"] = 0.6 },
					Set = {
						["Aim.Zoom"] = 2,
						["View.SightDistance"] = 0.4,
						["View.SightDrop"] = 0,
						["View.Reticle"] = true,
						["View.Scope"] = true,
					},
				},
			},
		},
		foregrip = {
			Title = "Foregrip",
			About = "A spray swings less and spreads less. Slower to draw.",
			Socket = "underbarrel",
			Model = "att_foregrip",
			Fits = {
				rifle = { Scale = { ["Recoil.Sway"] = 0.65, ["Spread.Spray"] = 0.8, EquipTime = 1.12 } },
			},
		},
		-- A box on the weapon's left side, the side its holder sees.
		laser = {
			Title = "Laser",
			About = "Shots from the hip stray less on the move. Its beam shows.",
			Socket = "side",
			Model = "att_laser",
			Fits = {
				rifle = {
					Scale = { ["Spread.Walk"] = 0.7, ["Spread.Run"] = 0.75, ["Spread.Air"] = 0.8 },
					Set = { ["View.Laser"] = true },
					Size = 1.4, -- the one box is made to suit the pistol; on the long rifle it would look lost
				},
				pistol = {
					Scale = { ["Spread.Walk"] = 0.7, ["Spread.Run"] = 0.75, ["Spread.Air"] = 0.8 },
					Set = { ["View.Laser"] = true },
				},
			},
		},
		magazine = {
			Title = "Extended magazine",
			About = "More rounds. Slower to reload.",
			Socket = "magazine",
			Stretch = 1.22,
			Fits = {
				rifle = { Add = { Magazine = 10 }, Scale = { ReloadTime = 1.12 } },
				pistol = { Add = { Magazine = 6 }, Scale = { ReloadTime = 1.12 } },
			},
		},
	},
}
