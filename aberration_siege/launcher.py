from __future__ import annotations

import sys

import pygame

from aberration_siege.core.constants import MIN_WINDOW_SIZE
from aberration_siege.core.palette import DAWNBRINGER32_FALLBACK
from aberration_siege.editor.app import LevelEditor
from aberration_siege.editor.ui import Button


LAUNCHER_SIZE = MIN_WINDOW_SIZE
BUTTON_WIDTH = 320
BUTTON_HEIGHT = 44


class EngineLauncher:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("AberrationSiege Engine Launcher")
        self.screen = pygame.display.set_mode(LAUNCHER_SIZE, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.Font(None, 42)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.palette = DAWNBRINGER32_FALLBACK
        self.buttons: list[Button] = []
        self.status = "Choose a tool"
        self.running = True

    def run(self) -> int:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    width = max(event.w, MIN_WINDOW_SIZE[0])
                    height = max(event.h, MIN_WINDOW_SIZE[1])
                    self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)

            self._draw()
            self.clock.tick(60)

        pygame.quit()
        return 0

    def _handle_click(self, pos: tuple[int, int]) -> None:
        for button in self.buttons:
            if not button.hit(pos):
                continue

            if button.id == "open:editor":
                pygame.quit()
                LevelEditor().run()
                self.running = False
            elif button.id == "open:game":
                self.status = "Game runtime is not built yet"
            elif button.id == "open:data":
                self.status = "Data editor tabs are not built yet"
            elif button.id == "app:quit":
                self.running = False
            return

    def _draw(self) -> None:
        self.buttons = []
        self.screen.fill(self.palette[1])

        width, height = self.screen.get_size()
        center_x = width // 2
        top = max(86, height // 2 - 190)

        self._draw_text("AberrationSiege", center_x, top, self.palette[17], self.title_font, center=True)
        self._draw_text("Engine Launcher", center_x, top + 42, self.palette[9], self.font, center=True)

        button_y = top + 104
        for button_id, label, enabled in (
            ("open:editor", "Level Editor", True),
            ("open:data", "Data Editor", False),
            ("open:game", "Run Game", False),
            ("app:quit", "Quit", True),
        ):
            button = Button(
                id=button_id,
                label=label,
                rect=pygame.Rect(center_x - BUTTON_WIDTH // 2, button_y, BUTTON_WIDTH, BUTTON_HEIGHT),
                enabled=enabled,
            )
            self._draw_button(button)
            self.buttons.append(button)
            button_y += BUTTON_HEIGHT + 12

        self._draw_text(self.status, center_x, button_y + 12, self.palette[18], self.small_font, center=True)
        self._draw_text("Esc exits", center_x, height - 42, self.palette[19], self.small_font, center=True)
        pygame.display.flip()

    def _draw_button(self, button: Button) -> None:
        fill = self.palette[19] if button.enabled else self.palette[20]
        border = self.palette[18]
        selected_fill = self.palette[23]
        text = self.palette[17] if button.enabled else self.palette[18]
        button.draw(self.screen, self.font, fill, border, text, selected_fill, self.palette[20])

    def _draw_text(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int],
        font: pygame.font.Font,
        center: bool = False,
    ) -> None:
        surface = font.render(text, True, color)
        rect = surface.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.screen.blit(surface, rect)


def main() -> int:
    try:
        return EngineLauncher().run()
    except ModuleNotFoundError as exc:
        if exc.name == "pygame":
            print("pygame is required. Install dependencies with: python3 -m pip install -r requirements.txt")
            return 1
        raise


if __name__ == "__main__":
    sys.exit(main())
