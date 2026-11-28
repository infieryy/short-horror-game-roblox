--!strict
-- Weapon numbers, read by the server (what a shot does) and the client (how it feels).
-- Angles are degrees, distances studs, times seconds.
return {
	-- What every player carries until the shop exists: a weapon in each slot, and armor (CombatConfig.Armor).
	-- What goes on a weapon, and what that changes in the numbers below, is in AttachmentConfig.
	Loadout = { primary = "rifle", secondary = "pistol", melee = "knife", armor = "heavy" },
	-- The slots, in key order: 1, 2, 3.
	Slots = { "primary", "secondary", "melee" },

	-- Shots the server lets through at once on top of the fire rate, to absorb network jitter.
	BurstAllowance = 2,
	-- Studs a shot may start from the shooter's head (the first-person camera sits in it).
	MaxOriginOffset = 4,
	-- Reloads, weapon switches and stance changes a player may ask for: one every AskInterval, AskBurst at once.
	AskInterval = 0.1,
	AskBurst = 6,
	-- Seconds early the server lets a draw or a reload finish, for the time the request took to arrive.
	Grace = 0.15,

	-- How fast the shooter moves decides how far shots stray. As a share of the weapon's run speed: at Still
	-- or slower a shot is as accurate as standing; from there it blends up to the running figure at Running.
	Still = 0.3,
	Running = 0.9,

	-- The field of view from the hip (degrees, top to bottom).
	FieldOfView = 70,

	-- The arms in front of the camera (Client/Viewmodel). What they do with each weapon is animation, made in
	-- Blender through a camera where the player's eye is (animations/README.md).
	ViewArms = {
		-- Where the arms' root sits from the camera: the animations' camera was 1.1 studs above it.
		Rig = CFrame.new(0, -1.1, 0),
		-- The collision group the arms are in. It collides with nothing.
		Group = "ViewArms",
		-- Studs a forearm and a hand are thick. A body's are a full stud, which at arm's length fills the view.
		Thickness = 0.6,
		-- Walking makes the weapon bob this far (studs), at this many swings a stud.
		Bob = 0.03,
		BobRate = 0.55,
		-- Turning the head leaves the weapon Lag of the turn behind, by LagMost degrees at most, and it
		-- catches up at LagSettle a second. A step to the side leans it Lean degrees.
		Lag = 0.6,
		LagMost = 4,
		LagSettle = 10,
		Lean = 2.5,
		-- How fast a weapon's bolt comes forward again after a shot (per second).
		BoltReturn = 16,
		-- Aiming needs to know where the weapon rests in the hands. It is measured once the arms have done
		-- nothing but hold it for Settle seconds, and followed from then on at RestFollow a second: fast, so
		-- that an aimed weapon stays on the line of sight instead of drifting with the breath of the idle
		-- (through an optic a few studs from the eye, a hundredth of a stud of drift is a degree).
		Settle = 0.3,
		RestFollow = 30,
	},

	Weapons = {
		-- The standard rifle. One shot to the head kills through any armor, at any range. The first shot goes
		-- where it is aimed if the shooter stands still; a spray climbs, then swings from side to side.
		rifle = {
			Kind = "gun",
			Title = "Rifle",
			Auto = true,
			FireInterval = 0.1, -- 600 a minute
			Magazine = 25,
			Reserve = 75,
			ReloadTime = 2.5,
			EquipTime = 0.8,
			Range = 600,
			-- Damage by where the shot lands (CombatConfig.Zones).
			Damage = { head = 160, body = 40, legs = 34 },
			-- { from this distance on, damage is multiplied by this }, nearest first. None: full damage at any range.
			Falloff = {},
			-- What a shot does to walls and props.
			WallDamage = 30,
			-- How well a shot goes through things (PenetrationConfig): 1 goes through a house wall and keeps
			-- under half its damage.
			Pierce = 1,
			RunSpeed = 16,

			-- How far a shot may stray from where it is sent: standing still, walking (Shift), running, in the
			-- air. Each shot of a spray adds Spray, up to SprayMost.
			Spread = { Still = 0.2, Walk = 1.3, Run = 5, Air = 8, Spray = 0.1, SprayMost = 1.2 },
			-- Recoil. Shot n of a spray leaves { up, right } of the aim: the Pattern, the same every time.
			-- Past its end the spray stays as high as the last entry and swings Sway to one side, then the other,
			-- changing sides every SwayEvery shots. Reset is the pause that ends a spray; Recover is how fast
			-- the aim comes back down. View is the share of the recoil that the view itself climbs. Rise is how
			-- much of the climb is left (1: all of it).
			Recoil = {
				Pattern = {
					{ 0, 0 },
					{ 0.4, 0.05 },
					{ 1.1, -0.1 },
					{ 2.1, 0.15 },
					{ 3.3, -0.2 },
					{ 4.6, 0.3 },
					{ 5.7, 0.1 },
					{ 6.6, -0.3 },
					{ 7.2, -0.6 },
					{ 7.6, -0.3 },
				},
				Rise = 1,
				Sway = 2.2,
				SwayEvery = 5,
				Reset = 0.35,
				Recover = 9,
				View = 0.5,
			},
			-- Aiming down the sights: Zoom is how much closer things look; shots stray Spread times as far and
			-- recoil Recoil times as much; the shooter moves at Speed of the usual; Time is how long raising takes.
			Aim = { Zoom = 1.25, Spread = 0.75, Recoil = 0.85, Speed = 0.75, Time = 0.16 },

			-- On the character everyone else sees: how the weapon sits in the right hand (the Tool's grip) and
			-- the animations its holder plays (AnimationConfig). Both come from posing the character with the
			-- weapon in Blender, so the weapon is level and the left hand is on it.
			Hand = CFrame.new(0, -0.18, 0.05, 0.46297, 0.7368, 0.49273, -0.47555, 0.67559, -0.56341, -0.748, 0.02653, 0.66316),
			Animations = { Hold = "FPS Rifle Hold", Fire = "FPS Rifle Fire", Reload = "FPS Rifle Reload" },
			-- What it sounds like (Sound/SoundConfig). The reload's sounds are heard where its animation has
			-- the magazine leave and come back and the bolt pulled (View, below).
			Sounds = {
				Fire = "Rifle Shot",
				Empty = "Dry Fire",
				Draw = "Rifle Draw",
				MagazineOut = "Rifle Magazine Out",
				MagazineIn = "Rifle Magazine In",
				Bolt = "Rifle Bolt",
			},

			-- In first person.
			View = {
				-- What the arms do with it (AnimationConfig).
				Animations = { Idle = "FPV Rifle Idle", Equip = "FPV Rifle Equip", Fire = "FPV Rifle Fire", Reload = "FPV Rifle Reload" },
				-- Aiming: how far in front of the eye the rear sight sits, and how far below the line of
				-- sight, so the sights frame the target instead of covering it.
				SightDistance = 1.3,
				SightDrop = 0.1,
				-- In the reload animation, as shares of its length: when the magazine leaves with the left
				-- hand and when a full one is back in, and when the bolt is pulled.
				Magazine = { Out = 0.187, In = 0.56 },
				Bolt = { From = 0.69, To = 0.77 },
			},
		},

		-- The sidearm. One shot at a time, as fast as the trigger is pulled. Two to the head close up, three
		-- from further off. Accurate on the move, where the rifle is not.
		pistol = {
			Kind = "gun",
			Title = "Pistol",
			Auto = false,
			FireInterval = 0.15,
			Magazine = 12,
			Reserve = 36,
			ReloadTime = 1.75,
			EquipTime = 0.5,
			Range = 400,
			Damage = { head = 78, body = 26, legs = 22 },
			Falloff = { { 100, 0.85 } },
			WallDamage = 12,
			-- Through a door or a market stall, and no wall.
			Pierce = 0.45,
			RunSpeed = 17,

			Spread = { Still = 0.35, Walk = 0.6, Run = 2, Air = 5, Spray = 0.3, SprayMost = 1.5 },
			Recoil = {
				Pattern = { { 0, 0 }, { 0.9, 0.1 }, { 1.6, -0.15 }, { 2.1, 0.2 }, { 2.5, -0.2 } },
				Rise = 1,
				Sway = 0.6,
				SwayEvery = 2,
				Reset = 0.3,
				Recover = 12,
				View = 0.6,
			},

			Hand = CFrame.new(-0.035, -0.204, -0.0175, 0.5246, 0.51696, 0.67642, -0.29871, 0.85579, -0.42238, -0.79722, 0.01953, 0.60337),
			Animations = { Hold = "FPS Pistol Hold", Fire = "FPS Pistol Fire", Reload = "FPS Pistol Reload" },
			Sounds = {
				Fire = "Pistol Shot",
				Empty = "Dry Fire",
				Draw = "Pistol Draw",
				MagazineOut = "Pistol Magazine Out",
				MagazineIn = "Pistol Magazine In",
			},

			View = {
				Animations = { Idle = "FPV Pistol Idle", Equip = "FPV Pistol Equip", Fire = "FPV Pistol Fire", Reload = "FPV Pistol Reload" },
				Magazine = { Out = 0.18, In = 0.6 },
			},
		},

		-- The knife. Fastest on foot. A slash from behind does BackDamage.
		knife = {
			Kind = "melee",
			Title = "Knife",
			FireInterval = 0.55,
			EquipTime = 0.4,
			Range = 6.5,
			Damage = 50,
			BackDamage = 100,
			WallDamage = 15,
			RunSpeed = 18,

			Hand = CFrame.new(-0.0104, -0.061, 0.0712, 0.95692, -0.07396, 0.28077, 0.25866, 0.65646, -0.70863, -0.13191, 0.75073, 0.64731),
			Animations = { Hold = "FPS Knife Hold", Fire = "FPS Knife Slash" },
			Sounds = { Fire = "Knife Swing", Draw = "Knife Draw" },

			View = {
				-- It slashes one way, then back the other.
				Animations = { Idle = "FPV Knife Idle", Equip = "FPV Knife Equip", Fire = { "FPV Knife Slash A", "FPV Knife Slash B" } },
			},
		},
	},
}
