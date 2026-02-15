import pygame


def build():
    world_w = 2800
    world_h = 2000

    walls = []

    walls.append(pygame.Rect(0, 0, world_w, 40))
    walls.append(pygame.Rect(0, world_h - 40, world_w, 40))
    walls.append(pygame.Rect(0, 0, 40, world_h))
    walls.append(pygame.Rect(world_w - 40, 0, 40, world_h))

    walls += [
        pygame.Rect(250, 250, 2300, 40),
        pygame.Rect(250, 250, 40, 650),
        pygame.Rect(250, 860, 1100, 40),
        pygame.Rect(1310, 420, 40, 480),
        pygame.Rect(700, 420, 650, 40),
        pygame.Rect(700, 420, 40, 360),

        pygame.Rect(300, 1200, 2100, 40),
        pygame.Rect(2360, 1200, 40, 520),
        pygame.Rect(300, 1680, 2100, 40),
        pygame.Rect(300, 1200, 40, 520),

        pygame.Rect(1600, 520, 900, 40),
        pygame.Rect(1600, 520, 40, 520),
        pygame.Rect(1900, 820, 40, 520),
        pygame.Rect(2200, 520, 40, 820),

        pygame.Rect(1000, 1450, 700, 40),
        pygame.Rect(1000, 1450, 40, 230),
        pygame.Rect(1660, 1450, 40, 230),
    ]

    key_rect = pygame.Rect(2600, 350, 26, 18)
    door_rect = pygame.Rect(1400, 1860, 60, 90)

    shooter_spawn = (120, 120)
    runner_spawn = (120, 1840)

    return {
        "world_size": (world_w, world_h),
        "walls": walls,
        "key_rect": key_rect,
        "door_rect": door_rect,
        "shooter_spawn": shooter_spawn,
        "runner_spawn": runner_spawn,
    }