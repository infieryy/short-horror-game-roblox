--!strict
-- Plays the game's sounds on this client. Sound/SoundConfig says what each sound is, how loud and how far it
-- carries; everything else names a sound and says where it is:
--   Sounds.play("Rifle Shot")                 in the player's own head (their own weapon, the display)
--   Sounds.play("Rifle Shot", position)       at a point in the world
--   Sounds.play("Step", part)                 on a part or an attachment, moving with it
-- A sound in the world fades with distance and is not heard past its Far.

local ContentProvider = game:GetService("ContentProvider")
local Debris = game:GetService("Debris")
local SoundService = game:GetService("SoundService")

local Config = require(script.Parent.Parent.Sound.SoundConfig)

local Sounds = {}

-- One recording a sound may be played from: see SoundConfig.
type Take = { Id: number, Gain: number?, From: number?, To: number? }
type Entry = { Takes: { Take }, Volume: number, Pitch: { number }?, Near: number?, Far: number? }

-- Seconds after which a sound that never said it ended is taken away (one that failed to load, say).
local GIVE_UP = 8
-- The loudest Roblox plays a sound.
local LOUDEST = 10

local random = Random.new()
local group: SoundGroup? = nil
local heads: Instance? = nil -- sounds in the player's own head
local world: BasePart? = nil -- holds a point for each sound at a place in the world
local last: { [string]: Take } = {} -- the take each sound played last
local played: { [string]: number } = {} -- how often each sound has been played, for tests
local at: { [string]: Vector3 } = {} -- where each sound in the world was played last, for tests

local function content(id: number): string
	return "rbxassetid://" .. id
end

-- One of a sound's takes: not the one it played last, if it has others.
local function pick(name: string, takes: { Take }): Take
	local take = takes[random:NextInteger(1, #takes)]
	if #takes > 1 and take == last[name] then
		take = takes[table.find(takes, take) :: number % #takes + 1]
	end
	last[name] = take
	return take
end

-- `parent` is where sounds in the player's head are kept. Call once, before the first sound.
function Sounds.start(parent: Instance)
	local made = Instance.new("SoundGroup")
	made.Name = "DesertFps"
	made.Volume = Config.Master
	made.Parent = SoundService
	group = made

	local folder = Instance.new("Folder")
	folder.Name = "Sounds"
	folder.Parent = parent
	heads = folder

	local anchor = Instance.new("Part")
	anchor.Name = "SoundPoints"
	anchor.Anchored = true
	anchor.Transparency = 1
	anchor.Size = Vector3.one * 0.2
	anchor.CanCollide = false
	anchor.CanQuery = false
	anchor.CanTouch = false
	anchor.Parent = parent
	world = anchor

	-- Fetched now, so that the first shot is heard when it is fired and not when its sound arrives.
	task.spawn(function()
		local fetch = {}
		for _, entry: Entry in Config.Sounds :: any do
			for _, take in entry.Takes do
				table.insert(fetch, content(take.Id))
			end
		end
		ContentProvider:PreloadAsync(fetch)
	end)
end

-- Plays the sound of that name: in the player's head, or at a place or on a part in the world. `volume`
-- multiplies its own. Returns nothing if there is no such sound (a weapon need not have every sound).
function Sounds.play(name: string?, where: (Vector3 | Instance)?, volume: number?): Sound?
	local entry: Entry? = if name then (Config.Sounds :: any)[name] else nil
	if not (name and entry and heads and world) or #entry.Takes == 0 then
		return nil
	end
	local take = pick(name, entry.Takes)
	local sound = Instance.new("Sound")
	sound.Name = name
	sound.SoundId = content(take.Id)
	sound.Volume = math.min(entry.Volume * (take.Gain or 1) * (volume or 1), LOUDEST)
	if entry.Pitch then
		sound.PlaybackSpeed = random:NextNumber(entry.Pitch[1], entry.Pitch[2])
	end
	if take.From or take.To then
		sound.PlaybackRegionsEnabled = true
		sound.PlaybackRegion = NumberRange.new(take.From or 0, take.To or GIVE_UP)
	end
	sound.RollOffMode = Enum.RollOffMode.InverseTapered
	sound.RollOffMinDistance = entry.Near or 10
	sound.RollOffMaxDistance = entry.Far or 100
	sound.SoundGroup = group

	local holder: Instance = sound -- what goes when the sound is over
	if typeof(where) == "Vector3" then
		local point = Instance.new("Attachment")
		point.WorldPosition = where
		point.Parent = world
		sound.Parent = point
		holder = point
		at[name] = where
	elseif typeof(where) == "Instance" then
		sound.Parent = where
		at[name] = if where:IsA("BasePart")
			then where.Position
			elseif where:IsA("Attachment") then where.WorldPosition
			else Vector3.zero
	else
		sound.Parent = heads
	end
	sound.Ended:Once(function()
		holder:Destroy()
	end)
	Debris:AddItem(holder, GIVE_UP)
	sound:Play()
	played[name] = (played[name] or 0) + 1
	return sound
end

-- How often each sound has been played and where each sound in the world was played last, for tests.
function Sounds.state(): { played: { [string]: number }, at: { [string]: Vector3 } }
	return { played = table.clone(played), at = table.clone(at) }
end

return Sounds
