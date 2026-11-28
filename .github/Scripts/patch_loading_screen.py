#!/usr/bin/env python3
"""Patch Polytoria's UILoadingScreen.cs for the polyiphone mobile port.

Usage: patch_loading_screen.py PATH_TO_UILoadingScreen.cs

What it does (PolyDroid-style loading screen):
  * "Waiting for server..." is never shown (it becomes "Loading...").
  * Progress text reads "Loading parts (5170 / 5219)".
  * On mobile, the centered tagline "Have you ever wanted to play Polytoria on
    mobile? Well now you can!" is added.

The script is idempotent and exits non-zero if an anchor is missing, so a
future change upstream fails loudly instead of silently showing the old screen.
"""
import sys
from pathlib import Path

MARKER = "AddMobileTagline"

READY_OLD = (
    '\t\tSetStatusText("Waiting for server...");\n'
    "\t\tVisible = true;\n"
)
READY_NEW = (
    '\t\tSetStatusText("Loading...");\n'
    "\t\tAddMobileTagline();\n"
    "\t\tVisible = true;\n"
)

METHOD_ANCHOR = "\tprivate void OnGameIconLoaded(Resource resource)\n"
METHOD_NEW = '''\t// polyiphone: PolyDroid-style tagline for the mobile loading screen.
\tprivate void AddMobileTagline()
\t{
\t\tif (!OS.HasFeature("mobile"))
\t\t{
\t\t\treturn;
\t\t}

\t\tLabel tagline = new()
\t\t{
\t\t\tText = "Have you ever wanted to play\\nPolytoria on mobile? Well now you can!",
\t\t\tHorizontalAlignment = HorizontalAlignment.Center,
\t\t\tVerticalAlignment = VerticalAlignment.Center,
\t\t\tMouseFilter = MouseFilterEnum.Ignore,
\t\t};
\t\ttagline.AddThemeFontSizeOverride("font_size", 34);
\t\ttagline.AddThemeColorOverride("font_color", Colors.White);
\t\ttagline.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
\t\tAddChild(tagline);
\t}

'''

SIMPLE = [
    # (old, new, expected occurrences)
    (
        'SetStatusText("Waiting for server...");',
        'SetStatusText("Loading...");',
        1,  # the second one in NetworkEssentialsReady(); _Ready() is handled above
    ),
    (
        'SetStatusText($"Constructing ({current}/{max})...");',
        'SetStatusText($"Loading parts ({current} / {max})");',
        1,
    ),
]


def fail(msg: str) -> int:
    print(f"::error::patch_loading_screen: {msg}")
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        return fail(f"{path} not found")

    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")

    if MARKER in text:
        print("UILoadingScreen.cs already patched; nothing to do.")
        return 0

    if text.count(READY_OLD) != 1:
        return fail("anchor in _Ready() not found (upstream file changed?)")
    text = text.replace(READY_OLD, READY_NEW)

    if text.count(METHOD_ANCHOR) != 1:
        return fail("OnGameIconLoaded anchor not found (upstream file changed?)")
    text = text.replace(METHOD_ANCHOR, METHOD_NEW + METHOD_ANCHOR)

    for old, new, expected in SIMPLE:
        found = text.count(old)
        if found != expected:
            return fail(f"expected {expected}x {old!r}, found {found}")
        text = text.replace(old, new)

    if "Waiting for server" in text:
        return fail("'Waiting for server' is still present after patching")

    path.write_text(text, encoding="utf-8", newline="\n")
    print("Patched UILoadingScreen.cs: no 'Waiting for server' screen, PolyDroid-style loading text added.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
