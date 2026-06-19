from __future__ import annotations

from dataclasses import dataclass

import pygame


Color = tuple[int, int, int]


@dataclass
class Button:
    id: str
    label: str
    rect: pygame.Rect
    selected: bool = False
    enabled: bool = True

    def hit(self, pos: tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(pos)

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        fill: Color,
        border: Color,
        text: Color,
        selected_fill: Color,
        disabled_fill: Color,
    ) -> None:
        color = selected_fill if self.selected else fill
        if not self.enabled:
            color = disabled_fill

        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, border, self.rect, 1)

        label = font.render(self.label, True, text)
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)


@dataclass
class Section:
    title: str
    y: int

    def draw(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        x: int,
        width: int,
        text: Color,
        line: Color,
    ) -> None:
        label = font.render(self.title, True, text)
        surface.blit(label, (x, self.y))
        pygame.draw.line(surface, line, (x, self.y + 19), (x + width, self.y + 19))
