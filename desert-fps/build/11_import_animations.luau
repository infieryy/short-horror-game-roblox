-- Loads the weapon animations into ReplicatedStorage.DesertFpsAnimations, as KeyframeSequences: the
-- characters' ("fps_") and the first-person arms' ("fpv_").
-- Run in Studio in edit mode. Safe to re-run: each sequence is replaced.
-- Studio can only load files from its own content folder, so copy them there first:
--   from  desert-fps/animations/*.rbxmx
--   to    %LOCALAPPDATA%\Roblox\Versions\<the version with RobloxStudioBeta.exe>\content\claude_anim\
-- (A Studio update makes a new version folder, and the copy has to be made again.)
-- The animations were made in Blender with the "Roblox Animation Kit" (animations/README.md).
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local FOLDER = "DesertFpsAnimations" -- AnimationConfig.Folder
local FILES = {
	"fps_rifle_hold",
	"fps_rifle_fire",
	"fps_rifle_reload",
	"fps_pistol_hold",
	"fps_pistol_fire",
	"fps_pistol_reload",
	"fps_knife_hold",
	"fps_knife_slash",
	"fpv_rifle_idle",
	"fpv_rifle_equip",
	"fpv_rifle_fire",
	"fpv_rifle_reload",
	"fpv_pistol_idle",
	"fpv_pistol_equip",
	"fpv_pistol_fire",
	"fpv_pistol_reload",
	"fpv_knife_idle",
	"fpv_knife_equip",
	"fpv_knife_slash_a",
	"fpv_knife_slash_b",
}

local folder = ReplicatedStorage:FindFirstChild(FOLDER)
if not folder then
	folder = Instance.new("Folder")
	folder.Name = FOLDER
	folder.Parent = ReplicatedStorage
end

local report = {}
for _, file in FILES do
	local sequence = game:GetObjects(`rbxasset://claude_anim/{file}.rbxmx`)[1] :: KeyframeSequence
	local old = folder:FindFirstChild(sequence.Name)
	if old then
		old:Destroy()
	end
	sequence.Parent = folder
	local frames = sequence:GetKeyframes()
	table.insert(report, `{sequence.Name}: {#frames} keyframes, {frames[#frames].Time} s`)
	task.wait()
end

game:GetService("ChangeHistoryService"):SetWaypoint("Import weapon animations")
return table.concat(report, "\n")
