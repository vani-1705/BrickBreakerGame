import tkinter as tk
import random

WIDTH = 500
HEIGHT = 400
PADDLE_WIDTH = 80
PADDLE_HEIGHT = 10
BALL_SIZE = 15
BRICK_ROWS = 5
BRICK_COLS = 8
BRICK_WIDTH = WIDTH // BRICK_COLS
BRICK_HEIGHT = 20

class BrickBreaker:
    def __init__(self, root):
        self.root = root
        self.root.title("Brick Breaker")

        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="black")
        self.canvas.pack()

        self.score = 0
        self.running = True

        self.score_text = self.canvas.create_text(10, 10, anchor="nw", fill="white", font=("Arial", 14),
                                                  text=f"Score: {self.score}")
        self.restart_button = tk.Button(root, text="Restart", font=("Arial", 14), command=self.restart_game)
        self.restart_window = self.canvas.create_window(WIDTH // 2, HEIGHT // 2 + 30, window=self.restart_button)
        self.canvas.itemconfigure(self.restart_window, state='hidden')

        self.init_game()

        self.root.bind("<Left>", self.move_left)
        self.root.bind("<Right>", self.move_right)

        self.update()

    def init_game(self):
        self.paddle = self.canvas.create_rectangle(
            WIDTH // 2 - PADDLE_WIDTH // 2, HEIGHT - 30,
            WIDTH // 2 + PADDLE_WIDTH // 2, HEIGHT - 20,
            fill="white"
        )

        self.ball = self.canvas.create_oval(
            WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2 - BALL_SIZE // 2,
            WIDTH // 2 + BALL_SIZE // 2, HEIGHT // 2 + BALL_SIZE // 2,
            fill="red"
        )

        self.ball_dx = 4 * random.choice([-1, 1])
        self.ball_dy = -4

        self.bricks = []
        for r in range(BRICK_ROWS):
            for c in range(BRICK_COLS):
                x1 = c * BRICK_WIDTH
                y1 = r * BRICK_HEIGHT + 30
                x2 = x1 + BRICK_WIDTH - 2
                y2 = y1 + BRICK_HEIGHT - 2
                brick = self.canvas.create_rectangle(x1, y1, x2, y2, fill="blue")
                self.bricks.append(brick)

    def move_left(self, event):
        if self.running:
            self.canvas.move(self.paddle, -20, 0)

    def move_right(self, event):
        if self.running:
            self.canvas.move(self.paddle, 20, 0)

    def update(self):
        if not self.running:
            return

        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        bx1, by1, bx2, by2 = self.canvas.coords(self.ball)

        if bx1 <= 0 or bx2 >= WIDTH:
            self.ball_dx = -self.ball_dx
        if by1 <= 0:
            self.ball_dy = -self.ball_dy
        if by2 >= HEIGHT:
            self.game_over()
            return

        # Paddle collision
        px1, py1, px2, py2 = self.canvas.coords(self.paddle)
        if by2 >= py1 and bx2 >= px1 and bx1 <= px2:
            self.ball_dy = -abs(self.ball_dy)

        # Brick collisions
        for brick in self.bricks:
            bx1, by1, bx2, by2 = self.canvas.coords(self.ball)
            rx1, ry1, rx2, ry2 = self.canvas.coords(brick)
            if bx2 >= rx1 and bx1 <= rx2 and by2 >= ry1 and by1 <= ry2:
                self.canvas.delete(brick)
                self.bricks.remove(brick)
                self.ball_dy = -self.ball_dy
                self.score += 10
                self.canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
                break

        if not self.bricks:
            self.canvas.create_text(WIDTH // 2, HEIGHT // 2, text="YOU WIN!", fill="green", font=("Arial", 24))
            self.running = False
            self.canvas.itemconfigure(self.restart_window, state='normal')
            return

        self.root.after(30, self.update)

    def game_over(self):
        self.canvas.create_text(WIDTH // 2, HEIGHT // 2, text="GAME OVER", fill="red", font=("Arial", 24))
        self.running = False
        self.canvas.itemconfigure(self.restart_window, state='normal')

    def restart_game(self):
        self.canvas.delete("all")
        self.score = 0
        self.running = True
        self.score_text = self.canvas.create_text(10, 10, anchor="nw", fill="white", font=("Arial", 14),
                                                  text=f"Score: {self.score}")
        self.restart_window = self.canvas.create_window(WIDTH // 2, HEIGHT // 2 + 30, window=self.restart_button)
        self.canvas.itemconfigure(self.restart_window, state='hidden')
        self.init_game()
        self.update()

# Run the game
root = tk.Tk()
game = BrickBreaker(root)
root.mainloop()