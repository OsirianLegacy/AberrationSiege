# Level & Data Editor MVP

The first pass focuses on the shared foundation between editor and game:

- 16x16 grid cells
- 16x16 sprites and tiles
- layered rendering order
- clickable pygame GUI controls
- designer-controlled map dimensions and maximum expansion size
- live level statistics and validation feedback
- 16x16 asset extraction from configured tilesets and spritesheets
- engine launcher entry point for opening editor tools
- per-layer visibility toggles for multi-layer authoring
- undo/redo history for level edits
- painted Kingdom Zone
- JSON level files
- validation before saving

The saved level schema already includes future-facing layers for defenses, buildings, units, enemies, walls, and decorations. Early tools only paint terrain and Kingdom Zone data.

## Layer Visibility

Each layer row has an `On` / `Off` visibility toggle. Visibility only affects editor rendering and does not remove or skip layer data when saving JSON.

## Undo And Redo

Level edits push undo snapshots before they mutate saved data. Painting, erasing, resizing, changing maximum size, creating a blank level, and loading a level can be undone and redone with toolbar controls or keyboard shortcuts.

## GUI Pass

The editor now has a reusable pygame GUI foundation with buttons and section headers. The current screen includes file controls, map dimension controls, validation feedback, level statistics, view controls, tool selection, layer selection, selected tile preview, and a scrollable tile picker.

## Launcher

`python3 -m aberration_siege` opens the pygame engine launcher. The launcher currently opens the Level Editor and reserves disabled slots for future Data Editor and Game runtime tools.

## Validation

The toolbar has a `Validate` action that runs the same JSON data validation used by save. The sidebar shows live cell totals, painted cell counts, terrain coverage, and Kingdom Zone coverage so level authors can quickly spot empty or incomplete maps.

## Asset Extraction

The editor and `scripts/extract_16px_assets.py` can extract 16x16 PNGs from every source listed in `data/asset_manifest.json`. Generated assets are placed in `assets/extracted/` with a matching `data/extracted_assets.json` manifest for later data-editor tabs.

## Level Sizing

The Designer can resize the current editable level with `W` and `H` controls. Existing painted cells are preserved while expanding, and cells outside the new bounds are clipped when shrinking. `Max W` and `Max H` set the fixed maximum size that future expansion rules can use during a run.

## Layers

1. terrain
2. decorations
3. kingdom_zone
4. walls
5. defenses
6. buildings
7. units
8. enemies

The game renderer should consume these layers in the same order so editor previews match game presentation.
