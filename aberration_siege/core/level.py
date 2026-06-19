from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aberration_siege.core.constants import LAYER_ORDER


Grid = list[list[int | None]]


def empty_grid(width: int, height: int, fill: int | None = None) -> Grid:
    return [[fill for _ in range(width)] for _ in range(height)]


@dataclass
class Level:
    name: str = "Editor Level"
    width: int = 48
    height: int = 32
    max_width: int = 80
    max_height: int = 45
    layers: dict[str, Grid] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for layer in LAYER_ORDER:
            grid = self.layers.get(layer)
            if not grid:
                self.layers[layer] = empty_grid(self.width, self.height)

    @classmethod
    def new(cls, width: int = 48, height: int = 32) -> "Level":
        return cls(width=width, height=height)

    @classmethod
    def load(cls, path: Path) -> "Level":
        payload = json.loads(path.read_text(encoding="utf-8"))
        level = cls(
            name=payload.get("name", "Editor Level"),
            width=int(payload["width"]),
            height=int(payload["height"]),
            max_width=int(payload.get("max_width", payload["width"])),
            max_height=int(payload.get("max_height", payload["height"])),
            layers=payload.get("layers", {}),
        )
        level.validate()
        return level

    def save(self, path: Path, tile_count: int) -> None:
        self.validate(tile_count=tile_count)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "max_width": self.max_width,
            "max_height": self.max_height,
            "tile_size": 16,
            "layer_order": LAYER_ORDER,
            "layers": self.layers,
        }

    def validate(self, tile_count: int | None = None) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Level dimensions must be positive.")
        if self.width > self.max_width or self.height > self.max_height:
            raise ValueError("Level dimensions cannot exceed the configured maximum size.")

        for layer in LAYER_ORDER:
            if layer not in self.layers:
                raise ValueError(f"Missing layer: {layer}")
            grid = self.layers[layer]
            if len(grid) != self.height:
                raise ValueError(f"Layer {layer} has the wrong row count.")
            for row in grid:
                if len(row) != self.width:
                    raise ValueError(f"Layer {layer} has the wrong column count.")

        if tile_count is not None:
            for layer_name, grid in self.layers.items():
                if layer_name == "kingdom_zone":
                    invalid_values = [cell for row in grid for cell in row if cell not in (None, 0, 1)]
                    if invalid_values:
                        raise ValueError("Kingdom Zone layer must only contain empty cells or 1.")
                    continue

                invalid_tiles = [
                    cell
                    for row in grid
                    for cell in row
                    if cell is not None and (not isinstance(cell, int) or cell < 0 or cell >= tile_count)
                ]
                if invalid_tiles:
                    raise ValueError(f"Layer {layer_name} references unavailable tile ids.")

    def validation_errors(self, tile_count: int | None = None) -> list[str]:
        try:
            self.validate(tile_count=tile_count)
        except ValueError as exc:
            return [str(exc)]
        return []

    def layer_cell_counts(self) -> dict[str, int]:
        return {
            layer: sum(1 for row in self.layers[layer] for cell in row if cell is not None)
            for layer in LAYER_ORDER
        }

    def painted_cell_count(self) -> int:
        return sum(self.layer_cell_counts().values())

    def resize(self, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Level dimensions must be positive.")
        if width > self.max_width or height > self.max_height:
            raise ValueError("Level dimensions cannot exceed the configured maximum size.")

        for layer in LAYER_ORDER:
            self.layers[layer] = _resize_grid(self.layers[layer], width, height)

        self.width = width
        self.height = height
        self.validate()

    def set_max_size(self, max_width: int, max_height: int) -> None:
        if max_width < self.width or max_height < self.height:
            raise ValueError("Maximum size cannot be smaller than the current level size.")

        self.max_width = max_width
        self.max_height = max_height
        self.validate()

    def paint(self, layer: str, x: int, y: int, value: int | None) -> None:
        if not self.in_bounds(x, y):
            return
        self.layers[layer][y][x] = value

    def sample(self, layer: str, x: int, y: int) -> int | None:
        if not self.in_bounds(x, y):
            return None
        return self.layers[layer][y][x]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height


def _resize_grid(grid: Grid, width: int, height: int) -> Grid:
    resized = empty_grid(width, height)
    copy_height = min(len(grid), height)

    for y in range(copy_height):
        row = grid[y]
        copy_width = min(len(row), width)
        resized[y][:copy_width] = row[:copy_width]

    return resized
