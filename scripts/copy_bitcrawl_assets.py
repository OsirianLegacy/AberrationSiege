from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/Users/boss/Downloads/Bitcrawl_Free_Roguelike_v1")

COPIES = [
    (SOURCE / "Dawnbringer32_Palette_By_Dawnbringer.png", ROOT / "assets/palettes/Dawnbringer32_Palette_By_Dawnbringer.png"),
    (SOURCE / "Tileset/Tileset.png", ROOT / "assets/tilesets/Tileset.png"),
    (SOURCE / "Characters/Thick_Outline_Sheet", ROOT / "assets/characters/thick_outline"),
    (SOURCE / "Items/Single_Icons_Thick_Outline", ROOT / "assets/items/single_icons_thick_outline"),
]


def main() -> int:
    for source, destination in COPIES:
        if not source.exists():
            print(f"Missing: {source}")
            continue
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            for child in source.iterdir():
                if child.is_file():
                    shutil.copy2(child, destination / child.name)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        print(f"Copied {source} -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
