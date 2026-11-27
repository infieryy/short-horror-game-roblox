--!strict
-- Switches for testing while the game has no rounds, teams or loadouts. Set them all to nil for the real game.
return {
	-- Every player spawns on this SpawnLocation (a path under Workspace) if it exists.
	SpawnPath = { "Buildings", "Spawn" } :: { string }?,
	-- Seconds after a breakable piece is completely destroyed before it is stood up again.
	RebuildSeconds = 30 :: number?,
	-- Lets a test script reach the running game: ServerStorage.DesertFps.DevDamage:Invoke(part, amount) does
	-- to `part` what a shot of that strength would. (Studio's command bar gets its own copies of the modules,
	-- so a test cannot call Breakable itself and have the running game notice.)
	TestHooks = true :: boolean?,
	-- Target dummies to shoot at: the plan cell each stands in, its armor (CombatConfig.Armor), and how many
	-- studs it paces from side to side, if it does. The cells are clear of stalls and goods: south of the dev
	-- spawn, in the market, and along the north side of the square.
	Dummies = {
		{ Row = 16, Column = 19, Armor = "none" },
		{ Row = 19, Column = 21, Armor = "heavy" },
		{ Row = 14, Column = 23, Armor = "heavy", Pace = 24 },
	} :: { { Row: number, Column: number, Armor: string, Pace: number? } }?,
}
