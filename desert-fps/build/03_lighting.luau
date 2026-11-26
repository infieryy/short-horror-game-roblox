-- Sets the place lighting to the look rules in HANDOFF.md section 2.
-- Run in Studio in edit mode. Safe to re-run.
-- A late-afternoon sun 38 degrees above the horizon (as in assets/preview.py), slightly dim and warm,
-- with lavender-blue light in the shade.
-- Brightness, ColorShift_Top and the two ambients were tuned against assets/out/preview.png with the kit
-- stood up by 05_kit_showcase.luau: sunlit plaster, ground and the teal band land within about 15 levels
-- (of 255) of the render. Shade stays lavender by the look rules; in the render it is warmer, because
-- Blender bounces light off the orange ground and Roblox does not.
local Lighting = game:GetService("Lighting")

local LOOK = {
	-- Realistic + PrioritizeLightingQuality is what the old "Future" technology is called now.
	LightingStyle = Enum.LightingStyle.Realistic,
	PrioritizeLightingQuality = true,
	GlobalShadows = true,
	Brightness = 2.5, -- template default is 3; lower so bright walls don't burn out
	-- Much more orange than the render's sun: Roblox's tone mapping washes bright warm colours out otherwise.
	ColorShift_Top = Color3.fromRGB(255, 186, 148),
	ColorShift_Bottom = Color3.fromRGB(0, 0, 0),
	OutdoorAmbient = Color3.fromRGB(115, 113, 165), -- lavender-blue
	Ambient = Color3.fromRGB(98, 86, 110), -- warm lavender; untested, the kit showcase has no indoors
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
