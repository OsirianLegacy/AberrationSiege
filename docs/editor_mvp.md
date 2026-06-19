# Level & Data Editor MVP

The first pass focuses on the shared foundation between editor and game:

- 16x16 grid cells
- 16x16 sprites and tiles
- layered rendering order
- painted Kingdom Zone
- JSON level files
- validation before saving

The saved level schema already includes future-facing layers for defenses, buildings, units, enemies, walls, and decorations. Early tools only paint terrain and Kingdom Zone data.

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
