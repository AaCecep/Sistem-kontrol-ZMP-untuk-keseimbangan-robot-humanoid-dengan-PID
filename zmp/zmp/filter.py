#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from my_msg.msg import Data
# from std_msgs.msg import Float32 # <-- Dihapus
import csv, time

class ZmpLogger(Node):
    def __init__(self):
        super().__init__('zmp_logger')

        # === Subscriptions ===
        # Hanya subscribe ke 'zmp'
        self.create_subscription(Data, 'zmp', self.cb_zmp, 10)
        # self.create_subscription(Float32, '/init_x', self.cb_initx, 10) # <-- Dihapus

        # === CSV setup ===
        filename = 'filter.csv'
        self.file = open(filename, 'w', newline='')
        self.writer = csv.writer(self.file)
        # Header CSV diubah sesuai permintaan
        self.writer.writerow([
            'time (s)', 
            'zmp_x', 'zmp_y',
            'zmp_x_lama', 'zmp_y_lama'
        ])
        self.get_logger().info(f"✅ Logger aktif, menyimpan data ke {filename}")

        # === Variabel data ===
        self.start_time = time.time()
        self.last_write_time = 0.0
        self.log_interval = 0.02  # 50 Hz (Logika ini dipertahankan dari skrip asli)

        # Nilai default disederhanakan
        self.zmp_x = 0.0
        self.zmp_y = 0.0
        self.zmp_x_lama = 0.0  # <-- Ditambahkan
        self.zmp_y_lama = 0.0  # <-- Ditambahkan

    # === Callback dari /zmp ===
    def cb_zmp(self, msg):
        # Update semua data yang relevan dari satu pesan ini
        self.zmp_x = msg.zmp_x
        self.zmp_y = msg.zmp_y
        self.zmp_x_lama = msg.zmp_x_lama
        self.zmp_y_lama = msg.zmp_y_lama
        
        # Coba tulis ke CSV (dibatasi oleh log_interval)
        self.write_csv()

    # === Callback dari /init_x ===
    # def cb_initx(self, msg): # <-- Seluruh fungsi dihapus
    #     ...

    # === Tulis CSV setiap interval ===
    def write_csv(self):
        now = time.time()
        # Logika rate-limiting (pembatasan frekuensi log)
        if now - self.last_write_time >= self.log_interval:
            elapsed = now - self.start_time
            # Tulis baris CSV baru dengan data yang sudah disederhanakan
            self.writer.writerow([
                round(elapsed, 3),
                self.zmp_x, self.zmp_y,
                self.zmp_x_lama, self.zmp_y_lama
            ])
            self.last_write_time = now

    # === Tutup file saat node dimatikan ===
    def destroy_node(self):
        self.file.close()
        super().destroy_node()

def main():
    rclpy.init()
    node = ZmpLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("🛑 Logging dihentikan oleh user.")
    finally:
        # Pastikan file ditutup dengan benar saat keluar
        node.file.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()