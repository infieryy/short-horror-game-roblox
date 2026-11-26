-- Sets the place lighting to the look rules in HANDOFF.md section 2.
-- Run in Studio in edit mode. Safe to re-run.
-- The numbers follow the Blender preview (assets/preview.py): a late-afternoon sun 38 degrees
-- above the horizon, slightly dim and warm, with lavender-blue light in the shade.
local Lighting = game:GetService("Lighting")

local LOOK = {
	-- Realistic + PrioritizeLightingQuality is what the old "Future" technology is called now.
	LightingStyle = Enum.LightingStyle.Realistic,
	PrioritizeLightingQuality = true,
	GlobalShadows = true,
	Brightness = 2.4, -- template default is 3; lower so bright walls don't burn out
	ColorShift_Top = Color3.fromRGB(255, 237, 209),
	ColorShift_Bottom = Color3.fromRGB(0, 0, 0),
	OutdoorAmbient = Color3.fromRGB(150, 146, 208), -- lavender-blue
	Ambient = Color3.fromRGB(128, 112, 142), -- warm lavender
	-- No sky-driven ambient or reflections: shade colour comes only from the two ambients, and nothing shines.
	EnvironmentDiffuseScale = 0,
	EnvironmentSpecularScale = 0,
	ExposureCompensation = 0,
	ShadowSoftness = 0.2,
	GeographicLatitude = 30,
}
local SUN_ELEVATION_DEGREES = 38 -- afternoon side

for property, value in LOOK do
	(Lighting :: any)[property] = value
end

-- Find the afternoon clock time that puts the sun at the wanted height.
local best, bestError = 15, math.huge
for minutes = 12 * 60, 18 * 60 do
	Lighting.ClockTime = minutes / 60
	local elevation = math.deg(math.asin(Lighting:GetSunDirection().Y))
	local miss = math.abs(elevation - SUN_ELEVATION_DEGREES)
	if miss < bestError then
		best, bestError = minutes / 60, miss
	end
end
Lighting.ClockTime = best

-- Post effects from the baseplate template that fight a flat, matte look.
local bloom = Lighting:FindFirstChildOfClass("BloomEffect")
if bloom then
	bloom.Intensity = 0.2
	bloom.Threshold = 2.5
end
local atmosphere = Lighting:FindFirstChildOfClass("Atmosphere")
if atmosphere then
	atmosphere.Color = Color3.fromRGB(226, 205, 190)
	atmosphere.Decay = Color3.fromRGB(150, 146, 208)
end

game:GetService("ChangeHistoryService"):SetWaypoint("Set Desert FPS lighting")
return { clockTime = Lighting.ClockTime, sunElevation = math.deg(math.asin(Lighting:GetSunDirection().Y)) }
