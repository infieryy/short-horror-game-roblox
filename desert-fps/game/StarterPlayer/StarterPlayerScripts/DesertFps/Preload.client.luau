--!strict
-- Loads every kit mesh and texture before they are needed, so a piece that cracks or crumbles shows all of
-- its shards at once.
local ContentProvider = game:GetService("ContentProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

ContentProvider:PreloadAsync({ ReplicatedStorage:WaitForChild("DesertFps"):WaitForChild("MeshPreload") })
