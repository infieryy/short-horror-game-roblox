-- Loads the uploaded kit pieces into ServerStorage.DesertFps.Meshes and checks every mesh against its data.
-- Run in Studio in edit mode, after 01_install_modules.luau. Safe to re-run: each piece is replaced.
-- To import only some pieces, pass their names: KitImporter.run({ "vat", "corner_upper" }).
local KitImporter = require(game:GetService("ServerStorage").DesertFps.Assets.KitImporter)

return KitImporter.run()
