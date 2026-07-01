import pygame
import random
import math
import json
import os
import sys

# =============================================================================
# 初始化
# =============================================================================
pygame.init()
pygame.mixer.init()

W, H = 480, 700
FPS = 60
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("飞翔小鸟")
clock = pygame.time.Clock()

# =============================================================================
# 颜色定义
# =============================================================================
SKY_TOP = (15, 5, 36)
SKY_MID = (75, 25, 70)
SKY_BOT = (196, 75, 45)
GROUND_COL = (45, 27, 14)
GROUND_LIGHT = (92, 58, 30)
GRASS_COL = (80, 160, 50)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)

BIRD_YELLOW = (255, 193, 7)
BIRD_LIGHT = (255, 224, 130)
BIRD_ORANGE = (255, 143, 0)
BIRD_DARK = (230, 81, 0)
BIRD_BEAK = (191, 54, 12)

PIPE_GREEN = (46, 125, 50)
PIPE_LIGHT = (67, 160, 71)
PIPE_DARK = (27, 94, 32)
PIPE_CAP = (76, 175, 80)

WORM_PINK = (255, 107, 157)
WORM_LIGHT = (255, 133, 168)
WORM_ANTENNA = (255, 171, 64)

CLOUD_COLOR = (255, 220, 200)
STAR_COLOR = (255, 255, 230)

# =============================================================================
# 字体
# =============================================================================
try:
    font_title = pygame.font.SysFont("simhei", 52, bold=True)
    font_score = pygame.font.SysFont("simhei", 60, bold=True)
    font_medium = pygame.font.SysFont("simhei", 28, bold=True)
    font_small = pygame.font.SysFont("simhei", 18)
    font_tiny = pygame.font.SysFont("simhei", 14)
except:
    font_title = pygame.font.Font(None, 52)
    font_score = pygame.font.Font(None, 60)
    font_medium = pygame.font.Font(None, 28)
    font_small = pygame.font.Font(None, 18)
    font_tiny = pygame.font.Font(None, 14)

# =============================================================================
# 常量
# =============================================================================
GRAVITY = 0.48
FLAP_FORCE = -8.0
BIRD_X = 90
BIRD_RADIUS = 15
PIPE_WIDTH = 62
PIPE_GAP = 160
PIPE_SPEED = 2.8
PIPE_SPAWN_MS = 1500
GROUND_H = 80
WORM_RADIUS = 11
WORM_BONUS = 50
GROUND_Y = H - GROUND_H

# =============================================================================
# 本地最高分
# =============================================================================
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flappy_save.json")


def load_high():
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            return data.get("high", 0)
    except:
        return 0


def save_high(v):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump({"high": v}, f)
    except:
        pass


# =============================================================================
# 工具函数
# =============================================================================
def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def draw_ellipse_aa(surf, color, cx, cy, rx, ry, width=0):
    """抗锯齿椭圆"""
    rect = pygame.Rect(int(cx - rx), int(cy - ry), int(rx * 2), int(ry * 2))
    pygame.draw.ellipse(surf, color, rect, width)


def draw_circle_aa(surf, color, cx, cy, r, width=0):
    pygame.draw.circle(surf, color, (int(cx), int(cy)), int(r), width)


# =============================================================================
# 粒子系统
# =============================================================================
class Particle:
    def __init__(self, x, y, color, speed=None, size=None, life=1.0):
        angle = random.uniform(0, math.pi * 2)
        spd = speed or random.uniform(1, 4)
        self.x, self.y = x, y
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd - 2
        self.size = size or random.uniform(2, 5)
        self.color = color
        self.life = life
        self.max_life = life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12
        self.life -= 0.025
        return self.life > 0

    def draw(self, surf):
        alpha = max(0, self.life / self.max_life)
        s = max(1, int(self.size * alpha))
        col = tuple(min(255, int(c * alpha + 50 * (1 - alpha))) for c in self.color)
        draw_circle_aa(surf, col, self.x, self.y, s)


# =============================================================================
# 小鸟类
# =============================================================================
class Bird:
    def __init__(self):
        self.x = BIRD_X
        self.y = H // 2 - 40
        self.vy = 0.0
        self.rotation = 0.0
        self.flap_anim = 0.0

    def flap(self):
        self.vy = FLAP_FORCE
        self.flap_anim = 0

    def update(self):
        self.vy += GRAVITY
        self.y += self.vy
        self.flap_anim += 0.45
        target = max(-0.5, min(1.2, self.vy * 0.06))
        self.rotation += (target - self.rotation) * 0.15

    def get_rect(self):
        return pygame.Rect(
            self.x - BIRD_RADIUS + 3,
            self.y - BIRD_RADIUS + 3,
            BIRD_RADIUS * 2 - 6,
            BIRD_RADIUS * 2 - 6,
        )

    def draw(self, surf):
        # 创建一个临时surface来旋转
        size = 48
        tmp = pygame.Surface((size, size), pygame.SRCALPHA)

        cx, cy = size // 2, size // 2

        # 身体
        draw_ellipse_aa(tmp, BIRD_ORANGE, cx, cy, BIRD_RADIUS + 2, BIRD_RADIUS - 1)
        draw_ellipse_aa(tmp, BIRD_YELLOW, cx, cy - 1, BIRD_RADIUS + 1, BIRD_RADIUS - 2)

        # 翅膀
        wing_off = math.sin(self.flap_anim) * 6
        draw_ellipse_aa(tmp, BIRD_DARK, cx - 5, cy + 2 + wing_off, 10, 5)
        draw_ellipse_aa(tmp, BIRD_ORANGE, cx - 4, cy + 1 + wing_off, 8, 4)

        # 眼睛白
        draw_circle_aa(tmp, WHITE, cx + 7, cy - 4, 6)
        # 瞳孔
        draw_circle_aa(tmp, BLACK, cx + 9, cy - 4, 3)
        # 高光
        draw_circle_aa(tmp, WHITE, cx + 10, cy - 5, 1)

        # 嘴
        beak_pts = [(cx + 13, cy - 1), (cx + 22, cy + 1), (cx + 13, cy + 4)]
        pygame.draw.polygon(tmp, BIRD_DARK, beak_pts)
        beak_pts2 = [(cx + 13, cy + 1), (cx + 22, cy + 1), (cx + 13, cy + 4)]
        pygame.draw.polygon(tmp, BIRD_BEAK, beak_pts2)

        # 旋转
        angle = -self.rotation * 57.2958
        rotated = pygame.transform.rotate(tmp, angle)
        rect = rotated.get_rect(center=(self.x, self.y))
        surf.blit(rotated, rect)


# =============================================================================
# 管道类
# =============================================================================
class Pipe:
    def __init__(self):
        self.x = W + 20
        self.gap_y = random.randint(120, GROUND_Y - 120)
        self.scored = False

    def update(self):
        self.x -= PIPE_SPEED

    def off_screen(self):
        return self.x < -PIPE_WIDTH - 10

    def collides(self, bird_rect):
        top_h = self.gap_y - PIPE_GAP // 2
        bot_y = self.gap_y + PIPE_GAP // 2
        top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, top_h)
        bot_rect = pygame.Rect(self.x, bot_y, PIPE_WIDTH, GROUND_Y - bot_y)
        return bird_rect.colliderect(top_rect) or bird_rect.colliderect(bot_rect)

    def draw(self, surf):
        top_h = self.gap_y - PIPE_GAP // 2
        bot_y = self.gap_y + PIPE_GAP // 2
        cap_h = 28

        # 阴影
        shadow = pygame.Surface((PIPE_WIDTH + 4, H), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 40))
        surf.blit(shadow, (self.x + 4, 0))

        # 上管道体
        body_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, top_h)
        pygame.draw.rect(surf, PIPE_GREEN, body_rect)
        # 渐变效果 - 左亮
        shine = pygame.Rect(self.x + 4, 0, 10, top_h)
        pygame.draw.rect(surf, PIPE_LIGHT, shine)
        # 右暗
        dark = pygame.Rect(self.x + PIPE_WIDTH - 8, 0, 8, top_h)
        pygame.draw.rect(surf, PIPE_DARK, dark)

        # 上管道帽
        cap_rect = pygame.Rect(self.x - 5, top_h - cap_h, PIPE_WIDTH + 10, cap_h)
        pygame.draw.rect(surf, PIPE_CAP, cap_rect, border_radius=4)
        pygame.draw.rect(surf, PIPE_DARK, cap_rect, 2, border_radius=4)
        # 帽子高光
        pygame.draw.rect(surf, (100, 200, 105), pygame.Rect(self.x, top_h - cap_h + 3, 8, cap_h - 6))

        # 下管道体
        bot_h = GROUND_Y - bot_y
        body_rect2 = pygame.Rect(self.x, bot_y, PIPE_WIDTH, bot_h)
        pygame.draw.rect(surf, PIPE_GREEN, body_rect2)
        shine2 = pygame.Rect(self.x + 4, bot_y, 10, bot_h)
        pygame.draw.rect(surf, PIPE_LIGHT, shine2)
        dark2 = pygame.Rect(self.x + PIPE_WIDTH - 8, bot_y, 8, bot_h)
        pygame.draw.rect(surf, PIPE_DARK, dark2)

        # 下管道帽
        cap_rect2 = pygame.Rect(self.x - 5, bot_y, PIPE_WIDTH + 10, cap_h)
        pygame.draw.rect(surf, PIPE_CAP, cap_rect2, border_radius=4)
        pygame.draw.rect(surf, PIPE_DARK, cap_rect2, 2, border_radius=4)
        pygame.draw.rect(surf, (100, 200, 105), pygame.Rect(self.x, bot_y + 3, 8, cap_h - 6))


# =============================================================================
# 虫子类
# =============================================================================
class Worm:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.spawn_tick = pygame.time.get_ticks()

    def update(self):
        self.x -= PIPE_SPEED

    def draw(self, surf):
        if self.collected:
            return
        t = (pygame.time.get_ticks() - self.spawn_tick) * 0.004
        wobble_y = math.sin(t * 3) * 4
        wobble_x = math.cos(t * 2) * 2
        cy = self.y + wobble_y

        # 发光效果
        glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        draw_circle_aa(glow_surf, (255, 107, 157, 50), 20, 20, 16)
        surf.blit(glow_surf, (self.x - 20, cy - 20 + wobble_x))

        # 身体段
        segments = 5
        for i in range(segments):
            sx = self.x - i * 5 + math.sin(t * 3 + i * 0.8) * 3
            sy2 = cy + math.cos(t * 2 + i * 0.5) * 2
            r = max(2, 4 - i * 0.4)
            col = WORM_LIGHT if i % 2 == 0 else WORM_PINK
            draw_circle_aa(surf, col, sx, sy2, r)

        # 头
        draw_circle_aa(surf, WORM_LIGHT, self.x + 3, cy, 5)

        # 眼睛
        draw_circle_aa(surf, BLACK, self.x + 5, cy - 2, 1.5)
        draw_circle_aa(surf, BLACK, self.x + 5, cy + 2, 1.5)

        # 触角
        ant_x = self.x + 6
        pygame.draw.line(surf, WORM_LIGHT, (ant_x, cy - 4),
                         (ant_x + 5 + math.sin(t * 4) * 2, cy - 10), 1)
        pygame.draw.line(surf, WORM_LIGHT, (ant_x, cy + 4),
                         (ant_x + 5 + math.cos(t * 4) * 2, cy + 10), 1)
        draw_circle_aa(surf, WORM_ANTENNA, ant_x + 5 + math.sin(t * 4) * 2, cy - 10, 2)
        draw_circle_aa(surf, WORM_ANTENNA, ant_x + 5 + math.cos(t * 4) * 2, cy + 10, 2)

    def get_rect(self):
        return pygame.Rect(self.x - WORM_RADIUS, self.y - WORM_RADIUS,
                           WORM_RADIUS * 2, WORM_RADIUS * 2)


# =============================================================================
# 背景
# =============================================================================
class Background:
    def __init__(self):
        self.clouds = []
        self.stars = []
        self.mountains = []
        self.ground_offset = 0
        self._init_clouds()
        self._init_stars()
        self._init_mountains()

    def _init_clouds(self):
        for _ in range(6):
            self.clouds.append({
                "x": random.uniform(0, W * 1.5),
                "y": random.uniform(30, 220),
                "w": random.uniform(60, 140),
                "h": random.uniform(20, 40),
                "speed": random.uniform(0.15, 0.4),
                "alpha": random.randint(10, 20),
            })

    def _init_stars(self):
        random.seed(42)
        for _ in range(35):
            self.stars.append((random.randint(0, W), random.randint(0, int(H * 0.4)),
                               random.uniform(0.5, 2), random.uniform(0.2, 0.8)))
        random.seed()

    def _init_mountains(self):
        for i in range(8):
            self.mountains.append({
                "x": i * 120 - 60,
                "h": random.uniform(80, 180),
                "w": random.uniform(100, 170),
                "shade": random.randint(20, 45),
            })

    def update(self):
        for c in self.clouds:
            c["x"] -= c["speed"]
            if c["x"] + c["w"] < 0:
                c["x"] = W + c["w"]
                c["y"] = random.uniform(30, 220)

    def scroll_ground(self, amount):
        self.ground_offset += amount

    def draw_sky(self, surf, tick):
        for y in range(H):
            if y < H * 0.4:
                t = y / (H * 0.4)
                col = lerp_color(SKY_TOP, SKY_MID, t)
            elif y < H * 0.75:
                t = (y - H * 0.4) / (H * 0.35)
                col = lerp_color(SKY_MID, SKY_BOT, t)
            else:
                t = (y - H * 0.75) / (H * 0.25)
                col = lerp_color(SKY_BOT, (244, 195, 160), t)
            pygame.draw.line(surf, col, (0, y), (W, y))

    def draw_stars(self, surf, tick):
        for sx, sy, sz, sa in self.stars:
            twinkle = math.sin(tick * 0.003 + sx * 0.01) * 0.3 + 0.7
            alpha = int(sa * twinkle * 120)
            alpha = max(0, min(255, alpha))
            r = max(1, int(sz))
            s2 = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            draw_circle_aa(s2, (*STAR_COLOR, alpha), r + 2, r + 2, r)
            surf.blit(s2, (sx - r - 2, sy - r - 2))

    def draw_clouds(self, surf):
        for c in self.clouds:
            s2 = pygame.Surface((int(c["w"] + 20), int(c["h"] + 20)), pygame.SRCALPHA)
            draw_ellipse_aa(s2, (*CLOUD_COLOR, c["alpha"]),
                            c["w"] / 2 + 10, c["h"] / 2 + 10, c["w"] / 2, c["h"] / 2)
            draw_ellipse_aa(s2, (*CLOUD_COLOR, c["alpha"] - 3),
                            c["w"] * 0.3 + 10, c["h"] * 0.6 + 10, c["w"] * 0.35, c["h"] * 0.4)
            surf.blit(s2, (c["x"], c["y"]))

    def draw_mountains(self, surf):
        for m in self.mountains:
            pts = [
                (m["x"] - m["w"] / 2, GROUND_Y),
                (m["x"], GROUND_Y - m["h"]),
                (m["x"] + m["w"] / 2, GROUND_Y),
            ]
            s2 = pygame.Surface((W, H), pygame.SRCALPHA)
            col = (m["shade"], m["shade"] // 2, m["shade"] + 15, 120)
            pygame.draw.polygon(s2, col, pts)
            surf.blit(s2, (0, 0))

    def draw_ground(self, surf):
        # 主体
        g_rect = pygame.Rect(0, GROUND_Y, W, GROUND_H)
        pygame.draw.rect(surf, GROUND_LIGHT, g_rect)

        # 渐变
        for y in range(10):
            t = y / 10
            col = lerp_color(GROUND_LIGHT, GROUND_COL, t)
            pygame.draw.line(surf, col, (0, GROUND_Y + 8 + y * 7), (W, GROUND_Y + 8 + y * 7))

        # 草线
        for x in range(0, W + 4, 4):
            gy = GROUND_Y + math.sin((x + self.ground_offset * 0.5) * 0.15) * 3
            pygame.draw.line(surf, GRASS_COL, (x, GROUND_Y - 1), (x, int(gy)), 2)

        # 地面纹理
        for i in range(15):
            lx = int((i * 50 + self.ground_offset * 0.8) % (W + 40)) - 20
            pygame.draw.line(surf, (*GROUND_COL, ), (lx, GROUND_Y + 18), (lx + 25, GROUND_Y + 18), 1)
            pygame.draw.line(surf, (*GROUND_COL,), (lx + 12, GROUND_Y + 38), (lx + 32, GROUND_Y + 38), 1)


# =============================================================================
# 浮动加分
# =============================================================================
class FloatingText:
    def __init__(self, x, y, text, color):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.life = 1.0

    def update(self):
        self.y -= 1.2
        self.life -= 0.025
        return self.life > 0

    def draw(self, surf):
        alpha = int(self.life * 255)
        alpha = max(0, min(255, alpha))
        txt_surf = font_medium.render(self.text, True, self.color)
        txt_surf.set_alpha(alpha)
        surf.blit(txt_surf, (self.x - txt_surf.get_width() // 2, self.y))


# =============================================================================
# 主游戏
# =============================================================================
class Game:
    STATE_READY = 0
    STATE_PLAYING = 1
    STATE_DEAD = 2

    def __init__(self):
        self.high_score = load_high()
        self.bg = Background()
        self.reset()
        self.state = self.STATE_READY
        self.death_time = 0
        self.particles = []
        self.floating_texts = []
        self.score = 0
        self.frame = 0
        self.pulse_timer = 0

    def reset(self):
        self.bird = Bird()
        self.pipes = []
        self.worms = []
        self.particles = []
        self.floating_texts = []
        self.score = 0
        self.frame = 0
        self.last_spawn = pygame.time.get_ticks()
        self.pulse_timer = 0
        self.bg = Background()

    def start(self):
        self.state = self.STATE_PLAYING
        self.last_spawn = pygame.time.get_ticks()

    def flap(self):
        self.bird.flap()
        # 拍打粒子
        for _ in range(4):
            self.particles.append(Particle(self.bird.x - 10, self.bird.y + 5,
                                           BIRD_LIGHT, speed=2, size=3, life=0.5))

    def die(self):
        if self.state == self.STATE_DEAD:
            return
        self.state = self.STATE_DEAD
        self.death_time = pygame.time.get_ticks()

        # 死亡粒子
        for _ in range(25):
            self.particles.append(Particle(self.bird.x, self.bird.y,
                                           BIRD_YELLOW, speed=3, size=4, life=1.2))
        for _ in range(10):
            self.particles.append(Particle(self.bird.x, self.bird.y,
                                           (255, 100, 50), speed=5, size=3, life=0.8))

        is_new = False
        if self.score > self.high_score:
            self.high_score = self.score
            save_high(self.high_score)
            is_new = True

        return is_new

    def update(self):
        tick = pygame.time.get_ticks()
        self.frame += 1

        # 更新粒子
        self.particles = [p for p in self.particles if p.update()]
        self.floating_texts = [f for f in self.floating_texts if f.update()]

        if self.state == self.STATE_READY:
            self.bg.update()
            # 轻微浮动
            self.bird.y = H // 2 - 40 + math.sin(tick * 0.003) * 10
            return

        if self.state == self.STATE_DEAD:
            # 小鸟掉落
            if self.bird.y < GROUND_Y - BIRD_RADIUS:
                self.bird.vy += GRAVITY * 0.5
                self.bird.y += self.bird.vy
                self.bird.rotation = min(1.5, self.bird.rotation + 0.04)
            self.bg.update()
            return

        # --- PLAYING ---
        self.bird.update()
        self.bg.update()
        self.bg.scroll_ground(PIPE_SPEED)

        # 分数随时间增加
        if self.frame % 6 == 0:
            self.score += 1

        # 生成管道
        if tick - self.last_spawn > PIPE_SPAWN_MS:
            p = Pipe()
            self.pipes.append(p)
            self.last_spawn = tick

            # 60%概率在缝隙中放虫子
            if random.random() < 0.6:
                self.worms.append(Worm(p.x + PIPE_WIDTH // 2, p.gap_y))

        # 更新管道
        for p in self.pipes:
            p.update()
            if not p.scored and p.x + PIPE_WIDTH < self.bird.x:
                p.scored = True
                self.score += 10
                self.pulse_timer = 15
        self.pipes = [p for p in self.pipes if not p.off_screen()]

        # 更新虫子
        for w in self.worms:
            w.update()
        self.worms = [w for w in self.worms if w.x > -30 and not w.collected]

        # 碰撞检测 - 地面/天花板
        bird_rect = self.bird.get_rect()
        if self.bird.y + BIRD_RADIUS > GROUND_Y:
            self.bird.y = GROUND_Y - BIRD_RADIUS
            self.die()
            return
        if self.bird.y - BIRD_RADIUS < 0:
            self.bird.y = BIRD_RADIUS
            self.bird.vy = 0

        # 碰撞检测 - 管道
        for p in self.pipes:
            if p.collides(bird_rect):
                self.die()
                return

        # 碰撞检测 - 虫子
        for w in self.worms:
            if w.collected:
                continue
            dx = self.bird.x - w.x
            dy = self.bird.y - w.y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < BIRD_RADIUS + WORM_RADIUS + 5:
                w.collected = True
                self.score += WORM_BONUS
                # 收集粒子
                for _ in range(12):
                    self.particles.append(Particle(w.x, w.y,
                                                   WORM_PINK, speed=3, size=4, life=0.8))
                self.floating_texts.append(FloatingText(w.x, w.y - 20, f"+{WORM_BONUS}", WORM_PINK))

        if self.pulse_timer > 0:
            self.pulse_timer -= 1

    def draw(self, surf):
        tick = pygame.time.get_ticks()

        # 背景
        self.bg.draw_sky(surf, tick)
        self.bg.draw_stars(surf, tick)
        self.bg.draw_clouds(surf)
        self.bg.draw_mountains(surf)

        # 管道
        for p in self.pipes:
            p.draw(surf)

        # 虫子
        for w in self.worms:
            w.draw(surf)

        # 地面
        self.bg.draw_ground(surf)

        # 粒子
        for p in self.particles:
            p.draw(surf)

        # 小鸟
        self.bird.draw(surf)

        # 浮动文字
        for f in self.floating_texts:
            f.draw(surf)

        # 分数
        if self.state in (self.STATE_PLAYING, self.STATE_DEAD):
            self._draw_score(surf)

    def _draw_score(self, surf):
        score_text = str(self.score)

        # 背景半透明条
        score_bg = pygame.Surface((W, 80), pygame.SRCALPHA)
        score_bg.fill((0, 0, 0, 40))
        surf.blit(score_bg, (0, 10))

        # 分数
        scale = 1.1 if self.pulse_timer > 0 else 1.0
        txt = font_score.render(score_text, True, WHITE)
        if scale != 1.0:
            new_w = int(txt.get_width() * scale)
            new_h = int(txt.get_height() * scale)
            txt = pygame.transform.smoothscale(txt, (new_w, new_h))

        # 阴影
        shadow = font_score.render(score_text, True, (0, 0, 0))
        if scale != 1.0:
            shadow = pygame.transform.smoothscale(shadow, (new_w, new_h))
        shadow.set_alpha(100)
        surf.blit(shadow, (W // 2 - shadow.get_width() // 2 + 2, 20 + 2))
        surf.blit(txt, (W // 2 - txt.get_width() // 2, 20))

        # 最高分
        if self.high_score > 0:
            hs = font_tiny.render(f"最高分 {self.high_score}", True, (255, 224, 102))
            surf.blit(hs, (W // 2 - hs.get_width() // 2, 20 + txt.get_height() + 6))

    def draw_overlay_ready(self, surf):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((10, 5, 20, 160))
        surf.blit(ov, (0, 0))

        # 标题
        title = font_title.render("飞翔小鸟", True, (255, 224, 102))
        # 阴影
        title_sh = font_title.render("飞翔小鸟", True, (0, 0, 0))
        title_sh.set_alpha(100)
        surf.blit(title_sh, (W // 2 - title.get_width() // 2 + 2, H // 2 - 100 + 2))
        surf.blit(title, (W // 2 - title.get_width() // 2, H // 2 - 100))

        sub = font_small.render("点击鼠标或按空格键开始", True, (200, 200, 200))
        surf.blit(sub, (W // 2 - sub.get_width() // 2, H // 2 - 30))

        sub2 = font_tiny.render("吃虫加分  躲避障碍  挑战记录", True, (180, 160, 140))
        surf.blit(sub2, (W // 2 - sub2.get_width() // 2, H // 2 + 10))

        if self.high_score > 0:
            hs = font_medium.render(f"历史最高  {self.high_score}", True, (255, 224, 102))
            surf.blit(hs, (W // 2 - hs.get_width() // 2, H // 2 + 55))

        # 闪烁提示
        blink = int((pygame.time.get_ticks() // 500) % 2 == 0)
        if blink:
            hint = font_small.render("点击任意位置", True, (150, 150, 150))
            surf.blit(hint, (W // 2 - hint.get_width() // 2, H // 2 + 110))

    def draw_overlay_dead(self, surf):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((10, 5, 20, 160))
        surf.blit(ov, (0, 0))

        y_off = H // 2 - 120

        title = font_title.render("游戏结束", True, (255, 100, 80))
        title_sh = font_title.render("游戏结束", True, (0, 0, 0))
        title_sh.set_alpha(100)
        surf.blit(title_sh, (W // 2 - title.get_width() // 2 + 2, y_off + 2))
        surf.blit(title, (W // 2 - title.get_width() // 2, y_off))
        y_off += 70

        score_txt = font_score.render(str(self.score), True, WHITE)
        surf.blit(score_txt, (W // 2 - score_txt.get_width() // 2, y_off))
        y_off += 70

        is_new = self.score > 0 and self.score >= self.high_score and self.score > 0
        if is_new:
            nr = font_medium.render("★ 新纪录! ★", True, (255, 107, 157))
            # 跳动
            bounce = math.sin(pygame.time.get_ticks() * 0.008) * 5
            surf.blit(nr, (W // 2 - nr.get_width() // 2, y_off + bounce))
            y_off += 40

        hs = font_small.render(f"历史最高  {self.high_score}", True, (255, 224, 102))
        surf.blit(hs, (W // 2 - hs.get_width() // 2, y_off))
        y_off += 50

        # 只在死亡0.5秒后允许重开
        if pygame.time.get_ticks() - self.death_time > 500:
            hint = font_small.render("点击重新开始", True, (150, 150, 150))
            surf.blit(hint, (W // 2 - hint.get_width() // 2, y_off))


# =============================================================================
# 主循环
# =============================================================================
def main():
    game = Game()

    running = True
    while running:
        dt = clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN or (
                    event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_UP)):

                if game.state == Game.STATE_READY:
                    game.start()
                    game.flap()

                elif game.state == Game.STATE_PLAYING:
                    game.flap()

                elif game.state == Game.STATE_DEAD:
                    if pygame.time.get_ticks() - game.death_time > 500:
                        game.reset()
                        game.start()
                        game.flap()

        game.update()
        game.draw(screen)

        if game.state == Game.STATE_READY:
            game.draw_overlay_ready(screen)
        elif game.state == Game.STATE_DEAD:
            game.draw_overlay_dead(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()