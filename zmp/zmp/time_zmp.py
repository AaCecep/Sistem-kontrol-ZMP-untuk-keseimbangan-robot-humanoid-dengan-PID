#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from my_msg.msg import Data
from std_msgs.msg import Float32
import time
import matplotlib.pyplot as plt

class ZmpPlotter(Node):
    def __init__(self):
        super().__init__('zmp_plotter')

        # --- Subscriptions ---
        self.create_subscription(Data, 'zmp', self.cb_zmp, 10)
        self.create_subscription(Float32, '/init_x', self.cb_initx, 10)

        # --- Variabel data ---
        self.start_time = time.time()
        self.zmp_x = 0.0
        self.init_x_offset = 0.0
        self.time_data = []
        self.zmp_data = []
        self.offset_data = []
        self.last_update_time = 0.0
        self.update_interval = 0.02  # 50 Hz

        # --- Setup Matplotlib ---
        plt.ion()
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 6))

        # Grafik ZMP
        self.line_zmp, = self.ax1.plot([], [], 'b-', label='ZMP X')
        self.ax1.set_title('ZMP X vs Time')
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('ZMP X')
        self.ax1.grid(True)
        self.ax1.legend()

        # Grafik Offset
        self.line_offset, = self.ax2.plot([], [], 'r-', label='Init X Offset')
        self.ax2.set_title('Init X Offset vs Time')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Init X Offset')
        self.ax2.grid(True)
        self.ax2.legend()

        self.get_logger().info("📈 Plotter aktif — menampilkan grafik dari /zmp dan /init_x")

    # === Callback dari /zmp ===
    def cb_zmp(self, msg):
        self.zmp_x = msg.zmp_x
        self.update_plot_data()

    # === Callback dari /init_x ===
    def cb_initx(self, msg):
        self.init_x_offset = msg.data
        self.update_plot_data()

    # === Update data dan refresh grafik ===
    def update_plot_data(self):
        now = time.time()
        if now - self.last_update_time >= self.update_interval:
            elapsed = now - self.start_time
            self.time_data.append(elapsed)
            self.zmp_data.append(self.zmp_x)
            self.offset_data.append(self.init_x_offset)
            self.last_update_time = now
            self.refresh_plot()

    # === Update tampilan grafik ===
    def refresh_plot(self):
        self.line_zmp.set_data(self.time_data, self.zmp_data)
        self.line_offset.set_data(self.time_data, self.offset_data)

        for ax, ydata in zip([self.ax1, self.ax2], [self.zmp_data, self.offset_data]):
            ax.relim()
            ax.autoscale_view()

        plt.pause(0.001)

def main():
    rclpy.init()
    node = ZmpPlotter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("🛑 Plot dihentikan oleh user.")
    finally:
        rclpy.shutdown()
        plt.ioff()
        plt.show()

if __name__ == '__main__':
    main()
