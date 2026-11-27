--!strict
-- The loadout: what is on the weapon in hand, and what else could be. A row for each socket of the weapon that
-- something fits, with a choice for each thing that fits and one for nothing. It only shows and asks: a
-- choice calls `pick`, and the weapons decide what comes of it.
-- While it shows the mouse is free, and a click beside the panel closes it.

local AttachmentConfig = require(script.Parent.Parent.Weapons.AttachmentConfig)
local Attachments = require(script.Parent.Parent.Weapons.Attachments)
local Config = require(script.Parent.HudConfig)
local Hud = require(script.Parent.Hud)

local LoadoutMenu = {}
LoadoutMenu.__index = LoadoutMenu

local Menu = Config.Menu

local function padding(target: Instance, x: number, y: number)
	local pad = Instance.new("UIPadding")
	pad.PaddingLeft, pad.PaddingRight = UDim.new(0, x), UDim.new(0, x)
	pad.PaddingTop, pad.PaddingBottom = UDim.new(0, y), UDim.new(0, y)
	pad.Parent = target
end

local function list(target: Instance, direction: Enum.FillDirection, gap: number): UIListLayout
	local layout = Instance.new("UIListLayout")
	layout.FillDirection = direction
	layout.Padding = UDim.new(0, gap)
	layout.SortOrder = Enum.SortOrder.LayoutOrder
	layout.Parent = target
	return layout
end

-- `gui`: the display's own ScreenGui, so the menu is scaled with it. `pick(socket, name)`: the player chose
-- that attachment for that socket, or nothing for it (no name). `close()`: the player clicked beside the panel.
function LoadoutMenu.new(gui: ScreenGui, pick: (socket: string, name: string?) -> (), close: () -> ())
	local self = setmetatable({}, LoadoutMenu)
	self.pick = pick
	self.shown = false

	local root = Instance.new("Frame")
	root.Name = "Loadout"
	root.BackgroundTransparency = 1
	root.Size = UDim2.fromScale(1, 1)
	root.ZIndex = 10
	root.Visible = false

	-- Everything behind is dimmed. A button that is Modal frees the mouse while it shows.
	local behind = Instance.new("TextButton")
	behind.Text = ""
	behind.AutoButtonColor = false
	behind.Modal = true
	behind.AnchorPoint = Vector2.new(0.5, 0.5)
	behind.Position = UDim2.fromScale(0.5, 0.5)
	behind.Size = UDim2.fromScale(1 / Config.SmallestScale, 1 / Config.SmallestScale)
	behind.BackgroundColor3 = Config.Shade
	behind.BackgroundTransparency = Menu.Behind
	behind.BorderSizePixel = 0
	behind.Activated:Connect(close)
	behind.Parent = root

	local panel = Instance.new("Frame")
	panel.Active = true -- a click on the panel is not a click beside it
	panel.AnchorPoint = Vector2.new(0.5, 0.5)
	panel.Position = UDim2.fromScale(0.5, 0.5)
	panel.Size = UDim2.fromOffset(Menu.Width, 0)
	panel.AutomaticSize = Enum.AutomaticSize.Y
	panel.BackgroundColor3 = Config.Shade
	panel.BackgroundTransparency = Menu.Panel
	panel.BorderSizePixel = 0
	padding(panel, Menu.Padding, Menu.Padding)
	list(panel, Enum.FillDirection.Vertical, Menu.Gap)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, Menu.Corner)
	corner.Parent = panel
	panel.Parent = root

	local heading = Instance.new("Frame")
	heading.BackgroundTransparency = 1
	heading.Size = UDim2.fromScale(1, 0)
	heading.AutomaticSize = Enum.AutomaticSize.Y
	heading.LayoutOrder = 0
	list(heading, Enum.FillDirection.Vertical, 2)
	self.title = Hud.label(heading, Config.Medium, Config.Font, Enum.TextXAlignment.Left)
	local under = Hud.label(heading, Config.Small, Config.CaptionFont, Enum.TextXAlignment.Left)
	under.Text = "ATTACHMENTS"
	under.TextTransparency = Config.Dim
	under.LayoutOrder = 1
	heading.Parent = panel

	self.rows = Instance.new("Frame")
	self.rows.BackgroundTransparency = 1
	self.rows.Size = UDim2.fromScale(1, 0)
	self.rows.AutomaticSize = Enum.AutomaticSize.Y
	self.rows.LayoutOrder = 1
	list(self.rows, Enum.FillDirection.Vertical, Menu.Gap)
	self.rows.Parent = panel

	-- What the choice under the mouse does, or how to leave.
	self.about = Hud.label(panel, Config.Small, Config.CaptionFont, Enum.TextXAlignment.Left)
	self.about.TextTransparency = Config.Dim
	self.about.LayoutOrder = 2
	self.about.Text = Menu.Hint

	root.Parent = gui
	self.root = root
	return self
end

local function choice(self: any, parent: Instance, order: number, socket: string, name: string?, picked: boolean)
	local what = if name then (AttachmentConfig.Attachments :: any)[name] else nil
	local button = Instance.new("TextButton")
	button.LayoutOrder = order
	button.AutoButtonColor = false
	button.AutomaticSize = Enum.AutomaticSize.XY
	button.BorderSizePixel = 0
	button.Font = Config.Font
	button.TextSize = Config.Small
	button.Text = string.upper(if what then what.Title else "None")
	-- The one that is on the weapon is the town's turquoise; the rest wait, pale.
	button.BackgroundColor3 = if picked then Config.Accent else Config.Ink
	button.BackgroundTransparency = if picked then 0 else Menu.Choice
	button.TextColor3 = if picked then Config.Shade else Config.Ink
	padding(button, Menu.ChoicePadding.X, Menu.ChoicePadding.Y)
	local corner = Instance.new("UICorner")
	corner.CornerRadius = UDim.new(0, Menu.Corner)
	corner.Parent = button
	button.MouseEnter:Connect(function()
		self.about.Text = if what then what.About else "Nothing on this socket."
		if not picked then
			button.BackgroundTransparency = Menu.ChoiceUnder
		end
	end)
	button.MouseLeave:Connect(function()
		self.about.Text = Menu.Hint
		if not picked then
			button.BackgroundTransparency = Menu.Choice
		end
	end)
	button.Activated:Connect(function()
		self.pick(socket, name)
	end)
	button.Parent = parent
end

-- Shows the loadout of a weapon. `weapon`: its numbers as it is fitted (Attachments.build).
function LoadoutMenu.show(self: any, weapon: any)
	self.rows:ClearAllChildren()
	list(self.rows, Enum.FillDirection.Vertical, Menu.Gap)
	self.title.Text = string.upper(weapon.Title)
	self.about.Text = Menu.Hint

	local rows = 0
	for order, socket in AttachmentConfig.Sockets do
		local names = {}
		for name in AttachmentConfig.Attachments :: { [string]: any } do
			if Attachments.fits(weapon.Name, name) == socket then
				table.insert(names, name)
			end
		end
		if #names == 0 then
			continue
		end
		table.sort(names)
		rows += 1

		local row = Instance.new("Frame")
		row.BackgroundTransparency = 1
		row.Size = UDim2.fromScale(1, 0)
		row.AutomaticSize = Enum.AutomaticSize.Y
		row.LayoutOrder = order
		local caption = Hud.label(row, Config.Small, Config.CaptionFont, Enum.TextXAlignment.Left)
		caption.AutomaticSize = Enum.AutomaticSize.None
		caption.Size = UDim2.fromOffset(Menu.Caption, Config.Small + 2 * Menu.ChoicePadding.Y) -- as tall as a choice
		caption.TextYAlignment = Enum.TextYAlignment.Center
		caption.TextTransparency = Config.Dim
		caption.Text = string.upper(socket)
		local choices = Instance.new("Frame")
		choices.BackgroundTransparency = 1
		choices.Position = UDim2.fromOffset(Menu.Caption, 0)
		choices.Size = UDim2.new(1, -Menu.Caption, 0, 0)
		choices.AutomaticSize = Enum.AutomaticSize.Y
		list(choices, Enum.FillDirection.Horizontal, Menu.ChoiceGap).Wraps = true
		local on = weapon.Attached[socket]
		choice(self, choices, 0, socket, nil, on == nil)
		for index, name in names do
			choice(self, choices, index, socket, name, on == name)
		end
		choices.Parent = row
		row.Parent = self.rows
	end
	if rows == 0 then
		local none = Hud.label(self.rows, Config.Small, Config.CaptionFont, Enum.TextXAlignment.Left)
		none.Text = `Nothing goes on the {string.lower(weapon.Title)}.`
	end

	self.root.Visible = true
	self.shown = true
end

function LoadoutMenu.hide(self: any)
	self.root.Visible = false
	self.shown = false
end

return LoadoutMenu
