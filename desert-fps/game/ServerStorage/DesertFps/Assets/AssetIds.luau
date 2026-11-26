--!strict
-- Roblox asset ids of the uploaded kit, one entry per piece in assets/out.
--   Model    <piece>.bundle.fbx: the whole mesh, the low-detail mesh and every shard or part
--   Texture  <piece>.png: the painted colour map all of those meshes share
-- build/04_import_meshes.luau turns these into ServerStorage.DesertFps.Meshes.
return {
	-- walls and what stands on them
	wall_plain = { Model = 135688760968419, Texture = 138862098007028 },
	wall_window = { Model = 84401295749564, Texture = 75786669681463 },
	wall_door = { Model = 134685181880905, Texture = 96011352369868 },
	door = { Model = 79949303134565, Texture = 120854672972528 },
	corner = { Model = 126928037378035, Texture = 120740401415426 },
	pillar = { Model = 80140756085473, Texture = 80059467709614 },
	parapet_plain = { Model = 124854673762242, Texture = 128242936773612 },
	parapet_crenel = { Model = 137862454262948, Texture = 125725717635992 },
	parapet_corner = { Model = 99714040554264, Texture = 113932597907446 },
	roof = { Model = 114453280831147, Texture = 97601750519030 },
	stairs = { Model = 134838433413299, Texture = 101377539341138 },
	ladder = { Model = 137098393738794, Texture = 124723098743310 },
	plank = { Model = 138354709513038, Texture = 83514224005756 },
	ground = { Model = 107524302751331, Texture = 88795384306156 },
	-- cover and props
	stall = { Model = 113703101813884, Texture = 80448297701448 },
	awning = { Model = 97299946127892, Texture = 107100457175250 },
	cloth = { Model = 75836189447925, Texture = 115993995556316 },
	sacks = { Model = 120260512172843, Texture = 139029465132365 },
	well = { Model = 135593641026960, Texture = 96683377023018 },
	pot_tall = { Model = 97423098986423, Texture = 135563924597401 },
	pot_round = { Model = 88286217449531, Texture = 71678345962449 },
	vase = { Model = 98791326366622, Texture = 98382732716420 },
	crate = { Model = 120166642128370, Texture = 128550663157206 },
	barrel = { Model = 101362585656532, Texture = 127482096828316 },
	-- weapons
	rifle = { Model = 118729713583609, Texture = 98441666077201 },
	pistol = { Model = 87247004083333, Texture = 102072335700837 },
	knife = { Model = 102511369777617, Texture = 76665044243244 },
	smoke = { Model = 70814577468884, Texture = 135660649189835 },
}
