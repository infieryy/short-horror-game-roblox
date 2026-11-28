--!strict
-- A weapon as it is with its attachments on: its numbers (WeaponConfig with AttachmentConfig's changes worked
-- in) and what to add to its model. The server uses this to decide what a shot does and to build the weapon
-- everyone sees; the client to make the weapon feel and look the same.

local WeaponConfig = require(script.Parent.WeaponConfig)
local AttachmentConfig = require(script.Parent.AttachmentConfig)

local Attachments = {}

-- socket -> attachment name
export type Chosen = { [string]: string }
-- What to do to a weapon's model: parts to copy onto it (`at` is where the part's middle goes from the weapon's
-- origin, `size` how big the part is to be, `socket` the socket it is on), and which of its own parts to make
-- how many times as long.
export type Fitting = {
	adds: { { template: BasePart, at: Vector3, size: Vector3, socket: string } },
	stretch: { [string]: number },
	-- Named points on what was added, from the weapon's origin: an optic's "eye", a laser's "beam".
	points: { [string]: Vector3 },
}

local built: { [string]: any } = {}

local function copy(value: any): any
	if typeof(value) ~= "table" then
		return value
	end
	local twin = {}
	for key, inner in value do
		twin[key] = copy(inner)
	end
	return twin
end

-- The table that holds the last name of a path like "Recoil.Sway", and that name. Tables on the way are made.
local function reach(config: any, path: string): (any, string)
	local names = string.split(path, ".")
	local holder = config
	for index = 1, #names - 1 do
		if typeof(holder[names[index]]) ~= "table" then
			holder[names[index]] = {}
		end
		holder = holder[names[index]]
	end
	return holder, names[#names]
end

-- The socket that attachment goes on, on that weapon. Nil: it does not go on it.
function Attachments.fits(weapon: string, attachment: string): string?
	local what = (AttachmentConfig.Attachments :: any)[attachment]
	return if what and what.Fits[weapon] then what.Socket else nil
end

-- The weapon's numbers with these attachments on. Do not change the table: it is shared, and the same
-- weapon with the same attachments is always the same table.
-- It also carries: Name (the weapon), Attached (socket -> attachment, those of `chosen` that go on it), and
-- Quicken, how many times as fast as made its draw and reload animations play to last as long as the draw
-- and the reload do.
function Attachments.build(weapon: string, chosen: Chosen?): any
	local names = {}
	for socket, name in chosen or {} do
		table.insert(names, `{socket}={name}`)
	end
	table.sort(names)
	local key = `{weapon}|{table.concat(names, ",")}`
	if built[key] then
		return built[key]
	end

	local plain = (WeaponConfig.Weapons :: any)[weapon]
	local config = copy(plain)
	local attached = {}
	for socket, name in chosen or {} do
		if Attachments.fits(weapon, name) ~= socket then
			continue
		end
		attached[socket] = name
		local changes = (AttachmentConfig.Attachments :: any)[name].Fits[weapon]
		for path, value in changes.Set or {} do
			local holder, last = reach(config, path)
			holder[last] = copy(value)
		end
		for path, amount in changes.Add or {} do
			local holder, last = reach(config, path)
			holder[last] = (holder[last] or 0) + amount
		end
		for path, factor in changes.Scale or {} do
			local holder, last = reach(config, path)
			if typeof(holder[last]) == "number" then
				holder[last] *= factor
			end
		end
	end
	config.Name = weapon
	config.Attached = attached
	config.Quicken = {
		Equip = plain.EquipTime / config.EquipTime,
		Reload = if plain.ReloadTime then plain.ReloadTime / config.ReloadTime else 1,
	}
	built[key] = config
	return config
end

-- What `attached` (a weapon's Attached) adds to the weapon's model. `weapon` is the weapon's model, named
-- after the weapon, and `models` holds the attachments' (ReplicatedStorage.DesertFps.WeaponModels.<weapon>
-- and .AttachmentModels): their parts carry an "Offset" and the models a "Socket_<name>" for each socket,
-- both from the model's origin.
function Attachments.fitting(weapon: Instance, models: Instance, attached: Chosen): Fitting
	local fitting: Fitting = { adds = {}, stretch = {}, points = {} }
	for socket, name in attached do
		local what = (AttachmentConfig.Attachments :: any)[name]
		local at = weapon:GetAttribute("Socket_" .. socket) :: Vector3?
		if not at then
			continue
		end
		if what.Stretch then
			fitting.stretch[socket] = what.Stretch
		end
		local model = what.Model and models:FindFirstChild(what.Model)
		if model then
			-- A piece is as big as it was made, or Size times that: it grows from where it meets the weapon.
			local size = what.Fits[weapon.Name].Size or 1
			for _, template in model:GetChildren() do
				if template:IsA("BasePart") then
					table.insert(fitting.adds, {
						template = template,
						at = at + (template:GetAttribute("Offset") :: Vector3) * size,
						size = template.Size * size,
						socket = socket,
					})
				end
			end
			for attribute, value in model:GetAttributes() do
				if string.sub(attribute, 1, 7) == "Socket_" then
					fitting.points[string.sub(attribute, 8)] = at + (value :: Vector3) * size
				end
			end
			-- Shots leave from the end of what is on the muzzle (weapons point along +X), not from under it.
			if socket == "muzzle" then
				local tip = at.X
				for _, template in model:GetChildren() do
					if template:IsA("BasePart") then
						tip = math.max(tip, at.X + ((template:GetAttribute("Offset") :: Vector3).X + template.Size.X / 2) * size)
					end
				end
				fitting.points.muzzle = Vector3.new(tip, at.Y, at.Z)
			end
		end
	end
	return fitting
end

-- A part `size` big with its middle `offset` from the weapon's origin, made `stretch` times as long downward
-- from its top: its new size and offset.
function Attachments.stretched(size: Vector3, offset: Vector3, stretch: number): (Vector3, Vector3)
	local longer = size.Y * (stretch - 1)
	return size + Vector3.new(0, longer, 0), offset - Vector3.new(0, longer / 2, 0)
end

return Attachments
