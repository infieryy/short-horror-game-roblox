--!strict
-- What the player reads off the screen: health and armor, the weapon in hand and its rounds, the crosshair,
-- the mark of a hit, being hit, and who killed whom. It only shows what it is told.

local TweenService = game:GetService("TweenService")

local Config = require(script.Parent.HudConfig)

local Hud = {}
Hud.__index = Hud

local function outline(target: Instance, thickness: number)
	local stroke = Instance.new("UIStroke")
	stroke.Color = Config.Shade
	stroke.Thickness = thickness
	stroke.Transparency = 0.25
	stroke.Parent = target
end

local function label(parent: Instance, size: number, font: Enum.Font, alignX: Enum.TextXAlignment): TextLabel
	local text = Instance.new("TextLabel")
	text.BackgroundTransparency = 1
	text.Font = font
	text.TextSize = size
	text.TextColor3 = Config.Ink
	text.TextXAlignment = alignX
	text.TextYAlignment = Enum.TextYAlignment.Bottom
	text.AutomaticSize = Enum.AutomaticSize.XY
	text.Text = ""
	outline(text, 1.5)
	text.Parent = parent
	return text
end

-- A row or column that lays its children out from one corner of the screen.
local function block(parent: Instance, anchor: Vector2, position: UDim2, direction: Enum.FillDirection, gap: number): Frame
	local frame = Instance.new("Frame")
	frame.BackgroundTransparency = 1
	frame.AnchorPoint = anchor
	frame.Position = position
	frame.AutomaticSize = Enum.AutomaticSize.XY
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = direction
	layout.Padding = UDim.new(0, gap)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.HorizontalAlignment = if anchor.X > 0.5 then Enum.HorizontalAlignment.Right else Enum.HorizontalAlignment.Left
	layout.VerticalAlignment = Enum.VerticalAlignment.Bottom
	layout.Parent = frame
	frame.Parent = parent
	return frame
end

-- A number over a caption. Returns both.
local function reading(
	parent: Instance,
	caption: string,
	size: number,
	colour: Color3,
	alignX: Enum.TextXAlignment
): (TextLabel, TextLabel)
	local column = block(parent, Vector2.zero, UDim2.new(), Enum.FillDirection.Vertical, 0)
	local layout = column:FindFirstChildOfClass("UIListLayout") :: UIListLayout
	layout.HorizontalAlignment = if alignX == Enum.TextXAlignment.Right
		then Enum.HorizontalAlignment.Right
		else Enum.HorizontalAlignment.Left
	local number = label(column, size, Config.Font, alignX)
	number.TextColor3 = colour
	number.LayoutOrder = 1
	local under = label(column, Config.Small, Config.CaptionFont, alignX)
	under.Text = caption
	under.TextTransparency = Config.Dim
	under.LayoutOrder = 2
	return number, under
end

-- Four lines round a middle point: straight for the crosshair, turned 45 degrees for the hit mark.
local function cross(parent: Instance, shape: { Gap: number, Length: number, Thickness: number }, turned: boolean): Frame
	local holder = Instance.new("Frame")
	holder.BackgroundTransparency = 1
	holder.AnchorPoint = Vector2.new(0.5, 0.5)
	holder.Position = UDim2.fromScale(0.5, 0.5)
	holder.Size = UDim2.fromOffset(0, 0)
	holder.Rotation = if turned then 45 else 0
	local reach = shape.Gap + shape.Length / 2
	for _, way in { Vector2.new(1, 0), Vector2.new(-1, 0), Vector2.new(0, 1), Vector2.new(0, -1) } do
		local line = Instance.new("Frame")
		line.AnchorPoint = Vector2.new(0.5, 0.5)
		line.Position = UDim2.fromOffset(way.X * reach, way.Y * reach)
		line.Size = if way.X ~= 0
			then UDim2.fromOffset(shape.Length, shape.Thickness)
			else UDim2.fromOffset(shape.Thickness, shape.Length)
		line.BackgroundColor3 = Config.Ink
		line.BorderSizePixel = 0
		outline(line, 1)
		line.Parent = holder
	end
	holder.Parent = parent
	return holder
end

-- A part of a scope's view, and how see-through it is when the view is all there.
type Veil = { item: Instance, property: string, solid: number }

-- Draws a scope's view on a screen of that size: rings that make it blacker outward from the window's edge,
-- one that is all black, and bars from there to the screen's edges. Returns what was drawn.
local function scopeView(gui: ScreenGui, screen: Vector2): { Veil }
	gui:ClearAllChildren()
	local shape = Config.Scope
	local veils: { Veil } = {}
	local function ring(inner: number, thickness: number, transparency: number)
		local frame = Instance.new("Frame")
		frame.BackgroundTransparency = 1
		frame.AnchorPoint = Vector2.new(0.5, 0.5)
		frame.Position = UDim2.fromScale(0.5, 0.5)
		frame.Size = UDim2.fromOffset(2 * inner, 2 * inner)
		local round = Instance.new("UICorner")
		round.CornerRadius = UDim.new(1, 0)
		round.Parent = frame
		local stroke = Instance.new("UIStroke")
		stroke.Color = shape.Color
		stroke.Thickness = thickness
		stroke.Transparency = transparency
		stroke.Parent = frame
		frame.Parent = gui
		table.insert(veils, { item = stroke, property = "Transparency", solid = transparency })
	end
	local window = shape.Window * screen.Y / 2
	local fuzz = shape.Fuzz * screen.Y
	local step = fuzz / shape.Steps
	-- Every ring reaches from its own inner edge to where the black begins, so they lie on one another:
	-- rings laid side by side leave hairlines of light between them.
	local behind = 0 -- how black the rings inside this one already make it
	for index = 1, shape.Steps do
		local along = index / shape.Steps
		local wanted = along * along * (3 - 2 * along)
		ring(window + (index - 1) * step, fuzz - (index - 1) * step + 1, (1 - wanted) / (1 - behind))
		behind = wanted
	end
	-- The black ring reaches to the corners of the square round it; the bars take over from the square's sides.
	local black = window + fuzz
	ring(black, black * 0.45, 0)
	local sides = math.max(0, screen.X / 2 - black + 1)
	local ends = math.max(0, screen.Y / 2 - black + 1)
	for _, bar in
		{
			{ UDim2.fromScale(0, 0), UDim2.new(0, sides, 1, 0), Vector2.zero },
			{ UDim2.fromScale(1, 0), UDim2.new(0, sides, 1, 0), Vector2.new(1, 0) },
			{ UDim2.fromScale(0, 0), UDim2.new(1, 0, 0, ends), Vector2.zero },
			{ UDim2.fromScale(0, 1), UDim2.new(1, 0, 0, ends), Vector2.new(0, 1) },
		}
	do
		local frame = Instance.new("Frame")
		frame.Position, frame.Size, frame.AnchorPoint = bar[1], bar[2], bar[3]
		frame.BackgroundColor3 = shape.Color
		frame.BorderSizePixel = 0
		frame.Parent = gui
		table.insert(veils, { item = frame, property = "BackgroundTransparency", solid = 0 })
	end
	return veils
end

function Hud.new(playerGui: Instance, camera: Camera)
	local self = setmetatable({}, Hud)

	-- A scope's view, behind everything else the display shows. It is measured off the screen itself, not
	-- scaled with the rest.
	local scope = Instance.new("ScreenGui")
	scope.Name = "ScopeView"
	scope.IgnoreGuiInset = true
	scope.ResetOnSpawn = false
	scope.DisplayOrder = -1
	scope.Enabled = false
	scope.Parent = playerGui
	self.scope = scope
	self.camera = camera
	self.scopeVeils = {} :: { Veil }
	self.scopeIn = 0

	local gui = Instance.new("ScreenGui")
	gui.Name = "Hud"
	gui.IgnoreGuiInset = true
	gui.ResetOnSpawn = false
	gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	local scale = Instance.new("UIScale")
	scale.Parent = gui
	local function fit()
		scale.Scale = math.max(camera.ViewportSize.Y / Config.ReferenceHeight, Config.SmallestScale)
	end
	camera:GetPropertyChangedSignal("ViewportSize"):Connect(function()
		fit()
		self.scopeVeils = {} -- drawn for the old size: drawn again when next looked through
		self:setScope(0)
	end)
	fit()

	-- Being hit: the whole screen, behind everything else.
	local hurt = Instance.new("Frame")
	hurt.Size = UDim2.fromScale(1 / Config.SmallestScale, 1 / Config.SmallestScale)
	hurt.BackgroundColor3 = Config.Harm
	hurt.BackgroundTransparency = 1
	hurt.BorderSizePixel = 0
	hurt.Parent = gui
	self.hurtTint = hurt

	self.crosshair = cross(gui, Config.Crosshair, false)
	if Config.Crosshair.Dot then
		local dot = Instance.new("Frame")
		dot.AnchorPoint = Vector2.new(0.5, 0.5)
		dot.Size = UDim2.fromOffset(Config.Crosshair.Thickness, Config.Crosshair.Thickness)
		dot.BackgroundColor3 = Config.Ink
		dot.BorderSizePixel = 0
		dot.Parent = self.crosshair
	end
	-- An optic's mark, in place of the crosshair while looking through one: a red cross. Each of its bars
	-- lies on a dark one a little bigger, so the dark shows as a line round the whole cross and not across
	-- its middle.
	local mark = Config.SightCross
	local sightCross = Instance.new("Frame")
	sightCross.BackgroundTransparency = 1
	sightCross.AnchorPoint = Vector2.new(0.5, 0.5)
	sightCross.Position = UDim2.fromScale(0.5, 0.5)
	sightCross.Size = UDim2.fromOffset(0, 0)
	sightCross.Visible = false
	for layer, grow in { mark.Outline, 0 } do
		local long, thick = 2 * (mark.Arm + grow), mark.Thickness + 2 * grow
		for _, size in { UDim2.fromOffset(long, thick), UDim2.fromOffset(thick, long) } do
			local bar = Instance.new("Frame")
			bar.AnchorPoint = Vector2.new(0.5, 0.5)
			bar.Size = size
			bar.BackgroundColor3 = if grow > 0 then mark.OutlineColor else mark.Color
			bar.BackgroundTransparency = if grow > 0 then mark.OutlineTransparency else 0
			bar.BorderSizePixel = 0
			bar.ZIndex = layer
			bar.Parent = sightCross
		end
	end
	sightCross.Parent = gui
	self.sightCross = sightCross
	self.crosshairShown, self.throughOptic = true, false

	self.hitMark = cross(gui, Config.HitMark, true)
	self.hitMark.Visible = false

	-- Bottom left: health, then armor.
	local vitals = block(gui, Vector2.new(0, 1), UDim2.new(0, Config.Edge, 1, -Config.Edge), Enum.FillDirection.Horizontal, 28)
	self.health = reading(vitals, "HEALTH", Config.Big, Config.Ink, Enum.TextXAlignment.Left)
	self.armor = reading(vitals, "ARMOR", Config.Medium, Config.Accent, Enum.TextXAlignment.Left)

	-- Bottom right: rounds in reserve, then rounds in the magazine over the weapon's name.
	local rounds = block(gui, Vector2.new(1, 1), UDim2.new(1, -Config.Edge, 1, -Config.Edge), Enum.FillDirection.Horizontal, 16)
	self.reserve = reading(rounds, "IN RESERVE", Config.Medium, Config.Ink, Enum.TextXAlignment.Right)
	self.reserve.TextTransparency = Config.Dim
	self.magazine, self.weaponName = reading(rounds, "", Config.Big, Config.Ink, Enum.TextXAlignment.Right)

	-- Right, above the rounds: the weapons carried, the one in hand picked out.
	self.slots = block(gui, Vector2.new(1, 1), UDim2.new(1, -Config.Edge, 1, -Config.Edge - 120), Enum.FillDirection.Vertical, 4)
	self.slotLines = {} :: { [string]: TextLabel }

	-- Under the crosshair: a reload filling up.
	local reload = Instance.new("Frame")
	reload.AnchorPoint = Vector2.new(0.5, 0)
	reload.Position = UDim2.new(0.5, 0, 0.5, 44)
	reload.Size = UDim2.fromOffset(120, 4)
	reload.BackgroundColor3 = Config.Shade
	reload.BackgroundTransparency = 0.4
	reload.BorderSizePixel = 0
	reload.Visible = false
	local filled = Instance.new("Frame")
	filled.Size = UDim2.fromScale(0, 1)
	filled.BackgroundColor3 = Config.Ink
	filled.BorderSizePixel = 0
	filled.Parent = reload
	reload.Parent = gui
	self.reload, self.reloadFilled = reload, filled

	-- Under the crosshair: a word for what just happened.
	self.noticeLine = label(gui, Config.Medium, Config.Font, Enum.TextXAlignment.Center)
	self.noticeLine.AnchorPoint = Vector2.new(0.5, 0)
	self.noticeLine.Position = UDim2.new(0.5, 0, 0.5, Config.Notice.Below)
	self.noticeLine.Visible = false
	self.noticeAt = 0
	self.utilityLines = {} :: { [number]: TextLabel }

	-- Top right: who killed whom.
	self.feed = block(gui, Vector2.new(1, 0), UDim2.new(1, -Config.Edge, 0, Config.Edge), Enum.FillDirection.Vertical, 6)
	local feedLayout = self.feed:FindFirstChildOfClass("UIListLayout") :: UIListLayout
	feedLayout.VerticalAlignment = Enum.VerticalAlignment.Top
	self.feedCount = 0

	gui.Parent = playerGui
	self.gui = gui
	return self
end

-- A line of text in the display's type, for what else is drawn in its ScreenGui (the loadout).
Hud.label = label

function Hud.setVitals(self: any, health: number, armor: number)
	self.health.Text = tostring(math.ceil(health))
	self.armor.Text = tostring(math.ceil(armor))
end

-- `rounds` is nil for a weapon that takes none.
function Hud.setRounds(self: any, title: string, rounds: { magazine: number, reserve: number }?)
	self.weaponName.Text = string.upper(title)
	self.magazine.Text = if rounds then tostring(rounds.magazine) else ""
	self.reserve.Text = if rounds then tostring(rounds.reserve) else ""
	(self.reserve.Parent :: Frame).Visible = rounds ~= nil
end

-- The weapons carried, in key order, and which is in hand.
function Hud.setSlots(self: any, names: { string }, titles: { [string]: string }, current: string)
	for index, name in names do
		local line = self.slotLines[name]
		if not line then
			line = label(self.slots, Config.Small, Config.Font, Enum.TextXAlignment.Right)
			line.LayoutOrder = index
			self.slotLines[name] = line
		end
		line.Text = `{string.upper(titles[name])}   {index}`
		line.TextColor3 = if name == current then Config.Accent else Config.Ink
		line.TextTransparency = if name == current then 0 else Config.Dim
	end
end

-- How far through a reload, 0 to 1, or nil when not reloading.
function Hud.setReload(self: any, progress: number?)
	self.reload.Visible = progress ~= nil
	if progress then
		self.reloadFilled.Size = UDim2.fromScale(math.clamp(progress, 0, 1), 1)
	end
end

function Hud.setCrosshair(self: any, shown: boolean)
	self.crosshairShown = shown
	self.crosshair.Visible = shown and not self.throughOptic
	self.sightCross.Visible = shown and self.throughOptic
end

-- Whether the player is looking through an optic: its cross then stands in for the crosshair.
function Hud.setOptic(self: any, through: boolean)
	if through ~= self.throughOptic then
		self.throughOptic = through
		self:setCrosshair(self.crosshairShown)
	end
end

-- How far a weapon with a scope is raised, 0 to 1; 0 for any other weapon. Returns how much of the scope's
-- view is there, 0 to 1: once it is, the weapon itself should not be drawn.
function Hud.setScope(self: any, raised: number): number
	local from = Config.Scope.From
	local there = math.clamp((raised - from) / (1 - from), 0, 1)
	if there > 0 and #self.scopeVeils == 0 then
		self.scopeVeils = scopeView(self.scope, self.camera.ViewportSize)
		self.scopeIn = -1
	end
	if there ~= self.scopeIn then
		self.scopeIn = there
		self.scope.Enabled = there > 0
		for _, veil: Veil in self.scopeVeils do
			(veil.item :: any)[veil.property] = 1 - (1 - veil.solid) * there
		end
	end
	return there
end

-- A utility the player carries, under the weapons: its place in the list, its name, its key, how many are left.
function Hud.setUtility(self: any, order: number, title: string, key: string, left: number)
	local line = self.utilityLines[order]
	if not line then
		line = label(self.slots, Config.Small, Config.Font, Enum.TextXAlignment.Right)
		line.LayoutOrder = 50 + order
		self.utilityLines[order] = line
	end
	line.Text = `{string.upper(title)}  x{left}   {key}`
	line.TextTransparency = if left > 0 then 0 else Config.Dim
end

-- A word under the crosshair for a moment.
function Hud.notice(self: any, text: string, colour: Color3)
	self.noticeLine.Text = text
	self.noticeLine.TextColor3 = colour
	self.noticeLine.Visible = true
	self.noticeAt = os.clock()
	task.delay(Config.Notice.Time, function()
		if os.clock() - self.noticeAt >= Config.Notice.Time then
			self.noticeLine.Visible = false
		end
	end)
end

-- A line under the weapons carried, naming a key and what it is for.
function Hud.addKey(self: any, title: string, key: string)
	local line = label(self.slots, Config.Small, Config.Font, Enum.TextXAlignment.Right)
	line.LayoutOrder = 100
	line.Text = `{string.upper(title)}   {key}`
	line.TextTransparency = Config.Dim
end

-- A shot of the player's landed.
function Hud.hit(self: any, zone: string, killed: boolean)
	local colour = if killed then Config.Harm elseif zone == "head" then Config.Head else Config.Ink
	for _, line in self.hitMark:GetChildren() do
		if line:IsA("Frame") then
			line.BackgroundColor3 = colour
		end
	end
	self.hitMark.Visible = true
	self.hitAt = os.clock()
	task.delay(Config.HitMark.Time, function()
		if os.clock() - self.hitAt >= Config.HitMark.Time then
			self.hitMark.Visible = false
		end
	end)
end

-- The player was hit.
function Hud.hurt(self: any)
	self.hurtTint.BackgroundTransparency = Config.HurtTint
	TweenService:Create(self.hurtTint, TweenInfo.new(Config.HurtTime), { BackgroundTransparency = 1 }):Play()
end

-- A kill, for the list: who, whom, with what, whether to the head, whether through something (a wallbang).
function Hud.killed(self: any, killer: string, victim: string, weapon: string, head: boolean, through: boolean?)
	local line = label(self.feed, Config.Small, Config.CaptionFont, Enum.TextXAlignment.Right)
	line.RichText = true
	self.feedCount += 1
	line.LayoutOrder = self.feedCount
	local how = string.upper(weapon) .. (if head then ", HEAD" else "") .. (if through then ", THROUGH WALL" else "")
	local dim = Config.Ink:Lerp(Config.Shade, Config.Dim):ToHex()
	line.Text = `<b>{killer}</b>  <font color="#{dim}">{how}</font>  <b>{victim}</b>`
	task.delay(Config.FeedTime, line.Destroy, line)
	local lines = {}
	for _, child in self.feed:GetChildren() do
		if child:IsA("TextLabel") then
			table.insert(lines, child)
		end
	end
	table.sort(lines, function(a, b)
		return a.LayoutOrder < b.LayoutOrder
	end)
	for index = 1, #lines - Config.FeedLines do
		lines[index]:Destroy()
	end
end

return Hud
