--!strict
-- A laser's light: a thin beam from the laser on a weapon to what it points at, and a dot there.
-- The player's own shines from the weapon in front of their camera to where their shot will go. Everyone
-- else's shines straight out of the weapon in their character's hand, so a laser gives its holder away.

local Players = game:GetService("Players")

local AttachmentConfig = require(script.Parent.Parent.Weapons.AttachmentConfig)

local LaserSight = {}
LaserSight.__index = LaserSight

local Look = AttachmentConfig.Laser

function LaserSight.new(parent: Instance)
	local self = setmetatable({}, LaserSight)
	local dot = Instance.new("Part")
	dot.Name = "LaserDot"
	dot.Shape = Enum.PartType.Ball
	dot.Material = Enum.Material.Neon
	dot.Color = Look.Color
	dot.Anchored = true
	dot.CanCollide = false
	dot.CanQuery = false
	dot.CanTouch = false
	dot.CastShadow = false
	local finish = Instance.new("Attachment")
	finish.Parent = dot
	local beam = Instance.new("Beam")
	beam.Attachment1 = finish
	beam.FaceCamera = true
	beam.Segments = 1
	beam.Color = ColorSequence.new(Look.Color)
	beam.LightEmission = Look.Beam.Glow
	beam.LightInfluence = 0
	beam.Transparency = NumberSequence.new(Look.Beam.Near, Look.Beam.Far)
	beam.Width0 = Look.Beam.Width
	beam.Parent = dot
	self.parent, self.dot, self.beam = parent, dot, beam
	return self
end

-- Shines it at `at`: the dot there if it landed on something (`landed`), and a beam to it from `from`, the
-- laser's emitter, if one is given. With no `at` it goes dark.
function LaserSight.shine(self: any, at: Vector3?, landed: boolean?, from: Attachment?)
	if not at then
		self.dot.Parent = nil
		return
	end
	-- Both are sized by how far they are from the eye, so that neither thins to nothing across a square.
	local away = (at - workspace.CurrentCamera.CFrame.Position).Magnitude
	self.dot.Size = Vector3.one * math.max(Look.Least, away * Look.PerStud)
	self.dot.Transparency = if landed then 0 else 1
	self.dot.Position = at
	self.beam.Attachment0 = from
	self.beam.Enabled = from ~= nil
	self.beam.Width1 = math.max(Look.Beam.Width, away * Look.Beam.PerStud)
	self.dot.Parent = self.parent
end

function LaserSight.destroy(self: any)
	self.dot:Destroy()
end

-- The lasers on the weapons other players hold, by player. The server puts an attachment named "Laser" on a
-- weapon that carries one, at the emitter, looking along the barrel.
local theirs: { [Player]: any } = {}

-- Shines every other player's laser: call each frame. `me` is left out.
function LaserSight.shineOthers(parent: Instance, me: Player?)
	for _, other in Players:GetPlayers() do
		local tool = if other ~= me and other.Character then other.Character:FindFirstChildOfClass("Tool") else nil
		local handle = tool and tool:FindFirstChild("Handle")
		local emitter = handle and handle:FindFirstChild("Laser")
		if not (emitter and emitter:IsA("Attachment")) then
			if theirs[other] then
				theirs[other]:shine(nil)
			end
			continue
		end
		local laser = theirs[other]
		if not laser then
			laser = LaserSight.new(parent)
			theirs[other] = laser
		end
		local params = RaycastParams.new()
		params.FilterType = Enum.RaycastFilterType.Exclude
		params.FilterDescendantsInstances = { other.Character :: Instance, parent }
		local from, along = emitter.WorldPosition, emitter.WorldCFrame.LookVector
		local hit = workspace:Raycast(from, along * Look.Range, params)
		laser:shine(if hit then hit.Position else from + along * Look.Range, hit ~= nil, emitter)
	end
end

Players.PlayerRemoving:Connect(function(gone)
	if theirs[gone] then
		theirs[gone]:destroy()
		theirs[gone] = nil
	end
end)

return LaserSight
