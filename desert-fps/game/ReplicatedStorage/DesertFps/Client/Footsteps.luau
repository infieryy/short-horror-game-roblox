--!strict
-- Footsteps and landings, everyone's: each client works them out from how the bodies it sees move.
-- Someone who runs is heard; someone who walks (Shift) is not. That is the point of walking.
-- Roblox's own footsteps play at any pace, so its script is switched off here and the sounds it put in each
-- body are silenced. (A script of the same name in StarterPlayerScripts is meant to stand in for it; in
-- Studio, on 2026-11-28, Roblox's own ran all the same.)

local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local Config = require(script.Parent.Parent.Sound.SoundConfig)
local Sounds = require(script.Parent.Sounds)

local Footsteps = {}

local How = Config.Footsteps
-- Roblox's script for the sounds of bodies, in PlayerScripts.
local THEIRS = "RbxCharacterSounds"

-- How far each body has run since its last step, whether it was in the air, and how fast it fell.
type Gait = { run: number, air: boolean, fell: number }
local gaits: { [Model]: Gait } = {}
local me: Player? = nil

local function step(dt: number)
	for _, player in Players:GetPlayers() do
		local character = player.Character
		local humanoid = character and character:FindFirstChildOfClass("Humanoid")
		local root = character and character:FindFirstChild("HumanoidRootPart")
		if not (character and humanoid and humanoid.Health > 0 and root and root:IsA("BasePart")) then
			continue
		end
		local gait = gaits[character]
		if not gait then
			gait = { run = 0, air = false, fell = 0 }
			gaits[character] = gait
			-- What Roblox put in this body. The game's own sounds come later, one at a time.
			for _, theirs in root:GetChildren() do
				if theirs:IsA("Sound") then
					theirs.Playing = false
					theirs.Volume = 0
				end
			end
		end
		-- The player's own are heard in the head, and softer: they tell the player nothing new.
		local where: Instance? = if player == me then nil else root
		local volume = if player == me then How.Own else 1
		local velocity = root.AssemblyLinearVelocity
		if humanoid.FloorMaterial == Enum.Material.Air then
			gait.air = true
			gait.fell = math.max(gait.fell, -velocity.Y)
			continue
		end
		if gait.air then
			if gait.fell >= How.LandFrom then
				Sounds.play(How.Land, where, volume)
			end
			gait.air, gait.fell = false, 0
		end
		local speed = Vector3.new(velocity.X, 0, velocity.Z).Magnitude
		if speed < How.From then
			-- Standing or walking. The first step of a run comes soon after it starts.
			gait.run = How.Stride * How.First
			continue
		end
		gait.run += speed * dt
		if gait.run >= How.Stride then
			gait.run -= How.Stride
			Sounds.play(How.Step, where, volume)
		end
	end
	for character in gaits do
		if not character:IsDescendantOf(workspace) then
			gaits[character] = nil
		end
	end
end

-- `player` is the one whose steps are their own.
function Footsteps.start(player: Player)
	me = player
	task.spawn(function()
		local theirs = player:WaitForChild("PlayerScripts"):WaitForChild(THEIRS, 10)
		if theirs and theirs:IsA("LocalScript") then
			theirs.Enabled = false
		end
	end)
	RunService.Heartbeat:Connect(step)
end

return Footsteps
