# AberrationSiege

AberrationSiege is a Python and pygame deckbuilder base-defense game. The first development target is the Level & Data Editor, which will share rendering, grid, layer, and asset-loading concepts with the eventual game.

## First Editor Pass

- pygame editor shell with a resizable window and 720p minimum size
- 16x16 tile slicing from the project tileset
- layered grid data model
- painted Kingdom Zone layer
- level JSON save/load
- save-time validation

## Running

Install dependencies, then launch the editor:

```bash
python3 -m pip install -r requirements.txt
python3 -m aberration_siege.editor
```

The editor saves to `data/levels/editor_level.json` by default.
