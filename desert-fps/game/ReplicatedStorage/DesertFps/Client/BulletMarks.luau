--!strict
-- The marks shots leave on the town. A shot that went through something leaves a dark hole where it went in
-- and a wider, torn one where it came out; a shot that was stopped leaves a pale chip and no hole. So the wall
-- says which it was. They are drawn on this client alone: the player's own shots at once, everyone else's
-- when the server says. Both go by Penetration.marks. MarkConfig is how they look.
--
-- A mark is fixed to the thing it is on: it moves with it and falls with it. When that thing goes the mark
-- goes too, unless something stands in its place: a wall that cracks keeps its marks.

local Debris = game:GetService("Debris")
local TweenService = game:GetService("TweenService")

local Config = require(script.Parent.MarkConfig)
local Sounds = require(script.Parent.Sounds)
local Effects = require(script.Parent.Effects)
local Penetration = require(script.Parent.Parent.Weapons.Penetration)

local BulletMarks = {}
BulletMarks.__index = BulletMarks

-- A shape of a drawing: how wide and high it is, where its middle is and how far it is turned (degrees).
-- Lengths are shares of the mark's own size, from the middle of the mark.
type Shape = { size: Vector2, at: Vector2, turn: number }
type Paints = { Hole: Color3, Rim: Color3, Edge: Color3 }

-- A drawing has this much room, in marks across, for what sticks out of the mark.
local ROOM = 2.2
-- How wide the line round a rim or a chip is.
local LINE = 0.05

local random = Random.new()

local function dab(across: number, at: Vector2?): Shape
	return { size = Vector2.new(across, across), at = at or Vector2.zero, turn = 0 }
end

-- `count` strokes pointing out of the middle, about evenly round it and no two alike. Each starts `from` the
-- middle.
local function rays(count: number, long: NumberRange, wide: NumberRange, from: number): { Shape }
	local list = {}
	for index = 1, count do
		local angle = (index + random:NextNumber(-0.35, 0.35)) / count * 360
		local length = random:NextNumber(long.Min, long.Max)
		local along = Vector2.new(math.cos(math.rad(angle)), math.sin(math.rad(angle)))
		table.insert(list, {
			size = Vector2.new(length, random:NextNumber(wide.Min, wide.Max)),
			at = along * (from + length / 2),
			turn = angle,
		})
	end
	return list
end

-- Paints shapes in one colour, each `grow` larger all round. Every shape is round at its ends, like the
-- strokes the town is painted with.
local function paint(gui: SurfaceGui, shapes: { Shape }, colour: Color3, layer: number, grow: number?)
	local more = (grow or 0) * 2
	for _, each in shapes do
		local frame = Instance.new("Frame")
		frame.AnchorPoint = Vector2.new(0.5, 0.5)
		frame.BackgroundColor3 = colour
		frame.BorderSizePixel = 0
		frame.Size = UDim2.fromScale((each.size.X + more) / ROOM, (each.size.Y + more) / ROOM)
		frame.Position = UDim2.fromScale(0.5 + each.at.X / ROOM, 0.5 + each.at.Y / ROOM)
		frame.Rotation = each.turn
		frame.ZIndex = layer
		local corner = Instance.new("UICorner")
		corner.CornerRadius = UDim.new(0.5, 0)
		corner.Parent = frame
		frame.Parent = gui
	end
end

-- Shapes in the look's Rim, with its Edge as a line round them all.
local function rim(gui: SurfaceGui, shapes: { Shape }, look: Paints, line: number)
	paint(gui, shapes, look.Edge, 1, line)
	paint(gui, shapes, look.Rim, 2)
end

local kinds: { [string]: (gui: SurfaceGui, look: Paints) -> () } = {
	-- Where a shot went in: a dark hole in a rim chipped in a few places.
	["in"] = function(gui, look)
		local broken = rays(3, NumberRange.new(0.16, 0.3), NumberRange.new(0.12, 0.18), 0.28)
		table.insert(broken, dab(0.8))
		rim(gui, broken, look, LINE)
		paint(gui, { dab(0.5, Vector2.new(0.02, -0.01)), dab(0.3, Vector2.new(-0.1, 0.08)) }, look.Hole, 3)
	end,
	-- Where it came out: the hole is torn open, outwards all round.
	out = function(gui, look)
		local torn = rays(7, NumberRange.new(0.2, 0.42), NumberRange.new(0.11, 0.19), 0.22)
		table.insert(torn, dab(0.66))
		rim(gui, torn, look, LINE * 0.8)
		paint(
			gui,
			{ dab(0.42), dab(0.28, Vector2.new(0.1, 0.07)), dab(0.22, Vector2.new(-0.12, -0.06)) },
			look.Hole,
			3
		)
	end,
	-- Where it was stopped: a chip off the surface with cracks from under it, and no hole.
	stop = function(gui, look)
		paint(gui, rays(3, NumberRange.new(0.4, 0.62), NumberRange.new(0.045, 0.06), 0.1), look.Edge, 0)
		rim(gui, {
			dab(0.56),
			dab(0.36, Vector2.new(0.2, 0.1)),
			dab(0.3, Vector2.new(-0.16, -0.18)),
		}, look, LINE)
		paint(gui, { dab(0.2, Vector2.new(0.03, 0.02)) }, look.Rim:Lerp(look.Edge, 0.3), 3)
	end,
}

local function draw(kind: string, look: Paints): BasePart
	local across = (Config.Size :: any)[kind] * ROOM
	local part = Instance.new("Part")
	part.Name = "BulletMark"
	part.Size = Vector3.new(across, across, 0.02)
	part.Transparency = 1
	part.Massless = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	local gui = Instance.new("SurfaceGui")
	gui.Face = Enum.NormalId.Front
	gui.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
	gui.PixelsPerStud = Config.PixelsPerStud
	gui.LightInfluence = 1 -- lit like the wall it is on, not glowing in the shade
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	gui.Parent = part
	kinds[kind](gui, look)
	return part
end

-- The drawings of each kind for each material, made the first time one is needed and copied after that.
local drawn: { [string]: { BasePart } } = {}

local function drawing(material: string, kind: string, look: Paints): BasePart
	local key = material .. " " .. kind
	local made = drawn[key]
	if not made then
		made = {}
		for index = 1, Config.Drawings do
			made[index] = draw(kind, look)
		end
		drawn[key] = made
	end
	return made[random:NextInteger(1, #made)]:Clone()
end

-- A mark that was left: its drawing, its kind, what it is on, and the breakable piece that is a part of.
type Left = { part: BasePart, kind: string, on: BasePart, piece: Instance? }

-- `parent` is where the marks and what flies off them are drawn.
function BulletMarks.new(parent: Instance)
	local self = setmetatable({}, BulletMarks)
	self.parent = parent
	self.left = {} :: { Left } -- the marks there are, the oldest first
	self.watched = {} :: { [BasePart]: RBXScriptConnection } -- what they are on, until it goes
	return self
end

-- The breakable piece a part belongs to, if it belongs to one.
local function pieceOf(part: Instance): Instance?
	local model = part:FindFirstAncestorWhichIsA("Model")
	while model and model:GetAttribute("Piece") == nil do
		model = model:FindFirstAncestorWhichIsA("Model")
	end
	return model
end

-- Makes a mark a part of `on`, where the mark is now.
local function fix(left: Left, on: BasePart)
	local old = left.part:FindFirstChildOfClass("WeldConstraint")
	if old then
		old:Destroy()
	end
	local weld = Instance.new("WeldConstraint")
	weld.Part0 = on
	weld.Part1 = left.part
	weld.Parent = left.part
	left.part.Anchored = false
	left.on = on
end

-- A mark whose surface is gone looks for what stands there now. A wall that cracks is swapped for its
-- shards, a little out of place: the mark moves onto the shard under it. False if there is nothing.
function BulletMarks.rehome(self: any, left: Left): boolean
	local piece = left.piece
	if not (piece and piece:IsDescendantOf(workspace)) then
		return false
	end
	local only = RaycastParams.new()
	only.FilterType = Enum.RaycastFilterType.Include
	only.FilterDescendantsInstances = { piece }
	local frame = left.part.CFrame
	local out = frame.LookVector
	local hit = workspace:Raycast(frame.Position + out * Config.Reach, -out * Config.Reach * 2, only)
	if not hit then
		return false
	end
	left.part.CFrame = frame.Rotation + (hit.Position + out * Config.Lift)
	fix(left, hit.Instance :: BasePart)
	self:watch(hit.Instance)
	return true
end

-- Watches what a mark is on. When it goes, its marks hold still until what replaces it has had time to
-- arrive, and then move onto that or go too.
function BulletMarks.watch(self: any, on: BasePart)
	if self.watched[on] then
		return
	end
	self.watched[on] = on.AncestryChanged:Connect(function()
		local watching = self.watched[on]
		if on:IsDescendantOf(workspace) or not watching then
			return
		end
		watching:Disconnect()
		self.watched[on] = nil
		local orphans = {}
		for _, left in self.left do
			if left.on == on and left.part.Parent then
				left.part.Anchored = true
				table.insert(orphans, left)
			end
		end
		task.delay(Config.Settle, function()
			for _, left in orphans do
				if left.part.Parent and not self:rehome(left) then
					left.part:Destroy()
				end
			end
		end)
	end)
end

-- Forgets the marks that are gone, takes the oldest away if there are too many, and stops watching what no
-- mark is on any more.
function BulletMarks.tidy(self: any)
	local left: { Left } = {}
	for _, each in self.left do
		if each.part.Parent then
			table.insert(left, each)
		end
	end
	while #left > Config.Most do
		(table.remove(left, 1) :: Left).part:Destroy()
	end
	self.left = left
	local marked: { [BasePart]: boolean } = {}
	for _, each in left do
		marked[each.on] = true
	end
	for on, gone in self.watched do
		if not marked[on] then
			gone:Disconnect()
			self.watched[on] = nil
		end
	end
end

-- A ball of dust off the surface.
local function puff(parent: Instance, mark: Penetration.Mark, colour: Color3)
	local how = (Config.Puff :: any)[mark.kind]
	local ball = Instance.new("Part")
	ball.Shape = Enum.PartType.Ball
	ball.Material = Enum.Material.SmoothPlastic
	ball.Color = colour
	ball.Transparency = Config.Puff.Start
	ball.Anchored = true
	ball.CanCollide = false
	ball.CanQuery = false
	ball.CanTouch = false
	ball.CastShadow = false
	ball.Size = Vector3.one * how.From
	ball.Position = mark.at + mark.normal * (how.From / 2)
	ball.Parent = parent
	local drift = TweenInfo.new(how.Time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	TweenService:Create(ball, drift, {
		Size = Vector3.one * how.To,
		Position = mark.at + mark.normal * how.Out,
		Transparency = 1,
	}):Play()
	Debris:AddItem(ball, how.Time)
end

-- Leaves the marks of a shot (Penetration.marks).
function BulletMarks.leave(self: any, marks: { Penetration.Mark })
	if typeof(marks) ~= "table" then
		return
	end
	-- A shot is heard where it first meets something, and where it ends if that is somewhere else: not at
	-- every hole of a shot that goes through four things.
	local sounded = 0
	for index, mark in marks do
		local on = mark.part
		-- What the shot broke is gone by the time its marks are heard of.
		if typeof(on) ~= "Instance" or not on:IsA("BasePart") or not on:IsDescendantOf(workspace) then
			continue
		end
		local size = (Config.Size :: any)[mark.kind]
		if not size or typeof(mark.at) ~= "Vector3" or typeof(mark.normal) ~= "Vector3" then
			continue
		end
		local material = Penetration.material(on) or "hard"
		local look = (Config.Materials :: any)[material] or Config.Materials.hard
		if look.Dust then
			puff(self.parent, mark, look.Dust)
		end
		if look.Sparks ~= false then
			Effects.sparks(mark.at, mark.normal, mark.kind, look.Chip)
		end
		if look.Sound and mark.kind ~= "out" and (sounded == 0 or index == #marks) then
			sounded += 1
			Sounds.play(if mark.kind == "stop" then look.Sound.Stopped else look.Sound.Through, mark.at)
		end
		if not look.Rim then
			continue
		end

		local part = drawing(material, mark.kind, look)
		local across = part.Size.X * (1 + random:NextNumber(-Config.Vary, Config.Vary))
		part.Size = Vector3.new(across, across, part.Size.Z)
		local off = mark.at + mark.normal * (Config.Lift + random:NextNumber(0, Config.LiftSpread))
		-- The drawing is on the part's front, which looks out of the surface.
		local up = if math.abs(mark.normal.Y) > 0.99 then Vector3.xAxis else Vector3.yAxis
		part.CFrame = CFrame.lookAlong(off, mark.normal, up) * CFrame.Angles(0, 0, random:NextNumber(0, math.pi * 2))
		local left: Left = { part = part, kind = mark.kind, on = on, piece = pieceOf(on) }
		fix(left, on)
		part.Parent = self.parent
		self:watch(on)

		table.insert(self.left, left)
		Debris:AddItem(part, Config.Life)
	end
	self:tidy()
end

-- How many marks there are now, in all and of each kind, for tests.
function BulletMarks.state(self: any): { [string]: number }
	local counts = { total = 0 }
	for _, each in self.left do
		if each.part.Parent then
			counts.total += 1
			counts[each.kind] = (counts[each.kind] or 0) + 1
		end
	end
	return counts
end

return BulletMarks
