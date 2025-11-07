# sim.py
"""
Simulator yang menggunakan DroneBrain (brain.py).
Grid tile-based; zones: protected_zone dan safe_zone.
Perilaku:
- Bila person berbahaya & masuk protected_zone -> drone akan lock + pursue (serang).
- Bila person berbahaya & BELUM masuk protected_zone -> drone hanya WARN (broadcast), tidak pursue.
File ini menjalankan pygame UI grid kotak-kotak.
"""

import pygame
import random
import math
import time
from brain import DroneBrain

# ---------- Konfigurasi Grid ----------
CELL_SIZE = 28
GRID_W = 28   # jumlah kolom
GRID_H = 20   # jumlah baris
WIDTH = CELL_SIZE * GRID_W
HEIGHT = CELL_SIZE * GRID_H + 80  # extra top UI
FPS = 20

NUM_PEOPLE = 12
NUM_DRONES = 3
THREAT_THRESHOLD = 0.66

# colors
WHITE = (255,255,255)
BLACK = (10,10,10)
GRAY = (140,140,140)
GREEN = (50,200,50)
YELLOW = (240,210,50)
RED = (220,40,40)
DRONE_BLUE = (60,130,220)
DRONE_LOCK = (0,200,200)
PROTECTED_COLOR = (180,40,40, 80)  # not used directly; draw as rect

# ---------- Utility ----------
def clamp(v,a,b): return max(a,min(b,v))

# ---------- Entities ----------
class Person:
    def __init__(self, pid):
        self.id = pid
        self.cell_x = random.randrange(1, GRID_W-1)
        self.cell_y = random.randrange(4, GRID_H-1)  # keep top rows for UI
        self.threat = random.random()
        self.caught = False

    def move(self):
        if self.caught:
            return
        dx, dy = random.choice([(0,1),(1,0),(-1,0),(0,-1),(0,0)])
        self.cell_x = clamp(self.cell_x + dx, 0, GRID_W-1)
        self.cell_y = clamp(self.cell_y + dy, 2, GRID_H-1)

class Drone:
    def __init__(self, did, cell_x, cell_y, shared_targets):
        self.id = did
        self.cell_x = cell_x
        self.cell_y = cell_y
        self.shared_targets = shared_targets
        self.brain = DroneBrain(drone_id=did, shared_targets=shared_targets, scan_cells=4, threshold=THREAT_THRESHOLD)
        # for smooth pos in px
        self.px = cell_x * CELL_SIZE + CELL_SIZE//2
        self.py = cell_y * CELL_SIZE + CELL_SIZE//2
        self.speed = 6.0  # pixels per tick
        self.locked_pid = None

    def update(self, people, protected_zone):
        # call brain.decide using grid cells
        drone_cell = (self.cell_x, self.cell_y)
        action = self.brain.decide(drone_cell, people, protected_zone)
        # if brain locked a target for pursuit, update local locked_pid
        self.locked_pid = self.brain.target_id

        # If we have a locked target to pursue, move toward that person's cell center
        if self.locked_pid:
            p = next((x for x in people if x.id == self.locked_pid), None)
            if p is None:
                self.brain.release_lock(self.locked_pid)
                self.locked_pid = None
                return action
            # compute target pixel pos
            tx = p.cell_x * CELL_SIZE + CELL_SIZE//2
            ty = p.cell_y * CELL_SIZE + CELL_SIZE//2
            # move toward tx,ty with simple steering
            dx = tx - self.px
            dy = ty - self.py
            dist = math.hypot(dx,dy) + 1e-6
            step = min(self.speed, dist)
            self.px += (dx/dist) * step
            self.py += (dy/dist) * step
            # update cell position when center crossed
            self.cell_x = int(self.px // CELL_SIZE)
            self.cell_y = int((self.py - 80) // CELL_SIZE) if self.py >= 80 else self.cell_y
            # capture if reached cell center
            if dist < 6:
                # mark caught
                p.caught = True
                # inform brain registry
                self.brain.capture_occurred(p.id)
                self.locked_pid = None
            return action
        else:
            # patrol randomly (move cell by cell occasionally)
            if random.random() < 0.3:
                dx, dy = random.choice([(0,1),(1,0),(-1,0),(0,-1),(0,0)])
                self.cell_x = clamp(self.cell_x + dx, 0, GRID_W-1)
                self.cell_y = clamp(self.cell_y + dy, 2, GRID_H-1)
                # snap pixel pos to cell center
                self.px = self.cell_x * CELL_SIZE + CELL_SIZE//2
                self.py = self.cell_y * CELL_SIZE + CELL_SIZE//2
            return action

# ---------- Zones ----------
# protected_zone: rectangle in cell coords (x1,y1,x2,y2)
PROTECTED_ZONE = (10, 8, 17, 15)  # example: a rectangle near center

# ---------- Pygame Drawing ----------
def draw_grid(screen):
    for gx in range(GRID_W):
        for gy in range(GRID_H):
            rect = pygame.Rect(gx*CELL_SIZE, gy*CELL_SIZE + 80, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (30,30,30), rect, 1)

def draw_zone(screen, zone, color=(180,40,40,60)):
    x1,y1,x2,y2 = zone
    rect = pygame.Rect(x1*CELL_SIZE, y1*CELL_SIZE + 80, (x2-x1+1)*CELL_SIZE, (y2-y1+1)*CELL_SIZE)
    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    s.fill((180,40,40,60))
    screen.blit(s, (rect.x, rect.y))
    pygame.draw.rect(screen, (180,40,40), rect, 2)

def draw_entities(screen, people, drones, shared_targets, font):
    # people
    for p in people:
        px = p.cell_x*CELL_SIZE + CELL_SIZE//2
        py = p.cell_y*CELL_SIZE + CELL_SIZE//2 + 80
        col = GREEN if p.threat <= 0.33 else YELLOW if p.threat <= 0.66 else RED
        if p.caught:
            col = (100,100,100)
        pygame.draw.rect(screen, col, pygame.Rect(px-8, py-8, 16, 16))
        lbl = font.render(p.id, True, WHITE)
        screen.blit(lbl, (px+10, py-10))
        # threat bar
        bar_w = 24
        pygame.draw.rect(screen, (50,50,50), (px - bar_w//2, py+10, bar_w, 4))
        pygame.draw.rect(screen, (0,255,0), (px - bar_w//2, py+10, int(bar_w * p.threat), 4))

    # drones
    for d in drones:
        px = int(d.px)
        py = int(d.py)
        color = DRONE_LOCK if d.locked_pid else DRONE_BLUE
        pygame.draw.rect(screen, color, pygame.Rect(px-10, py-10, 20, 20))
        lbl = font.render(d.id, True, WHITE)
        screen.blit(lbl, (px-10, py-26))
        # draw scan range (faint)
        s = pygame.Surface((d.brain.scan_cells*2*CELL_SIZE, d.brain.scan_cells*2*CELL_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(s, (60,60,60,18), (d.brain.scan_cells*CELL_SIZE, d.brain.scan_cells*CELL_SIZE), d.brain.scan_cells*CELL_SIZE)
        screen.blit(s, (px - d.brain.scan_cells*CELL_SIZE, py - d.brain.scan_cells*CELL_SIZE))

    # shared targets list
    y0 = 12
    x0 = 8
    label = font.render("Shared Targets:", True, WHITE)
    screen.blit(label, (WIDTH - 360, y0))
    i = 1
    for tid, info in shared_targets.items():
        line = f"{tid} pos={info['pos']} locked_by={info.get('locked_by')} warn={info.get('warning_only')}"
        txt = font.render(line, True, WHITE)
        screen.blit(txt, (WIDTH - 360, y0 + 18*i))
        i += 1

# ---------- Main ----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Grid Drone Simulator (brain separated)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 14)

    # init entities
    people = [Person(f"P{i}") for i in range(NUM_PEOPLE)]
    shared_targets = {}
    drones = []
    for i in range(NUM_DRONES):
        cx = int((i+1) * GRID_W / (NUM_DRONES+1))
        cy = 3
        drones.append(Drone(f"D{i}", cx, cy, shared_targets))

    running = True

    while running:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                mx,my = pygame.mouse.get_pos()
                # map click to cell
                if my >= 80:
                    cell_x = mx // CELL_SIZE
                    cell_y = (my - 80) // CELL_SIZE
                    # nearest person?
                    nearest = None; nd = 9999
                    for p in people:
                        d = abs(p.cell_x - cell_x) + abs(p.cell_y - cell_y)
                        if d < nd:
                            nd = d; nearest = p
                    if nearest and nd <= 1:
                        # toggle threat up
                        nearest.threat = min(1.0, nearest.threat + 0.25)
                        print(f"[USER] raise threat {nearest.id} -> {nearest.threat:.2f}")
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    # spawn new person
                    pid = f"P{len(people)}"
                    p = Person(pid)
                    people.append(p)
                    print(f"[USER] spawn {p.id}")

        # update people
        for p in people:
            p.move()
            if p.caught and p.id in shared_targets:
                # remove from shared_targets when captured
                del shared_targets[p.id]

        # update drones (brain + movement)
        for d in drones:
            action = d.update(people, PROTECTED_ZONE)
            # optionally log
            # print(f"[{d.id}] {action}")

        # cleanup stale shared_targets older than 20s (and not locked)
        now = time.time()
        to_remove = []
        for tid, info in list(shared_targets.items()):
            if now - info.get("ts", now) > 20 and info.get("locked_by") is None:
                to_remove.append(tid)
        for tid in to_remove:
            del shared_targets[tid]

        # draw world
        screen.fill(BLACK)
        # top UI area
        pygame.draw.rect(screen, (40,40,40), (0,0, WIDTH, 80))
        title = font.render("Protected Zone: red rectangle. Click near person to raise threat. SPACE to spawn.", True, WHITE)
        screen.blit(title, (8,8))
        # grid
        draw_grid(screen)
        # zone
        draw_zone(screen, PROTECTED_ZONE)
        # entities
        draw_entities(screen, people, drones, shared_targets, font)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
