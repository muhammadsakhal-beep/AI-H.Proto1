"""
drone_security_sim.py
Simulasi Drone AI Penjaga Rumah 2D Interaktif
Python 3.12 + Pygame
"""

import pygame
import random
import math
import csv
from datetime import datetime

# --- KONFIGURASI DASAR ---
WIDTH, HEIGHT = 900, 600
FPS = 30
SAFE_ZONE = (300, 200, 300, 200)

# --- WARNA ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
RED = (255, 50, 50)
BLUE = (0, 120, 255)
GRAY = (100, 100, 100)

# --- PYGAME SETUP ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulasi Drone AI Penjaga Rumah (2D)")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 18)

# --- LOG SETUP ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"log_drone_sim_{timestamp}.csv"
with open(LOG_FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["tick", "event", "detail"])
    writer.writeheader()

# --- OBJEK DASAR ---
class Entity:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.color = color
        self.caught = False

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x - 5, self.y - 5, 10, 10))

    def distance_to(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)


class Person(Entity):
    def __init__(self, x, y, status="green"):
        super().__init__(x, y, GREEN if status == "green" else
                         (YELLOW if status == "yellow" else RED))
        self.status = status
        self.speed = 2

    def move(self):
        if self.caught:
            return
        dx, dy = random.choice([-1, 0, 1]), random.choice([-1, 0, 1])
        self.x = min(max(10, self.x + dx * self.speed), WIDTH - 10)
        self.y = min(max(10, self.y + dy * self.speed), HEIGHT - 10)

    def update_color(self):
        if self.status == "green":
            self.color = GREEN
        elif self.status == "yellow":
            self.color = YELLOW
        elif self.status == "red":
            self.color = RED


class Police(Entity):
    def __init__(self, x, y, target):
        super().__init__(x, y, BLACK)
        self.speed = 4
        self.target = target

    def move(self):
        if not self.target:
            return
        dx, dy = self.target.x - self.x, self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 2:
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist
        else:
            self.target.caught = True
            return True  # sudah menangkap


class Drone(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, BLUE)
        self.home_x, self.home_y = x, y
        self.speed = 3
        self.target = None
        self.state = "IDLE"

    def in_safe_zone(self, target):
        zx, zy, zw, zh = SAFE_ZONE
        return zx <= target.x <= zx + zw and zy <= target.y <= zy + zh

    def move_toward(self, target):
        dx, dy = target.x - self.x, target.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist

    def return_home(self):
        home = Entity(self.home_x, self.home_y, BLUE)
        if self.distance_to(home) > 5:
            self.move_toward(home)
        else:
            self.state = "IDLE"

    def act(self, people, polices, tick):
        # Cari ancaman merah
        reds = [p for p in people if p.status == "red" and not p.caught]
        yellows = [p for p in people if p.status == "yellow" and not p.caught]

        if self.state == "IDLE":
            # Jika ada merah, serang
            if reds:
                self.target = reds[0]
                self.state = "ATTACK"
                print("[INFO] Drone menyerang penjahat!")
            elif yellows:
                for y in yellows:
                    if self.in_safe_zone(y):
                        self.target = y
                        self.state = "FOLLOW"
                        break

        if self.state == "FOLLOW" and self.target:
            if not self.in_safe_zone(self.target):
                self.target = None
                self.state = "RETURN"
            else:
                self.move_toward(self.target)
                if random.random() < 0.01:
                    print("[INFO] Drone mengikuti orang yang diawasi...")

        elif self.state == "ATTACK" and self.target:
            self.move_toward(self.target)
            if self.distance_to(self.target) < 10:
                self.target.caught = True
                self.state = "WAIT_POLICE"
                polices.append(Police(self.x, self.y, self.target))
                print("[INFO] Drone menangkap penjahat, memanggil polisi.")
                with open(LOG_FILE, "a", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=["tick", "event", "detail"])
                    writer.writerow({"tick": tick, "event": "catch", "detail": "Drone menangkap penjahat"})

        elif self.state == "WAIT_POLICE":
            # Drone menunggu polisi sampai menangkap target
            caught_target = any(p.caught for p in people if p.status == "red")
            if caught_target:
                self.state = "RETURN"
                print("[INFO] Polisi sudah menangkap, drone kembali.")

        elif self.state == "RETURN":
            self.return_home()

        elif self.state == "IDLE":
            # Drone tetap di area aman
            pass


# --- FUNGSI UTILITAS ---
def in_safe_zone(entity):
    zx, zy, zw, zh = SAFE_ZONE
    return zx <= entity.x <= zx + zw and zy <= entity.y <= zy + zh


def maybe_change_yellow_status(person):
    """Ketika kuning masuk zona aman, ubah status"""
    if person.status == "yellow" and in_safe_zone(person):
        roll = random.random()
        if roll < 0.3:
            person.status = "red"
        elif roll < 0.6:
            person.status = "green"
        else:
            person.status = "yellow"
        person.update_color()


# --- INISIALISASI AWAL ---
people = [
    Person(random.randint(100, 800), random.randint(100, 500), "red"),
    *[Person(random.randint(100, 800), random.randint(100, 500), "yellow") for _ in range(3)],
    *[Person(random.randint(100, 800), random.randint(100, 500), "green") for _ in range(2)]
]
drones = [Drone(SAFE_ZONE[0] + 100, SAFE_ZONE[1] + 100),
          Drone(SAFE_ZONE[0] + 200, SAFE_ZONE[1] + 150)]
polices = []

# Tombol spawn
def draw_buttons():
    buttons = {
        "Spawn Hijau": (50, 550, GREEN),
        "Spawn Kuning": (200, 550, YELLOW),
        "Spawn Merah": (350, 550, RED),
        "Spawn Drone": (500, 550, BLUE)
    }
    for text, (x, y, color) in buttons.items():
        pygame.draw.rect(screen, color, (x, y, 120, 30))
        label = font.render(text, True, BLACK)
        screen.blit(label, (x + 5, y + 5))
    return buttons


# --- LOOP UTAMA ---
tick = 0
running = True
while running:
    tick += 1
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Klik tombol spawn
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if 50 <= mx <= 170 and 550 <= my <= 580:
                people.append(Person(random.randint(50, 850), random.randint(50, 500), "green"))
            elif 200 <= mx <= 320 and 550 <= my <= 580:
                people.append(Person(random.randint(50, 850), random.randint(50, 500), "yellow"))
            elif 350 <= mx <= 470 and 550 <= my <= 580:
                people.append(Person(random.randint(50, 850), random.randint(50, 500), "red"))
            elif 500 <= mx <= 620 and 550 <= my <= 580:
                drones.append(Drone(SAFE_ZONE[0] + random.randint(50, 250),
                                    SAFE_ZONE[1] + random.randint(50, 150)))

    # Update entitas
    for p in people:
        p.move()
        maybe_change_yellow_status(p)
        p.update_color()

    for d in drones:
        d.act(people, polices, tick)

    for pol in polices[:]:
        done = pol.move()
        if done:
            print("[INFO] Polisi menangkap penjahat dan keluar.")
            polices.remove(pol)
            # Hapus target yang ditangkap
            people = [p for p in people if not p.caught]

    # --- DRAW ---
    screen.fill(GRAY)
    pygame.draw.rect(screen, (0, 80, 0), SAFE_ZONE, 3)
    for p in people:
        p.draw()
    for d in drones:
        d.draw()
    for pol in polices:
        pol.draw()

    draw_buttons()
    info = font.render(f"Tick: {tick} | Drone: {len(drones)} | Orang: {len(people)} | Polisi: {len(polices)}",
                       True, WHITE)
    screen.blit(info, (10, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
print(f"[INFO] Simulasi selesai. Log tersimpan di {LOG_FILE}")
