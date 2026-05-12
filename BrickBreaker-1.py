import tkinter as tk
import random

# ─── CONSTANTS ───────────────────────────────────────────────
WIDTH, HEIGHT   = 800, 600
PADDLE_W        = 100
PADDLE_H        = 12
PADDLE_Y        = HEIGHT - 50
BALL_R          = 10
BRICK_ROWS      = 5
BRICK_COLS      = 10
BRICK_W         = WIDTH // BRICK_COLS
BRICK_H         = 28
BRICK_TOP       = 60
FPS             = 16   # ms per frame (~60 fps)

# Brick tiers: (color, points, label)
BRICK_TIERS = [
    ("#FF4C4C", 30, "30"),   # row 0 – hardest colour
    ("#FF8C00", 20, "20"),
    ("#FFD700", 15, "15"),
    ("#4CAF50", 10, "10"),
    ("#29B6F6", 5,  "5"),    # row 4 – easiest
]

# Power-up types
PU_WIDE      = "wide"
PU_MULTIBALL = "multi"
PU_COLORS    = {PU_WIDE: "#FF69B4", PU_MULTIBALL: "#00FFFF"}
PU_LABELS    = {PU_WIDE: "WIDE", PU_MULTIBALL: "x2 BALL"}

# Level configs  (ball_speed, brick_rows)
LEVELS = [
    {"speed": 5,  "rows": 3, "label": "Level 1 – Easy"},
    {"speed": 6,  "rows": 4, "label": "Level 2 – Medium"},
    {"speed": 7,  "rows": 5, "label": "Level 3 – Hard"},
    {"speed": 8,  "rows": 6, "label": "Level 4 – Expert"},
]

# ─── SOUND HELPER (safe on non-Windows) ─────────────────────
def beep(freq=800, dur=40):
        pass  # Linux / Mac – silent

# ─── BALL CLASS ─────────────────────────────────────────────
class Ball:
    def __init__(self, canvas, x, y, dx, dy, speed):
        self.canvas = canvas
        self.x, self.y = x, y
        self.dx, self.dy = dx, dy
        self.speed = speed
        self.r = BALL_R
        self.id = canvas.create_oval(
            x - self.r, y - self.r, x + self.r, y + self.r,
            fill="white", outline="#aee"
        )

    def move(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.canvas.coords(
            self.id,
            self.x - self.r, self.y - self.r,
            self.x + self.r, self.y + self.r
        )

    def delete(self):
        self.canvas.delete(self.id)

# ─── POWERUP CLASS ───────────────────────────────────────────
class PowerUp:
    def __init__(self, canvas, x, y, kind):
        self.canvas = canvas
        self.x, self.y = x, y
        self.kind = kind
        self.vy = 3
        self.w, self.h = 56, 18
        col = PU_COLORS[kind]
        self.rect = canvas.create_rectangle(
            x - self.w//2, y - self.h//2,
            x + self.w//2, y + self.h//2,
            fill=col, outline="white"
        )
        self.text = canvas.create_text(
            x, y, text=PU_LABELS[kind],
            fill="#111", font=("Consolas", 9, "bold")
        )

    def move(self):
        self.y += self.vy
        self.canvas.move(self.rect, 0, self.vy)
        self.canvas.move(self.text, 0, self.vy)

    def delete(self):
        self.canvas.delete(self.rect)
        self.canvas.delete(self.text)

# ─── MAIN GAME CLASS ─────────────────────────────────────────
class BrickBreaker:
    def __init__(self, root):
        self.root = root
        self.root.title("🧱 Brick Breaker – Ultimate Edition")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT,
                                bg="#0d0d1a", highlightthickness=0)
        self.canvas.pack()

        # Key bindings
        self.root.bind("<Left>",  self.move_left)
        self.root.bind("<Right>", self.move_right)
        self.root.bind("<r>",     lambda e: self.restart())
        self.root.bind("<R>",     lambda e: self.restart())

        self.level_idx = 0
        self.high_score = 0
        self.init_game()

    # ── INITIALISE / RESTART ─────────────────────────────────
    def init_game(self):
        self.canvas.delete("all")
        cfg = LEVELS[self.level_idx]
        self.ball_base_speed = cfg["speed"]
        self.num_brick_rows  = cfg["rows"]

        self.score       = 0
        self.lives       = 3
        self.running     = False
        self.game_over   = False
        self.won         = False
        self.wide_timer  = 0          # frames remaining for wide paddle

        self.paddle_x    = WIDTH // 2
        self.paddle_speed= 22
        self.bricks      = []
        self.balls       = []
        self.powerups    = []

        self._draw_background()
        self._draw_hud()
        self._create_bricks()
        self._create_paddle()
        self._spawn_ball()
        self._show_start_banner()

    def restart(self):
        self.level_idx = 0
        self.high_score = max(self.high_score, self.score)
        self.init_game()

    # ── BACKGROUND ───────────────────────────────────────────
    def _draw_background(self):
        # Gradient-like stripes
        for i in range(0, HEIGHT, 4):
            shade = int(13 + i * 0.022)
            col = f"#{shade:02x}{shade:02x}{min(shade+20,50):02x}"
            self.canvas.create_line(0, i, WIDTH, i, fill=col)

    # ── HUD ──────────────────────────────────────────────────
    def _draw_hud(self):
        # Top bar
        self.canvas.create_rectangle(0, 0, WIDTH, 40,
                                     fill="#111133", outline="")
        self.score_txt = self.canvas.create_text(
            10, 20, anchor="w",
            text=self._score_str(),
            fill="#FFD700", font=("Consolas", 13, "bold")
        )
        self.lives_txt = self.canvas.create_text(
            WIDTH//2, 20, anchor="center",
            text=self._lives_str(),
            fill="#FF6B6B", font=("Consolas", 13, "bold")
        )
        self.level_txt = self.canvas.create_text(
            WIDTH - 10, 20, anchor="e",
            text=LEVELS[self.level_idx]["label"],
            fill="#80CFFF", font=("Consolas", 11, "bold")
        )

    def _score_str(self):
        return f"⭐ Score: {self.score}   Best: {self.high_score}"

    def _lives_str(self):
        return "❤️ " * self.lives

    def _update_hud(self):
        self.canvas.itemconfig(self.score_txt, text=self._score_str())
        self.canvas.itemconfig(self.lives_txt, text=self._lives_str())
        self.canvas.itemconfig(self.level_txt,
                               text=LEVELS[self.level_idx]["label"])

    # ── BRICKS ───────────────────────────────────────────────
    def _create_bricks(self):
        rows = min(self.num_brick_rows, len(BRICK_TIERS))
        for row in range(rows):
            color, pts, lbl = BRICK_TIERS[row]
            for col in range(BRICK_COLS):
                x1 = col * BRICK_W + 2
                y1 = BRICK_TOP + row * (BRICK_H + 3)
                x2 = x1 + BRICK_W - 4
                y2 = y1 + BRICK_H
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color, outline="#0d0d1a", width=2
                )
                txt = self.canvas.create_text(
                    (x1+x2)//2, (y1+y2)//2,
                    text=lbl, fill="white",
                    font=("Consolas", 8, "bold")
                )
                self.bricks.append({
                    "rect": rect, "txt": txt,
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "pts": pts, "alive": True
                })

    # ── PADDLE ───────────────────────────────────────────────
    def _create_paddle(self):
        pw = PADDLE_W + (40 if self.wide_timer > 0 else 0)
        self.paddle = self.canvas.create_rectangle(
            self.paddle_x - pw//2, PADDLE_Y,
            self.paddle_x + pw//2, PADDLE_Y + PADDLE_H,
            fill="#38BDF8", outline="#0ea5e9", width=2
        )

    def _redraw_paddle(self):
        pw = PADDLE_W + (40 if self.wide_timer > 0 else 0)
        col = "#FF69B4" if self.wide_timer > 0 else "#38BDF8"
        self.canvas.coords(
            self.paddle,
            self.paddle_x - pw//2, PADDLE_Y,
            self.paddle_x + pw//2, PADDLE_Y + PADDLE_H
        )
        self.canvas.itemconfig(self.paddle, fill=col)

    # ── BALL ─────────────────────────────────────────────────
    def _spawn_ball(self, x=None, y=None, dx=None, dy=None):
        if x is None:
            x = self.paddle_x
            y = PADDLE_Y - BALL_R - 2
        if dx is None:
            dx = random.choice([-1, 1])
        if dy is None:
            dy = -1
        spd = self.ball_base_speed + self.score // 150   # speed scales with score
        b = Ball(self.canvas, x, y, dx, dy, spd)
        self.balls.append(b)

    # ── BANNERS ──────────────────────────────────────────────
    def _show_start_banner(self):
        self._banner("Press ← → to move paddle\nPress any arrow key to start!",
                     color="#80CFFF", tag="startbanner")

    def _banner(self, msg, color="#FFD700", tag="banner"):
        self.canvas.create_rectangle(
            WIDTH//2-220, HEIGHT//2-55,
            WIDTH//2+220, HEIGHT//2+55,
            fill="#0d0d1a", outline=color, width=2, tags=tag
        )
        self.canvas.create_text(
            WIDTH//2, HEIGHT//2,
            text=msg, fill=color,
            font=("Consolas", 15, "bold"),
            justify="center", tags=tag
        )

    def _clear_tag(self, tag):
        self.canvas.delete(tag)

    # ── INPUT ────────────────────────────────────────────────
    def move_left(self, event=None):
        if not self.running and not self.game_over:
            self._clear_tag("startbanner")
            self.running = True
            self._loop()
        pw = PADDLE_W + (40 if self.wide_timer > 0 else 0)
        self.paddle_x = max(pw//2, self.paddle_x - self.paddle_speed)
        self._redraw_paddle()

    def move_right(self, event=None):
        if not self.running and not self.game_over:
            self._clear_tag("startbanner")
            self.running = True
            self._loop()
        pw = PADDLE_W + (40 if self.wide_timer > 0 else 0)
        self.paddle_x = min(WIDTH - pw//2, self.paddle_x + self.paddle_speed)
        self._redraw_paddle()

    # ── MAIN LOOP ────────────────────────────────────────────
    def _loop(self):
        if not self.running:
            return

        self._move_balls()
        self._move_powerups()
        self._check_powerup_catch()
        self._update_hud()

        if self.wide_timer > 0:
            self.wide_timer -= 1
            if self.wide_timer == 0:
                self._redraw_paddle()

        if not self.game_over:
            self.root.after(FPS, self._loop)

    # ── BALL MOVEMENT & COLLISIONS ───────────────────────────
    def _move_balls(self):
        dead = []
        for ball in self.balls:
            ball.move()
            bx, by = ball.x, ball.y
            r = ball.r

            # Wall bounce
            if bx - r <= 0:
                ball.dx = abs(ball.dx)
                beep(600, 30)
            if bx + r >= WIDTH:
                ball.dx = -abs(ball.dx)
                beep(600, 30)
            if by - r <= 40:           # top (below HUD)
                ball.dy = abs(ball.dy)
                beep(600, 30)

            # Paddle collision
            pw = PADDLE_W + (40 if self.wide_timer > 0 else 0)
            px1 = self.paddle_x - pw//2
            px2 = self.paddle_x + pw//2
            if (px1 <= bx <= px2 and
                    PADDLE_Y <= by + r <= PADDLE_Y + PADDLE_H + 6 and
                    ball.dy > 0):
                # Angle based on hit position
                offset = (bx - self.paddle_x) / (pw / 2)
                ball.dx = offset * 1.2
                mag = (ball.dx**2 + 1)**0.5
                ball.dx /= mag * 0.85
                ball.dy = -abs(ball.dy)
                beep(900, 35)

            # Bottom – lose a life
            if by - r > HEIGHT:
                dead.append(ball)
                continue

            # Brick collision
            self._check_brick(ball)

        for b in dead:
            b.delete()
            self.balls.remove(b)

        if not self.balls:
            self.lives -= 1
            beep(250, 300)
            if self.lives <= 0:
                self._end_game(won=False)
            else:
                self._update_hud()
                self._spawn_ball()

    def _check_brick(self, ball):
        bx, by, r = ball.x, ball.y, ball.r
        for brick in self.bricks:
            if not brick["alive"]:
                continue
            x1, y1, x2, y2 = brick["x1"], brick["y1"], brick["x2"], brick["y2"]

            if not (bx + r > x1 and bx - r < x2 and
                    by + r > y1 and by - r < y2):
                continue

            # Hit!
            brick["alive"] = False
            self.canvas.delete(brick["rect"])
            self.canvas.delete(brick["txt"])
            self.score += brick["pts"]
            beep(1000, 30)

            # Bounce direction
            overlap_x = min(bx + r - x1, x2 - (bx - r))
            overlap_y = min(by + r - y1, y2 - (by - r))
            if overlap_x < overlap_y:
                ball.dx *= -1
            else:
                ball.dy *= -1

            # Speed up ball slightly
            ball.speed = self.ball_base_speed + self.score // 150

            # Random power-up drop (20% chance)
            if random.random() < 0.20:
                kind = random.choice([PU_WIDE, PU_MULTIBALL])
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                self.powerups.append(PowerUp(self.canvas, cx, cy, kind))

            # Check win
            if all(not b["alive"] for b in self.bricks):
                self._advance_level()
            break

    # ── POWER-UPS ────────────────────────────────────────────
    def _move_powerups(self):
        for pu in self.powerups:
            pu.move()

    def _check_powerup_catch(self):
        pw = PADDLE_W + (40 if self.wide_timer > 0 else 0)
        px1 = self.paddle_x - pw//2
        px2 = self.paddle_x + pw//2
        caught = []
        for pu in self.powerups:
            if pu.y > HEIGHT:
                caught.append(pu); pu.delete(); continue
            if (px1 <= pu.x <= px2 and
                    PADDLE_Y - 10 <= pu.y <= PADDLE_Y + PADDLE_H + 10):
                beep(1200, 60)
                if pu.kind == PU_WIDE:
                    self.wide_timer = 300   # ~5 seconds
                    self._redraw_paddle()
                elif pu.kind == PU_MULTIBALL:
                    for ball in list(self.balls):
                        self._spawn_ball(
                            x=ball.x, y=ball.y,
                            dx=-ball.dx * random.uniform(0.9, 1.1),
                            dy=ball.dy
                        )
                caught.append(pu); pu.delete()
        for pu in caught:
            if pu in self.powerups:
                self.powerups.remove(pu)

    # ── LEVEL ADVANCE ────────────────────────────────────────
    def _advance_level(self):
        self.running = False
        if self.level_idx + 1 >= len(LEVELS):
            self._end_game(won=True)
            return
        self.level_idx += 1
        self.high_score = max(self.high_score, self.score)
        # Keep score, lives; reset board
        saved_score = self.score
        saved_lives = self.lives
        saved_hi    = self.high_score
        self.canvas.delete("all")
        cfg = LEVELS[self.level_idx]
        self.ball_base_speed = cfg["speed"]
        self.num_brick_rows  = cfg["rows"]
        self.score       = saved_score
        self.lives       = saved_lives
        self.high_score  = saved_hi
        self.wide_timer  = 0
        self.bricks      = []
        self.balls       = []
        self.powerups    = []
        self.paddle_x    = WIDTH // 2
        self._draw_background()
        self._draw_hud()
        self._create_bricks()
        self._create_paddle()
        self._spawn_ball()
        beep(1400, 100)
        self._banner(f"🏆 {LEVELS[self.level_idx]['label']} Unlocked!\nPress ← → to continue",
                     color="#FFD700", tag="levelbanner")
        self.running = False

    # ── GAME OVER / WIN ──────────────────────────────────────
    def _end_game(self, won):
        self.running   = False
        self.game_over = True
        self.high_score = max(self.high_score, self.score)
        if won:
            msg   = f"🎉 YOU WIN! 🎉\nFinal Score: {self.score}\nBest: {self.high_score}\n\nPress R to Play Again"
            color = "#FFD700"
            beep(1500, 200)
        else:
            msg   = f"💀 GAME OVER 💀\nFinal Score: {self.score}\nBest: {self.high_score}\n\nPress R to Restart"
            color = "#FF4C4C"
            beep(200, 500)

        self.canvas.create_rectangle(
            WIDTH//2 - 240, HEIGHT//2 - 85,
            WIDTH//2 + 240, HEIGHT//2 + 85,
            fill="#0d0d1a", outline=color, width=3
        )
        self.canvas.create_text(
            WIDTH//2, HEIGHT//2,
            text=msg, fill=color,
            font=("Consolas", 16, "bold"),
            justify="center"
        )


# ─── ENTRY POINT ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    game = BrickBreaker(root)
    root.mainloop()
