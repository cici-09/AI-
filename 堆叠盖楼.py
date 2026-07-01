import pygame
import sys
import random

pygame.init()

# ─── 配置 ────────────────────────────────────────────────────────
WIDTH, HEIGHT = 480, 800
FPS = 60
BLOCK_H = 38
BASE_W = 180
GROUND_Y = HEIGHT - 120
INITIAL_SPEED = 2.8
GRAVITY = 0.55
MAX_SPEED = 10
PERFECT_THRESHOLD = 6

COLORS = [
    (231, 76, 60),  (230, 126, 34), (241, 196, 15),
    (46, 204, 113),  (52, 152, 219), (155, 89, 182),
    (236, 64, 122),  (26, 188, 156), (22, 160, 133),
    (192, 57, 43),   (142, 68, 173), (44, 62, 80),
]

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("盖房子  -  Tower Stacker")
clock = pygame.time.Clock()

# ─── 预渲染背景 ──────────────────────────────────────────────────
bg = pygame.Surface((WIDTH, HEIGHT))
for _y in range(HEIGHT):
    _t = _y / HEIGHT
    pygame.draw.line(
        bg,
        (int(10 + 18 * _t), int(8 + 14 * _t), int(25 + 25 * _t)),
        (0, _y), (WIDTH, _y),
    )
_sr = random.Random(42)
for _ in range(90):
    _sx, _sy = _sr.randint(0, WIDTH), _sr.randint(0, HEIGHT)
    _br = _sr.randint(80, 200)
    pygame.draw.circle(
        bg, (_br, _br, min(255, _br + 30)),
        (_sx, _sy), _sr.choice([1, 1, 1, 2]),
    )


# ─── 粒子效果 ────────────────────────────────────────────────────
class Particle:
    __slots__ = ("x", "y", "w", "h", "color", "vx", "vy", "alpha")

    def __init__(self, x, y, w, h, color, vx, vy):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.color = color
        self.vx, self.vy = vx, vy
        self.alpha = 255

    def update(self):
        self.x += self.vx
        self.vy += 0.4
        self.y += self.vy
        self.alpha = max(0, self.alpha - 5)

    def draw(self, surf):
        if self.alpha <= 0 or self.w < 1 or self.h < 1:
            return
        s = pygame.Surface((int(self.w), int(self.h)), pygame.SRCALPHA)
        s.fill((*self.color, self.alpha))
        surf.blit(s, (int(self.x), int(self.y)))


# ─── 绘制方块 ────────────────────────────────────────────────────
def draw_block(surf, x, y, w, h, color):
    ix, iy, iw, ih = int(x), int(y), max(1, int(w)), int(h)
    if ih <= 0 or iw <= 0:
        return
    pygame.draw.rect(surf, color, (ix, iy, iw, ih))
    lighter = tuple(min(255, c + 32) for c in color)
    darker = tuple(max(0, c - 32) for c in color)
    mid_l = tuple(min(255, c + 16) for c in color)
    mid_d = tuple(max(0, c - 16) for c in color)
    pygame.draw.rect(surf, lighter, (ix, iy, iw, 3))
    pygame.draw.rect(surf, darker, (ix, iy + ih - 3, iw, 3))
    pygame.draw.rect(surf, mid_l, (ix, iy + 3, 2, ih - 6))
    pygame.draw.rect(surf, mid_d, (ix + iw - 2, iy + 3, 2, ih - 6))
    if iw > 25:
        wc = tuple(min(255, c + 48) for c in color)
        wx = ix + 7
        while wx + 5 <= ix + iw - 4:
            pygame.draw.rect(surf, wc, (wx, iy + 7, 4, 7))
            if ih >= 30:
                pygame.draw.rect(surf, wc, (wx, iy + 21, 4, 7))
            wx += 10


# ─── 游戏主逻辑 ──────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.font_big = pygame.font.SysFont("Arial", 52, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_sm = pygame.font.SysFont("Arial", 22)
        self.font_xs = pygame.font.SysFont("Arial", 18)
        self.best = 0
        self.state = "title"
        self._init_game()

    # ---- 初始化 ----
    def _init_game(self):
        bx = (WIDTH - BASE_W) // 2
        self.blocks = [(bx, BASE_W)]
        self.cur_w = float(BASE_W)
        self.cur_x = float(WIDTH + 50)
        self.speed = INITIAL_SPEED
        self.dir = -1
        self.dropping = False
        self.drop_y = 0.0
        self.drop_vy = 0.0
        self.locked_x = 0.0
        self.cam = 0.0
        self.target_cam = 0.0
        self.score = 0
        self.particles = []
        self.combo = 0
        self.perfect_timer = 0

    # ---- 点击 ----
    def click(self):
        if self.state == "title":
            self._init_game()
            self.state = "playing"
            return
        if self.state == "gameover":
            self.best = max(self.best, self.score)
            self._init_game()
            self.state = "playing"
            return
        if not self.dropping:
            self.dropping = True
            self.drop_y = -220
            self.drop_vy = 0.0
            self.locked_x = self.cur_x

    # ---- 下一块的目标 Y (世界坐标) ----
    def _next_world_y(self):
        return GROUND_Y - (len(self.blocks) + 1) * BLOCK_H

    # ---- 更新 ----
    def update(self):
        if self.state == "title":
            return
        if self.state == "gameover":
            for p in self.particles:
                p.update()
            self.particles = [p for p in self.particles if p.alpha > 0]
            return

        # 摆动
        if not self.dropping:
            self.cur_x += self.speed * self.dir
            if self.cur_x + self.cur_w > WIDTH:
                self.dir = -1
            elif self.cur_x < 0:
                self.dir = 1
        else:
            self.drop_vy += GRAVITY
            self.drop_y += self.drop_vy
            if self.drop_y >= 0:
                self.drop_y = 0
                self._land()

        self.cam += (self.target_cam - self.cam) * 0.08
        if self.perfect_timer > 0:
            self.perfect_timer -= 1
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alpha > 0]

    # ---- 落地逻辑 ----
    def _land(self):
        prev_x, prev_w = self.blocks[-1]
        cx = self.locked_x

        left = max(cx, prev_x)
        right = min(cx + self.cur_w, prev_x + prev_w)
        overlap = right - left

        color = COLORS[len(self.blocks) % len(COLORS)]
        ny = self._next_world_y() + self.cam

        if overlap <= 0:
            self.state = "gameover"
            self.best = max(self.best, self.score)
            self.particles.append(
                Particle(cx, ny, max(1, self.cur_w), BLOCK_H, color, 0, 0)
            )
            return

        is_perfect = abs(overlap - prev_w) < PERFECT_THRESHOLD
        if is_perfect:
            self.combo += 1
            self.perfect_timer = 60
            overlap = prev_w
            left = prev_x
            for _ in range(12):
                self.particles.append(
                    Particle(
                        left + random.uniform(0, overlap),
                        ny + random.uniform(0, BLOCK_H),
                        3, 3, (255, 215, 0),
                        random.uniform(-4, 4),
                        random.uniform(-6, -1),
                    )
                )
        else:
            self.combo = 0

        # 左侧裁切碎片
        if cx < prev_x - 1:
            cw = prev_x - cx
            n = max(1, int(cw / 15))
            pw = cw / n
            for i in range(n):
                self.particles.append(
                    Particle(
                        cx + i * pw, ny, max(1, pw - 1), BLOCK_H, color,
                        random.uniform(-3, -0.5), random.uniform(-6, -1),
                    )
                )
        # 右侧裁切碎片
        if cx + self.cur_w > prev_x + prev_w + 1:
            cs = prev_x + prev_w
            cw = (cx + self.cur_w) - cs
            n = max(1, int(cw / 15))
            pw = cw / n
            for i in range(n):
                self.particles.append(
                    Particle(
                        cs + i * pw, ny, max(1, pw - 1), BLOCK_H, color,
                        random.uniform(0.5, 3), random.uniform(-6, -1),
                    )
                )

        self.blocks.append((left, overlap))
        self.score = len(self.blocks) - 1
        self.cur_w = overlap
        self.speed = min(self.speed + 0.05, MAX_SPEED)
        if is_perfect and self.combo >= 3:
            self.speed = min(self.speed + 0.15, MAX_SPEED)

        if len(self.blocks) > 5:
            self.target_cam = (len(self.blocks) - 5) * BLOCK_H

        self.dropping = False
        self.dir = -self.dir
        self.cur_x = -self.cur_w - 20 if self.dir == 1 else float(WIDTH + 20)

    # ---- 绘制 ----
    def draw(self, surf):
        surf.blit(bg, (0, 0))
        if self.state == "title":
            self._draw_title(surf)
            return

        # 地面
        gy = int(GROUND_Y + self.cam)
        if gy < HEIGHT:
            pygame.draw.rect(surf, (35, 38, 50), (0, gy, WIDTH, HEIGHT - gy + 200))
            pygame.draw.line(surf, (55, 60, 75), (0, gy), (WIDTH, gy), 2)

        # 已堆叠的楼层
        for i, (bx, bw) in enumerate(self.blocks):
            by = GROUND_Y - (i + 1) * BLOCK_H + self.cam
            if by > HEIGHT + 10 or by + BLOCK_H < -10:
                continue
            draw_block(surf, bx, by, bw, BLOCK_H, COLORS[i % len(COLORS)])

        # 顶层发光
        if self.state == "playing" and self.blocks:
            tx, tw = self.blocks[-1]
            ty = GROUND_Y - len(self.blocks) * BLOCK_H + self.cam
            pulse = abs(2 * (pygame.time.get_ticks() % 2000) / 2000 - 1)
            alpha = int(18 + 22 * pulse)
            glow = pygame.Surface((tw + 10, BLOCK_H + 10), pygame.SRCALPHA)
            glow.fill((*COLORS[(len(self.blocks) - 1) % len(COLORS)], alpha))
            surf.blit(glow, (tx - 5, ty - 5))

        # 当前吊着的楼层 & 起重机线
        if self.state == "playing":
            color = COLORS[len(self.blocks) % len(COLORS)]
            if not self.dropping:
                by = self._next_world_y() + self.cam
                draw_block(surf, self.cur_x, by, self.cur_w, BLOCK_H, color)
                cx = int(self.cur_x + self.cur_w / 2)
                pygame.draw.line(surf, (140, 140, 155), (cx, -5), (cx, int(by)), 2)
                pygame.draw.circle(surf, (180, 180, 190), (cx, -2), 4)
            else:
                by = self._next_world_y() + self.cam + self.drop_y
                draw_block(surf, self.locked_x, by, self.cur_w, BLOCK_H, color)
                cx = int(self.locked_x + self.cur_w / 2)
                if int(by) > -5:
                    pygame.draw.line(
                        surf, (140, 140, 155), (cx, -5), (cx, int(by)), 2
                    )

        # 粒子
        for p in self.particles:
            p.draw(surf)

        # 分数 HUD
        sc = self.font_med.render(str(self.score), True, (255, 255, 255))
        surf.blit(sc, (WIDTH // 2 - sc.get_width() // 2, 18))
        if self.score > 0:
            ht = self.font_xs.render(
                f"{self.score * 3}m  |  best {self.best}", True, (100, 100, 130)
            )
            surf.blit(ht, (WIDTH // 2 - ht.get_width() // 2, 52))

        # PERFECT 提示
        if self.perfect_timer > 0 and self.combo >= 1:
            txt_s = (
                f"PERFECT x{self.combo}!" if self.combo >= 3 else "PERFECT!"
            )
            txt = self.font_med.render(txt_s, True, (255, 215, 0))
            surf.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 82))

        # 游戏结束
        if self.state == "gameover":
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 150))
            surf.blit(ov, (0, 0))
            cy = HEIGHT // 2 - 100
            t1 = self.font_big.render("GAME OVER", True, (255, 255, 255))
            t2 = self.font_med.render(
                f"Score: {self.score}", True, (220, 220, 220)
            )
            t3 = self.font_sm.render(
                f"Best: {self.best}", True, (170, 170, 170)
            )
            t4 = self.font_xs.render(
                "Click / Space to restart", True, (130, 130, 130)
            )
            surf.blit(t1, (WIDTH // 2 - t1.get_width() // 2, cy))
            surf.blit(t2, (WIDTH // 2 - t2.get_width() // 2, cy + 70))
            surf.blit(t3, (WIDTH // 2 - t3.get_width() // 2, cy + 110))
            surf.blit(t4, (WIDTH // 2 - t4.get_width() // 2, cy + 150))

    # ---- 标题画面 ----
    def _draw_title(self, surf):
        t = pygame.time.get_ticks() / 1000.0
        t1 = self.font_big.render("TOWER", True, (255, 255, 255))
        t2 = self.font_big.render("STACKER", True, COLORS[0])
        alpha = int(155 + 100 * abs(2 * (t % 2) / 2 - 1))
        t3 = self.font_sm.render("Click or Press Space", True, (alpha, alpha, alpha))
        hint = self.font_xs.render("Stack floors as high as you can!", True, (120, 120, 140))

        # 装饰方块
        for i in range(5):
            w = 90 - i * 12
            x = WIDTH // 2 - w // 2
            y = 340 + i * BLOCK_H
            draw_block(surf, x, y, w, BLOCK_H - 2, COLORS[i % len(COLORS)])

        surf.blit(t1, (WIDTH // 2 - t1.get_width() // 2, 110))
        surf.blit(t2, (WIDTH // 2 - t2.get_width() // 2, 170))
        surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, 240))
        surf.blit(t3, (WIDTH // 2 - t3.get_width() // 2, 620))


# ─── 主循环 ───────────────────────────────────────────────────────
def main():
    game = Game()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game.click()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    game.click()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        game.update()
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()