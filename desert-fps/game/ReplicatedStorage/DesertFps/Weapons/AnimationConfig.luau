--!strict
-- The weapon animations. "FPS ..." are for the character everyone sees: how it holds what it carries, and what
-- its arms do when it fires, reloads or slashes. "FPV ..." are for the arms in front of the player's own
-- camera. WeaponConfig says which of these each weapon uses.
-- Each was made in Blender on the R15 rig (animations/ in the repository) and is kept in the place as a
-- KeyframeSequence in ReplicatedStorage.<Folder>. They move the chest, head and arms only, so a character's
-- legs go on walking underneath.
-- A live game can only play animations that have been uploaded to Roblox: these are their asset ids (uploaded
-- 2026-11-27 from animations/*.rbxm). With an id of 0, Studio plays the stored sequence itself, so a new
-- or changed animation can be tested before it is uploaded.
return {
	Folder = "DesertFpsAnimations",
	Ids = {
		["FPS Rifle Hold"] = 83028381190337,
		["FPS Rifle Fire"] = 96286693108659,
		["FPS Rifle Reload"] = 124740467076400,
		["FPS Pistol Hold"] = 108605858556304,
		["FPS Pistol Fire"] = 137279406699731,
		["FPS Pistol Reload"] = 126204687311857,
		["FPS Knife Hold"] = 108323231141444,
		["FPS Knife Slash"] = 78142187319149,
		["FPV Rifle Idle"] = 111039337689658,
		["FPV Rifle Equip"] = 85685273923057,
		["FPV Rifle Fire"] = 106892581186919,
		["FPV Rifle Reload"] = 71514583960293,
		["FPV Pistol Idle"] = 126691491055902,
		["FPV Pistol Equip"] = 108763930015179,
		["FPV Pistol Fire"] = 123277761668379,
		["FPV Pistol Reload"] = 108603579052641,
		["FPV Knife Idle"] = 132308344203954,
		["FPV Knife Equip"] = 75892368916750,
		["FPV Knife Slash A"] = 105972440774537,
		["FPV Knife Slash B"] = 90002196614241,
	},
	-- Seconds a hold takes to blend in when a weapon is drawn, and an action takes to blend in.
	HoldFade = 0.2,
	ActionFade = 0.05,
}
