import pygame
from dataclasses import dataclass

GRAVITY = 2200.0
MOVE_SPEED = 260.0
JUMP_SPEED = 720.0

COYOTE_TIME = 0.10
JUMP_BUFFER_TIME = 0.12

@dataclass
class Player:
    rect: pygame.Rect
    color: tuple
    vx: float = 0.0
    vy: float = 0.0
    on_ground: bool = False
    facing: int = 1
    has_gun: bool = False
    coyote: float = 0.0
    jump_buffer: float = 0.0

def collide_axis(rect: pygame.Rect, dx: int, dy: int, solids: list[pygame.Rect]) -> bool:
    on_ground = False

    rect.x += dx
    for s in solids:
        if rect.colliderect(s):
            if dx > 0:
                rect.right = s.left
            elif dx < 0:
                rect.left = s.right

    rect.y += dy
    for s in solids:
        if rect.colliderect(s):
            if dy > 0:
                rect.bottom = s.top
                on_ground = True
            elif dy < 0:
                rect.top = s.bottom

    return on_ground

class Level1:
    def __init__(self, w: int, h: int, p1_controls, p2_controls):
        self.w = w
        self.h = h
        self.p1c = p1_controls
        self.p2c = p2_controls

        self.font = pygame.font.SysFont(None, 22)
        self.big_font = pygame.font.SysFont(None, 44)

        self.solids = self.build_solids()

        self.cage_area = pygame.Rect(40, self.h - 210, 180, 170)
        self.cage_walls = [
            pygame.Rect(self.cage_area.left, self.cage_area.top, self.cage_area.width, 10),
            pygame.Rect(self.cage_area.left, self.cage_area.bottom - 10, self.cage_area.width, 10),
            pygame.Rect(self.cage_area.left, self.cage_area.top, 10, self.cage_area.height),
            pygame.Rect(self.cage_area.right - 10, self.cage_area.top, 10, self.cage_area.height),
        ]

        red_spawn = pygame.Rect(self.cage_area.left + 60, self.cage_area.bottom - 44, 28, 34)

        self.p1 = Player(red_spawn.copy(), (220, 70, 70), has_gun=False)
        self.p2 = Player(pygame.Rect(260, self.h - 120, 28, 34), (70, 210, 140), has_gun=False)

        self.key_rect = pygame.Rect(760, 260, 18, 18)
        self.gun_pickup = pygame.Rect(740, self.h - 78, 40, 40)
        self.exit_zone = pygame.Rect(880, self.h - 140, 60, 100)

        self.key_collected = False
        self.cage_open = False
        self.red_released = False
        self.guns_available = False
        self.guns_collected = False

    def build_solids(self):
        solids = []
        solids.append(pygame.Rect(0, self.h - 40, self.w, 40))
        solids.append(pygame.Rect(0, 0, self.w, 20))
        solids.append(pygame.Rect(0, 0, 20, self.h))
        solids.append(pygame.Rect(self.w - 20, 0, 20, self.h))

        solids.append(pygame.Rect(120, 420, 240, 20))
        solids.append(pygame.Rect(430, 360, 240, 20))
        solids.append(pygame.Rect(710, 300, 190, 20))
        solids.append(pygame.Rect(250, 280, 160, 20))
        solids.append(pygame.Rect(70, 320, 120, 20))
        return solids

    def apply_jump_helpers(self, p: Player, dt: float):
        p.jump_buffer = max(0.0, p.jump_buffer - dt)
        p.coyote = max(0.0, p.coyote - dt)
        if p.on_ground:
            p.coyote = COYOTE_TIME
        if p.jump_buffer > 0.0 and p.coyote > 0.0:
            p.vy = -JUMP_SPEED
            p.jump_buffer = 0.0
            p.coyote = 0.0

    def update_player(self, p: Player, ctrl, dt: float, solids: list[pygame.Rect]):
        keys = pygame.key.get_pressed()

        p.vx = 0.0
        if keys[ctrl.left]:
            p.vx -= MOVE_SPEED
            p.facing = -1
        if keys[ctrl.right]:
            p.vx += MOVE_SPEED
            p.facing = 1

        p.vy += GRAVITY * dt

        dx = int(p.vx * dt)
        dy = int(p.vy * dt)

        g1 = collide_axis(p.rect, dx, 0, solids)
        g2 = collide_axis(p.rect, 0, dy, solids)

        p.on_ground = g1 or g2
        if p.on_ground and p.vy > 0:
            p.vy = 0.0

    def draw_panel(self, screen, rect, title, lines, accent):
        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        screen.blit(panel, (rect.x, rect.y))
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=12)

        title_surf = self.font.render(title, True, accent)
        screen.blit(title_surf, (rect.x + 12, rect.y + 10))

        y = rect.y + 36
        for line in lines:
            surf = self.font.render(line, True, (235, 235, 240))
            screen.blit(surf, (rect.x + 12, y))
            y += 20

    def draw_badge(self, screen, x, y, label, on, on_color, off_color=(120, 120, 140)):
        text = f"{label}: {'YES' if on else 'NO'}"
        color = on_color if on else off_color
        pad_x = 10
        pad_y = 6
        surf = self.font.render(text, True, (20, 20, 26))
        w = surf.get_width() + pad_x * 2
        h = surf.get_height() + pad_y * 2

        badge = pygame.Rect(x, y, w, h)
        pygame.draw.rect(screen, color, badge, border_radius=999)
        screen.blit(surf, (x + pad_x, y + pad_y))
        return w

    def objective_text(self):
        if not self.key_collected:
            return "Objective: Green get the key"
        if not self.red_released:
            return "Objective: Red leave the cage"
        if not self.guns_collected:
            return "Objective: Collect guns"
        return "Objective: Both enter exit"

    def update(self, dt: float, events: list[pygame.event.Event]):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
                if event.key == pygame.K_r:
                    return "reset"
                if event.key == self.p1c.jump:
                    self.p1.jump_buffer = JUMP_BUFFER_TIME
                if event.key == self.p2c.jump:
                    self.p2.jump_buffer = JUMP_BUFFER_TIME

        current_solids = list(self.solids)
        if not self.cage_open:
            current_solids.extend(self.cage_walls)

        self.update_player(self.p1, self.p1c, dt, current_solids)
        self.update_player(self.p2, self.p2c, dt, current_solids)

        self.apply_jump_helpers(self.p1, dt)
        self.apply_jump_helpers(self.p2, dt)

        if (not self.key_collected) and self.p2.rect.colliderect(self.key_rect):
            self.key_collected = True
            self.cage_open = True

        if self.cage_open and (not self.red_released):
            if not self.cage_area.contains(self.p1.rect):
                self.red_released = True
                self.guns_available = True

        if self.guns_available and (not self.guns_collected):
            if self.p1.rect.colliderect(self.gun_pickup) or self.p2.rect.colliderect(self.gun_pickup):
                self.guns_collected = True
                self.p1.has_gun = True
                self.p2.has_gun = True

        if self.guns_collected:
            both_in_exit = self.p1.rect.colliderect(self.exit_zone) and self.p2.rect.colliderect(self.exit_zone)
            if both_in_exit:
                return "next_level"

        return None

    def draw(self, screen: pygame.Surface):
        screen.fill((18, 18, 26))

        for s in self.solids:
            pygame.draw.rect(screen, (70, 70, 90), s)

        cage_surface = pygame.Surface((self.cage_area.width, self.cage_area.height), pygame.SRCALPHA)
        cage_surface.fill((110, 200, 255, 55) if not self.cage_open else (90, 230, 150, 40))
        screen.blit(cage_surface, (self.cage_area.x, self.cage_area.y))

        if not self.cage_open:
            for w in self.cage_walls:
                pygame.draw.rect(screen, (170, 220, 255), w)
        else:
            for w in self.cage_walls:
                pygame.draw.rect(screen, (90, 230, 150), w, 2)

        if not self.key_collected:
            pygame.draw.rect(screen, (230, 210, 80), self.key_rect)

        if self.guns_available and not self.guns_collected:
            pygame.draw.rect(screen, (120, 120, 140), self.gun_pickup)
        if self.guns_collected:
            pygame.draw.rect(screen, (80, 200, 120), self.gun_pickup)

        pygame.draw.rect(screen, (210, 190, 70), self.exit_zone)

        pygame.draw.rect(screen, self.p1.color, self.p1.rect)
        pygame.draw.rect(screen, self.p2.color, self.p2.rect)

        top = pygame.Rect(16, 12, self.w - 32, 58)
        bar = pygame.Surface((top.width, top.height), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 140))
        screen.blit(bar, (top.x, top.y))
        pygame.draw.rect(screen, (255, 255, 255), top, 2, border_radius=14)

        title = self.big_font.render("LEVEL 1", True, (255, 255, 255))
        screen.blit(title, (top.x + 14, top.y + 10))

        obj = self.font.render(self.objective_text(), True, (235, 235, 240))
        screen.blit(obj, (top.x + 180, top.y + 22))

        bx = top.x + top.width - 14
        by = top.y + 16
        for label, on, col in [
            ("Key", self.key_collected, (230, 210, 80)),
            ("Cage", self.cage_open, (90, 230, 150)),
            ("Guns", self.guns_collected, (90, 230, 150)),
        ]:
            w = self.draw_badge(screen, bx - 10, by, label, on, col)
            bx -= (w + 10)

        left_panel = pygame.Rect(16, 86, 320, 120)
        right_panel = pygame.Rect(self.w - 336, 86, 320, 120)

        p1_lines = [
            f"Move: {pygame.key.name(self.p1c.left)}  {pygame.key.name(self.p1c.right)}",
            f"Jump: {pygame.key.name(self.p1c.jump)}",
            f"Shoot: {pygame.key.name(self.p1c.shoot)}",
            f"Gun: {'YES' if self.p1.has_gun else 'NO'}",
        ]
        p2_lines = [
            f"Move: {pygame.key.name(self.p2c.left)}  {pygame.key.name(self.p2c.right)}",
            f"Jump: {pygame.key.name(self.p2c.jump)}",
            f"Shoot: {pygame.key.name(self.p2c.shoot)}",
            f"Gun: {'YES' if self.p2.has_gun else 'NO'}",
        ]

        self.draw_panel(screen, left_panel, "PLAYER 1 RED", p1_lines, (220, 70, 70))
        self.draw_panel(screen, right_panel, "PLAYER 2 GREEN", p2_lines, (70, 210, 140))

        help_text = self.font.render("R reset    Esc quit", True, (200, 200, 210))
        screen.blit(help_text, (16, self.h - 28))
