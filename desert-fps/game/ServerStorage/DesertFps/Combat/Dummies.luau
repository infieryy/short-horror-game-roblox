--!strict
-- Target dummies to shoot at while there are no opponents (DevConfig.Dummies).
-- A dummy is a plain character that the server owns. It can be hurt like a player, and stands up again a
-- moment after it dies. One that paces walks from side to side, to test shots at a moving target.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CombatConfig = require(ReplicatedStorage:WaitForChild("DesertFps").Combat.CombatConfig)
local Combat = require(script.Parent.Combat)
local TownBuilder = require(script.Parent.Parent.Town.TownBuilder)

local Dummies = {}

export type Spot = { Row: number, Column: number, Armor: string, Pace: number? }

local FOLDER = "Dummies"
-- A dummy is one flat colour, so nobody takes it for a player.
local COLOR = Color3.fromRGB(170, 160, 190)
-- Seconds a dead dummy lies before it is cleared away.
local LIE = 2

local function pace(humanoid: Humanoid, middle: Vector3, reach: number)
	local side = 1
	while humanoid.Health > 0 and humanoid.Parent do
		humanoid:MoveTo(middle + Vector3.new(side * reach / 2, 0, 0))
		humanoid.MoveToFinished:Wait()
		side = -side
	end
end

local function stand(spot: Spot, folder: Instance)
	local looks = Instance.new("HumanoidDescription")
	for _, part in { "Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg" } do
		(looks :: any)[part .. "Color"] = COLOR
	end
	local model = Players:CreateHumanoidModelFromDescription(looks, Enum.HumanoidRigType.R15)
	local humanoid = model:FindFirstChildOfClass("Humanoid") :: Humanoid
	model.Name = "Dummy"
	humanoid.DisplayName = if spot.Armor == "none" then "Dummy (no armor)" else `Dummy ({spot.Armor} armor)`
	humanoid.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOn

	-- Middle of the plan cell, standing on the street.
	local at = TownBuilder.cellCorner(spot.Row, spot.Column) * CFrame.new(4, humanoid.HipHeight + 1.5, 4)
	model:PivotTo(at)
	model.Parent = folder
	local root = model:FindFirstChild("HumanoidRootPart")
	if root and root:IsA("BasePart") then
		root:SetNetworkOwner(nil)
	end
	Combat.enlist(model, spot.Armor)

	humanoid.Died:Once(function()
		task.delay(LIE, model.Destroy, model)
		task.delay(CombatConfig.RespawnSeconds, stand, spot, folder)
	end)
	if spot.Pace then
		task.spawn(pace, humanoid, at.Position, spot.Pace)
	end
end

function Dummies.start(spots: { Spot })
	local folder = Instance.new("Folder")
	folder.Name = FOLDER
	folder.Parent = workspace
	for _, spot in spots do
		task.spawn(stand, spot, folder)
	end
end

return Dummies
