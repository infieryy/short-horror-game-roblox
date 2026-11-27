--!strict
-- The path of a shot through the town: what it goes through, how much force it has left after each thing, and
-- where it ends. Worked out the same way by the client (to show the shot and to say whom it thinks it hit) and
-- by the server (to decide). PenetrationConfig says what can be gone through.

local Config = require(script.Parent.PenetrationConfig)
local CombatConfig = require(script.Parent.Parent.Combat.CombatConfig)

local Penetration = {}

-- Something the shot went through: the part, how far along the shot it was entered and left, where it was
-- entered, and the share of its force the shot had before and after.
export type Pierced = { part: BasePart, enter: number, leave: number, at: Vector3, before: number, left: number }
export type Path = {
	finish: Vector3, -- where the shot ends
	reach: number, -- how far that is along it
	pierced: { Pierced },
	stopped: RaycastResult?, -- what it ended in; nil if it ran out of range, or met a body
	force: number, -- the share of its force it had where it ended
	body: RaycastResult?, -- the part of a body it met, if bodies are not left out of the cast
}

-- The kit piece a part belongs to: a piece that breaks is a model that says so; dressing that does not is a
-- part, or is in a model, named after its piece.
local function materialOf(part: Instance): { Loss: number }?
	local names = { part.Name, if part.Parent then part.Parent.Name else "" }
	local model = part:FindFirstAncestorWhichIsA("Model")
	while model do
		local piece = model:GetAttribute("Piece")
		if typeof(piece) == "string" then
			names = { piece }
			break
		end
		model = model:FindFirstAncestorWhichIsA("Model")
	end
	for _, name in names do
		local material = (Config.Pieces :: any)[name] or (Config.Pieces :: any)[string.match(name, "^[^_]+") or name]
		if material then
			return (Config.Materials :: any)[material]
		end
	end
	return nil
end

-- The body a part belongs to, if it belongs to one.
local function bodyOf(part: Instance): Model?
	local model = part:FindFirstAncestorWhichIsA("Model")
	while model do
		if model:FindFirstChildOfClass("Humanoid") then
			return model
		end
		model = model:FindFirstAncestorWhichIsA("Model")
	end
	return nil
end

-- How thick `hit.Instance` is along the shot, if it is no thicker than `most`: found by looking back at it from
-- that far on. A look that starts inside the part sees nothing of it, and then it is too thick.
local function thickness(hit: RaycastResult, direction: Vector3, most: number): number?
	local only = RaycastParams.new()
	only.FilterType = Enum.RaycastFilterType.Include
	only.FilterDescendantsInstances = { hit.Instance }
	local reach = most + 0.02
	local back = workspace:Raycast(hit.Position + direction * reach, -direction * reach, only)
	return if back then (back.Position - hit.Position).Magnitude else nil
end

-- The path of a shot from `origin` along `direction` (a unit vector), `range` studs at most, from a weapon
-- with that `pierce`. `params` says what the shot does not meet at all (the shooter; on the server, every
-- body, which it tests for itself).
function Penetration.trace(origin: Vector3, direction: Vector3, range: number, pierce: number, params: RaycastParams): Path
	local mine = RaycastParams.new()
	mine.FilterType = params.FilterType
	local ignore = table.clone(params.FilterDescendantsInstances)
	mine.FilterDescendantsInstances = ignore
	local pierced: { Pierced } = {}
	local from, travelled, force = origin, 0, 1
	while true do
		local hit = workspace:Raycast(from, direction * (range - travelled), mine)
		if not hit then
			break
		end
		local enter = travelled + hit.Distance
		local body = bodyOf(hit.Instance)
		if body then
			if hit.Instance.Parent == body and (CombatConfig.Zones :: any)[hit.Instance.Name] then
				return { finish = hit.Position, reach = enter, pierced = pierced, force = force, body = hit }
			end
			-- Hair, a hat, a pack on the back: on a body, and no part of it. The shot goes on to what is under
			-- it. (Told that a shot met "hair", the server had to guess which part was meant, and a shot to
			-- the head was taken for one to the hand held up in front of it.)
			table.insert(ignore, hit.Instance)
			mine.FilterDescendantsInstances = ignore
			from, travelled = hit.Position, enter
			continue
		end
		local material = if pierce > 0 and #pierced < Config.Most then materialOf(hit.Instance) else nil
		local most = if material then (force - Config.Least) * pierce / material.Loss else 0
		local thick = if material and most > 0 then thickness(hit, direction, most) else nil
		if not (material and thick) then
			return { finish = hit.Position, reach = enter, pierced = pierced, force = force, stopped = hit }
		end
		local left = force - material.Loss * thick / pierce
		table.insert(pierced, {
			part = hit.Instance :: BasePart,
			enter = enter,
			leave = enter + thick,
			at = hit.Position,
			before = force,
			left = left,
		})
		force = left
		-- On from just inside it, and no longer meeting it: something that overlaps it is met at its own face.
		table.insert(ignore, hit.Instance)
		mine.FilterDescendantsInstances = ignore
		from, travelled = hit.Position + direction * 0.01, enter + 0.01
	end
	return { finish = origin + direction * range, reach = range, pierced = pierced, force = force }
end

-- The share of its force the shot has `distance` along its path.
function Penetration.left(path: Path, distance: number): number
	local force = 1
	for _, each in path.pierced do
		if each.enter < distance then
			force = each.left
		end
	end
	return force
end

return Penetration
