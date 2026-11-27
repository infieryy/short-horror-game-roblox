--!strict
-- The characters' weapon animations: how a character holds what it carries, and what its arms do when it
-- fires, reloads or slashes. WeaponConfig says which of these each weapon uses.
-- Each was made in Blender on the R15 rig (animations/ in the repository) and is kept in the place as a
-- KeyframeSequence in ReplicatedStorage.<Folder>. They move the chest, head and arms only, so the legs go
-- on walking underneath.
-- A live game can only play animations that have been uploaded to Roblox: these are their asset ids (uploaded
-- 2026-11-27 from animations/fps_*.rbxm). With an id of 0, Studio plays the stored sequence itself, so a new
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
	},
	-- Seconds a hold takes to blend in when a weapon is drawn, and an action takes to blend in.
	HoldFade = 0.2,
	ActionFade = 0.05,
}
