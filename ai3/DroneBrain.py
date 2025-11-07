# --- DroneBrain.py ---

import time
import random

class DroneBrain:
    """Mengelola status drone dan logika deteksi/keputusan."""
    
    # Status yang mungkin
    STATUS = ["STANDBY", "FOLLOWING", "ALERT", "ATTACKING"]
    
    def __init__(self):
        self.status = "STANDBY"
        self.sim_person_rect = None # Objek simulasi (posisi)
        self.sim_object_timer = 0
        self.last_alert_time = time.time()
        self.alert_interval = 10 # 10 detik konsistensi dianggap bahaya

    def update_status(self, current_time, screen_width, screen_height):
        """Logika utama untuk memperbarui status drone."""
        
        # Inisialisasi: Coba 'temukan' objek jika STANDBY
        if self.status == "STANDBY" and self.sim_person_rect is None:
            if random.randint(1, 150) == 1:
                # Objek 'muncul' di sekitar batas bawah layar
                self.sim_person_rect = pygame.Rect(random.randint(50, screen_width - 150), screen_height - 150, 50, 100)
                self.status = "FOLLOWING"
                self.sim_object_timer = current_time
                print("LOGIKA: Orang asing terdeteksi. Beralih ke FOLLOWING.")
                
        # Logika KETIKA objek terdeteksi
        if self.sim_person_rect is not None:
            # Transisi ke ALERT (Simulasi Bahaya Konsisten)
            if self.status == "FOLLOWING" and (current_time - self.sim_object_timer) > self.alert_interval:
                self.status = "ALERT"
                self.last_alert_time = current_time
                print(f"LOGIKA: Gerakan Konsisten. Mengirim Notifikasi ALERT! ({time.ctime()})")
            
            # Logika Pergerakan Simulasi
            if self.status in ["FOLLOWING", "ALERT"]:
                # Pergerakan acak dalam batas
                self.sim_person_rect.x += random.choice([-1, 0, 1]) * 2
                self.sim_person_rect.y += random.choice([-1, 0, 1]) * 2
                
            # Logika Objek Keluar Batas
            if self.sim_person_rect.x < 0 or self.sim_person_rect.x > screen_width or \
               self.sim_person_rect.y < 0 or self.sim_person_rect.y > screen_height:
                self.reset_to_standby()
                print("LOGIKA: Objek keluar batas. Kembali ke STANDBY.")
        
        # Logika Aksi ATTACKING selesai
        if self.status == "ATTACKING":
            if (current_time - self.last_alert_time) > 3: # Simulasi aksi 3 detik
                self.reset_to_standby()
                print("LOGIKA: Aksi Pertahanan Selesai. Kembali ke STANDBY.")
        
        # Logika Objek Hilang (Kembali ke STANDBY jika FOLLOWING dan objek hilang)
        # (Tambahan: Jika objek hilang secara acak)
        elif self.status == "FOLLOWING" and random.randint(1, 300) == 1:
             self.reset_to_standby()
             print("LOGIKA: Objek hilang. Kembali ke STANDBY.")


    def process_owner_command(self, command):
        """Memproses perintah SERANG atau ABAIKAN dari pemilik."""
        if self.status == "ALERT":
            if command == "SERANG":
                self.status = "ATTACKING"
                self.last_alert_time = time.time() # Reset timer untuk durasi attack
                print("LOGIKA: Perintah SERANG diterima!")
            elif command == "ABAIKAN":
                self.status = "FOLLOWING" # Kembali ke following, menunggu jika masih ada
                print("LOGIKA: Perintah ABAIKAN diterima. Melanjutkan FOLLOWING.")

    def reset_to_standby(self):
        """Mengatur ulang semua variabel ke kondisi awal."""
        self.status = "STANDBY"
        self.sim_person_rect = None
        self.sim_object_timer = 0

    def get_status(self):
        return self.status

    def get_sim_object(self):
        return self.sim_person_rect
    
# Catatan: Perintah 'pygame' harus diimpor di file utama untuk digunakan oleh self.sim_person_rect
import pygame # Tambahkan impor pygame di sini karena Rect membutuhkan pygame