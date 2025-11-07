# --- EyeXSimulator.py ---

import pygame
import time
from DroneBrain import DroneBrain # Mengimpor Logika Otak

# --- Konfigurasi Pygame ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Eye X Drone Simulator - Modular")

# Warna & Font
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
FONT = pygame.font.Font(None, 36)

# Inisialisasi Otak Drone
drone_brain = DroneBrain()

# --- Fungsi Gambar UI ---
def draw_button(x, y, w, h, text, color):
    pygame.draw.rect(screen, color, (x, y, w, h))
    text_surface = FONT.render(text, True, BLACK)
    text_rect = text_surface.get_rect(center=(x + w // 2, y + h // 2))
    screen.blit(text_surface, text_rect)

# --- Fungsi Penanganan Input (Mouse) ---
def handle_input(pos):
    # Logika dikirim ke Otak Drone
    if drone_brain.get_status() == "ALERT":
        # Area Tombol SERANG (650, 500)
        if 650 <= pos[0] <= 780 and 500 <= pos[1] <= 550:
            drone_brain.process_owner_command("SERANG")
        # Area Tombol ABAIKAN (500, 500)
        elif 500 <= pos[0] <= 630 and 500 <= pos[1] <= 550:
            drone_brain.process_owner_command("ABAIKAN")

# --- Loop Utama Badang Drone (Pygame) ---
running = True
clock = pygame.time.Clock()

while running:
    current_time = time.time()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            handle_input(event.pos)

    # 1. Update Otak Drone
    drone_brain.update_status(current_time, SCREEN_WIDTH, SCREEN_HEIGHT)

    # 2. Gambar Background (Simulasi Video Feed)
    screen.fill((50, 50, 70))
    pygame.draw.rect(screen, GRAY, (50, 50, 700, 400), 1)

    # 3. Gambar Objek Simulasi (dari Otak Drone)
    sim_object_rect = drone_brain.get_sim_object()
    if sim_object_rect is not None:
        # Gambar kotak pembatas
        pygame.draw.rect(screen, YELLOW, sim_object_rect, 2)
        # Teks label
        person_text = FONT.render("PERSON (SIMULATED)", True, YELLOW)
        screen.blit(person_text, (sim_object_rect.x, sim_object_rect.y - 20))

    # 4. Gambar UI Status dan Tombol
    
    # Status Teks
    current_status = drone_brain.get_status()
    status_color = RED if current_status in ["ALERT", "ATTACKING"] else GREEN
    status_text = FONT.render(f"DRONE STATUS: {current_status}", True, status_color)
    screen.blit(status_text, (10, SCREEN_HEIGHT - 80))

    # Tampilkan Tombol Kontrol hanya saat ALERT
    if current_status == "ALERT":
        draw_button(650, 500, 130, 50, "SERANG", RED)
        draw_button(500, 500, 130, 50, "ABAIKAN", GREEN)

    pygame.display.flip()
    clock.tick(60)

# --- Penutupan ---
pygame.quit()
print("Sistem Eye X Nonaktif.")