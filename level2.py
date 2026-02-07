import pygame
from dataclasses import dataclass

GRAVITY = 2200.0
MOVE_SPEED = 260.0
JUMP_SPEED = 720.0

COYOTE_TIME = 0.10
JUMP_BUFFER_TIME = 0.12

BULLET_SPEED = 900.0

@dataclass
class Player:
    rect: pygame.Rect
    color: tuple
    vx: float = 0.0
    vy: float = 0.0
    on_ground: bool = False
    facing: int = 1
    has_gun: bool = True
    coyote: float = 0.0
    jump_buffer: float = 0.0

@dataclass
class Bullet:
    pos: pygame.Vector2
    vel: pygame.Vector2

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

def rect_hit_point(r: pygame.Rect, p: pygame.Vector2) -> bool:
    return r.left <= p.x <= r.right and r.top <= p.y <= r.bottom

class Level2:
    def __init__(self, w: int, h: int, p1_controls, p2_controls):
        self.w = w
        self.h = h
        self.p1c = p1_controls
        self.p2c = p2_controls

        self.font = pygame.font.SysFont(None, 22)
        self.big_font = pygame.font.SysFont(None, 44)

        self.solids = self.build_solids()

        self.btn_left = pygame.Rect(130, 392, 70, 16)
        self.btn_right = pygame.Rect(740, 272, 70, 16)

        self.door = pygame.Rect(910, self.h - 140, 30, 100)
        self.exit_zone = pygame.Rect(840, self.h - 140, 70, 100)

        self.p1 = Player(pygame.Rect(60, self.h - 120, 28, 34), (220, 70, 70), has_gun=True)
        self.p2 = Player(pygame.Rect(120, self.h - 120, 28, 34), (70, 210, 140), has_gun=True)

        self.bullets: list[Bullet] = []

        self.left_on = False
        self.right_on = False

        self.won = False

    def build_solids(self):
        solids = []
        solids.append(pygame.Rect(0, self.h - 40, self.w, 40))
        solids.append(pygame.Rect(0, 0, self.w, 20))
        solids.append(pygame.Rect(0, 0, 20, self.h))
        solids.append(pygame.Rect(self.w - 20, 0, 20, self.h))

        solids.append(pygame.Rect(120, 420, 220, 20))
        solids.append(pygame.Rect(420, 360, 220, 20))
        solids.append(pygame.Rect(690, 300, 170, 20))
        solids.append(pygame.Rect(290, 260, 160, 20))
        solids.append(pygame.Rect(60, 300, 120, 20))
        return solids

    def fire_bullet(self, player: Player):
        y = player.rect.centery
        x = player.rect.centerx + (18 * player.facing)
        vel = pygame.Vector2(BULLET_SPEED * player.facing, 0)
        self.bullets.append(Bullet(pygame.Vector2(x, y), vel))

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
        text = f"{label}: {'ON' if on else 'OFF'}"
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

                if event.key == self.p1c.shoot:
                    self.fire_bullet(self.p1)
                if event.key == self.p2c.shoot:
                    self.fire_bullet(self.p2)

        door_open = self.left_on and self.right_on

        current_solids = list(self.solids)
        if not door_open:
            current_solids.append(self.door)

        self.update_player(self.p1, self.p1c, dt, current_solids)
        self.update_player(self.p2, self.p2c, dt, current_solids)

        self.apply_jump_helpers(self.p1, dt)
        self.apply_jump_helpers(self.p2, dt)

        new_bullets = []
        for b in self.bullets:
            b.pos += b.vel * dt

            alive = True
            if b.pos.x < -50 or b.pos.x > self.w + 50 or b.pos.y < -50 or b.pos.y > self.h + 50:
                alive = False

            if alive and (not self.left_on) and rect_hit_point(self.btn_left, b.pos):
                self.left_on = True
                alive = False

            if alive and (not self.right_on) and rect_hit_point(self.btn_right, b.pos):
                self.right_on = True
                alive = False

            if alive:
                hit_solid = False
                for s in current_solids:
                    if rect_hit_point(s, b.pos):
                        hit_solid = True
                        break
                if hit_solid:
                    alive = False

            if alive:
                new_bullets.append(b)

        self.bullets = new_bullets

        door_open = self.left_on and self.right_on
        both_in_exit = self.p1.rect.colliderect(self.exit_zone) and self.p2.rect.colliderect(self.exit_zone)
        if door_open and both_in_exit:
            self.won = True

        return None

    def draw(self, screen: pygame.Surface):
        screen.fill((18, 18, 26))

        for s in self.solids:
            pygame.draw.rect(screen, (70, 70, 90), s)

        door_open = self.left_on and self.right_on

        pygame.draw.rect(screen, (80, 170, 240) if not self.left_on else (80, 220, 140), self.btn_left)
        pygame.draw.rect(screen, (80, 170, 240) if not self.right_on else (80, 220, 140), self.btn_right)

        pygame.draw.rect(screen, (70, 170, 90) if door_open else (170, 70, 70), self.door)
        pygame.draw.rect(screen, (210, 190, 70), self.exit_zone)

        for b in self.bullets:
            pygame.draw.circle(screen, (255, 255, 255), (int(b.pos.x), int(b.pos.y)), 3)

        pygame.draw.rect(screen, self.p1.color, self.p1.rect)
        pygame.draw.rect(screen, self.p2.color, self.p2.rect)

        top = pygame.Rect(16, 12, self.w - 32, 58)
        bar = pygame.Surface((top.width, top.height), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 140))
        screen.blit(bar, (top.x, top.y))
        pygame.draw.rect(screen, (255, 255, 255), top, 2, border_radius=14)

        title = self.big_font.render("LEVEL 2", True, (255, 255, 255))
        screen.blit(title, (top.x + 14, top.y + 10))

        obj = self.font.render("Objective: Shoot both buttons once. Door stays open.", True, (235, 235, 240))
        screen.blit(obj, (top.x + 180, top.y + 22))

        bx = top.x + top.width - 14
        by = top.y + 16

        w1 = self.draw_badge(screen, bx - 10, by, "Left", self.left_on, (80, 220, 140))
        bx -= (w1 + 10)
        w2 = self.draw_badge(screen, bx - 10, by, "Right", self.right_on, (80, 220, 140))
        bx -= (w2 + 10)
        _ = self.draw_badge(screen, bx - 10, by, "Door", door_open, (80, 220, 140))

        left_panel = pygame.Rect(16, 86, 320, 120)
        right_panel = pygame.Rect(self.w - 336, 86, 320, 120)

        p1_lines = [
            f"Move: {pygame.key.name(self.p1c.left)}  {pygame.key.name(self.p1c.right)}",
            f"Jump: {pygame.key.name(self.p1c.jump)}",
            f"Shoot: {pygame.key.name(self.p1c.shoot)}",
        ]
        p2_lines = [
            f"Move: {pygame.key.name(self.p2c.left)}  {pygame.key.name(self.p2c.right)}",
            f"Jump: {pygame.key.name(self.p2c.jump)}",
            f"Shoot: {pygame.key.name(self.p2c.shoot)}",
        ]

        self.draw_panel(screen, left_panel, "PLAYER 1 RED", p1_lines, (220, 70, 70))
        self.draw_panel(screen, right_panel, "PLAYER 2 GREEN", p2_lines, (70, 210, 140))

        help_text = self.font.render("R reset    Esc quit", True, (200, 200, 210))
        screen.blit(help_text, (16, self.h - 28))

        if self.won:
            win = pygame.font.SysFont(None, 56).render("YOU WIN", True, (255, 255, 255))
            screen.blit(win, (self.w // 2 - win.get_width() // 2, self.h // 2 - 40))
            msg = self.font.render("Press R to play again", True, (235, 235, 240))
            screen.blit(msg, (self.w // 2 - msg.get_width() // 2, self.h // 2 + 10))
