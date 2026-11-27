--!strict
-- Models of kit pieces for clients to show: a weapon in front of the camera, an attachment on it, a dart in
-- flight. The kit's meshes and the parts data never leave the server; what a client needs to place and pose a
-- piece is copied onto the model.

local ServerStorage = game:GetService("ServerStorage")

local DesertFps = (ServerStorage :: any).DesertFps
local PartsData = require(script.Parent.PartsData)

local KitModels = {}

local function vector(values: { number }): Vector3
	return Vector3.new(values[1], values[2], values[3])
end

-- A model of piece `name` under `parent`: every part of it, anchored and out of the way of everything. Each
-- part keeps its "Offset" (its middle from the piece's origin). The model has a "Socket_<name>" attribute for
-- each of the piece's sockets, and a part that moves has "Slide" (how far, and which way) or "Detach" (the way
-- it pulls out).
function KitModels.view(name: string, parent: Instance): Model
	local data = PartsData[name]
	local model = Instance.new("Model")
	model.Name = name
	for _, socket in data.sockets do
		model:SetAttribute("Socket_" .. socket.name, vector(socket.position))
	end
	for _, template in DesertFps.Meshes[name].Parts:GetChildren() do
		local part = template:Clone() :: BasePart
		part.Anchored = true
		part.CastShadow = false
		part.CanCollide = false
		part.CanQuery = false
		part.CanTouch = false
		part.Parent = model
	end
	for _, joint in data.joints do
		local part = model:FindFirstChild(joint.part)
		if part and joint.type == "slide" then
			part:SetAttribute("Slide", vector(joint.axis) * joint.amount)
		elseif part and joint.type == "detach" then
			part:SetAttribute("Detach", vector(joint.axis).Unit)
		end
	end
	model.Parent = parent
	return model
end

return KitModels
