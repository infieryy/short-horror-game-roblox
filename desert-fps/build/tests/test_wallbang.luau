-- Test: what a shot goes through. Run on the SERVER during a playtest. It stands kit pieces in the air far
-- above the town, works out the path of a shot through each (Weapons/Penetration, the function the weapons
-- use) and takes the pieces away again. Takes a second or two. Returns one line per check, each starting
-- "ok" or "WRONG":
--   the rifle goes through one house wall and keeps 0.45 of its force, and is stopped by a second
--   it goes through a door, a crate and a rack of cloth, and keeps what PenetrationConfig says
--   a corner post and the town wall stop it
--   the pistol goes through a door and is stopped by a wall; the knife goes through nothing
--   the force left at a distance along the path is the force after the last thing before it
-- That a body behind a wall is hurt by that much is checked with a second player, not here.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage.DesertFps
local Penetration = require(Shared.Weapons.Penetration)
local Config = require(Shared.Weapons.PenetrationConfig)
local WeaponConfig = require(Shared.Weapons.WeaponConfig)
local Breakable = require(ServerStorage.DesertFps.Destruction.Breakable)

local RIFLE, PISTOL = WeaponConfig.Weapons.rifle.Pierce, WeaponConfig.Weapons.pistol.Pierce
local HIGH = 600 -- studs above the town

local lines = {}
local function check(right: boolean, what: string)
	table.insert(lines, (if right then "ok     " else "WRONG  ") .. what)
end

local stage = Instance.new("Folder")
stage.Name = "WallbangTest"
stage.Parent = workspace
local everything = RaycastParams.new()
everything.FilterType = Enum.RaycastFilterType.Exclude
everything.FilterDescendantsInstances = {}

-- Stands `pieces` one behind the other, `gap` studs apart, at stand number `place`, and returns the path of a
-- shot through the middle of them all, across their thin side.
local function through(place: number, pieces: { string }, pierce: number, gap: number?): Penetration.Path
	local at = Vector3.new(place * 60, HIGH, 0)
	local middle, across
	for index, piece in pieces do
		local model = Breakable.place(piece, CFrame.new(at + Vector3.new(0, 0, (index - 1) * (gap or 6))), stage)
		local frame, size = model:GetBoundingBox()
		if index == 1 then
			-- Walls are wide along X: their thin side is Z. Whatever this piece is, shoot across its thin side.
			across = if size.X < size.Z then frame.XVector else frame.ZVector
			middle = frame.Position
		end
	end
	task.wait() -- the pieces are there for a cast from the next step on
	return Penetration.trace(middle - across * 12, across, 60, pierce, everything)
end

local function near(a: number, b: number, by: number): boolean
	return math.abs(a - b) <= by
end

local wall = through(1, { "wall2_plain" }, RIFLE)
check(
	#wall.pierced == 1 and not wall.stopped and near(wall.force, 1 - Config.Materials.plaster.Loss, 0.03),
	("rifle, one wall: through %d, %.2f studs thick, %.2f left"):format(
		#wall.pierced,
		if wall.pierced[1] then wall.pierced[1].leave - wall.pierced[1].enter else 0,
		wall.force
	)
)
check(
	Penetration.left(wall, wall.pierced[1].enter - 0.1) == 1 and Penetration.left(wall, wall.pierced[1].leave + 1) == wall.force,
	"the force left is whole before the wall and what is left after it"
)

local two = through(2, { "wall2_plain", "wall2_plain" }, RIFLE)
check(
	#two.pierced == 1 and two.stopped ~= nil and near(two.reach - two.pierced[1].enter, 6, 0.3),
	("rifle, two walls: through %d, stopped %.1f studs on, in the second"):format(
		#two.pierced,
		if two.pierced[1] then two.reach - two.pierced[1].enter else 0
	)
)

local door = through(3, { "door2_wood" }, RIFLE)
check(#door.pierced >= 1 and not door.stopped and door.force > 0.88, ("rifle, a door: %.2f left"):format(door.force))

local crate = through(4, { "crate" }, RIFLE)
check(
	#crate.pierced == 1 and not crate.stopped and crate.force > Config.Least and crate.force < 0.4,
	("rifle, a crate: %.2f left"):format(crate.force)
)

local rack = through(5, { "rack_red" }, RIFLE)
check(not rack.stopped and rack.force > 0.95, ("rifle, a rack of cloth: %.2f left"):format(rack.force))

local post = through(6, { "corner2" }, RIFLE)
check(post.stopped ~= nil and #post.pierced == 0, "rifle, a corner post: stopped")

local town = through(7, { "townwall" }, RIFLE)
check(town.stopped ~= nil and #town.pierced == 0, "rifle, the town wall: stopped")

local behind = through(8, { "door2_wood", "wall2_plain" }, RIFLE)
check(
	#behind.pierced == 2 and not behind.stopped and near(behind.force, door.force - Config.Materials.plaster.Loss, 0.04),
	("rifle, a door and then a wall: through both, %.2f left"):format(behind.force)
)

local pistolDoor = through(9, { "door2_wood" }, PISTOL)
check(
	not pistolDoor.stopped and pistolDoor.force < door.force and pistolDoor.force > 0.7,
	("pistol, a door: %.2f left"):format(pistolDoor.force)
)
local pistolWall = through(10, { "wall2_plain" }, PISTOL)
check(pistolWall.stopped ~= nil and #pistolWall.pierced == 0, "pistol, a wall: stopped")

local knife = through(11, { "door2_wood" }, 0)
check(knife.stopped ~= nil and #knife.pierced == 0, "knife, a door: stopped")

stage:Destroy()
return table.concat(lines, "\n")
