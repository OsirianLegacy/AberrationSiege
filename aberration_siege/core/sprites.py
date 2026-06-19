from __future__ import annotations

from pathlib import Path

from aberration_siege.core.constants import TILE_SIZE


def load_sliced_tiles(path: Path, tile_size: int = TILE_SIZE) -> list["pygame.Surface"]:
    import pygame

    if not path.exists():
        return [_placeholder_tile(i, tile_size) for i in range(16)]

    sheet = pygame.image.load(str(path)).convert_alpha()
    tiles: list[pygame.Surface] = []

    for y in range(0, sheet.get_height() - tile_size + 1, tile_size):
        for x in range(0, sheet.get_width() - tile_size + 1, tile_size):
            tile = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
            tile.blit(sheet, (0, 0), (x, y, tile_size, tile_size))
            tiles.append(tile)

    return tiles or [_placeholder_tile(0, tile_size)]


def _placeholder_tile(index: int, tile_size: int) -> "pygame.Surface":
    import pygame

    colors = [
        (34, 32, 52),
        (69, 42, 63),
        (56, 183, 100),
        (59, 93, 201),
        (239, 125, 87),
        (255, 205, 117),
    ]
    surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
    surface.fill(colors[index % len(colors)])
    pygame.draw.rect(surface, (244, 244, 244), surface.get_rect(), 1)
    return surface
