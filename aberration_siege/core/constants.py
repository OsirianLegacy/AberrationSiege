from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = ROOT_DIR / "assets"
DATA_DIR = ROOT_DIR / "data"

TILE_SIZE = 16
MIN_WINDOW_SIZE = (1280, 720)

DEFAULT_LEVEL_PATH = DATA_DIR / "levels" / "editor_level.json"
DEFAULT_TILESET_PATH = ASSETS_DIR / "tilesets" / "Tileset.png"
DEFAULT_PALETTE_PATH = ASSETS_DIR / "palettes" / "Dawnbringer32_Palette_By_Dawnbringer.png"

LAYER_ORDER = [
    "terrain",
    "decorations",
    "kingdom_zone",
    "walls",
    "defenses",
    "buildings",
    "units",
    "enemies",
]
