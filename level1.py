import pygame
import math


def draw_offwhite_background(surface):
    surface.fill((245, 242, 235))


def draw_solid_runner(surface, rect, color, t, vx):
    cx = rect.centerx
    head_r = 10
    thickness = 7

    head_cy = rect.y + head_r + 2
    body_top_y = head_cy + head_r + 2
    hip_y = rect.bottom - 18

    speed = min(1.0, abs(vx) / 260.0)
    swing = math.sin(t * (10.0 + 6.0 * speed)) * (10 + 6 * speed)

    pygame.draw.circle(surface, color, (cx, head_cy), head_r)

    pygame.draw.line(surface, color, (cx, body_top_y), (cx, hip_y), thickness)

    shoulder_y = body_top_y + 12
    arm_len = 18
    a1 = int(swing * 0.6)
    pygame.draw.line(surface, color, (cx, shoulder_y), (cx - arm_len, shoulder_y + a1), thickness)
    pygame.draw.line(surface, color, (cx, shoulder_y), (cx + arm_len, shoulder_y - a1), thickness)

    leg_len = 22
    l1 = int(swing)
    l2 = -int(swing)
    pygame.draw.line(surface, color, (cx - 6, hip_y), (cx - 10, hip_y + leg_len + l1 // 3), thickness)
    pygame.draw.line(surface, color, (cx + 6, hip_y), (cx + 10, hip_y + leg_len + l2 // 3), thickness)


def draw_key_icon(surface, rect):
    x, y, w, h = rect
    cx = x + w // 3
    cy = y + h // 2
    r = max(4, min(w, h) // 4)

    pygame.draw.circle(surface, (235, 215, 90), (cx, cy), r, 0)
    shaft = pygame.Rect(cx + r - 1, cy - 3, w - (cx - x) - r - 2, 6)
    pygame.draw.rect(surface, (235, 215, 90), shaft)
    pygame.draw.rect(surface, (235, 215, 90), pygame.Rect(shaft.right - 10, cy + 3, 4, 8))
    pygame.draw.rect(surface, (235, 215, 90), pygame.Rect(shaft.right - 18, cy + 3, 4, 8))


def draw_gun_icon(surface, rect):
    x, y, w, h = rect
    body = pygame.Rect(x + 2, y + 6, w - 4, h - 14)
    grip = pygame.Rect(x + w // 2, y + h // 2, w // 3, h // 2 - 2)
    barrel = pygame.Rect(x + w - 8, y + 8, 8, 6)

    pygame.draw.rect(surface, (55, 55, 60), body, border_radius=3)
    pygame.draw.rect(surface, (45, 45, 52), grip, border_radius=3)
    pygame.draw.rect(surface, (70, 70, 80), barrel, border_radius=2)


class Player:
    def __init__(self, x, y, color, controls):
        self.rect = pygame.Rect(x, y, 26, 58)
        self.color = color
        self.controls = controls

        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.coyote = 0.0

    def handle_input(self, keys):
        speed = 260.0
        self.vx = 0.0
        if keys[self.controls.left]:
            self.vx -= speed
        if keys[self.controls.right]:
            self.vx += speed

        if keys[self.controls.jump] and (self.on_ground or self.coyote > 0.0):
            self.vy = -560.0
            self.on_ground = False
            self.coyote = 0.0

    def physics(self, dt, solids):
        gravity = 1050.0
        self.vy += gravity * dt

        dx = int(self.vx * dt)
        dy = int(self.vy * dt)

        self.rect.x += dx
        for s in solids:
            if self.rect.colliderect(s):
                if dx > 0:
                    self.rect.right = s.left
                elif dx < 0:
                    self.rect.left = s.right

        self.rect.y += dy
        self.on_ground = False
        for s in solids:
            if self.rect.colliderect(s):
                if dy > 0:
                    self.rect.bottom = s.top
                    self.vy = 0.0
                    self.on_ground = True
                elif dy < 0:
                    self.rect.top = s.bottom
                    self.vy = 0.0

        if self.on_ground:
            self.coyote = 0.10
        else:
            self.coyote = max(0.0, self.coyote - dt)


class Level1:
    def __init__(self, width, height, p1_controls, p2_controls):
        self.w = width
        self.h = height
        self.p1_controls = p1_controls
        self.p2_controls = p2_controls

        pygame.font.init()
        self.font_title = pygame.font.SysFont("Arial", 44, bold=True)
        self.font_ui = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)

        self.colors = {
            "border": (45, 45, 55),
            "muted": (70, 70, 85),
            "red": (220, 70, 70),
            "green": (70, 210, 140),
            "yellow": (210, 190, 80),
            "chip_dark": (140, 140, 150),
            "chip_green": (120, 220, 160),
            "chip_yellow": (220, 205, 110),
        }

        self.level_title = "LEVEL 1"
        self.objective = "Objective: GREEN get key"

        self.margin = 24
        self.top_h = 84
        self.top_bar = pygame.Rect(self.margin, self.margin, self.w - self.margin * 2, self.top_h)

        self._wood_cache = {}

        self.base_solids, self.platforms = self._build_level_solids()

        self.cage = pygame.Rect(36, self.h - 290, 260, 240)
        self.cage_open = False
        self.cage_solids = self._build_cage_solids(self.cage)

        self.key_rect = pygame.Rect(560, self.h - 280, 40, 24)
        self.key_taken = False
        self.key_drop_box_visible = False
        self.key_dropped = False

        self.key_drop_box = pygame.Rect(self.cage.right + 14, self.cage.bottom - 86, 70, 70)

        self.gun_spawned = False
        self.gun_taken = False
        self.gun_rect = pygame.Rect(self.cage.right + 105, self.cage.bottom - 68, 44, 28)

        self.gate_spawned = False
        self.gate_rect = pygame.Rect(self.w - 160, self.h - 240, 120, 220)

        self.p1 = Player(self.cage.x + 50, self.cage.bottom - 82, self.colors["red"], p1_controls)
        self.p2 = Player(420, self.h - 90, self.colors["green"], p2_controls)

        self.time_in_level = 0.0

    def _build_level_solids(self):
        solids = []
        plats = []

        solids.append(pygame.Rect(0, 0, self.w, 18))
        solids.append(pygame.Rect(0, self.h - 18, self.w, 18))
        solids.append(pygame.Rect(0, 0, 18, self.h))
        solids.append(pygame.Rect(self.w - 18, 0, 18, self.h))

        p0 = pygame.Rect(60, self.h - 60, 820, 18)
        p1 = pygame.Rect(240, self.h - 150, 320, 18)
        p2 = pygame.Rect(520, self.h - 260, 480, 18)

        plats.extend([p0, p1, p2])
        solids.extend(plats)

        return solids, plats

    def _build_cage_solids(self, cage_rect):
        x, y, w, h = cage_rect
        thick = 18
        return {
            "left": pygame.Rect(x, y, thick, h),
            "top": pygame.Rect(x, y, w, thick),
            "bottom": pygame.Rect(x, y + h - thick, w, thick),
            "door": pygame.Rect(x + w - thick, y, thick, h),
        }

    def update(self, dt, events):
        self.time_in_level += dt

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return "quit"
                if e.key == pygame.K_r:
                    return "reset"

        keys = pygame.key.get_pressed()

        self.p1.handle_input(keys)
        self.p2.handle_input(keys)

        solids = list(self.base_solids)
        solids.extend([self.cage_solids["left"], self.cage_solids["top"], self.cage_solids["bottom"]])
        if not self.cage_open:
            solids.append(self.cage_solids["door"])

        self.p1.physics(dt, solids)
        self.p2.physics(dt, solids)

        action_pressed_green = any(
            e.type == pygame.KEYDOWN and e.key == self.p2_controls.shoot
            for e in events
        )

        # 1) GREEN gets key
        if not self.key_taken and self.p2.rect.colliderect(self.key_rect):
            self.key_taken = True
            self.key_drop_box_visible = True
            self.objective = "Objective: Bring key to drop box and press action"

        # 2) Drop key into box (near cage) to open cage
        if self.key_taken and (not self.key_dropped) and self.key_drop_box_visible:
            if self.p2.rect.colliderect(self.key_drop_box) and action_pressed_green:
                self.key_dropped = True
                self.key_drop_box_visible = False
                self.cage_open = True

                self.gun_spawned = True
                self.objective = "Objective: RED grab the gun"

        # 3) Only RED can pick up gun
        if self.gun_spawned and (not self.gun_taken):
            if self.p1.rect.colliderect(self.gun_rect):
                self.gun_taken = True
                self.gate_spawned = True
                self.objective = "Objective: Gate appeared. Both go to gate"

        # 4) Win only after gate appears
        if self.gate_spawned:
            if self.p1.rect.colliderect(self.gate_rect) and self.p2.rect.colliderect(self.gate_rect):
                return "next_level"

        return None

    def draw(self, screen):
        draw_offwhite_background(screen)
        self._draw_world(screen)
        self._draw_ui(screen)

    def _wood_surface(self, w, h):
        key = (w, h)
        if key in self._wood_cache:
            return self._wood_cache[key]

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        base = (145, 110, 78)
        surf.fill(base)

        plank_h = max(10, h // 2)
        y = 0
        toggle = 0
        while y < h:
            shade = 12 if toggle % 2 == 0 else -6
            r = max(0, min(255, base[0] + shade))
            g = max(0, min(255, base[1] + shade))
            b = max(0, min(255, base[2] + shade))
            pygame.draw.rect(surf, (r, g, b), pygame.Rect(0, y, w, plank_h))
            pygame.draw.line(surf, (110, 80, 52), (0, y), (w, y), 2)
            y += plank_h
            toggle += 1

        for x in range(0, w, 7):
            drift = int(math.sin(x * 0.22) * 2)
            pygame.draw.line(surf, (170, 135, 95), (x, 0 + drift), (x, h + drift), 1)

        pygame.draw.rect(surf, (95, 70, 45), pygame.Rect(0, 0, w, h), 2)

        self._wood_cache[key] = surf
        return surf

    def _draw_wood_platform(self, screen, rect):
        wood = self._wood_surface(rect.w, rect.h)
        screen.blit(wood, (rect.x, rect.y))

        shadow = pygame.Surface((rect.w, 6), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 35))
        screen.blit(shadow, (rect.x, rect.y + rect.h))

    def _draw_world(self, screen):
        for s in self.platforms:
            self._draw_wood_platform(screen, s)

        # Cage
        x, y, w, h = self.cage
        cage_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(cage_surf, (235, 232, 225, 255), pygame.Rect(0, 0, w, h), border_radius=18)
        pygame.draw.rect(cage_surf, self.colors["border"], pygame.Rect(0, 0, w, h), 3, border_radius=18)
        door_alpha = 60 if self.cage_open else 255
        pygame.draw.rect(
            cage_surf,
            (*self.colors["border"], door_alpha),
            pygame.Rect(w - 18, 0, 18, h),
            border_radius=6,
        )
        screen.blit(cage_surf, (x, y))

        # Key
        if not self.key_taken:
            pygame.draw.ellipse(screen, (0, 0, 0), self.key_rect.inflate(42, 26))
            draw_key_icon(screen, self.key_rect)

        # Key drop box appears near cage after green has key
        if self.key_drop_box_visible and (not self.key_dropped):
            pygame.draw.rect(screen, (220, 210, 175), self.key_drop_box, border_radius=14)
            pygame.draw.rect(screen, self.colors["border"], self.key_drop_box, 3, border_radius=14)
            label = self.font_small.render("DROP", True, self.colors["border"])
            screen.blit(label, (self.key_drop_box.centerx - label.get_width() // 2, self.key_drop_box.y + 10))
            krect = pygame.Rect(self.key_drop_box.centerx - 18, self.key_drop_box.y + 34, 36, 20)
            draw_key_icon(screen, krect)

        # Gun appears only after key is dropped, and only red can pick
        if self.gun_spawned and (not self.gun_taken):
            pygame.draw.ellipse(screen, (0, 0, 0), self.gun_rect.inflate(46, 28))
            draw_gun_icon(screen, self.gun_rect)

        # Gate appears only after red grabs gun
        if self.gate_spawned:
            pygame.draw.rect(screen, (220, 210, 175), self.gate_rect, border_radius=18)
            pygame.draw.rect(screen, self.colors["border"], self.gate_rect, 3, border_radius=18)

        # Players with leg animation
        draw_solid_runner(screen, self.p1.rect, self.colors["red"], self.time_in_level, self.p1.vx)
        draw_solid_runner(screen, self.p2.rect, self.colors["green"], self.time_in_level, self.p2.vx)

        # Float key above green while carrying (before drop)
        if self.key_taken and (not self.key_dropped):
            float_rect = pygame.Rect(self.p2.rect.centerx + 10, self.p2.rect.y - 14, 32, 20)
            draw_key_icon(screen, float_rect)

    def _draw_ui(self, screen):
        self._panel(screen, self.top_bar, radius=18, alpha=230)
        self._draw_top_bar_content(screen)

        hint = "R reset   Esc quit   GREEN action is your shoot key (press to drop key)"
        hint_s = self.font_small.render(hint, True, self.colors["muted"])
        screen.blit(hint_s, (self.margin, self.h - 28))

    def _panel(self, screen, rect, radius, alpha):
        surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (255, 255, 255, alpha), pygame.Rect(0, 0, rect.w, rect.h), border_radius=radius)
        pygame.draw.rect(surf, self.colors["border"], pygame.Rect(0, 0, rect.w, rect.h), 2, border_radius=radius)
        screen.blit(surf, (rect.x, rect.y))

    def _draw_top_bar_content(self, screen):
        pad_x = 22
        center_y = self.top_bar.y + self.top_bar.h // 2

        title = self.font_title.render(self.level_title, True, self.colors["border"])
        screen.blit(title, (self.top_bar.x + pad_x, center_y - title.get_height() // 2))

        obj = self.font_ui.render(self.objective, True, self.colors["border"])
        screen.blit(obj, (self.top_bar.centerx - obj.get_width() // 2, center_y - obj.get_height() // 2 + 2))


    def _draw_chips_right(self, screen, bar_rect, chips):
        chip_h = 34
        gap = 10
        pad = 14

        x = bar_rect.right - pad
        y = bar_rect.centery - chip_h // 2

        for label, value, style in reversed(chips):
            text = f"{label}: {value}"
            s = self.font_small.render(text, True, (25, 25, 30))

            w = s.get_width() + 22
            x -= w

            if style == "green":
                bg = self.colors["chip_green"]
            elif style == "yellow":
                bg = self.colors["chip_yellow"]
            else:
                bg = self.colors["chip_dark"]

            r = pygame.Rect(x, y, w, chip_h)
            pygame.draw.rect(screen, bg, r, border_radius=999)
            pygame.draw.rect(screen, self.colors["border"], r, 2, border_radius=999)

            screen.blit(s, (r.x + 11, r.y + (chip_h - s.get_height()) // 2))
            x -= gap
