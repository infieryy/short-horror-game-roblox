--!strict
-- Switches for testing while the game has no rounds, teams or loadouts. Set both to nil for the real game.
return {
	-- Every player spawns on this SpawnLocation (a path under Workspace) if it exists.
	-- { "KitShowcase", "Spawn" } is the firing range outside the town wall.
	SpawnPath = { "Map", "Zones", "market", "SpawnA" } :: { string }?,
	-- Seconds after a breakable piece is completely destroyed before it is stood up again.
	RebuildSeconds = 30 :: number?,
}
