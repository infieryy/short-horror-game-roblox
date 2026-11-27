--!strict
-- The arms and the weapon in front of the camera. Only the player sees them.
-- The arms are a character rig of their own (ReplicatedStorage.DesertFps.ViewArms, made by the server) hung
-- off the camera: forearms and hands show, in the player's own skin and shirt, the rest is unseen. The weapon
-- sits in its right hand exactly as it does on the character everyone else sees. What the arms do with it
-- (hold, draw, fire, reload, slash) is animation, made in Blender through a camera where the player's eye is.
-- On top of the animation this adds what depends on the moment: aiming down the sights, the bob of walking,
-- the weapon lagging a turn of the head, the bolt and the magazine.

local WeaponConfig = require(script.Parent.Parent.Weapons.WeaponConfig)
local AnimationPlayer = require(script.Parent.AnimationPlayer)

local Viewmodel = {}
Viewmodel.__index = Viewmodel

local Arms = WeaponConfig.ViewArms

-- Weapons are modelled pointing along +X; a hand holds a tool pointing along -Z.
local AIM = CFrame.Angles(0, math.pi / 2, 0)
local SHOWN = { LeftLowerArm = true, LeftHand = true, RightLowerArm = true, RightHand = true }

type Piece = { weld: Weld, home: CFrame, offset: Vector3, slide: Vector3, magazine: boolean }
type Held = {
	model: Model,
	handle: BasePart,
	pieces: { Piece },
	sockets: { [string]: Vector3 },
	config: any,
	rest: Vector3?, -- where the rear sight is from the camera with the weapon at rest in the hands
}

export type Pose = {
	camera: CFrame,
	dt: number,
	aim: number, -- 0 at the hip, 1 at the eye
	kick: number, -- 1 right after a shot, settling to 0: the bolt
	reload: number?, -- how far through a reload, 0 to 1
	walked: number, -- studs walked, for the bob
	moving: number, -- how fast, as a share of the run speed
	sideways: number, -- how much of that is to the right (-1 to 1)
}

local function ease(x: number): number
	x = math.clamp(x, 0, 1)
	return x * x * (3 - 2 * x)
end

local function unseen(part: BasePart)
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
	part.Massless = true
end

-- `models`: the weapons (WeaponModels). `arms`: the rig to copy (ViewArms). Both come from the server.
function Viewmodel.new(models: Instance, arms: Model, parent: Instance)
	local self = setmetatable({}, Viewmodel)
	local rig = arms:Clone()
	local humanoid = rig:FindFirstChildOfClass("Humanoid") :: Humanoid
	-- It is a body only so that it can wear a shirt and be animated: it never stands, falls or shows a name.
	humanoid.EvaluateStateMachine = false
	humanoid.AutomaticScalingEnabled = false -- or it puts the forearms back to a body's thickness
	humanoid.RequiresNeck = false
	humanoid.BreakJointsOnDeath = false
	humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	humanoid.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	for _, part in rig:GetDescendants() do
		if part:IsA("BasePart") then
			unseen(part)
			part.Anchored = false
			if SHOWN[part.Name] then
				part.Size = Vector3.new(Arms.Thickness, part.Size.Y, Arms.Thickness)
			else
				part.Transparency = 1
			end
		end
	end
	local root = rig:FindFirstChild("HumanoidRootPart") :: BasePart
	root.Anchored = true
	self.rig, self.root = rig, root
	self.rightHand = rig:FindFirstChild("RightHand") :: BasePart
	self.leftHand = rig:FindFirstChild("LeftHand") :: BasePart
	local grip = self.rightHand:FindFirstChild("RightGripAttachment") :: Attachment

	local sets = {}
	self.held = {} :: { [string]: Held }
	self.current = nil :: Held?
	for _, source in models:GetChildren() do
		local config = (WeaponConfig.Weapons :: any)[source.Name]
		local model = source:Clone() :: Model
		-- The weapon's own origin, held where a Tool's handle would be.
		local handle = Instance.new("Part")
		handle.Name = "Handle"
		handle.Size = Vector3.one * 0.2
		handle.Transparency = 1
		unseen(handle)
		local hold = Instance.new("Weld")
		hold.Part0, hold.Part1 = self.rightHand, handle
		hold.C0, hold.C1 = grip.CFrame, config.Hand
		hold.Parent = handle
		local pieces, sockets = {}, {}
		for _, part in model:GetChildren() do
			if part:IsA("BasePart") then
				part.Anchored = false
				unseen(part)
				local offset = part:GetAttribute("Offset") :: Vector3
				local weld = Instance.new("Weld")
				weld.Part0, weld.Part1 = handle, part
				weld.C0 = AIM * CFrame.new(offset)
				weld.Parent = part
				table.insert(pieces, {
					weld = weld,
					home = weld.C0,
					offset = offset,
					slide = (part:GetAttribute("Slide") :: Vector3?) or Vector3.zero,
					magazine = part:GetAttribute("Detach") ~= nil,
				})
			end
		end
		for name, value in model:GetAttributes() do
			if string.sub(name, 1, 7) == "Socket_" then
				sockets[string.sub(name, 8)] = value :: Vector3
			end
		end
		handle.Parent = model
		self.held[model.Name] = { model = model, handle = handle, pieces = pieces, sockets = sockets, config = config }
		table.insert(sets, config.View.Animations)
	end

	rig.Parent = parent
	local animator = humanoid:FindFirstChildOfClass("Animator") or Instance.new("Animator", humanoid)
	self.animations = AnimationPlayer.new(animator, sets)
	self.magazineOut = false
	self.rested = 0 -- seconds the arms have done nothing but hold the weapon
	self.look = nil :: CFrame?
	self.lagYaw, self.lagPitch, self.lean = 0, 0, 0
	return self
end

-- The arms take the skin and the shirt of the player's own body. (A body is coloured through its BodyColors:
-- colouring its parts one by one does nothing.)
function Viewmodel.wear(self: any, character: Model)
	for _, kind in { "BodyColors", "Shirt" } do
		local old = self.rig:FindFirstChildOfClass(kind)
		if old then
			old:Destroy()
		end
		local theirs = character:FindFirstChildOfClass(kind)
		if theirs then
			theirs:Clone().Parent = self.rig
		end
	end
end

-- Puts the weapon of that name in the hands and draws it, or shows nothing.
function Viewmodel.show(self: any, name: string?)
	if self.current then
		self.current.model.Parent = nil
	end
	self.current = if name then self.held[name] else nil
	self.magazineOut = false
	local held: Held? = self.current
	for _, part in self.rig:GetChildren() do
		if part:IsA("BasePart") and SHOWN[part.Name] then
			part.LocalTransparencyModifier = if held then 0 else 1
		end
	end
	if held then
		for _, piece in held.pieces do
			piece.weld.Part0, piece.weld.C0 = held.handle, piece.home
		end
		held.model.Parent = self.rig
		self.animations:switch(held.config.View.Animations, "Idle")
		self.animations:play("Equip", 0)
	else
		self.animations:switch(nil, "Idle")
	end
end

-- Plays an action of the weapon in hand: "Fire", "Reload".
function Viewmodel.play(self: any, action: string)
	self.animations:play(action)
end

function Viewmodel.update(self: any, pose: Pose)
	local held: Held? = self.current
	if not held then
		return
	end
	local view = held.config.View
	local steady = 1 - 0.8 * ease(pose.aim)

	-- Aiming: the whole of it moves until the rear sight is SightDistance ahead, SightDrop under the line of sight.
	-- Where the sight starts from is measured, with the weapon at rest, not taken from where the animation
	-- was meant to hold it: the body Roblox makes is not quite the one the animations were made on, and a
	-- weapon a twentieth of a stud out of place aims visibly off centre. It goes on being measured while the
	-- weapon rests, slowly, so the breath of the idle evens out.
	local shift = Vector3.zero
	local sight = held.sockets.aim_rear
	self.rested = if self.animations:resting("Idle") then self.rested + pose.dt else 0
	if sight and view.SightDistance then
		if self.rested >= Arms.Settle then
			local now = (Arms.Rig * self.root.CFrame:ToObjectSpace(held.handle.CFrame * AIM * CFrame.new(sight))).Position
			held.rest = if held.rest then held.rest:Lerp(now, 1 - math.exp(-Arms.RestFollow * pose.dt)) else now
		end
		if held.rest then
			shift = (Vector3.new(0, -(view.SightDrop or 0), -view.SightDistance) - held.rest) * ease(pose.aim)
		end
	end
	local stride = pose.walked * Arms.BobRate * math.pi
	local bob = Vector3.new(math.sin(stride), -math.abs(math.cos(stride)), 0) * Arms.Bob * math.min(pose.moving, 1) * steady

	-- A turn of the head leaves the weapon a little behind, and a step to the side leans it that way.
	local look = self.look or pose.camera
	local turned = look:ToObjectSpace(pose.camera).LookVector
	self.look = pose.camera
	local settle = 1 - math.exp(-Arms.LagSettle * pose.dt)
	local most = math.rad(Arms.LagMost)
	self.lagYaw = math.clamp(self.lagYaw + turned.X * Arms.Lag, -most, most) * (1 - settle)
	self.lagPitch = math.clamp(self.lagPitch - turned.Y * Arms.Lag, -most, most) * (1 - settle)
	self.lean += (math.rad(-Arms.Lean) * pose.sideways - self.lean) * settle

	self.root.CFrame = pose.camera
		* CFrame.new(shift + bob)
		* CFrame.Angles(self.lagPitch * steady, self.lagYaw * steady, self.lean * steady)
		* Arms.Rig

	-- The bolt goes back with a shot and with the pull that ends a reload; the magazine leaves with the left
	-- hand and a full one comes back in it.
	local pull = 0
	local out = false
	if pose.reload then
		local bolt, magazine = view.Bolt, view.Magazine
		if bolt then
			local through = (pose.reload - bolt.From) / (bolt.To - bolt.From)
			pull = if through > 0 and through < 1 then math.sin(math.pi * through) else 0
		end
		out = magazine ~= nil and pose.reload >= magazine.Out and pose.reload < magazine.In
	end
	local back = math.max(pose.kick, pull)
	for _, piece in held.pieces do
		if piece.magazine then
			if out and not self.magazineOut then
				piece.weld.Part0 = self.leftHand
				piece.weld.C0 = self.leftHand.CFrame:ToObjectSpace((piece.weld.Part1 :: BasePart).CFrame)
			elseif self.magazineOut and not out then
				piece.weld.Part0, piece.weld.C0 = held.handle, piece.home
			end
		elseif piece.slide ~= Vector3.zero then
			piece.weld.C0 = AIM * CFrame.new(piece.offset + piece.slide * back)
		end
	end
	self.magazineOut = out
end

-- Where a socket of the weapon in hand is in the world (the muzzle, for a tracer).
function Viewmodel.socket(self: any, name: string): Vector3?
	local held: Held? = self.current
	local at = held and held.sockets[name]
	return if held and at then held.handle.CFrame * AIM * at else nil
end

return Viewmodel
