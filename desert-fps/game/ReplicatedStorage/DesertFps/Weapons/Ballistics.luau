--!strict
-- Where a shot goes and what it does, worked out the same way wherever it is asked.
-- The client uses the first three for the shot it sends; the server uses `damage` for the hit it decides.
-- Both use `pace`.
local WeaponConfig = require(script.Parent.WeaponConfig)
local CombatConfig = require(script.Parent.Parent.Combat.CombatConfig)

local Ballistics = {}

export type Stance = {
	speed: number, -- how fast the shooter moves, as a share of the weapon's run speed
	airborne: boolean,
	walking: boolean, -- Shift held
	aiming: boolean, -- down the sights
	spray: number, -- shots already fired in this spray
}

-- Degrees a shot may stray from where it is sent.
function Ballistics.spread(weapon: any, stance: Stance): number
	local spread = weapon.Spread
	local stray
	if stance.airborne then
		stray = spread.Air
	else
		local moving = math.clamp((stance.speed - WeaponConfig.Still) / (WeaponConfig.Running - WeaponConfig.Still), 0, 1)
		stray = spread.Still + ((if stance.walking then spread.Walk else spread.Run) - spread.Still) * moving
	end
	stray += math.min(spread.Spray * stance.spray, spread.SprayMost)
	if stance.aiming and weapon.Aim then
		stray *= weapon.Aim.Spread
	end
	return stray
end

-- Degrees up and to the right of the aim that shot number `spray + 1` of a spray leaves.
function Ballistics.recoil(weapon: any, spray: number, aiming: boolean): (number, number)
	local recoil = weapon.Recoil
	local pattern = recoil.Pattern
	local up, right
	if spray < #pattern then
		up, right = pattern[spray + 1][1], pattern[spray + 1][2]
	else
		local past = spray - #pattern
		local side = if math.floor(past / recoil.SwayEvery) % 2 == 0 then 1 else -1
		up, right = pattern[#pattern][1], side * recoil.Sway
	end
	up *= recoil.Rise
	if aiming and weapon.Aim then
		up, right = up * weapon.Aim.Recoil, right * weapon.Aim.Recoil
	end
	return up, right
end

-- The direction of a shot sent along `look`, `up` and `right` degrees off it, straying by up to `stray`.
function Ballistics.direction(look: CFrame, up: number, right: number, stray: number, random: Random): Vector3
	-- Even over the disc: most shots near the middle would make the edge of the cone meaningless.
	local angle, reach = random:NextNumber(0, 2 * math.pi), math.sqrt(random:NextNumber()) * stray
	local pitch = math.rad(up + math.sin(angle) * reach)
	local yaw = math.rad(-right - math.cos(angle) * reach)
	return (look * CFrame.Angles(0, yaw, 0) * CFrame.Angles(pitch, 0, 0)).LookVector
end

-- What a shot does to a character, by where it lands and from how far.
function Ballistics.damage(weapon: any, zone: string, distance: number): number
	local amount = weapon.Damage[zone] or weapon.Damage.body
	local factor = 1
	for _, step in weapon.Falloff do
		if distance >= step[1] then
			factor = step[2]
		end
	end
	return amount * factor
end

-- How fast someone holding `weapon` moves on foot.
function Ballistics.pace(weapon: any, walking: boolean, aiming: boolean): number
	local speed = weapon.RunSpeed
	if walking then
		speed *= CombatConfig.WalkFactor
	end
	if aiming and weapon.Aim then
		speed *= weapon.Aim.Speed
	end
	return speed
end

return Ballistics
