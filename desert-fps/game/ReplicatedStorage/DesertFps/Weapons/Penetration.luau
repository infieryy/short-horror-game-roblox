--!strict
-- The path of a shot through the town: what it goes through, how much force it has left after each thing, and
-- where it ends. Worked out the same way by the client (to show the shot and to say whom it thinks it hit) and
-- by the server (to decide). PenetrationConfig says what can be gone through.

local Config = require(script.Parent.PenetrationConfig)
local CombatConfig = require(script.Parent.Parent.Combat.CombatConfig)

local Penetration = {}

-- Something the shot went through: the part, how far along the shot it was entered and left, where it was
-- entered and left and which way those faces look, and the share of its force the shot had before and after.
export type Pierced = {
	part: BasePart,
	enter: number,
	leave: number,
	at: Vector3,
	normal: Vector3,
	out: Vector3,
	outNormal: Vector3,
	before: number,
	left: number,
}
-- A mark a shot leaves on what it met: "in" where it went into something it came out of, "out" where it came
-- out, "stop" where it was stopped.
export type Mark = { part: BasePart, at: Vector3, normal: Vector3, kind: string }
export type Path = {
	finish: Vector3, -- where the shot ends
	reach: number, -- how far that is along it
	pierced: { Pierced },
	stopped: RaycastResult?, -- what it ended in; nil if it ran out of range, or met a body
	force: number, -- the share of its force it had where it ended
	body: RaycastResult?, -- the part of a body it met, if bodies are not left out of the cast
}

-- What a part is made of: a name in PenetrationConfig.Materials, or nil if it stops every shot. It goes by
-- the kit piece the part belongs to: a piece that breaks is a model that says so; dressing that does not is a
-- part, or is in a model, named after its piece.
function Penetration.material(part: Instance): string?
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
			return material
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

-- Where the shot comes out of `hit.Instance`, if that is no thicker along the shot than `most`: found by
-- looking back at it from that far on. A look that starts inside the part sees nothing of it, and then it is
-- too thick.
local function farSide(hit: RaycastResult, direction: Vector3, most: number): RaycastResult?
	local only = RaycastParams.new()
	only.FilterType = Enum.RaycastFilterType.Include
	only.FilterDescendantsInstances = { hit.Instance }
	local reach = most + 0.02
	return workspace:Raycast(hit.Position + direction * reach, -direction * reach, only)
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
		local made = if pierce > 0 and #pierced < Config.Most then Penetration.material(hit.Instance) else nil
		local material: { Loss: number }? = if made then (Config.Materials :: any)[made] else nil
		local most = if material then (force - Config.Least) * pierce / material.Loss else 0
		local back = if material and most > 0 then farSide(hit, direction, most) else nil
		if not (material and back) then
			return { finish = hit.Position, reach = enter, pierced = pierced, force = force, stopped = hit }
		end
		local thick = (back.Position - hit.Position).Magnitude
		local left = force - material.Loss * thick / pierce
		table.insert(pierced, {
			part = hit.Instance :: BasePart,
			enter = enter,
			leave = enter + thick,
			at = hit.Position,
			normal = hit.Normal,
			out = back.Position,
			outNormal = back.Normal,
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

-- The marks the shot leaves, as far as `ends` along its path (where it met a body, if the server says it
-- did): a way in and a way out for everything it went through, and where it was stopped.
function Penetration.marks(path: Path, ends: number?): { Mark }
	local upTo = ends or path.reach
	local marks: { Mark } = {}
	for _, each in path.pierced do
		if each.enter < upTo then
			table.insert(marks, { part = each.part, at = each.at, normal = each.normal, kind = "in" })
			if each.leave < upTo then
				table.insert(marks, { part = each.part, at = each.out, normal = each.outNormal, kind = "out" })
			end
		end
	end
	local stopped = path.stopped
	if stopped and path.reach <= upTo and stopped.Instance:IsA("BasePart") then
		table.insert(marks, { part = stopped.Instance, at = stopped.Position, normal = stopped.Normal, kind = "stop" })
	end
	return marks
end

return Penetration
