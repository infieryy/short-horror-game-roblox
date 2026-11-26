--!strict
-- Switches for testing while the game has no rounds, teams or loadouts. Set both to nil for the real game.
return {
	-- Every player spawns on this SpawnLocation (a path under Workspace) if it exists.
	SpawnPath = { "KitShowcase", "Spawn" } :: { string }?,
	-- Seconds after a breakable piece is completely destroyed before it is stood up again.
	RebuildSeconds = 8 :: number?,
}
