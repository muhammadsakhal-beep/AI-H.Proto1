"""
drone_sim.py
Simulasi AI Drone Penjaga Rumah (2D)
Python 3.12 + Pygame
"""

import pygame
import random
import math

# =========================
#  KONFIGURASI DASAR
# =========================
WIDTH, HEIGHT = 800, 600
FPS = 30
NUM_PEOPLE = 15
NUM_DRONES = 2
THREAT_THRESHOLD = 0.66

# =========================
#  WARNA
# =========================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 50, 50)
BLUE = (0, 120, 255)
CYAN = (0, 255, 255)

# =========================
#  KELAS PERSON (ORANG)
# =========================
class Person:
    def __init__(self):
        self.x = random.randint(50, WIDTH - 50)
        self.y = random.randint(50, HEIGHT - 50)
        self.threat = random.random()
        self.caught = False

    def move(self):
        if self.caught:
            return
        dx, dy = random.choice([-2, -1, 0, 1, 2]), random.choice([-2, -1, 0, 1, 2])
        self.x = min(max(0, self.x + dx), WIDTH)
        self.y = min(max(0, self.y + dy), HEIGHT)

    def color(self):
        if self.caught:
            return (100, 100, 100)
        if self.threat <= 0.33:
            return GREEN
        elif self.threat <= 0.66:
            return YELLOW
        else:
            return RED

# =========================
#  KELAS DRONE
# =========================
class Drone:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.speed = 4
        self.target = None

    def scan(self, people):
        visible_threats = [
            p for p in people if not p.caught and p.threat > THREAT_THRESHOLD
        ]
        if not visible_threats:
            self.target = None
            return
        # cari target terdekat
        nearest = min(
            visible_threats, key=lambda p: math.hypot(p.x - self.x, p.y - self.y)
        )
        self.target = nearest

    def move(self):
        if self.target is None or self.target.caught:
            # patroli acak
            self.x += random.choice([-2, -1, 0, 1, 2])
            self.y += random.choice([-2, -1, 0, 1, 2])
        else:
            # kejar target
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.x += self.speed * dx / dist
                self.y += self.speed * dy / dist
            # jika sudah dekat, tangkap target
            if dist < 10:
                self.target.caught = True
                print(
                    f"[INFO] Drone menangkap target di ({int(self.target.x)}, {int(self.target.y)})"
                )
                self.target = None

        # pastikan tetap di dalam layar
        self.x = max(0, min(WIDTH, self.x))
        self.y = max(0, min(HEIGHT, self.y))

# =========================
#  SETUP PYGAME
# =========================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulasi Drone AI Penjaga Rumah")
clock = pygame.time.Clock()

# =========================
#  OBJEK SIMULASI
# =========================
people = [Person() for _ in range(NUM_PEOPLE)]
drones = [
    Drone(WIDTH // (NUM_DRONES + 1) * (i + 1), HEIGHT // 2)
    for i in range(NUM_DRONES)
]

font = pygame.font.SysFont("Arial", 18)

# =========================
#  LOOP UTAMA
# =========================
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    # Update & gambar orang
    for p in people:
        p.move()
        pygame.draw.circle(screen, p.color(), (int(p.x), int(p.y)), 6)

    # Update & gambar drone
    for d in drones:
        d.scan(people)
        d.move()
        color = CYAN if d.target else BLUE
        pygame.draw.rect(screen, color, pygame.Rect(d.x - 5, d.y - 5, 10, 10))

    # Teks status
    active_threats = len([p for p in people if not p.caught and p.threat > THREAT_THRESHOLD])
    text = font.render(
        f"Drones: {len(drones)} | People: {len(people)} | Threat Aktif: {active_threats}",
        True,
        WHITE,
    )
    screen.blit(text, (10, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
