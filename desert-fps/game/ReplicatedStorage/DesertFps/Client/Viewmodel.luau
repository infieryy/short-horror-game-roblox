--!strict
-- The arms and the weapon in front of the camera. Only the player sees them.
-- The arms are a character rig of their own (ReplicatedStorage.DesertFps.ViewArms, made by the server) hung
-- off the camera: forearms and hands show, in the player's own skin and shirt, the rest is unseen. The weapon
-- sits in its right hand exactly as it does on the character everyone else sees. What the arms do with it
-- (hold, draw, fire, reload, slash) is animation, made in Blender through a camera where the player's eye is.
-- On top of the animation this adds what depends on the moment: aiming down the sights, the bob of walking,
-- the weapon lagging a turn of the head, the bolt and the magazine. What is attached to the weapon is put on
-- it here, as the server puts it on the weapon everyone else sees (Attachments.fitting).

local WeaponConfig = require(script.Parent.Parent.Weapons.WeaponConfig)
local Attachments = require(script.Parent.Parent.Weapons.Attachments)
local AnimationPlayer = require(script.Parent.AnimationPlayer)

local Viewmodel = {}
Viewmodel.__index = Viewmodel

local Arms = WeaponConfig.ViewArms

-- Weapons are modelled pointing along +X; a hand holds a tool pointing along -Z.
local AIM = CFrame.Angles(0, math.pi / 2, 0)
local SHOWN = { LeftLowerArm = true, LeftHand = true, RightLowerArm = true, RightHand = true }

-- A part of the weapon. `size` and `offset` are as it was made; `at` and `home` are where it is as the weapon
-- is fitted now (a longer magazine hangs lower).
type Piece = {
	part: BasePart,
	weld: Weld,
	size: Vector3,
	offset: Vector3,
	at: Vector3,
	home: CFrame,
	slide: Vector3,
	magazine: boolean,
}
type Held = {
	source: Instance, -- the model it was copied from
	model: Model,
	handle: BasePart,
	pieces: { Piece },
	added: { BasePart }, -- the parts of what is attached
	sockets: { [string]: Vector3 },
	config: any, -- its numbers as it is fitted now (Attachments.build)
	sight: Vector3?, -- the point that comes to the eye when aiming: the rear sight, or the middle of an optic
	muzzle: Vector3?, -- where shots leave it: the end of the barrel, or of what is fitted on it
	rest: CFrame?, -- where the weapon is from the camera, at rest in the hands
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

-- `models`: the weapons (WeaponModels). `attachments`: what goes on them (AttachmentModels). `arms`: the rig
-- to copy (ViewArms). All come from the server.
function Viewmodel.new(models: Instance, attachments: Instance, arms: Model, parent: Instance)
	local self = setmetatable({}, Viewmodel)
	self.attachments = attachments
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
		local config = Attachments.build(source.Name)
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
					part = part,
					weld = weld,
					size = part.Size,
					offset = offset,
					at = offset,
					home = weld.C0,
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
		self.held[model.Name] = {
			source = source,
			model = model,
			handle = handle,
			pieces = pieces,
			added = {},
			sockets = sockets,
			config = config,
			sight = sockets.aim_rear,
			muzzle = sockets.muzzle,
		}
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

-- Makes a weapon's model what `config` says it is fitted with.
local function fit(held: Held, config: any, attachments: Instance)
	held.config = config
	for _, part in held.added do
		part:Destroy()
	end
	table.clear(held.added)
	local fitting = Attachments.fitting(held.source, attachments, config.Attached)
	for _, piece in held.pieces do
		local stretch = fitting.stretch[piece.part.Name]
		piece.part.Size, piece.at = piece.size, piece.offset
		if stretch then
			piece.part.Size, piece.at = Attachments.stretched(piece.size, piece.offset, stretch)
		end
		piece.home = AIM * CFrame.new(piece.at)
		piece.weld.Part0, piece.weld.C0 = held.handle, piece.home
	end
	for _, each in fitting.adds do
		local part = each.template:Clone()
		part.Size = each.size
		part.Anchored = false
		unseen(part)
		local weld = Instance.new("Weld")
		weld.Part0, weld.Part1 = held.handle, part
		weld.C0 = AIM * CFrame.new(each.at)
		weld.Parent = part
		part.Parent = held.model
		table.insert(held.added, part)
	end
	held.sight = fitting.points.eye or held.sockets.aim_rear
	held.muzzle = fitting.points.muzzle or held.sockets.muzzle
	-- Where a laser's beam leaves the weapon.
	local emitter = held.handle:FindFirstChild("Laser")
	if emitter then
		emitter:Destroy()
	end
	if fitting.points.beam then
		local from = Instance.new("Attachment")
		from.Name = "Laser"
		from.Position = AIM * fitting.points.beam
		from.Parent = held.handle
	end
end

-- Puts a weapon in the hands and draws it, or shows nothing. `config`: the weapon's numbers as it is fitted
-- (Attachments.build).
function Viewmodel.show(self: any, config: any?)
	if self.current then
		self.current.model.Parent = nil
	end
	self.current = if config then self.held[config.Name] else nil
	self.magazineOut = false
	self.veiled = false
	local held: Held? = self.current
	for _, part in self.rig:GetChildren() do
		if part:IsA("BasePart") and SHOWN[part.Name] then
			part.LocalTransparencyModifier = if held then 0 else 1
		end
	end
	if held then
		fit(held, config, self.attachments)
		for _, part in held.model:GetChildren() do
			if part:IsA("BasePart") then
				part.LocalTransparencyModifier = 0 -- it may have been put away while veiled
			end
		end
		held.model.Parent = self.rig
		self.animations:switch(held.config.View.Animations, "Idle")
		self.animations:play("Equip", 0, config.Quicken.Equip)
	else
		self.animations:switch(nil, "Idle")
	end
end

-- Stops drawing the arms and the weapon, or draws them again, without putting the weapon away: a scope's
-- view takes their place while the player looks through it.
function Viewmodel.veil(self: any, veiled: boolean)
	local held: Held? = self.current
	if veiled == self.veiled or not held then
		return
	end
	self.veiled = veiled
	local unseenNow = if veiled then 1 else 0
	for _, part in self.rig:GetChildren() do
		if part:IsA("BasePart") and SHOWN[part.Name] then
			part.LocalTransparencyModifier = unseenNow
		end
	end
	for _, part in held.model:GetChildren() do
		if part:IsA("BasePart") then
			part.LocalTransparencyModifier = unseenNow
		end
	end
end

-- Plays an action of the weapon in hand: "Fire", "Reload".
function Viewmodel.play(self: any, action: string)
	local held: Held? = self.current
	self.animations:play(action, nil, held and held.config.Quicken[action])
end

function Viewmodel.update(self: any, pose: Pose)
	local held: Held? = self.current
	if not held then
		return
	end
	local view = held.config.View
	local steady = 1 - 0.8 * ease(pose.aim)

	-- Aiming: the whole of it moves until the weapon points where the eye looks, with its sight SightDistance
	-- ahead and SightDrop under the line of sight.
	-- Where the weapon starts from is measured, at rest, not taken from where the animation was meant to hold
	-- it: the body Roblox makes is not quite the one the animations were made on, and a weapon a twentieth of
	-- a stud out of place aims visibly off centre. It goes on being measured while the weapon rests, so an
	-- aimed weapon does not drift with the breath of the idle; a shot or a reload moves it from there.
	local shift = CFrame.identity
	self.rested = if self.animations:resting("Idle") then self.rested + pose.dt else 0
	if held.sight and view.SightDistance then
		if self.rested >= Arms.Settle then
			local now = Arms.Rig * self.root.CFrame:ToObjectSpace(held.handle.CFrame * AIM)
			held.rest = if held.rest then held.rest:Lerp(now, 1 - math.exp(-Arms.RestFollow * pose.dt)) else now
		end
		if held.rest then
			local aimed = CFrame.new(0, -(view.SightDrop or 0), -view.SightDistance) * AIM * CFrame.new(-held.sight)
			shift = CFrame.identity:Lerp(aimed * held.rest:Inverse(), ease(pose.aim))
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
		* shift
		* CFrame.new(bob)
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
			piece.weld.C0 = AIM * CFrame.new(piece.at + piece.slide * back)
		end
	end
	self.magazineOut = out
end

-- Where the beam of a laser on the weapon in hand starts, if it carries one and is being drawn.
function Viewmodel.emitter(self: any): Attachment?
	local held: Held? = self.current
	local emitter = if held and not self.veiled then held.handle:FindFirstChild("Laser") else nil
	return if emitter and emitter:IsA("Attachment") then emitter else nil
end

-- Where shots leave the weapon in hand, looking along its barrel: the end of the barrel, or of what is
-- fitted on it. The flash and the tracer start here.
function Viewmodel.muzzle(self: any): CFrame?
	local held: Held? = self.current
	local at = held and held.muzzle
	if not (held and at) then
		return nil
	end
	local frame = held.handle.CFrame
	return CFrame.lookAlong(frame * AIM * at, frame.LookVector, frame.UpVector)
end

return Viewmodel
