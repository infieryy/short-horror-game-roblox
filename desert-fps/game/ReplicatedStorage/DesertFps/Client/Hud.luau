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

function Hud.new(playerGui: Instance, camera: Camera)
	local self = setmetatable({}, Hud)

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
	camera:GetPropertyChangedSignal("ViewportSize"):Connect(fit)
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
	-- An optic's dot, in place of the crosshair while looking through one.
	local sightDot = Instance.new("Frame")
	sightDot.AnchorPoint = Vector2.new(0.5, 0.5)
	sightDot.Position = UDim2.fromScale(0.5, 0.5)
	sightDot.Size = UDim2.fromOffset(Config.SightDot.Size, Config.SightDot.Size)
	sightDot.BackgroundColor3 = Config.SightDot.Color
	sightDot.BorderSizePixel = 0
	sightDot.Visible = false
	local round = Instance.new("UICorner")
	round.CornerRadius = UDim.new(1, 0)
	round.Parent = sightDot
	sightDot.Parent = gui
	self.sightDot = sightDot
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
	self.sightDot.Visible = shown and self.throughOptic
end

-- Whether the player is looking through an optic: its dot then stands in for the crosshair.
function Hud.setOptic(self: any, through: boolean)
	if through ~= self.throughOptic then
		self.throughOptic = through
		self:setCrosshair(self.crosshairShown)
	end
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

function Hud.killed(self: any, killer: string, victim: string, weapon: string, head: boolean)
	local line = label(self.feed, Config.Small, Config.CaptionFont, Enum.TextXAlignment.Right)
	line.RichText = true
	self.feedCount += 1
	line.LayoutOrder = self.feedCount
	local how = if head then `{string.upper(weapon)}, HEAD` else string.upper(weapon)
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
