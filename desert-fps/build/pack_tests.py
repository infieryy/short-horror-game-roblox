"""Packs the tests in tests/ into a model file, so a test can be run in a playtest without pasting it.

    python pack_tests.py

Writes out/Tests.rbxmx: a folder DesertFpsTests with one ModuleScript per tests/test_*.luau. Each test ends
by returning its result, so requiring the module runs the test and gives the result.

Import it into ReplicatedStorage of the RUNNING SERVER of a playtest (not the place in edit mode: the tests
are no part of the game), then on the side the test's first line names:

    task.spawn(function()
        shared.result = require(game.ReplicatedStorage.DesertFpsTests.test_marks)
    end)

and read shared.result when it is done. A module runs once per side: to run a test again, import again.
"""
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.join(HERE, "tests")
OUT = os.path.join(HERE, "out")


def main():
    items = []
    for name in sorted(os.listdir(TESTS)):
        if not (name.startswith("test_") and name.endswith(".luau")):
            continue
        with open(os.path.join(TESTS, name), encoding="utf-8") as f:
            source = f.read().replace("]]>", "]]]]><![CDATA[>")
        items.append(
            '    <Item class="ModuleScript">\n      <Properties>\n'
            f'        <string name="Name">{escape(name[: -len(".luau")])}</string>\n'
            f'        <ProtectedString name="Source"><![CDATA[{source}]]></ProtectedString>\n'
            "      </Properties>\n    </Item>\n"
        )
        print("ModuleScript  DesertFpsTests/" + name[: -len(".luau")])
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "Tests.rbxmx"), "w", encoding="utf-8", newline="\n") as f:
        f.write(
            '<roblox version="4">\n  <Item class="Folder">\n    <Properties>\n'
            '      <string name="Name">DesertFpsTests</string>\n    </Properties>\n'
            + "".join(items)
            + "  </Item>\n</roblox>\n"
        )


if __name__ == "__main__":
    main()
