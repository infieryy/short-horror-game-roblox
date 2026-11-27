--!strict
-- Switches for testing while the game has no rounds, teams or loadouts. Set both to nil for the real game.
return {
	-- Every player spawns on this SpawnLocation (a path under Workspace) if it exists.
	-- { "KitShowcase", "Spawn" } is the firing range; { "Map", "Zones", "market", "SpawnA" } is the old town.
	SpawnPath = { "Buildings", "Spawn" } :: { string }?,
	-- Seconds after a breakable piece is completely destroyed before it is stood up again.
	RebuildSeconds = 30 :: number?,
	-- Lets a test script reach the running game: ServerStorage.DesertFps.DevDamage:Invoke(part, amount) does
	-- to `part` what a shot of that strength would. (Studio's command bar gets its own copies of the modules,
	-- so a test cannot call Breakable itself and have the running game notice.)
	TestHooks = true :: boolean?,
}
