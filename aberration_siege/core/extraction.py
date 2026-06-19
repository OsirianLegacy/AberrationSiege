from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from aberration_siege.core.constants import ROOT_DIR, TILE_SIZE


@dataclass(frozen=True)
class ExtractedSprite:
    id: str
    source: str
    path: str
    x: int
    y: int
    width: int
    height: int


def extract_from_asset_manifest(
    manifest_path: Path,
    output_dir: Path,
    output_manifest_path: Path,
) -> list[ExtractedSprite]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    extracted: list[ExtractedSprite] = []

    for tileset in manifest.get("tilesets", []):
        extracted.extend(
            extract_sheet(
                source_path=_resolve_project_path(tileset["path"]),
                output_dir=output_dir / tileset["id"],
                sprite_id_prefix=tileset["id"],
                tile_width=int(tileset.get("tile_width", TILE_SIZE)),
                tile_height=int(tileset.get("tile_height", TILE_SIZE)),
            )
        )

    for source in manifest.get("sprite_sources", []):
        source_path = _resolve_project_path(source["path"])
        tile_width = int(source.get("tile_width", TILE_SIZE))
        tile_height = int(source.get("tile_height", TILE_SIZE))

        if source_path.is_dir():
            for child in sorted(source_path.glob("*.png")):
                extracted.extend(
                    extract_sheet(
                        source_path=child,
                        output_dir=output_dir / source["id"] / child.stem,
                        sprite_id_prefix=f"{source['id']}_{child.stem}",
                        tile_width=tile_width,
                        tile_height=tile_height,
                    )
                )
        else:
            extracted.extend(
                extract_sheet(
                    source_path=source_path,
                    output_dir=output_dir / source["id"],
                    sprite_id_prefix=source["id"],
                    tile_width=tile_width,
                    tile_height=tile_height,
                )
            )

    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "tile_size": TILE_SIZE,
        "sprites": [sprite.__dict__ for sprite in extracted],
    }
    output_manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return extracted


def extract_sheet(
    source_path: Path,
    output_dir: Path,
    sprite_id_prefix: str,
    tile_width: int = TILE_SIZE,
    tile_height: int = TILE_SIZE,
) -> list[ExtractedSprite]:
    import pygame

    if not source_path.exists():
        raise FileNotFoundError(source_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    sheet = pygame.image.load(str(source_path))
    extracted: list[ExtractedSprite] = []
    index = 0

    for y in range(0, sheet.get_height() - tile_height + 1, tile_height):
        for x in range(0, sheet.get_width() - tile_width + 1, tile_width):
            sprite = pygame.Surface((tile_width, tile_height), pygame.SRCALPHA)
            sprite.blit(sheet, (0, 0), (x, y, tile_width, tile_height))

            sprite_id = f"{sprite_id_prefix}_{index:03d}"
            output_path = output_dir / f"{sprite_id}.png"
            pygame.image.save(sprite, str(output_path))

            extracted.append(
                ExtractedSprite(
                    id=sprite_id,
                    source=_project_relative(source_path),
                    path=_project_relative(output_path),
                    x=x,
                    y=y,
                    width=tile_width,
                    height=tile_height,
                )
            )
            index += 1

    return extracted


def _resolve_project_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return ROOT_DIR / candidate


def _project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return path.as_posix()
