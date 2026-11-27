--!strict
-- Who can be hurt, and what a hit does to them. Only the server decides either.
-- A combatant is a character model: a player's, or a target dummy. Its health is its Humanoid's; its armor is
-- the "Armor" attribute on the model, which takes damage first.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local CombatConfig = require(ReplicatedStorage:WaitForChild("DesertFps").Combat.CombatConfig)
local Hitboxes = require(script.Parent.Hitboxes)

local Combat = {}

-- through: the shot came through something on its way (a wallbang).
export type Hit = { attacker: Player?, weapon: string, zone: string, from: Vector3, through: boolean? }

-- Called with every hit that does damage, and with every death a hit causes.
Combat.Hurt = {} :: { (victim: Model, amount: number, hit: Hit) -> () }
Combat.Died = {} :: { (victim: Model, hit: Hit) -> () }

local combatants: { [Model]: true } = {}

-- Characters heal by themselves through a script named Health that every character is given. Not here.
local function stopHealing(character: Model)
	local function remove(child: Instance)
		if child.Name == "Health" and child:IsA("Script") then
			task.defer(child.Destroy, child)
		end
	end
	for _, child in character:GetChildren() do
		remove(child)
	end
	character.ChildAdded:Connect(remove)
end

-- Makes `character` someone who can be shot, at full health, with `armor` (a key of CombatConfig.Armor).
function Combat.enlist(character: Model, armor: string)
	local humanoid = character:FindFirstChildOfClass("Humanoid")
	assert(humanoid, `{character.Name} has no Humanoid`)
	humanoid.MaxHealth = CombatConfig.Health
	humanoid.Health = CombatConfig.Health
	stopHealing(character)
	if Players:GetPlayerFromCharacter(character) then
		-- A name over a head gives a position away.
		humanoid.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	end
	character:SetAttribute("Armor", (CombatConfig.Armor :: any)[armor])

	combatants[character] = true
	Hitboxes.track(character)
	local function discharge()
		combatants[character] = nil
		Hitboxes.untrack(character)
	end
	humanoid.Died:Once(discharge)
	character.Destroying:Once(discharge)
end

function Combat.is(character: Instance): boolean
	return combatants[character :: Model] ~= nil
end

-- Every combatant, for a ray that should pass through them all.
function Combat.all(): { Instance }
	local all = {}
	for character in combatants do
		table.insert(all, character)
	end
	return all
end

-- Takes `amount` off the victim's armor, then its health. Returns what was taken and whether it killed.
function Combat.damage(victim: Model, amount: number, hit: Hit): (number, boolean)
	local humanoid = victim:FindFirstChildOfClass("Humanoid")
	if not (combatants[victim] and humanoid and humanoid.Health > 0) then
		return 0, false
	end
	local armor = (victim:GetAttribute("Armor") :: number?) or 0
	local fromArmor = math.min(armor, amount)
	local fromHealth = math.min(humanoid.Health, amount - fromArmor)
	victim:SetAttribute("Armor", armor - fromArmor)
	humanoid.Health -= fromHealth

	local killed = humanoid.Health <= 0
	for _, heard in Combat.Hurt do
		task.spawn(heard, victim, fromArmor + fromHealth, hit)
	end
	if killed then
		for _, heard in Combat.Died do
			task.spawn(heard, victim, hit)
		end
	end
	return fromArmor + fromHealth, killed
end

function Combat.start()
	Players.RespawnTime = CombatConfig.RespawnSeconds
	Hitboxes.start()
end

return Combat
