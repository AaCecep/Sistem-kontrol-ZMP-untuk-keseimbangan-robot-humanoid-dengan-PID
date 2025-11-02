#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from my_msg.msg import Data
from std_msgs.msg import Float32
import csv, time

class ZmpLogger(Node):
    def __init__(self):
        super().__init__('zmp_logger')

        # --- Subscriptions ---
        self.create_subscription(Data, 'zmp', self.cb_zmp, 10)
        self.create_subscription(Float32, '/init_x', self.cb_initx, 10)

        # --- CSV setup ---
        filename = 'zmp.csv'
        self.file = open(filename, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(['time (s)', 'zmp_x', 'init_x_offset'])
        self.get_logger().info(f"✅ Logger aktif, menyimpan data ke {filename}")

        # --- Variabel data ---
        self.start_time = time.time()
        self.zmp_x = 0.0
        self.init_x_offset = 0.0
        self.last_write_time = 0.0
        self.log_interval = 0.02  # 50 Hz

    # === Callback dari /zmp ===
    def cb_zmp(self, msg):
        self.zmp_x = msg.zmp_x
        self.write_csv()

    # === Callback dari /init_x ===
    def cb_initx(self, msg):
        self.init_x_offset = msg.data
        self.write_csv()

    # === Tulis CSV setiap interval ===
    def write_csv(self):
        now = time.time()
        if now - self.last_write_time >= self.log_interval:
            elapsed = now - self.start_time
            self.writer.writerow([round(elapsed, 3), self.zmp_x, self.init_x_offset])
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
        node.file.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
