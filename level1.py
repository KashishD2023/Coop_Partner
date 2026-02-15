import pygame


def build():
    world_w = 2400
    world_h = 1800

    walls = []

    walls.append(pygame.Rect(0, 0, world_w, 40))
    walls.append(pygame.Rect(0, world_h - 40, world_w, 40))
    walls.append(pygame.Rect(0, 0, 40, world_h))
    walls.append(pygame.Rect(world_w - 40, 0, 40, world_h))

    walls += [
        pygame.Rect(200, 200, 900, 40),
        pygame.Rect(200, 200, 40, 700),
        pygame.Rect(200, 900, 700, 40),
        pygame.Rect(860, 520, 40, 420),

        pygame.Rect(1200, 150, 40, 900),
        pygame.Rect(1200, 1010, 900, 40),
        pygame.Rect(1600, 300, 700, 40),
        pygame.Rect(1600, 300, 40, 520),
        pygame.Rect(1900, 600, 40, 520),
        pygame.Rect(1400, 820, 540, 40),

        pygame.Rect(500, 1200, 1300, 40),
        pygame.Rect(500, 1200, 40, 420),
        pygame.Rect(1760, 1200, 40, 420),
        pygame.Rect(900, 1550, 900, 40),
    ]

    key_rect = pygame.Rect(2100, 200, 26, 18)
    door_rect = pygame.Rect(2200, 1650, 60, 90)

    shooter_spawn = (120, 120)
    runner_spawn = (120, 1600)

    return {
        "world_size": (world_w, world_h),
        "walls": walls,
        "key_rect": key_rect,
        "door_rect": door_rect,
        "shooter_spawn": shooter_spawn,
        "runner_spawn": runner_spawn,
    }