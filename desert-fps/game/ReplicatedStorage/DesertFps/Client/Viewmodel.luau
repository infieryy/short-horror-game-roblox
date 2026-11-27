--!strict
-- The weapon in front of the camera. It is posed part by part every frame: where it sits from the hip or at
-- the eye, how a shot kicks it, how it comes up when drawn, how the magazine leaves and returns in a reload,
-- how a knife swings. The models come from the server (ReplicatedStorage.DesertFps.WeaponModels).

local WeaponConfig = require(script.Parent.Parent.Weapons.WeaponConfig)

local Viewmodel = {}
Viewmodel.__index = Viewmodel

-- Weapons are modelled pointing along +X; the camera looks along -Z.
local AIM = CFrame.Angles(0, math.pi / 2, 0)

-- How a weapon that is not ready hangs below the view: studs down, degrees tipped forward.
local DRAW_DROP, DRAW_TIP = 0.9, 40
-- A reload: the weapon dips (studs), tips up and rolls over (degrees) at its middle; the magazine travels
-- this far out along its own way out, between these shares of the reload, and back between those.
local RELOAD_DIP, RELOAD_TIP, RELOAD_ROLL = 0.18, 14, 24
local MAGAZINE_TRAVEL = 1.4
local MAGAZINE_OUT, MAGAZINE_IN = { 0.1, 0.35 }, { 0.5, 0.8 }
-- Walking makes the weapon bob this far (studs) at this many swings a stud.
local BOB, BOB_RATE = 0.03, 0.55

type Piece = { part: BasePart, offset: Vector3, slide: Vector3, detach: Vector3 }
type Held = { model: Model, pieces: { Piece }, sockets: { [string]: Vector3 }, config: any }

export type Pose = {
	camera: CFrame,
	aim: number, -- 0 at the hip, 1 at the eye
	kick: number, -- 1 right after a shot, settling to 0
	draw: number, -- 0 just drawn, 1 ready
	reload: number?, -- how far through a reload, 0 to 1
	slash: number?, -- how far through a knife slash, 0 to 1
	walked: number, -- studs walked, for the bob
	moving: number, -- how fast, as a share of the run speed
}

local function ease(x: number): number
	x = math.clamp(x, 0, 1)
	return x * x * (3 - 2 * x)
end

local function between(x: number, range: { number }): number
	return ease((x - range[1]) / (range[2] - range[1]))
end

function Viewmodel.new(models: Instance, parent: Instance)
	local self = setmetatable({}, Viewmodel)
	self.parent = parent
	self.held = {} :: { [string]: Held }
	self.current = nil :: Held?
	self.frame = CFrame.identity
	for _, source in models:GetChildren() do
		local model = source:Clone() :: Model
		local pieces, sockets = {}, {}
		for _, part in model:GetChildren() do
			if part:IsA("BasePart") then
				table.insert(pieces, {
					part = part,
					offset = part:GetAttribute("Offset") :: Vector3,
					slide = (part:GetAttribute("Slide") :: Vector3?) or Vector3.zero,
					detach = (part:GetAttribute("Detach") :: Vector3?) or Vector3.zero,
				})
			end
		end
		for name, value in model:GetAttributes() do
			if string.sub(name, 1, 7) == "Socket_" then
				sockets[string.sub(name, 8)] = value :: Vector3
			end
		end
		self.held[model.Name] = { model = model, pieces = pieces, sockets = sockets, config = (WeaponConfig.Weapons :: any)[model.Name] }
	end
	return self
end

-- Shows the weapon of that name, or nothing.
function Viewmodel.show(self: any, name: string?)
	if self.current then
		self.current.model.Parent = nil
	end
	self.current = if name then self.held[name] else nil
	if self.current then
		self.current.model.Parent = self.parent
	end
end

function Viewmodel.update(self: any, pose: Pose)
	local held: Held? = self.current
	if not held then
		return
	end
	local view = held.config.View

	-- At the eye, the rear sight sits SightDistance ahead, SightDrop under the line of sight.
	local place = view.Offset
	local sight = held.sockets.aim_rear
	if sight and view.SightDistance then
		local eye = Vector3.new(-sight.Z, -sight.Y - (view.SightDrop or 0), sight.X - view.SightDistance)
		place = place:Lerp(eye, ease(pose.aim))
	end
	local steady = 1 - 0.8 * pose.aim
	local bob = Vector3.new(
		math.sin(pose.walked * BOB_RATE * math.pi) * BOB,
		-math.abs(math.cos(pose.walked * BOB_RATE * math.pi)) * BOB,
		0
	) * math.min(pose.moving, 1) * steady

	local frame = pose.camera
		* CFrame.new(place + bob + Vector3.new(0, 0, (view.KickBack or 0) * pose.kick))
		* CFrame.Angles(math.rad((view.KickPitch or 0) * pose.kick * steady), 0, 0)

	local down = 1 - ease(pose.draw)
	if down > 0 then
		frame *= CFrame.new(0, -DRAW_DROP * down, 0) * CFrame.Angles(math.rad(-DRAW_TIP * down), 0, 0)
	end
	local magazine = 0
	if pose.reload then
		local middle = math.sin(math.pi * pose.reload)
		frame *= CFrame.new(0, -RELOAD_DIP * middle, 0)
			* CFrame.Angles(math.rad(RELOAD_TIP * middle), 0, math.rad(RELOAD_ROLL * middle))
		magazine = (between(pose.reload, MAGAZINE_OUT) - between(pose.reload, MAGAZINE_IN)) * MAGAZINE_TRAVEL
	end
	if pose.slash then
		local swing = math.sin(math.pi * pose.slash)
		frame *= CFrame.new(-0.5 * swing, 0, -view.SlashReach * swing)
			* CFrame.Angles(0, math.rad(view.SlashAngle * swing), math.rad(-20 * swing))
	end

	frame *= AIM
	self.frame = frame
	for _, piece in held.pieces do
		piece.part.CFrame = frame * CFrame.new(piece.offset + piece.slide * pose.kick + piece.detach * magazine)
	end
end

-- Where a socket of the weapon in hand is in the world (the muzzle, for a tracer).
function Viewmodel.socket(self: any, name: string): Vector3?
	local held: Held? = self.current
	local at = held and held.sockets[name]
	return if at then self.frame * at else nil
end

return Viewmodel
