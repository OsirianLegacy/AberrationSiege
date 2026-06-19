# AberrationSiege

AberrationSiege is a Python and pygame deckbuilder base-defense game. The first development target is the Level & Data Editor, which will share rendering, grid, layer, and asset-loading concepts with the eventual game.

## First Editor Pass

- pygame editor shell with a resizable window and 720p minimum size
- 16x16 tile slicing from the project tileset
- layered grid data model
- painted Kingdom Zone layer
- clickable editor GUI controls for file actions, tools, layers, grid, and zoom
- level JSON save/load
- save-time validation

## Running

Install dependencies, then launch the editor:

```bash
python3 -m pip install -r requirements.txt
python3 -m aberration_siege.editor
```

The editor saves to `data/levels/editor_level.json` by default.

## Editor Controls

- `Save` / `Load` buttons or `Ctrl+S` / `Ctrl+O`
- `Paint`, `Erase`, and `Pick` tool buttons or `B`, `E`, and `I`
- clickable layer buttons or number keys `1-8`
- `Grid`, `-`, and `+` buttons for view controls
- left-click paints with the active tool; right-click erases
