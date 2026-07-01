import tkinter as tk
import random
import math
import json
import os


class BalloonGame:
    """射气球游戏 —— Tkinter 版本（固定 4 气球 + 可选颜色）"""

    # ══════════════════════════════════════════════════════════
    # 初始化
    # ══════════════════════════════════════════════════════════
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("射气球游戏")
        self.root.resizable(False, False)
        self.root.configure(bg="#0A0D1E")

        # 窗口居中
        self.W, self.H = 700, 760
        sx = self.root.winfo_screenwidth()
        sy = self.root.winfo_screenheight()
        self.root.geometry(
            f"{self.W}x{self.H}+{(sx - self.W) // 2}+{(sy - self.H) // 2}"
        )

        # ── 常量 ────────────────────────────────────────────
        self.GRID_N = 3
        self.GRID_SIZE = 480
        self.GRID_LEFT = (self.W - self.GRID_SIZE) // 2
        self.GRID_PAD = 15
        self.CELL = self.GRID_SIZE // self.GRID_N
        self.BALLOON_COUNT = 4
        self.GAME_TIME = 60

        self.DIFFS = {
            "large":  {"radius": 55, "mult": 1, "name": "大气球", "desc": "简单 ×1"},
            "medium": {"radius": 38, "mult": 2, "name": "中气球", "desc": "普通 ×2"},
            "small":  {"radius": 25, "mult": 3, "name": "小气球", "desc": "困难 ×3"},
        }
        self.DIFF_CLR = {
            "large": "#48D776", "medium": "#48ACFF", "small": "#FF4848"
        }

        self.COLORS = {
            "红色": "#FF4444", "蓝色": "#4488FF", "绿色": "#44CC66", "橙色": "#FF8822",
            "紫色": "#AA55FF", "粉色": "#FF66BB", "黄色": "#FFCC22", "青色": "#22CCBB",
        }

        # ── 状态 ────────────────────────────────────────────
        self.state = "menu"
        self.difficulty = "large"
        self.color_name = "红色"
        self.score = 0
        self.time_left = self.GAME_TIME
        self.balloons: list[dict] = []
        self.timer_id = None
        self.frame = None

        self.highscores = self._load_hs()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._show_menu()
        self.root.mainloop()

    # ══════════════════════════════════════════════════════════
    # 工具函数
    # ══════════════════════════════════════════════════════════
    def _on_close(self):
        self.state = "closed"
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.root.destroy()

    # ── 存 / 读 ──
    def _load_hs(self):
        try:
            if os.path.exists("balloon_hs.json"):
                with open("balloon_hs.json", "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"large": 0, "medium": 0, "small": 0}

    def _save_hs(self):
        try:
            with open("balloon_hs.json", "w") as f:
                json.dump(self.highscores, f)
        except Exception:
            pass

    # ── 颜色辅助 ──
    @staticmethod
    def _darken(h, f=0.65):
        h = h.lstrip("#")
        r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16)
        return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

    @staticmethod
    def _lighten(h, f=1.4):
        h = h.lstrip("#")
        r, g, b = int(h[:2], 16), int(h[2:4], 16), int(h[4:], 16)
        return (
            f"#{min(255,int(r*f)):02x}"
            f"{min(255,int(g*f)):02x}"
            f"{min(255,int(b*f)):02x}"
        )

    # ── 页面切换 ──
    def _switch(self, builder):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        if self.frame:
            self.frame.destroy()
        self.frame = tk.Frame(self.root, bg="#0A0D1E", width=self.W, height=self.H)
        self.frame.pack(fill="both", expand=True)
        self.frame.pack_propagate(False)
        builder()

    # ── 按钮工厂 ──
    def _btn(self, parent, text, fg, cmd, w=20):
        b = tk.Button(
            parent, text=text, font=("Arial", 15, "bold"),
            fg=fg, bg="#0A0D1E", activebackground="#1A1E3A",
            activeforeground=fg, width=w, bd=2, relief="ridge",
            command=cmd, cursor="hand2", pady=4,
        )
        b.bind("<Enter>", lambda e: b.config(relief="raised", bg="#151930"))
        b.bind("<Leave>", lambda e: b.config(relief="ridge", bg="#0A0D1E"))
        return b

    def _safe_del(self, item):
        try:
            self._canvas.delete(item)
        except tk.TclError:
            pass

    # ══════════════════════════════════════════════════════════
    #  主菜单
    # ══════════════════════════════════════════════════════════
    def _show_menu(self):
        self.state = "menu"
        self._switch(self._build_menu)

    def _build_menu(self):
        f = self.frame

        tk.Label(
            f, text="射 气 球 游 戏",
            font=("Arial", 38, "bold"), fg="#FFD700", bg="#0A0D1E",
        ).pack(pady=(55, 6))
        tk.Label(
            f, text="在 60 秒内点击尽可能多的气球!",
            font=("Arial", 15), fg="#8890A0", bg="#0A0D1E",
        ).pack(pady=(0, 18))

        tk.Frame(f, bg="#283050", height=1, width=320).pack(pady=8)

        # 最高分
        hs = tk.Frame(f, bg="#0A0D1E")
        hs.pack(pady=4)
        tk.Label(
            hs, text="── 历史最高分 ──",
            font=("Arial", 15), fg="#CCC", bg="#0A0D1E",
        ).pack(pady=(0, 6))
        for k, v in self.DIFFS.items():
            tk.Label(
                hs, text=f"{v['name']}: {self.highscores.get(k, 0)} 分",
                font=("Arial", 13), fg=self.DIFF_CLR[k], bg="#0A0D1E",
            ).pack(pady=2)

        tk.Frame(f, bg="#283050", height=1, width=320).pack(pady=14)

        bf = tk.Frame(f, bg="#0A0D1E")
        bf.pack(pady=4)
        self._btn(bf, "开 始 游 戏", "#FFD700", self._show_game).pack(pady=7)
        self._btn(bf, "设 置 中 心", "#48ACFF", self._show_settings).pack(pady=7)
        self._btn(bf, "退 出 游 戏", "#FF4848", self._on_close).pack(pady=7)

    # ══════════════════════════════════════════════════════════
    #  设置
    # ══════════════════════════════════════════════════════════
    def _show_settings(self):
        self.state = "settings"
        self._switch(self._build_settings)

    def _build_settings(self):
        f = self.frame

        tk.Label(
            f, text="设 置 中 心",
            font=("Arial", 36, "bold"), fg="#FFD700", bg="#0A0D1E",
        ).pack(pady=(30, 4))
        tk.Label(
            f, text="气球越小，难度越高，分数倍率越大",
            font=("Arial", 13), fg="#8890A0", bg="#0A0D1E",
        ).pack(pady=(0, 10))

        # ── 难度 ──
        df = tk.LabelFrame(
            f, text=" 难度选择 ", font=("Arial", 13, "bold"),
            fg="#CCC", bg="#0A0D1E", bd=1, relief="groove",
        )
        df.pack(pady=5, padx=50, fill="x")

        self._diff_var = tk.StringVar(value=self.difficulty)
        for k, v in self.DIFFS.items():
            tk.Radiobutton(
                df, text=f"  {v['name']}    {v['desc']}",
                variable=self._diff_var, value=k,
                font=("Arial", 14), fg=self.DIFF_CLR[k],
                bg="#0A0D1E", selectcolor="#1A1E3A",
                activebackground="#0A0D1E",
                activeforeground=self.DIFF_CLR[k], cursor="hand2",
            ).pack(anchor="w", padx=20, pady=4)

        # ── 气球颜色 ──
        cf = tk.LabelFrame(
            f, text=" 气球颜色 ", font=("Arial", 13, "bold"),
            fg="#CCC", bg="#0A0D1E", bd=1, relief="groove",
        )
        cf.pack(pady=5, padx=50, fill="x")

        self._color_var = tk.StringVar(value=self.color_name)
        grid = tk.Frame(cf, bg="#0A0D1E")
        grid.pack(pady=8)

        self._swatches: dict[str, dict] = {}

        for i, (name, hex_c) in enumerate(self.COLORS.items()):
            row, col = divmod(i, 4)
            cell = tk.Frame(grid, bg="#0A0D1E")
            cell.grid(row=row, column=col, padx=12, pady=3)

            cv = tk.Canvas(
                cell, width=44, height=44,
                bg="#0A0D1E", highlightthickness=0, cursor="hand2",
            )
            cv.pack()
            is_sel = name == self.color_name
            oid = cv.create_oval(
                4, 4, 40, 40, fill=hex_c,
                outline="white" if is_sel else "#444",
                width=3 if is_sel else 1,
            )
            lbl = tk.Label(
                cell, text=name, font=("Arial", 11),
                fg=hex_c, bg="#0A0D1E", cursor="hand2",
            )
            lbl.pack()
            self._swatches[name] = {"canvas": cv, "oval_id": oid}
            for w in (cell, cv, lbl):
                w.bind("<Button-1>", lambda e, n=name: self._pick_color(n))

        # 预览
        pf = tk.Frame(cf, bg="#0A0D1E")
        pf.pack(pady=6)
        tk.Label(
            pf, text="预览  ", font=("Arial", 13), fg="#777", bg="#0A0D1E",
        ).pack(side="left")

        self._pv_cv = tk.Canvas(
            pf, width=60, height=70, bg="#0A0D1E", highlightthickness=0,
        )
        self._pv_cv.pack(side="left")
        pc = self.COLORS[self.color_name]
        self._pv_cv.create_line(30, 62, 28, 70, fill="#666")
        self._pv_oval = self._pv_cv.create_oval(
            5, 5, 55, 55, fill=pc, outline="white", width=2,
        )
        self._pv_knot = self._pv_cv.create_polygon(
            25, 53, 35, 53, 30, 60, fill=self._darken(pc), outline="",
        )

        self._btn(f, "应 用 并 返 回", "#FFD700", self._apply_settings).pack(pady=10)

    def _pick_color(self, name):
        self._color_var.set(name)
        hex_c = self.COLORS[name]
        for n, sw in self._swatches.items():
            sel = n == name
            sw["canvas"].itemconfig(
                sw["oval_id"],
                outline="white" if sel else "#444",
                width=3 if sel else 1,
            )
        self._pv_cv.itemconfig(self._pv_oval, fill=hex_c)
        self._pv_cv.itemconfig(self._pv_knot, fill=self._darken(hex_c))

    def _apply_settings(self):
        self.difficulty = self._diff_var.get()
        self.color_name = self._color_var.get()
        self._show_menu()

    # ══════════════════════════════════════════════════════════
    #  游戏
    # ══════════════════════════════════════════════════════════
    def _show_game(self):
        self.state = "playing"
        self._switch(self._build_game)

    def _build_game(self):
        f = self.frame
        self.score = 0
        self.time_left = self.GAME_TIME
        self.balloons.clear()

        diff = self.DIFFS[self.difficulty]
        color = self.COLORS[self.color_name]

        # ── HUD ──
        hud = tk.Frame(f, bg="#0A0D1E")
        hud.pack(fill="x", pady=(8, 2))

        self._lbl_time = tk.Label(
            hud, text=f"时间: {self.time_left}s",
            font=("Arial", 22, "bold"), fg="white", bg="#0A0D1E",
        )
        self._lbl_time.pack()

        self._lbl_score = tk.Label(
            hud, text=f"得分: {self.score}",
            font=("Arial", 22, "bold"), fg="#FFD700", bg="#0A0D1E",
        )
        self._lbl_score.pack()

        tk.Label(
            hud,
            text=f"[ {diff['name']} - {diff['desc']} ]  颜色: {self.color_name}",
            font=("Arial", 12), fg=self.DIFF_CLR[self.difficulty], bg="#0A0D1E",
        ).pack()

        # ── 画布 ──
        ch = self.GRID_SIZE + self.GRID_PAD * 2 + 10
        self._canvas = tk.Canvas(
            f, width=self.W, height=ch, bg="#0A0D1E", highlightthickness=0,
        )
        self._canvas.pack()

        p = self.GRID_PAD
        self._canvas.create_rectangle(
            self.GRID_LEFT - p, p,
            self.GRID_LEFT + self.GRID_SIZE + p, p + self.GRID_SIZE + p,
            fill="#0E1228", outline="#283050", width=2,
        )
        for i in range(1, self.GRID_N):
            y = p + i * self.CELL
            self._canvas.create_line(
                self.GRID_LEFT, y, self.GRID_LEFT + self.GRID_SIZE, y, fill="#283050",
            )
            x = self.GRID_LEFT + i * self.CELL
            self._canvas.create_line(x, p, x, p + self.GRID_SIZE, fill="#283050")

        # 生成初始气球
        self._spawn_initial(color)

        # 事件
        self._canvas.bind("<Button-1>", self._on_click)
        self._canvas.bind("<Motion>", self._on_motion)

        # 计时
        self.timer_id = self.root.after(1000, self._tick)

    # ── 气球管理 ──
    def _cell_xy(self, r, c):
        return (
            self.GRID_LEFT + c * self.CELL + self.CELL // 2,
            self.GRID_PAD + r * self.CELL + self.CELL // 2,
        )

    def _occupied(self):
        return {(b["r"], b["c"]) for b in self.balloons}

    def _empty(self):
        occ = self._occupied()
        return [
            (r, c)
            for r in range(self.GRID_N)
            for c in range(self.GRID_N)
            if (r, c) not in occ
        ]

    def _spawn_initial(self, color):
        cells = self._empty()
        random.shuffle(cells)
        for r, c in cells[: self.BALLOON_COUNT]:
            self._spawn(r, c, color)

    def _spawn(self, r, c, color=None):
        if color is None:
            color = self.COLORS[self.color_name]
        rad = self.DIFFS[self.difficulty]["radius"]
        cx, cy = self._cell_xy(r, c)
        items: list[int] = []

        # 线
        sp = []
        for i in range(15):
            t = i / 14
            sp += [cx + math.sin(t * 3) * 4, cy + rad + 8 + t * 25]
        items.append(self._canvas.create_line(*sp, fill="#777", width=1))

        # 主体
        items.append(
            self._canvas.create_oval(
                cx - rad, cy - rad, cx + rad, cy + rad,
                fill=color, outline=self._darken(color), width=2,
            )
        )

        # 高光
        hs = max(3, int(rad * 0.25))
        hx, hy = cx - rad * 0.22, cy - rad * 0.22
        items.append(
            self._canvas.create_oval(
                hx - hs, hy - hs, hx + hs, hy + hs,
                fill=self._lighten(color), outline="",
            )
        )

        # 结
        kw, kh = max(3, rad // 8), max(4, rad // 5)
        items.append(
            self._canvas.create_polygon(
                cx - kw, cy + rad - 2, cx + kw, cy + rad - 2,
                cx, cy + rad + kh, fill=self._darken(color), outline="",
            )
        )

        self.balloons.append(
            {"r": r, "c": c, "cx": cx, "cy": cy, "radius": rad, "items": items}
        )

    # ── 点击 & 爆破 ──
    def _on_click(self, event):
        if self.state != "playing":
            return
        for b in self.balloons[:]:
            if math.hypot(event.x - b["cx"], event.y - b["cy"]) <= b["radius"] + 5:
                self._pop(b)
                return

    def _pop(self, b):
        pts = self.DIFFS[self.difficulty]["mult"]
        self.score += pts
        self._lbl_score.config(text=f"得分: {self.score}")

        for it in b["items"]:
            self._canvas.delete(it)

        cx, cy, rad = b["cx"], b["cy"], b["radius"]

        # 金光
        fl = self._canvas.create_oval(
            cx - rad - 8, cy - rad - 8, cx + rad + 8, cy + rad + 8,
            fill="", outline="#FFD700", width=3,
        )
        self.root.after(130, lambda: self._safe_del(fl))

        # 得分弹字
        self._popup(cx, cy - rad - 15, f"+{pts}")

        # 移除 & 刷新
        self.balloons.remove(b)
        emp = self._empty()
        if emp:
            nr, nc = random.choice(emp)
            self._spawn(nr, nc)

    def _popup(self, x, y, text):
        pid = self._canvas.create_text(
            x, y, text=text, fill="#FFD700", font=("Arial", 22, "bold"),
        )
        self._anim_popup(pid, 18)

    def _anim_popup(self, pid, n):
        if n > 0 and self.state == "playing":
            self._canvas.move(pid, 0, -2)
            self.root.after(30, lambda: self._anim_popup(pid, n - 1))
        else:
            self._safe_del(pid)

    def _on_motion(self, event):
        if self.state != "playing":
            return
        for b in self.balloons:
            if math.hypot(event.x - b["cx"], event.y - b["cy"]) <= b["radius"] + 5:
                self._canvas.config(cursor="hand2")
                return
        self._canvas.config(cursor="")

    # ── 计时 ──
    def _tick(self):
        if self.state != "playing":
            return
        self.time_left -= 1
        self._lbl_time.config(
            text=f"时间: {self.time_left}s",
            fg="#FF4848" if self.time_left <= 10 else "white",
        )
        if self.time_left <= 0:
            self._end_game()
        else:
            self.timer_id = self.root.after(1000, self._tick)

    def _end_game(self):
        self.state = "result"
        old = self.highscores.get(self.difficulty, 0)
        if self.score > old:
            self.highscores[self.difficulty] = self.score
            self._save_hs()
        self.root.after(350, self._show_result)

    # ══════════════════════════════════════════════════════════
    #  结算
    # ══════════════════════════════════════════════════════════
    def _show_result(self):
        self._switch(self._build_result)

    def _build_result(self):
        f = self.frame
        diff = self.DIFFS[self.difficulty]
        old = self.highscores.get(self.difficulty, 0)
        is_new = self.score >= old and self.score > 0

        tk.Label(
            f, text="时间到!",
            font=("Arial", 38, "bold"), fg="white", bg="#0A0D1E",
        ).pack(pady=(50, 4))

        if is_new:
            tk.Label(
                f, text="*  新 纪 录  *",
                font=("Arial", 26, "bold"), fg="#FFD700", bg="#0A0D1E",
            ).pack(pady=4)

        tk.Label(
            f, text=f"最终得分: {self.score}",
            font=("Arial", 30, "bold"), fg="#FFD700", bg="#0A0D1E",
        ).pack(pady=12)

        tk.Label(
            f, text=f"难度: {diff['name']}  ({diff['desc']})",
            font=("Arial", 15), fg=self.DIFF_CLR[self.difficulty], bg="#0A0D1E",
        ).pack(pady=2)

        hex_c = self.COLORS[self.color_name]
        row = tk.Frame(f, bg="#0A0D1E")
        row.pack(pady=2)
        tk.Label(row, text="气球颜色: ", font=("Arial", 14),
                 fg="#888", bg="#0A0D1E").pack(side="left")
        tk.Label(row, text=self.color_name, font=("Arial", 14, "bold"),
                 fg=hex_c, bg="#0A0D1E").pack(side="left")

        tk.Label(
            f, text=f"历史最高: {max(self.score, old)}",
            font=("Arial", 17), fg="white", bg="#0A0D1E",
        ).pack(pady=8)

        tk.Frame(f, bg="#283050", height=1, width=300).pack(pady=10)

        bf = tk.Frame(f, bg="#0A0D1E")
        bf.pack(pady=6)
        self._btn(bf, "再 来 一 局", "#FFD700", self._show_game).pack(pady=7)
        self._btn(bf, "返 回 主 菜 单", "#8890A0", self._show_menu).pack(pady=7)


# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    BalloonGame()