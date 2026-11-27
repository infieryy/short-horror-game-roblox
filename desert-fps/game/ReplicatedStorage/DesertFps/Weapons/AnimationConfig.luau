--!strict
-- The characters' weapon animations: how a character holds what it carries, and what its arms do when it
-- fires, reloads or slashes. WeaponConfig says which of these each weapon uses.
-- Each was made in Blender on the R15 rig (animations/ in the repository) and is kept in the place as a
-- KeyframeSequence in ReplicatedStorage.<Folder>. They move the chest, head and arms only, so the legs go
-- on walking underneath.
-- A live game can only play animations that have been uploaded to Roblox: put each one's asset id here once
-- it has been. With no id, Studio plays the stored sequence itself, so they can be tested before any upload.
return {
	Folder = "DesertFpsAnimations",
	Ids = {
		["FPS Rifle Hold"] = 0,
		["FPS Rifle Fire"] = 0,
		["FPS Rifle Reload"] = 0,
		["FPS Pistol Hold"] = 0,
		["FPS Pistol Fire"] = 0,
		["FPS Pistol Reload"] = 0,
		["FPS Knife Hold"] = 0,
		["FPS Knife Slash"] = 0,
	},
	-- Seconds a hold takes to blend in when a weapon is drawn, and an action takes to blend in.
	HoldFade = 0.2,
	ActionFade = 0.05,
}
