import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from dataclasses import dataclass

from level1 import Level1
from level2 import Level2

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 960, 540
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Coop Partner")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 24)
mid_font = pygame.font.SysFont(None, 30)
big_font = pygame.font.SysFont(None, 64)

@dataclass
class Controls:
    left: int
    right: int
    jump: int
    shoot: int

CONTROL_PRESETS_P1 = {
    1: Controls(left=pygame.K_a, right=pygame.K_d, jump=pygame.K_w, shoot=pygame.K_f),
    2: Controls(left=pygame.K_j, right=pygame.K_l, jump=pygame.K_i, shoot=pygame.K_o),
}

CONTROL_PRESETS_P2 = {
    1: Controls(left=pygame.K_LEFT, right=pygame.K_RIGHT, jump=pygame.K_UP, shoot=pygame.K_RSHIFT),
    2: Controls(left=pygame.K_KP4, right=pygame.K_KP6, jump=pygame.K_KP8, shoot=pygame.K_KP0),
}

def keyname(k):
    return pygame.key.name(k)

def pill(surface, x, y, text, bg, fg=(18, 18, 26)):
    pad_x = 12
    pad_y = 7
    s = font.render(text, True, fg)
    rect = pygame.Rect(x, y, s.get_width() + pad_x * 2, s.get_height() + pad_y * 2)
    pygame.draw.rect(surface, bg, rect, border_radius=999)
    surface.blit(s, (x + pad_x, y + pad_y))
    return rect

def draw_text(surface, x, y, text, fnt, color=(255, 255, 255)):
    surface.blit(fnt.render(text, True, color), (x, y))

def glow_rect(surface, rect, color, strength=10):
    for i in range(strength, 0, -1):
        alpha = max(0, 18 - i)
        glow = pygame.Surface((rect.width + i * 2, rect.height + i * 2), pygame.SRCALPHA)
        glow.fill((*color, alpha))
        surface.blit(glow, (rect.x - i, rect.y - i))

def card(surface, rect, title, lines, selected, accent):
    glow_rect(surface, rect, accent, strength=14 if selected else 8)

    bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 160))
    surface.blit(bg, (rect.x, rect.y))

    pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=18)
    if selected:
        pygame.draw.rect(surface, accent, rect, 4, border_radius=18)

    draw_text(surface, rect.x + 18, rect.y + 14, title, mid_font, (240, 240, 245))

    y = rect.y + 58
    for line in lines:
        draw_text(surface, rect.x + 18, y, line, font, (220, 220, 230))
        y += 26

def lines_for(ctrl: Controls):
    return [
        f"Move: {keyname(ctrl.left)}   {keyname(ctrl.right)}",
        f"Jump: {keyname(ctrl.jump)}",
        f"Shoot: {keyname(ctrl.shoot)}",
    ]

def start_screen() -> tuple[Controls, Controls]:
    p1_choice = 1
    p2_choice = 1

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise SystemExit

                if event.key == pygame.K_1:
                    p1_choice = 1
                if event.key == pygame.K_2:
                    p1_choice = 2

                if event.key == pygame.K_9:
                    p2_choice = 1
                if event.key == pygame.K_0:
                    p2_choice = 2

                if event.key == pygame.K_RETURN:
                    return CONTROL_PRESETS_P1[p1_choice], CONTROL_PRESETS_P2[p2_choice]

        screen.fill((12, 12, 18))

        # Background pattern dots
        for y in range(0, HEIGHT, 28):
            for x in range(0, WIDTH, 28):
                if (x // 28 + y // 28) % 2 == 0:
                    pygame.draw.circle(screen, (25, 25, 36), (x + 10, y + 10), 2)

        # Header
        draw_text(screen, 40, 26, "COOP PARTNER", big_font, (255, 255, 255))
        draw_text(screen, 42, 92, "Pick your controls", mid_font, (220, 220, 230))

        # Hint pills
        pill(screen, 40, 124, "Player 1 presets: 1 or 2", (220, 70, 70))
        pill(screen, 330, 124, "Player 2 presets: 9 or 0", (70, 210, 140))
        pill(screen, 610, 124, "Press Enter to start", (230, 210, 80))

        # Cards
        p1_rect = pygame.Rect(40, 170, 430, 250)
        p2_rect = pygame.Rect(490, 170, 430, 250)

        card(
            screen,
            p1_rect,
            f"PLAYER 1  RED   preset {p1_choice}",
            lines_for(CONTROL_PRESETS_P1[p1_choice]),
            True,
            (220, 70, 70),
        )
        card(
            screen,
            p2_rect,
            f"PLAYER 2  GREEN preset {p2_choice}",
            lines_for(CONTROL_PRESETS_P2[p2_choice]),
            True,
            (70, 210, 140),
        )

        # Bottom objectives panel
        obj = pygame.Rect(40, 438, 880, 80)
        bg = pygame.Surface((obj.width, obj.height), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        screen.blit(bg, (obj.x, obj.y))
        pygame.draw.rect(screen, (255, 255, 255), obj, 2, border_radius=18)

        draw_text(screen, 58, 454, "Level 1: Green gets key to open red cage. Red leaves. Guns appear. Collect. Exit together.", font)
        draw_text(screen, 58, 480, "Level 2: Shoot both blue buttons once. Door stays open. Exit together.", font)

        draw_text(screen, 40, 518, "Esc quit   In game: R reset", font, (200, 200, 210))

        pygame.display.flip()

def main():
    p1_controls, p2_controls = start_screen()

    level = 1
    current = Level1(WIDTH, HEIGHT, p1_controls, p2_controls)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        events = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                events.append(event)

        result = current.update(dt, events)
        current.draw(screen)
        pygame.display.flip()

        if result == "quit":
            running = False
        elif result == "reset":
            level = 1
            current = Level1(WIDTH, HEIGHT, p1_controls, p2_controls)
        elif result == "next_level":
            if level == 1:
                level = 2
                current = Level2(WIDTH, HEIGHT, p1_controls, p2_controls)
            else:
                level = 1
                current = Level1(WIDTH, HEIGHT, p1_controls, p2_controls)

    pygame.quit()

if __name__ == "__main__":
    main()
