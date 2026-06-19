from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pygame

from aberration_siege.core.constants import (
    DEFAULT_LEVEL_PATH,
    DEFAULT_PALETTE_PATH,
    DEFAULT_TILESET_PATH,
    LAYER_ORDER,
    MIN_WINDOW_SIZE,
    TILE_SIZE,
)
from aberration_siege.core.level import Level
from aberration_siege.core.palette import load_palette_from_image
from aberration_siege.core.sprites import load_sliced_tiles


SIDEBAR_WIDTH = 272
STATUS_HEIGHT = 28
PREVIEW_HEIGHT = 112
TILE_PICKER_GAP = 4
VISIBLE_PICKER_ROWS = 12


@dataclass
class Camera:
    x: int = 0
    y: int = 0
    zoom: int = 2


class LevelEditor:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("AberrationSiege Level Editor")
        self.screen = pygame.display.set_mode(MIN_WINDOW_SIZE, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)

        self.palette = load_palette_from_image(DEFAULT_PALETTE_PATH)
        self.tiles = load_sliced_tiles(DEFAULT_TILESET_PATH)
        self.level = self._load_or_new(DEFAULT_LEVEL_PATH)
        self.level_path = DEFAULT_LEVEL_PATH

        self.active_layer_index = 0
        self.selected_tile = 0
        self.tile_scroll = 0
        self.camera = Camera()
        self.status = "Ready"
        self.show_grid = True
        self.running = True

    @property
    def active_layer(self) -> str:
        return LAYER_ORDER[self.active_layer_index]

    def run(self) -> None:
        while self.running:
            self._handle_events()
            self._draw()
            self.clock.tick(60)

        pygame.quit()

    def _load_or_new(self, path: Path) -> Level:
        if path.exists():
            try:
                return Level.load(path)
            except Exception as exc:
                self.status = f"Load failed: {exc}"
        return Level.new()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                width = max(event.w, MIN_WINDOW_SIZE[0])
                height = max(event.h, MIN_WINDOW_SIZE[1])
                self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event)
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mouse_wheel(event)
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                self._handle_mouse_paint(event)

    def _handle_key(self, event: pygame.event.Event) -> None:
        mods = pygame.key.get_mods()

        if event.key == pygame.K_ESCAPE:
            self.running = False
        elif event.key == pygame.K_s and mods & pygame.KMOD_CTRL:
            self._save()
        elif event.key == pygame.K_o and mods & pygame.KMOD_CTRL:
            self._load()
        elif event.key == pygame.K_g:
            self.show_grid = not self.show_grid
        elif pygame.K_1 <= event.key <= pygame.K_8:
            self.active_layer_index = event.key - pygame.K_1
            self.status = f"Layer: {self.active_layer}"
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            self.camera.x = max(0, self.camera.x - 1)
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            self.camera.x = min(self.level.width - 1, self.camera.x + 1)
        elif event.key in (pygame.K_UP, pygame.K_w):
            self.camera.y = max(0, self.camera.y - 1)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.camera.y = min(self.level.height - 1, self.camera.y + 1)
        elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
            self.camera.zoom = min(5, self.camera.zoom + 1)
        elif event.key == pygame.K_MINUS:
            self.camera.zoom = max(1, self.camera.zoom - 1)

    def _handle_mouse_wheel(self, event: pygame.event.Event) -> None:
        mouse_x, _mouse_y = pygame.mouse.get_pos()
        if mouse_x < SIDEBAR_WIDTH:
            self.tile_scroll = max(0, self.tile_scroll - event.y)
        elif pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.camera.zoom = max(1, min(5, self.camera.zoom + event.y))
        else:
            self.camera.y = max(0, min(self.level.height - 1, self.camera.y - event.y))

    def _handle_mouse_paint(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION and not any(event.buttons):
            return

        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] < SIDEBAR_WIDTH:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._pick_tile(mouse_pos)
            return

        cell = self._mouse_to_cell(mouse_pos)
        if cell is None:
            return

        x, y = cell
        buttons = pygame.mouse.get_pressed(3)
        if buttons[0]:
            if self.active_layer == "kingdom_zone":
                self.level.paint(self.active_layer, x, y, 1)
            else:
                self.level.paint(self.active_layer, x, y, self.selected_tile)
        elif buttons[2]:
            self.level.paint(self.active_layer, x, y, None)

    def _pick_tile(self, mouse_pos: tuple[int, int]) -> None:
        picker_y = PREVIEW_HEIGHT
        if mouse_pos[1] < picker_y:
            return

        columns = max(1, (SIDEBAR_WIDTH - TILE_PICKER_GAP) // (TILE_SIZE * 2 + TILE_PICKER_GAP))
        col = mouse_pos[0] // (TILE_SIZE * 2 + TILE_PICKER_GAP)
        row = (mouse_pos[1] - picker_y) // (TILE_SIZE * 2 + TILE_PICKER_GAP)
        tile_index = (row + self.tile_scroll) * columns + col
        if 0 <= tile_index < len(self.tiles):
            self.selected_tile = tile_index
            self.status = f"Tile: {tile_index}"

    def _mouse_to_cell(self, mouse_pos: tuple[int, int]) -> tuple[int, int] | None:
        tile_px = TILE_SIZE * self.camera.zoom
        grid_x = mouse_pos[0] - SIDEBAR_WIDTH
        grid_y = mouse_pos[1]
        if grid_x < 0 or grid_y < 0:
            return None
        x = grid_x // tile_px + self.camera.x
        y = grid_y // tile_px + self.camera.y
        if not self.level.in_bounds(x, y):
            return None
        return int(x), int(y)

    def _save(self) -> None:
        try:
            self.level.save(self.level_path, tile_count=len(self.tiles))
            self.status = f"Saved {self.level_path.name}"
        except Exception as exc:
            self.status = f"Save failed: {exc}"

    def _load(self) -> None:
        try:
            self.level = Level.load(self.level_path)
            self.status = f"Loaded {self.level_path.name}"
        except Exception as exc:
            self.status = f"Load failed: {exc}"

    def _draw(self) -> None:
        self.screen.fill(self.palette[1])
        self._draw_sidebar()
        self._draw_level()
        self._draw_status()
        pygame.display.flip()

    def _draw_sidebar(self) -> None:
        sidebar = pygame.Rect(0, 0, SIDEBAR_WIDTH, self.screen.get_height())
        pygame.draw.rect(self.screen, self.palette[20], sidebar)
        pygame.draw.line(self.screen, self.palette[18], (SIDEBAR_WIDTH - 1, 0), (SIDEBAR_WIDTH - 1, sidebar.h))

        self._draw_text("AberrationSiege Editor", 12, 10, self.palette[17], self.font)
        self._draw_text(f"Layer {self.active_layer_index + 1}: {self.active_layer}", 12, 34, self.palette[9])
        self._draw_text(f"Tile {self.selected_tile}", 12, 54, self.palette[9])
        self._draw_text(f"Grid {self.level.width}x{self.level.height}", 12, 74, self.palette[9])

        preview_rect = pygame.Rect(196, 14, 48, 48)
        pygame.draw.rect(self.screen, self.palette[1], preview_rect)
        if self.tiles:
            preview = pygame.transform.scale(self.tiles[self.selected_tile], (48, 48))
            self.screen.blit(preview, preview_rect)
        pygame.draw.rect(self.screen, self.palette[17], preview_rect, 1)

        layer_y = 92
        for index, layer in enumerate(LAYER_ORDER):
            color = self.palette[23] if index == self.active_layer_index else self.palette[19]
            pygame.draw.rect(self.screen, color, (10, layer_y, 26, 18))
            self._draw_text(str(index + 1), 18, layer_y + 2, self.palette[1], self.small_font)
            self._draw_text(layer, 44, layer_y + 2, self.palette[17], self.small_font)
            layer_y += 20

        self._draw_tile_picker(PREVIEW_HEIGHT + 150)

    def _draw_tile_picker(self, top: int) -> None:
        columns = max(1, (SIDEBAR_WIDTH - TILE_PICKER_GAP) // (TILE_SIZE * 2 + TILE_PICKER_GAP))
        tile_px = TILE_SIZE * 2
        start_index = self.tile_scroll * columns
        end_index = min(len(self.tiles), start_index + columns * VISIBLE_PICKER_ROWS)

        for index in range(start_index, end_index):
            local_index = index - start_index
            col = local_index % columns
            row = local_index // columns
            x = TILE_PICKER_GAP + col * (tile_px + TILE_PICKER_GAP)
            y = top + row * (tile_px + TILE_PICKER_GAP)
            self.screen.blit(pygame.transform.scale(self.tiles[index], (tile_px, tile_px)), (x, y))
            border = self.palette[8] if index == self.selected_tile else self.palette[19]
            pygame.draw.rect(self.screen, border, (x, y, tile_px, tile_px), 1)

    def _draw_level(self) -> None:
        tile_px = TILE_SIZE * self.camera.zoom
        view_width = (self.screen.get_width() - SIDEBAR_WIDTH) // tile_px + 2
        view_height = (self.screen.get_height() - STATUS_HEIGHT) // tile_px + 2

        for y in range(self.camera.y, min(self.level.height, self.camera.y + view_height)):
            for x in range(self.camera.x, min(self.level.width, self.camera.x + view_width)):
                dest = pygame.Rect(
                    SIDEBAR_WIDTH + (x - self.camera.x) * tile_px,
                    (y - self.camera.y) * tile_px,
                    tile_px,
                    tile_px,
                )
                self._draw_cell(x, y, dest)

        if self.show_grid:
            self._draw_grid(tile_px, view_width, view_height)

    def _draw_cell(self, x: int, y: int, dest: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, self.palette[13], dest)

        for layer in LAYER_ORDER:
            value = self.level.sample(layer, x, y)
            if value is None:
                continue
            if layer == "kingdom_zone":
                overlay = pygame.Surface(dest.size, pygame.SRCALPHA)
                overlay.fill((*self.palette[10], 72))
                self.screen.blit(overlay, dest)
            elif isinstance(value, int) and 0 <= value < len(self.tiles):
                tile = pygame.transform.scale(self.tiles[value], dest.size)
                self.screen.blit(tile, dest)

    def _draw_grid(self, tile_px: int, view_width: int, view_height: int) -> None:
        color = self.palette[20]
        width = self.screen.get_width()
        height = self.screen.get_height() - STATUS_HEIGHT

        for col in range(view_width):
            x = SIDEBAR_WIDTH + col * tile_px
            pygame.draw.line(self.screen, color, (x, 0), (x, height))
        for row in range(view_height):
            y = row * tile_px
            pygame.draw.line(self.screen, color, (SIDEBAR_WIDTH, y), (width, y))

    def _draw_status(self) -> None:
        rect = pygame.Rect(0, self.screen.get_height() - STATUS_HEIGHT, self.screen.get_width(), STATUS_HEIGHT)
        pygame.draw.rect(self.screen, self.palette[0], rect)
        self._draw_text(self.status, 10, rect.y + 7, self.palette[17], self.small_font)
        controls = "Ctrl+S Save | Ctrl+O Load | 1-8 Layers | G Grid | +/- Zoom"
        self._draw_text(controls, SIDEBAR_WIDTH + 12, rect.y + 7, self.palette[18], self.small_font)

    def _draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
        font: pygame.font.Font | None = None,
    ) -> None:
        font = font or self.small_font
        self.screen.blit(font.render(text, True, color), (x, y))


def main() -> int:
    try:
        LevelEditor().run()
    except ModuleNotFoundError as exc:
        if exc.name == "pygame":
            print("pygame is required. Install dependencies with: python3 -m pip install -r requirements.txt")
            return 1
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
