-- Sets the place lighting to the look rules in HANDOFF.md section 2 and to the concept art's time of day.
-- Run in Studio in edit mode. Safe to re-run.
-- The concept is a golden-hour scene: a warm sun 38 degrees up, a violet sky with peach clouds, shade that
-- stays light and turns pink-violet, a pale peach haze towards the horizon, sand all round.
-- Targets measured from reference/ (red, green, blue of 255):
--   sunlit wall 252 184 131   wall in shade 178 103 83    sunlit paving 246 173 146   paving in shade 174 117 141
--   sky overhead 138 129 198  sky low 253 184 186         horizon 253 191 152         sand 253 180 123
-- The sky itself is painted (assets/sky.py) and set by 08_sky.luau; this script does the light, the haze,
-- the post effects and the bare ground.
local Lighting = game:GetService("Lighting")

local LOOK = {
	-- Realistic + PrioritizeLightingQuality is what the old "Future" technology is called now.
	LightingStyle = Enum.LightingStyle.Realistic,
	PrioritizeLightingQuality = true,
	GlobalShadows = true,
	Brightness = 2.5, -- template default is 3; lower so bright walls don't burn out
	-- Much more orange than a real sun: Roblox's tone mapping washes bright warm colours out otherwise.
	ColorShift_Top = Color3.fromRGB(255, 186, 148),
	ColorShift_Bottom = Color3.fromRGB(0, 0, 0),
	-- Shade is never gray: violet out of doors, warm rose under a roof. Both are bright enough that a wall
	-- in shade stays a colour instead of going dark.
	-- Rooms built from this kit take mostly OutdoorAmbient: the shade light leaks through walls and roofs one
	-- stud thick (tested by setting it to orange: every room turned orange). So it is a rosy violet, not a
	-- blue one, and the lamps do the warming indoors (Buildings/BuildingConfig.luau).
	OutdoorAmbient = Color3.fromRGB(165, 140, 186),
	Ambient = Color3.fromRGB(150, 120, 118),
	-- No sky-driven ambient or reflections: shade colour comes only from the two ambients, and nothing shines.
	EnvironmentDiffuseScale = 0,
	EnvironmentSpecularScale = 0,
	ExposureCompensation = 0,
	ShadowSoftness = 0.25,
	-- A high latitude swings the afternoon sun round to the south-west, so the fronts that face south (the
	-- Tea House porch) and west are both in the light. At 30 the sun stood due west and south fronts were dark.
	GeographicLatitude = 58,
}
local SUN_ELEVATION_DEGREES = 38 -- afternoon side
local SAND = Color3.fromRGB(240, 172, 128)

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

local function effect(className: string): Instance
	local found = Lighting:FindFirstChildOfClass(className)
	if not found then
		found = Instance.new(className)
		found.Parent = Lighting
	end
	return found
end

-- Lamp glass glows; nothing else is bright enough to bloom.
local bloom = effect("BloomEffect") :: BloomEffect
bloom.Intensity = 0.3
bloom.Size = 28
bloom.Threshold = 2.0 -- lower, and a lamp throws a star off the rifle in your hands
-- Distance fades into a peach haze that turns violet higher up, as in the concept's far hills.
local atmosphere = effect("Atmosphere") :: Atmosphere
atmosphere.Density = 0.3
atmosphere.Offset = 0.1
atmosphere.Color = Color3.fromRGB(252, 200, 170)
atmosphere.Decay = Color3.fromRGB(186, 150, 206)
atmosphere.Glare = 0.15
atmosphere.Haze = 1.4
-- A flat painted look has everything in focus.
local blur = Lighting:FindFirstChildOfClass("DepthOfFieldEffect")
if blur then
	blur.Enabled = false
end

-- The bare ground outside the town is sand, not the template's dark checkerboard.
local baseplate = workspace:FindFirstChild("Baseplate")
if baseplate and baseplate:IsA("BasePart") then
	baseplate.Color = SAND
	baseplate.Material = Enum.Material.SmoothPlastic
	for _, child in baseplate:GetChildren() do
		if child:IsA("Texture") or child:IsA("Decal") then
			child:Destroy()
		end
	end
end

game:GetService("ChangeHistoryService"):SetWaypoint("Set Desert FPS lighting")
return { clockTime = Lighting.ClockTime, sunElevation = math.deg(math.asin(Lighting:GetSunDirection().Y)) }
