--!strict
-- Plays weapon animations on one Animator: the player's own character (which everyone sees), or the arms in
-- front of the camera (which only the player sees). AnimationConfig says where each animation comes from.
-- A weapon's animations are a set: one that loops while the weapon is in hand, and actions by name.

local KeyframeSequenceProvider = game:GetService("KeyframeSequenceProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(script.Parent.Parent.Weapons.AnimationConfig)

local AnimationPlayer = {}
AnimationPlayer.__index = AnimationPlayer

-- An action is one animation, or several taken in turn (a knife slashes one way, then the other).
export type Set = { [string]: string | { string } }

-- What to load for the animation of that name: the uploaded asset, or in Studio the sequence kept in the place.
local function contentOf(name: string): string?
	local id = (Config.Ids :: { [string]: number })[name]
	if id and id ~= 0 then
		return `rbxassetid://{id}`
	end
	if RunService:IsStudio() then
		local folder = ReplicatedStorage:FindFirstChild(Config.Folder)
		local sequence = folder and folder:FindFirstChild(name)
		if sequence and sequence:IsA("KeyframeSequence") then
			return KeyframeSequenceProvider:RegisterKeyframeSequence(sequence)
		end
	end
	return nil
end

local function each(set: Set, visit: (string) -> ())
	for _, entry in set do
		if typeof(entry) == "table" then
			for _, name in entry do
				visit(name)
			end
		else
			visit(entry)
		end
	end
end

-- `sets`: every set this Animator will ever play. All of it is fetched now: an animation fetched at its first
-- use plays late, or not at all, that first time.
function AnimationPlayer.new(animator: Animator, sets: { Set })
	local self = setmetatable({}, AnimationPlayer)
	self.animator = animator
	self.tracks = {} :: { [string]: AnimationTrack | false }
	self.set = nil :: Set?
	self.turn = {} :: { [string]: number }
	task.spawn(function()
		for _, set in sets do
			each(set, function(name)
				self:track(name)
			end)
		end
	end)
	return self
end

function AnimationPlayer.track(self: any, name: string?): AnimationTrack?
	if not name then
		return nil
	end
	local track = self.tracks[name]
	if track == nil then
		local content = contentOf(name)
		if content then
			local animation = Instance.new("Animation")
			animation.Name = name
			animation.AnimationId = content
			track = self.animator:LoadAnimation(animation)
		else
			track = false -- none uploaded, none stored: looked for once
		end
		self.tracks[name] = track
	end
	return track or nil
end

-- The weapon in hand changed: whatever the last one was doing stops, and this one's `loop` takes over.
function AnimationPlayer.switch(self: any, set: Set?, loop: string)
	if self.set then
		each(self.set, function(name)
			local track = self:track(name)
			if track then
				track:Stop(Config.HoldFade)
			end
		end)
	end
	self.set = set
	local held = self:track(set and set[loop])
	if held then
		held:Play(Config.HoldFade)
	end
end

-- Plays an action of the weapon in hand from its start, `fade` seconds in (AnimationConfig.ActionFade if not
-- given), `speed` times as fast as it was made.
function AnimationPlayer.play(self: any, action: string, fade: number?, speed: number?)
	local entry = self.set and self.set[action]
	local name = entry
	if typeof(entry) == "table" then
		local turn = (self.turn[action] or 0) % #entry + 1
		self.turn[action] = turn
		name = entry[turn]
	end
	local track = self:track(name)
	if track then
		track:Stop(0)
		track:Play(fade or Config.ActionFade, 1, speed or 1)
	end
end

-- Whether the weapon in hand is doing nothing but its `loop`: that one is loaded and playing at full weight,
-- and no action is.
function AnimationPlayer.resting(self: any, loop: string): boolean
	local set: Set? = self.set
	local held = set and self.tracks[set[loop] :: string]
	if not (set and held and held.IsPlaying and held.Length > 0 and held.WeightCurrent > 0.99) then
		return false
	end
	local still = true
	each(set, function(name)
		local track = self.tracks[name]
		if track and track ~= held and track.IsPlaying then
			still = false
		end
	end)
	return still
end

return AnimationPlayer
