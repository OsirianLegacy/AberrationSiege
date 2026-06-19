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
from aberration_siege.editor.ui import Button, Section


SIDEBAR_WIDTH = 304
STATUS_HEIGHT = 30
TILE_PICKER_GAP = 4
TOOLBAR_HEIGHT = 44
SIDEBAR_PAD = 12
BUTTON_HEIGHT = 26
SECTION_GAP = 14

TOOLS = ["paint", "erase", "sample"]


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
        self.active_tool = "paint"
        self.selected_tile = 0
        self.tile_scroll = 0
        self.camera = Camera()
        self.status = "Ready"
        self.show_grid = True
        self.running = True
        self.buttons: list[Button] = []
        self.tile_rects: list[tuple[int, pygame.Rect]] = []
        self.tile_picker_rect = pygame.Rect(0, 0, 0, 0)
        self.viewport_rect = pygame.Rect(0, 0, 0, 0)

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
                self._handle_mouse_event(event)

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
            self.status = f"Grid: {'on' if self.show_grid else 'off'}"
        elif event.key == pygame.K_b:
            self._set_tool("paint")
        elif event.key == pygame.K_e:
            self._set_tool("erase")
        elif event.key == pygame.K_i:
            self._set_tool("sample")
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
        mouse_pos = pygame.mouse.get_pos()
        if self.tile_picker_rect.collidepoint(mouse_pos):
            self.tile_scroll = max(0, self.tile_scroll - event.y)
        elif pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.camera.zoom = max(1, min(5, self.camera.zoom + event.y))
        else:
            self.camera.y = max(0, min(self.level.height - 1, self.camera.y - event.y))

    def _handle_mouse_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION and not any(event.buttons):
            return

        mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._handle_button_click(mouse_pos):
                return
            if self._pick_tile(mouse_pos):
                return

        if not self.viewport_rect.collidepoint(mouse_pos):
            return

        cell = self._mouse_to_cell(mouse_pos)
        if cell is None:
            return

        x, y = cell
        buttons = pygame.mouse.get_pressed(3)
        if buttons[0] and self.active_tool == "sample":
            self._sample_cell(x, y)
        elif buttons[0] and self.active_tool == "erase":
            self.level.paint(self.active_layer, x, y, None)
        elif buttons[0]:
            if self.active_layer == "kingdom_zone":
                self.level.paint(self.active_layer, x, y, 1)
            else:
                self.level.paint(self.active_layer, x, y, self.selected_tile)
        elif buttons[2]:
            self.level.paint(self.active_layer, x, y, None)

    def _handle_button_click(self, mouse_pos: tuple[int, int]) -> bool:
        for button in self.buttons:
            if not button.hit(mouse_pos):
                continue

            if button.id.startswith("layer:"):
                self.active_layer_index = int(button.id.split(":", 1)[1])
                self.status = f"Layer: {self.active_layer}"
            elif button.id.startswith("tool:"):
                self._set_tool(button.id.split(":", 1)[1])
            elif button.id == "file:save":
                self._save()
            elif button.id == "file:load":
                self._load()
            elif button.id == "view:grid":
                self.show_grid = not self.show_grid
                self.status = f"Grid: {'on' if self.show_grid else 'off'}"
            elif button.id == "zoom:out":
                self.camera.zoom = max(1, self.camera.zoom - 1)
                self.status = f"Zoom: {self.camera.zoom}x"
            elif button.id == "zoom:in":
                self.camera.zoom = min(5, self.camera.zoom + 1)
                self.status = f"Zoom: {self.camera.zoom}x"
            return True

        return False

    def _pick_tile(self, mouse_pos: tuple[int, int]) -> bool:
        for tile_index, rect in self.tile_rects:
            if rect.collidepoint(mouse_pos):
                self.selected_tile = tile_index
                self.status = f"Tile: {tile_index}"
                return True
        return False

    def _set_tool(self, tool: str) -> None:
        if tool not in TOOLS:
            return
        self.active_tool = tool
        self.status = f"Tool: {tool}"

    def _sample_cell(self, x: int, y: int) -> None:
        value = self.level.sample(self.active_layer, x, y)
        if isinstance(value, int) and self.active_layer != "kingdom_zone":
            self.selected_tile = value
            self.status = f"Sampled tile {value}"
        elif value is None:
            self.status = "Sampled empty cell"
        else:
            self.status = f"Sampled {self.active_layer}"

    def _mouse_to_cell(self, mouse_pos: tuple[int, int]) -> tuple[int, int] | None:
        tile_px = TILE_SIZE * self.camera.zoom
        grid_x = mouse_pos[0] - self.viewport_rect.x
        grid_y = mouse_pos[1] - self.viewport_rect.y
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
        self.buttons = []
        self.tile_rects = []
        self.viewport_rect = pygame.Rect(
            SIDEBAR_WIDTH,
            TOOLBAR_HEIGHT,
            self.screen.get_width() - SIDEBAR_WIDTH,
            self.screen.get_height() - TOOLBAR_HEIGHT - STATUS_HEIGHT,
        )
        self._draw_toolbar()
        self._draw_sidebar()
        self._draw_level()
        self._draw_status()
        pygame.display.flip()

    def _draw_toolbar(self) -> None:
        rect = pygame.Rect(SIDEBAR_WIDTH, 0, self.screen.get_width() - SIDEBAR_WIDTH, TOOLBAR_HEIGHT)
        pygame.draw.rect(self.screen, self.palette[20], rect)
        pygame.draw.line(self.screen, self.palette[18], rect.bottomleft, rect.bottomright)

        x = SIDEBAR_WIDTH + 12
        y = 9
        for button_id, label in (
            ("file:save", "Save"),
            ("file:load", "Load"),
            ("view:grid", "Grid"),
            ("zoom:out", "-"),
            ("zoom:in", "+"),
        ):
            width = 64 if len(label) > 1 else 32
            button = Button(
                id=button_id,
                label=label,
                rect=pygame.Rect(x, y, width, BUTTON_HEIGHT),
                selected=button_id == "view:grid" and self.show_grid,
            )
            self._draw_button(button)
            self.buttons.append(button)
            x += width + 8

        self._draw_text(
            f"{self.level.name} | {self.level.width}x{self.level.height} | Zoom {self.camera.zoom}x",
            x + 8,
            15,
            self.palette[9],
            self.small_font,
        )

    def _draw_sidebar(self) -> None:
        sidebar = pygame.Rect(0, 0, SIDEBAR_WIDTH, self.screen.get_height())
        pygame.draw.rect(self.screen, self.palette[20], sidebar)
        pygame.draw.line(self.screen, self.palette[18], (SIDEBAR_WIDTH - 1, 0), (SIDEBAR_WIDTH - 1, sidebar.h))

        self._draw_text("AberrationSiege Editor", SIDEBAR_PAD, 10, self.palette[17], self.font)
        self._draw_text(f"Layer: {self.active_layer}", SIDEBAR_PAD, 34, self.palette[9])
        self._draw_text(f"Tool: {self.active_tool}", SIDEBAR_PAD, 54, self.palette[9])
        self._draw_text(f"Tile: {self.selected_tile}", SIDEBAR_PAD, 74, self.palette[9])

        preview_rect = pygame.Rect(SIDEBAR_WIDTH - SIDEBAR_PAD - 56, 18, 48, 48)
        pygame.draw.rect(self.screen, self.palette[1], preview_rect)
        if self.tiles:
            preview = pygame.transform.scale(self.tiles[self.selected_tile], (48, 48))
            self.screen.blit(preview, preview_rect)
        pygame.draw.rect(self.screen, self.palette[17], preview_rect, 1)

        y = 104
        Section("Tools", y).draw(
            self.screen, self.small_font, SIDEBAR_PAD, SIDEBAR_WIDTH - SIDEBAR_PAD * 2, self.palette[17], self.palette[18]
        )
        y += 28
        x = SIDEBAR_PAD
        tool_labels = {"paint": "Paint", "erase": "Erase", "sample": "Pick"}
        for tool in TOOLS:
            button = Button(
                id=f"tool:{tool}",
                label=tool_labels[tool],
                rect=pygame.Rect(x, y, 84, BUTTON_HEIGHT),
                selected=tool == self.active_tool,
            )
            self._draw_button(button)
            self.buttons.append(button)
            x += 92

        y += BUTTON_HEIGHT + SECTION_GAP
        Section("Layers", y).draw(
            self.screen, self.small_font, SIDEBAR_PAD, SIDEBAR_WIDTH - SIDEBAR_PAD * 2, self.palette[17], self.palette[18]
        )
        y += 28
        for index, layer in enumerate(LAYER_ORDER):
            button = Button(
                id=f"layer:{index}",
                label=f"{index + 1}  {layer}",
                rect=pygame.Rect(SIDEBAR_PAD, y, SIDEBAR_WIDTH - SIDEBAR_PAD * 2, BUTTON_HEIGHT),
                selected=index == self.active_layer_index,
            )
            self._draw_button(button, align_left=True)
            self.buttons.append(button)
            y += BUTTON_HEIGHT + 4

        y += SECTION_GAP - 2
        Section("Tiles", y).draw(
            self.screen, self.small_font, SIDEBAR_PAD, SIDEBAR_WIDTH - SIDEBAR_PAD * 2, self.palette[17], self.palette[18]
        )
        self._draw_tile_picker(y + 28)

    def _draw_tile_picker(self, top: int) -> None:
        left = SIDEBAR_PAD
        available_width = SIDEBAR_WIDTH - SIDEBAR_PAD * 2
        bottom = self.screen.get_height() - STATUS_HEIGHT - SIDEBAR_PAD
        self.tile_picker_rect = pygame.Rect(left, top, available_width, max(0, bottom - top))
        pygame.draw.rect(self.screen, self.palette[1], self.tile_picker_rect)
        pygame.draw.rect(self.screen, self.palette[18], self.tile_picker_rect, 1)

        columns = max(1, (available_width - TILE_PICKER_GAP) // (TILE_SIZE * 2 + TILE_PICKER_GAP))
        tile_px = TILE_SIZE * 2
        visible_rows = max(1, self.tile_picker_rect.height // (tile_px + TILE_PICKER_GAP))
        max_scroll = max(0, (len(self.tiles) + columns - 1) // columns - visible_rows)
        self.tile_scroll = min(self.tile_scroll, max_scroll)

        start_index = self.tile_scroll * columns
        end_index = min(len(self.tiles), start_index + columns * visible_rows)

        for index in range(start_index, end_index):
            local_index = index - start_index
            col = local_index % columns
            row = local_index // columns
            x = left + TILE_PICKER_GAP + col * (tile_px + TILE_PICKER_GAP)
            y = top + row * (tile_px + TILE_PICKER_GAP)
            rect = pygame.Rect(x, y, tile_px, tile_px)
            self.screen.blit(pygame.transform.scale(self.tiles[index], (tile_px, tile_px)), (x, y))
            border = self.palette[8] if index == self.selected_tile else self.palette[19]
            pygame.draw.rect(self.screen, border, rect, 1)
            self.tile_rects.append((index, rect))

    def _draw_level(self) -> None:
        tile_px = TILE_SIZE * self.camera.zoom
        view_width = self.viewport_rect.width // tile_px + 2
        view_height = self.viewport_rect.height // tile_px + 2

        for y in range(self.camera.y, min(self.level.height, self.camera.y + view_height)):
            for x in range(self.camera.x, min(self.level.width, self.camera.x + view_width)):
                dest = pygame.Rect(
                    self.viewport_rect.x + (x - self.camera.x) * tile_px,
                    self.viewport_rect.y + (y - self.camera.y) * tile_px,
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

        for col in range(view_width):
            x = self.viewport_rect.x + col * tile_px
            pygame.draw.line(self.screen, color, (x, self.viewport_rect.y), (x, self.viewport_rect.bottom))
        for row in range(view_height):
            y = self.viewport_rect.y + row * tile_px
            pygame.draw.line(self.screen, color, (self.viewport_rect.x, y), (self.viewport_rect.right, y))

    def _draw_status(self) -> None:
        rect = pygame.Rect(0, self.screen.get_height() - STATUS_HEIGHT, self.screen.get_width(), STATUS_HEIGHT)
        pygame.draw.rect(self.screen, self.palette[0], rect)
        self._draw_text(self.status, SIDEBAR_PAD, rect.y + 8, self.palette[17], self.small_font)
        controls = "B Paint | E Erase | I Pick | 1-8 Layers | Ctrl+S Save | Right-click Erase"
        self._draw_text(controls, SIDEBAR_WIDTH + 12, rect.y + 7, self.palette[18], self.small_font)

    def _draw_button(self, button: Button, align_left: bool = False) -> None:
        fill = self.palette[19]
        selected_fill = self.palette[23]
        border = self.palette[18]
        disabled_fill = self.palette[20]
        text = self.palette[1] if button.selected else self.palette[17]

        if align_left:
            pygame.draw.rect(self.screen, selected_fill if button.selected else fill, button.rect)
            pygame.draw.rect(self.screen, border, button.rect, 1)
            label = self.small_font.render(button.label, True, text)
            self.screen.blit(label, (button.rect.x + 10, button.rect.y + 7))
        else:
            button.draw(self.screen, self.small_font, fill, border, text, selected_fill, disabled_fill)

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
