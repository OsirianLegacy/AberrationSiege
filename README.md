# AberrationSiege

AberrationSiege is a Python and pygame deckbuilder base-defense game. The first development target is the Level & Data Editor, which will share rendering, grid, layer, and asset-loading concepts with the eventual game.

## First Editor Pass

- pygame editor shell with a resizable window and 720p minimum size
- 16x16 tile slicing from the project tileset
- layered grid data model
- painted Kingdom Zone layer
- clickable editor GUI controls for file actions, tools, layers, grid, and zoom
- designer-controlled level width, height, and maximum expansion size
- live level statistics and validation feedback
- 16x16 asset extraction from configured tilesets and spritesheets
- level JSON save/load
- save-time validation

## Running

Install dependencies, then launch the engine launcher:

```bash
python3 -m pip install -r requirements.txt
python3 -m aberration_siege
```

You can also run `python3 launch.py`.

The editor saves to `data/levels/editor_level.json` by default.

To skip the launcher and open the level editor directly:

```bash
python3 -m aberration_siege.editor
```

## Editor Controls

- `Save` / `Load` buttons or `Ctrl+S` / `Ctrl+O`
- `Undo` / `Redo` buttons or `Ctrl/Cmd+Z` and `Ctrl/Cmd+Y`
- `Validate` checks the level JSON data without saving
- `Extract` slices configured assets into generated 16x16 PNGs
- `New` creates a blank level using the current dimensions
- `W`, `H`, `Max W`, and `Max H` steppers resize the current level
- `Paint`, `Erase`, and `Pick` tool buttons or `B`, `E`, and `I`
- clickable layer buttons or number keys `1-8`
- layer `On` / `Off` buttons toggle editor visibility without changing saved data
- `Grid`, `-`, and `+` buttons for view controls
- left-click paints with the active tool; right-click erases

## Asset Extraction

Use the editor's `Extract` button or run:

```bash
python3 scripts/extract_16px_assets.py
```

Generated sprites are written to `assets/extracted/` and indexed in `data/extracted_assets.json`. Those outputs are ignored by Git because they can be regenerated from `data/asset_manifest.json`.
