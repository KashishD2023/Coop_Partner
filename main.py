import sys
import math
import pygame

import level1
import level2

pygame.init()

WINDOW_W = 1200
WINDOW_H = 600
HALF_W = WINDOW_W // 2
HALF_H = WINDOW_H

FPS = 60

WORLD_BG = (18, 20, 26)
WALL_COLOR = (90, 95, 110)
GRID_COLOR = (30, 34, 44)

SHOOTER_COLOR = (70, 170, 255)
RUNNER_COLOR = (255, 140, 80)
BULLET_COLOR = (245, 245, 245)

KEY_COLOR = (255, 220, 70)
DOOR_CLOSED = (170, 60, 70)
DOOR_OPEN = (70, 180, 90)

TEXT_COLOR = (235, 235, 240)

MINIMAP_BG = (10, 12, 16)
MINIMAP_BORDER = (220, 220, 230)
MINIMAP_WALL = (70, 74, 90)
MINIMAP_DOOR = (120, 230, 150)

ARROW_BG = (0, 0, 0)
ARROW_COLOR = (255, 220, 70)

PLAYER_SIZE = 34
PLAYER_SPEED = 280.0
RUNNER_SPEED = 300.0
RUNNER_SPRINT_SPEED = 420.0

BULLET_SPEED = 720.0
BULLET_RADIUS = 5
BULLET_COOLDOWN = 0.22

HIT_RESPAWN_TIME = 0.70


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def vec_len(x, y):
    return math.sqrt(x * x + y * y)


def norm(x, y):
    l = vec_len(x, y)
    if l <= 1e-6:
        return 0.0, 0.0
    return x / l, y / l


def move_and_collide(rect, vx, vy, walls):
    rect.x += int(vx)
    for w in walls:
        if rect.colliderect(w):
            if vx > 0:
                rect.right = w.left
            elif vx < 0:
                rect.left = w.right

    rect.y += int(vy)
    for w in walls:
        if rect.colliderect(w):
            if vy > 0:
                rect.bottom = w.top
            elif vy < 0:
                rect.top = w.bottom
    return rect


class Player:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(int(x), int(y), PLAYER_SIZE, PLAYER_SIZE)
        self.color = color
        self.facing = (1.0, 0.0)
        self.has_key = False
        self.dead_timer = 0.0

    @property
    def center(self):
        return self.rect.centerx, self.rect.centery

    def respawn(self, pos):
        self.rect.x = int(pos[0])
        self.rect.y = int(pos[1])
        self.dead_timer = HIT_RESPAWN_TIME


class Bullet:
    def __init__(self, x, y, vx, vy):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.r = BULLET_RADIUS
        self.alive = True

    def rect(self):
        return pygame.Rect(int(self.x - self.r), int(self.y - self.r), self.r * 2, self.r * 2)

    def update(self, dt, walls, world_rect):
        if not self.alive:
            return
        self.x += self.vx * dt
        self.y += self.vy * dt

        r = self.rect()
        if not world_rect.colliderect(r):
            self.alive = False
            return

        for w in walls:
            if r.colliderect(w):
                self.alive = False
                return


class GameState:
    def __init__(self):
        self.level_index = 1
        self.load_level(self.level_index)

    def load_level(self, idx):
        if idx == 2:
            data = level2.build()
            self.level_index = 2
        else:
            data = level1.build()
            self.level_index = 1

        self.world_w = data["world_size"][0]
        self.world_h = data["world_size"][1]
        self.world_rect = pygame.Rect(0, 0, self.world_w, self.world_h)

        self.walls = data["walls"]
        self.key_rect = data["key_rect"].copy()
        self.door_rect = data["door_rect"].copy()
        self.runner_spawn = data["runner_spawn"]
        self.shooter_spawn = data["shooter_spawn"]

        self.door_open = False
        self.runner_won = False
        self.runner_win_timer = 0.0

        self.shooter = Player(self.shooter_spawn[0], self.shooter_spawn[1], SHOOTER_COLOR)
        self.runner = Player(self.runner_spawn[0], self.runner_spawn[1], RUNNER_COLOR)

        self.bullets = []
        self.shooter_shot_cd = 0.0
        self.runner_hits = 0

    def drop_key_if_needed(self):
        if self.runner.has_key:
            self.runner.has_key = False
            self.key_rect.x = int(self.runner.rect.centerx - self.key_rect.w // 2)
            self.key_rect.y = int(self.runner.rect.centery - self.key_rect.h // 2)
            self.key_rect.x = clamp(self.key_rect.x, 0, self.world_w - self.key_rect.w)
            self.key_rect.y = clamp(self.key_rect.y, 0, self.world_h - self.key_rect.h)


def draw_grid(surface, cam_x, cam_y, view_w, view_h):
    step = 80
    start_x = int((cam_x // step) * step)
    start_y = int((cam_y // step) * step)

    for x in range(start_x, int(cam_x + view_w) + step, step):
        sx = int(x - cam_x)
        pygame.draw.line(surface, GRID_COLOR, (sx, 0), (sx, view_h), 1)

    for y in range(start_y, int(cam_y + view_h) + step, step):
        sy = int(y - cam_y)
        pygame.draw.line(surface, GRID_COLOR, (0, sy), (view_w, sy), 1)


def world_to_screen_rect(r, cam_x, cam_y):
    return pygame.Rect(r.x - int(cam_x), r.y - int(cam_y), r.w, r.h)


def compute_camera_centered(player_rect, world_w, world_h, view_w, view_h):
    cx = player_rect.centerx - view_w / 2
    cy = player_rect.centery - view_h / 2
    cx = clamp(cx, 0, world_w - view_w)
    cy = clamp(cy, 0, world_h - view_h)
    return cx, cy


def draw_minimap(view_surface, gs, cam_x, cam_y, view_w, view_h, show_door_for_runner):
    mm_w = 210
    mm_h = 150
    pad = 10

    mm_x = view_w - mm_w - pad
    mm_y = 36

    mm_rect = pygame.Rect(mm_x, mm_y, mm_w, mm_h)
    pygame.draw.rect(view_surface, MINIMAP_BG, mm_rect, 0)
    pygame.draw.rect(view_surface, MINIMAP_BORDER, mm_rect, 2)

    scale_x = (mm_w - 8) / gs.world_w
    scale_y = (mm_h - 8) / gs.world_h
    off_x = mm_x + 4
    off_y = mm_y + 4

    def w2m(px, py):
        return int(off_x + px * scale_x), int(off_y + py * scale_y)

    for w in gs.walls:
        x1, y1 = w2m(w.x, w.y)
        x2, y2 = w2m(w.x + w.w, w.y + w.h)
        rr = pygame.Rect(x1, y1, max(1, x2 - x1), max(1, y2 - y1))
        pygame.draw.rect(view_surface, MINIMAP_WALL, rr, 0)

    if show_door_for_runner:
        x1, y1 = w2m(gs.door_rect.x, gs.door_rect.y)
        x2, y2 = w2m(gs.door_rect.x + gs.door_rect.w, gs.door_rect.y + gs.door_rect.h)
        rr = pygame.Rect(x1, y1, max(2, x2 - x1), max(2, y2 - y1))
        pygame.draw.rect(view_surface, MINIMAP_DOOR, rr, 0)

    sx, sy = gs.shooter.center
    rx, ry = gs.runner.center

    msx, msy = w2m(sx, sy)
    mrx, mry = w2m(rx, ry)

    pygame.draw.circle(view_surface, RUNNER_COLOR, (msx, msy), 5)
    pygame.draw.circle(view_surface, SHOOTER_COLOR, (mrx, mry), 5)

    cam_cx = cam_x + view_w / 2
    cam_cy = cam_y + view_h / 2
    mcx, mcy = w2m(cam_cx, cam_cy)

    cam_box_w = int(view_w * scale_x)
    cam_box_h = int(view_h * scale_y)
    cam_box = pygame.Rect(mcx - cam_box_w // 2, mcy - cam_box_h // 2, cam_box_w, cam_box_h)
    pygame.draw.rect(view_surface, (200, 200, 210), cam_box, 1)


def draw_arrow_to_target_top(view_surface, from_pos, target_pos, view_w):
    fx, fy = from_pos
    tx, ty = target_pos
    dx = tx - fx
    dy = ty - fy
    if abs(dx) < 1e-3 and abs(dy) < 1e-3:
        return

    ang = math.atan2(dy, dx)

    cx = int(view_w * 0.5)
    cy = 44

    size = 18
    tip = (cx + math.cos(ang) * size, cy + math.sin(ang) * size)
    left = (cx + math.cos(ang + 2.5) * size * 0.85, cy + math.sin(ang + 2.5) * size * 0.85)
    right = (cx + math.cos(ang - 2.5) * size * 0.85, cy + math.sin(ang - 2.5) * size * 0.85)

    back = (cx - math.cos(ang) * size * 0.55, cy - math.sin(ang) * size * 0.55)
    poly = [(int(tip[0]), int(tip[1])), (int(left[0]), int(left[1])), (int(back[0]), int(back[1])), (int(right[0]), int(right[1]))]

    bg_rect = pygame.Rect(cx - 46, cy - 18, 92, 30)
    pygame.draw.rect(view_surface, ARROW_BG, bg_rect, 0)
    pygame.draw.rect(view_surface, (40, 40, 45), bg_rect, 1)

    pygame.draw.polygon(view_surface, ARROW_COLOR, poly, 0)
    pygame.draw.polygon(view_surface, (20, 20, 20), poly, 2)


def draw_world_to_view(surface, gs, cam_x, cam_y, view_w, view_h, font, title_text, is_runner_view):
    surface.fill(WORLD_BG)
    draw_grid(surface, cam_x, cam_y, view_w, view_h)

    for w in gs.walls:
        sr = world_to_screen_rect(w, cam_x, cam_y)
        if sr.colliderect(pygame.Rect(0, 0, view_w, view_h)):
            pygame.draw.rect(surface, WALL_COLOR, sr)

    if not gs.door_open:
        pygame.draw.rect(surface, DOOR_CLOSED, world_to_screen_rect(gs.door_rect, cam_x, cam_y))
    else:
        pygame.draw.rect(surface, DOOR_OPEN, world_to_screen_rect(gs.door_rect, cam_x, cam_y))

    if not gs.runner.has_key and not gs.door_open:
        pygame.draw.rect(surface, KEY_COLOR, world_to_screen_rect(gs.key_rect, cam_x, cam_y))

    for b in gs.bullets:
        if not b.alive:
            continue
        bx = int(b.x - cam_x)
        by = int(b.y - cam_y)
        if 0 <= bx < view_w and 0 <= by < view_h:
            pygame.draw.circle(surface, BULLET_COLOR, (bx, by), b.r)

    pygame.draw.rect(surface, gs.shooter.color, world_to_screen_rect(gs.shooter.rect, cam_x, cam_y))
    pygame.draw.rect(surface, gs.runner.color, world_to_screen_rect(gs.runner.rect, cam_x, cam_y))

    pygame.draw.rect(surface, (0, 0, 0), pygame.Rect(0, 0, view_w, 28))
    label = font.render(title_text, True, TEXT_COLOR)
    surface.blit(label, (8, 5))

    show_door = bool(is_runner_view and gs.runner.has_key and not gs.door_open)
    draw_minimap(surface, gs, cam_x, cam_y, view_w, view_h, show_door)

    if is_runner_view and (not gs.runner.has_key) and (not gs.door_open):
        kcx = gs.key_rect.centerx
        kcy = gs.key_rect.centery
        draw_arrow_to_target_top(surface, gs.runner.center, (kcx, kcy), view_w)

def handle_level_switch(gs, key):
    if key == pygame.K_1:
        gs.load_level(1)
    if key == pygame.K_2:
        gs.load_level(2)


def main():
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("coop_partner")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 18)
    big_font = pygame.font.SysFont("arial", 34)

    gs = GameState()

    left_view = pygame.Surface((HALF_W, HALF_H))
    right_view = pygame.Surface((HALF_W, HALF_H))

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                handle_level_switch(gs, event.key)

        keys = pygame.key.get_pressed()

        if gs.shooter.dead_timer > 0:
            gs.shooter.dead_timer -= dt
        if gs.runner.dead_timer > 0:
            gs.runner.dead_timer -= dt

        if gs.runner_won:
            gs.runner_win_timer += dt
            if gs.runner_win_timer > 1.6:
                gs.load_level(gs.level_index)

        if not gs.runner_won:
            shooter_ax = 0.0
            shooter_ay = 0.0
            if keys[pygame.K_a]:
                shooter_ax -= 1.0
            if keys[pygame.K_d]:
                shooter_ax += 1.0
            if keys[pygame.K_w]:
                shooter_ay -= 1.0
            if keys[pygame.K_s]:
                shooter_ay += 1.0
            shooter_dir = norm(shooter_ax, shooter_ay)

            aim_x = 0.0
            aim_y = 0.0
            if keys[pygame.K_j]:
                aim_x -= 1.0
            if keys[pygame.K_l]:
                aim_x += 1.0
            if keys[pygame.K_i]:
                aim_y -= 1.0
            if keys[pygame.K_k]:
                aim_y += 1.0
            aim_dir = norm(aim_x, aim_y)
            if aim_dir != (0.0, 0.0):
                gs.shooter.facing = aim_dir
            elif shooter_dir != (0.0, 0.0):
                gs.shooter.facing = shooter_dir

            if gs.shooter.dead_timer <= 0:
                gs.shooter.rect = move_and_collide(
                    gs.shooter.rect,
                    shooter_dir[0] * PLAYER_SPEED * dt,
                    shooter_dir[1] * PLAYER_SPEED * dt,
                    gs.walls,
                )

            runner_ax = 0.0
            runner_ay = 0.0
            if keys[pygame.K_LEFT]:
                runner_ax -= 1.0
            if keys[pygame.K_RIGHT]:
                runner_ax += 1.0
            if keys[pygame.K_UP]:
                runner_ay -= 1.0
            if keys[pygame.K_DOWN]:
                runner_ay += 1.0
            runner_dir = norm(runner_ax, runner_ay)

            runner_speed = RUNNER_SPRINT_SPEED if (keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]) else RUNNER_SPEED
            if runner_dir != (0.0, 0.0):
                gs.runner.facing = runner_dir

            if gs.runner.dead_timer <= 0:
                gs.runner.rect = move_and_collide(
                    gs.runner.rect,
                    runner_dir[0] * runner_speed * dt,
                    runner_dir[1] * runner_speed * dt,
                    gs.walls,
                )

            if not gs.runner.has_key and not gs.door_open:
                if gs.runner.rect.colliderect(gs.key_rect):
                    if keys[pygame.K_RETURN]:
                        gs.runner.has_key = True

            if not gs.door_open and gs.runner.has_key:
                if gs.runner.rect.colliderect(gs.door_rect):
                    gs.door_open = True
                    gs.runner_won = True
                    gs.runner_win_timer = 0.0

            if gs.shooter_shot_cd > 0:
                gs.shooter_shot_cd -= dt

            if keys[pygame.K_SPACE] and gs.shooter_shot_cd <= 0 and gs.shooter.dead_timer <= 0:
                dx, dy = gs.shooter.facing
                if dx == 0.0 and dy == 0.0:
                    dx, dy = 1.0, 0.0
                sx, sy = gs.shooter.center
                bx = sx + dx * (PLAYER_SIZE * 0.6)
                by = sy + dy * (PLAYER_SIZE * 0.6)
                gs.bullets.append(Bullet(bx, by, dx * BULLET_SPEED, dy * BULLET_SPEED))
                gs.shooter_shot_cd = BULLET_COOLDOWN

            for b in gs.bullets:
                b.update(dt, gs.walls, gs.world_rect)

            if gs.runner.dead_timer <= 0:
                for b in gs.bullets:
                    if not b.alive:
                        continue
                    if b.rect().colliderect(gs.runner.rect):
                        b.alive = False
                        gs.runner_hits += 1
                        gs.drop_key_if_needed()
                        gs.runner.respawn(gs.runner_spawn)
                        break

            gs.bullets = [b for b in gs.bullets if b.alive]

        cam_lx, cam_ly = compute_camera_centered(gs.shooter.rect, gs.world_w, gs.world_h, HALF_W, HALF_H)
        cam_rx, cam_ry = compute_camera_centered(gs.runner.rect, gs.world_w, gs.world_h, HALF_W, HALF_H)

        draw_world_to_view(
            left_view,
            gs,
            cam_lx,
            cam_ly,
            HALF_W,
            HALF_H,
            font,
            "Shooter   move WASD   shoot SPACE",
            False,
        )
        draw_world_to_view(
            right_view,
            gs,
            cam_rx,
            cam_ry,
            HALF_W,
            HALF_H,
            font,
            "Runner   move ARROWS   pick key ENTER",
            True,
        )

        screen.blit(left_view, (0, 0))
        screen.blit(right_view, (HALF_W, 0))

        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(HALF_W - 2, 0, 4, WINDOW_H))

        hud = (
            f"Level {gs.level_index}   Runner has key: {'YES' if gs.runner.has_key else 'NO'}   "
            f"Door open: {'YES' if gs.door_open else 'NO'}   Runner hits: {gs.runner_hits}   "
            f"Press 1 or 2 to switch level"
        )
        hud_s = font.render(hud, True, TEXT_COLOR)
        screen.blit(hud_s, (10, WINDOW_H - 26))

        if gs.runner_won:
            s = big_font.render("RUNNER WINS", True, (255, 255, 255))
            screen.blit(s, (WINDOW_W // 2 - s.get_width() // 2, 16))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()