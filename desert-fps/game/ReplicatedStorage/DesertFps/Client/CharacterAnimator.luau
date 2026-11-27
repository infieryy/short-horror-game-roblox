--!strict
-- Plays the weapon animations on the player's own character (AnimationConfig). Played here, on the character
-- its player controls, they show for everyone.

local KeyframeSequenceProvider = game:GetService("KeyframeSequenceProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Config = require(script.Parent.Parent.Weapons.AnimationConfig)

local CharacterAnimator = {}
CharacterAnimator.__index = CharacterAnimator

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

function CharacterAnimator.new(character: Model)
	local self = setmetatable({}, CharacterAnimator)
	local humanoid = character:WaitForChild("Humanoid")
	self.animator = humanoid:WaitForChild("Animator") :: Animator
	self.tracks = {} :: { [string]: AnimationTrack | false }
	self.set = nil :: { [string]: string }? -- the animations of the weapon in hand
	return self
end

function CharacterAnimator.track(self: any, name: string?): AnimationTrack?
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

-- The weapon in hand changed: whatever the last one was doing stops, and this one's hold takes over.
function CharacterAnimator.hold(self: any, set: { [string]: string }?)
	if self.set then
		for _, name in self.set do
			local track = self:track(name)
			if track then
				track:Stop(Config.HoldFade)
			end
		end
	end
	self.set = set
	local hold = self:track(set and set.Hold)
	if hold then
		hold:Play(Config.HoldFade)
	end
end

-- Plays an action of the weapon in hand ("Fire", "Reload") from its start.
function CharacterAnimator.play(self: any, action: string)
	local track = self:track(self.set and self.set[action])
	if track then
		if track.IsPlaying then
			track.TimePosition = 0
		else
			track:Play(Config.ActionFade)
		end
	end
end

function CharacterAnimator.stop(self: any, action: string)
	local track = self:track(self.set and self.set[action])
	if track then
		track:Stop(Config.ActionFade)
	end
end

return CharacterAnimator
