-- Sets the painted sky: the concept's golden-hour sky, violet overhead and peach at the horizon, with
-- peach clouds. Run in Studio in edit mode. Safe to re-run.
-- The six pictures are cut from one painting by assets/sky.py, which also holds which way Roblox turns
-- each face of the sky box (its "Rt" face is on the -X side, and the top and bottom lie a quarter turn round).
local Lighting = game:GetService("Lighting")

local FACES = {
	Ft = 139737408918411,
	Bk = 140688943288979,
	Rt = 86334069313589,
	Lf = 81141017514850,
	Up = 72189972138575,
	Dn = 115116885001171,
}

local sky = Lighting:FindFirstChildOfClass("Sky")
if not sky then
	sky = Instance.new("Sky")
	sky.Parent = Lighting
end
for face, id in FACES do
	(sky :: any)["Skybox" .. face] = `rbxassetid://{id}`
end
sky.StarCount = 0
sky.CelestialBodiesShown = true -- Roblox draws the sun itself, where the light comes from
sky.SunAngularSize = 9

game:GetService("ChangeHistoryService"):SetWaypoint("Set the painted sky")
return "sky set"
