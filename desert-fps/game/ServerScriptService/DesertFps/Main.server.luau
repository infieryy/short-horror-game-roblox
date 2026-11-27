--!strict
-- Starts the server side of the game.
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local DesertFps = (ServerStorage :: any).DesertFps
local DevConfig = require(DesertFps.DevConfig)
local DestructionConfig = require(DesertFps.Destruction.DestructionConfig)
local Breakable = require(DesertFps.Destruction.Breakable)
local Structure = require(DesertFps.Destruction.Structure)
local Combat = require(DesertFps.Combat.Combat)
local Dummies = require(DesertFps.Combat.Dummies)
local TownConfig = require(DesertFps.Town.TownConfig)
local WeaponService = require(DesertFps.Weapons.WeaponService)
local UtilityService = require(DesertFps.Utility.UtilityService)

Combat.start()
WeaponService.start()
UtilityService.start()
if DevConfig.Dummies then
	Dummies.start(DevConfig.Dummies)
end

-- Buildings come down when what holds them up is destroyed.
Structure.start(DevConfig.RebuildSeconds)
task.spawn(function()
	local buildings = workspace:FindFirstChild(TownConfig.Folder)
	if buildings then
		local report = Structure.register(buildings, TownConfig.Middle.Y)
		local unheld = {}
		for piece, count in report.unheld do
			table.insert(unheld, `{count} {piece}`)
		end
		print(`Structure: {report.pieces} pieces, {report.links} links; nothing holds: {table.concat(unheld, ", ")}`)
	end
end)

if DevConfig.TestHooks then
	local damage = Instance.new("BindableFunction")
	damage.Name = "DevDamage"
	damage.OnInvoke = function(part: BasePart, amount: number): boolean
		return Breakable.damage(part, amount, part.Position, Vector3.new(0, -1, 0)) or Structure.knock(part)
	end
	damage.Parent = DesertFps
	-- The client makes its own hook when it sees this (WeaponClient).
	ReplicatedStorage:WaitForChild("DesertFps"):SetAttribute("TestHooks", true)
end

-- Clients load every kit mesh up front (Preload.client.luau). Otherwise the shards of a piece pop in one by
-- one the first time it cracks. The low-detail meshes are not placed anywhere yet, so they are left out.
local preload = DesertFps.Meshes:Clone()
for _, piece in preload:GetChildren() do
	local low = piece:FindFirstChild("Low")
	if low then
		low:Destroy()
	end
end
preload.Name = "MeshPreload"
preload.Parent = ReplicatedStorage:WaitForChild("DesertFps")

-- Characters get their own collision group so rubble does not shove them around.
local function onCharacter(character: Model)
	local function group(part: Instance)
		if part:IsA("BasePart") then
			part.CollisionGroup = DestructionConfig.CharacterGroup
		end
	end
	for _, part in character:GetDescendants() do
		group(part)
	end
	character.DescendantAdded:Connect(group)
end

local function devSpawn(): SpawnLocation?
	local node: Instance? = workspace
	for _, name in DevConfig.SpawnPath or {} do
		node = node and node:FindFirstChild(name)
	end
	return if node and node:IsA("SpawnLocation") then node else nil
end

local function onPlayer(player: Player)
	local spawn = devSpawn()
	if spawn then
		player.RespawnLocation = spawn
	end
	player.CharacterAdded:Connect(onCharacter)
	local character = player.Character
	if character then
		onCharacter(character)
		if spawn then
			-- Already spawned somewhere else before this script ran.
			character:PivotTo(spawn.CFrame + Vector3.new(0, 4, 0))
		end
	end
end
Players.PlayerAdded:Connect(onPlayer)
for _, player in Players:GetPlayers() do
	onPlayer(player)
end

-- Testing aid: stand a piece up again some time after it is completely destroyed.
local function rebuild(model: Instance)
	local seconds = DevConfig.RebuildSeconds
	if not (seconds and model:IsA("Model")) then
		return
	end
	local piece, origin, parent = model:GetAttribute("Piece") :: string, model.WorldPivot, model.Parent
	local tint = model:GetAttribute("Tint") :: Color3?
	model.Destroying:Once(function()
		task.delay(seconds, function()
			if parent and parent:IsDescendantOf(workspace) then
				Breakable.place(piece, origin, parent, tint)
			end
		end)
	end)
end
CollectionService:GetInstanceAddedSignal(Breakable.Tag):Connect(rebuild)
for _, model in CollectionService:GetTagged(Breakable.Tag) do
	rebuild(model)
end
