--!strict
-- How the screen reads: colours, type, the crosshair. Sizes are pixels on a screen 1080 high; the whole
-- display is scaled to the screen it is on, no smaller than SmallestScale.
return {
	ReferenceHeight = 1080,
	SmallestScale = 0.6,

	Ink = Color3.fromRGB(255, 246, 232), -- text and marks
	Shade = Color3.fromRGB(46, 30, 40), -- the line round them, so they read over bright plaster
	Accent = Color3.fromRGB(72, 196, 186), -- armor, and the weapon in hand: the town's turquoise
	Head = Color3.fromRGB(255, 196, 84), -- a hit to the head
	Harm = Color3.fromRGB(232, 84, 76), -- a kill, and being hit
	-- How see-through what is not the main thing is (captions, the weapons not in hand).
	Dim = 0.45,

	Font = Enum.Font.GothamBold,
	CaptionFont = Enum.Font.GothamMedium,
	Big = 56, -- health, rounds in the magazine
	Medium = 30, -- armor, rounds in reserve
	Small = 18, -- captions, weapon list, kill feed
	-- Pixels from the screen edge to the corner blocks.
	Edge = 56,

	-- Four lines round the middle of the screen. It does not move: where it points is where a first shot goes.
	Crosshair = { Gap = 5, Length = 9, Thickness = 2, Dot = false },
	-- Looking through an optic, the crosshair gives way to the optic's own dot: its width and colour.
	SightDot = { Size = 5, Color = Color3.fromRGB(255, 72, 64) },
	-- The cross that flashes on a hit: seconds it shows, and its size.
	HitMark = { Time = 0.18, Gap = 8, Length = 10, Thickness = 2 },
	-- Being hit tints the screen for this long, this strongly (0 is solid colour, 1 is nothing).
	HurtTime = 0.45,
	HurtTint = 0.72,
	-- Kills listed top right: how many, and how long each stays.
	FeedLines = 5,
	FeedTime = 6,

	-- The loadout (Client/LoadoutMenu). The panel: its width, the space inside it and between its rows, how
	-- round its corners are, how see-through it is (Panel) and how much of the scene behind it shows (Behind).
	-- Caption is the width kept for a socket's name. A choice: the space inside it and between two, and how
	-- see-through one that is not on the weapon is, left alone (Choice) and under the mouse (ChoiceUnder).
	Menu = {
		Width = 820,
		Padding = 32,
		Gap = 20,
		Corner = 6,
		Panel = 0.1,
		Behind = 0.55,
		Caption = 170,
		ChoicePadding = Vector2.new(16, 10),
		ChoiceGap = 8,
		Choice = 0.9,
		ChoiceUnder = 0.75,
		Hint = "B closes. Changing the weapon in hand draws it again.",
	},
}
