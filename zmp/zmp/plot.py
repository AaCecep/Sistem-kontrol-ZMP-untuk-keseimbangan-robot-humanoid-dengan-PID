#!/usr/bin/env python3
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import rclpy
from rclpy.node import Node
import time

from my_msg.msg import Data  # pastikan berisi zmp_x, zmp_y, (opsional) area

def plot_dynamic_zmp_area():
    rclpy.init()

    # --- Node Subscriber untuk ambil data dari topik "zmp"
    class _ZmpSub(Node):
        def __init__(self):
            super().__init__('zmp_visualizer_sub')
            self.zmp_x = None
            self.zmp_y = None
            self.area = None
            self.create_subscription(Data, 'zmp', self.cb, 10)

        def cb(self, msg: Data):
            self.zmp_x = float(msg.zmp_x)
            self.zmp_y = float(msg.zmp_y)
            if hasattr(msg, 'area'):
                self.area = float(msg.area)

    node = _ZmpSub()

    # Tunggu data pertama
    print("⏳ Menunggu data pertama dari topik /zmp ...")
    timeout_s = 10.0
    t0 = time.time()
    while rclpy.ok() and (node.zmp_x is None or node.zmp_y is None):
        rclpy.spin_once(node, timeout_sec=0.1)
        if time.time() - t0 > timeout_s:
            print("❌ Timeout: tidak menerima data dari /zmp.")
            node.destroy_node()
            rclpy.shutdown()
            return
    print("✅ Data ZMP pertama diterima!")

    # Data awal
    ZMP_x = node.zmp_x
    ZMP_y = node.zmp_y
    luas = node.area if node.area is not None else 0.02

    # Rasio panjang:lebar 1.5:1
    r = 1.5
    lebar = (luas / r) ** 0.5
    panjang = r * lebar
    bottom_left_x = ZMP_x - panjang / 2.0
    bottom_left_y = ZMP_y - lebar / 2.0

    # --- Inisialisasi plot
    plt.ion()
    fig, ax = plt.subplots()
    rect = patches.Rectangle((bottom_left_x, bottom_left_y), panjang, lebar,
                             linewidth=2, edgecolor='blue', facecolor='lightblue')
    ax.add_patch(rect)

    point_plot, = ax.plot(ZMP_x, ZMP_y, 'ro')
    label = ax.text(ZMP_x, ZMP_y + 0.01 * lebar,
                    f'ZMP ({ZMP_x:.2f}, {ZMP_y:.2f})', ha='center')

    ax.set_xlim(ZMP_x - panjang, ZMP_x + panjang)
    ax.set_ylim(ZMP_y - lebar, ZMP_y + lebar)
    ax.set_aspect('equal')
    ax.set_title(f'Support Polygon (luas ≈ {luas:.4f})')
    ax.grid(True)
    fig.canvas.draw()
    fig.canvas.flush_events()

    # --- Loop utama (update terus)
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.05)

            if node.zmp_x is None or node.zmp_y is None:
                continue

            ZMP_x = node.zmp_x
            ZMP_y = node.zmp_y

            # --- Update rectangle kalau luas berubah ---
            if node.area is not None and node.area != luas:
                luas = node.area
                lebar = (luas / r) ** 0.5
                panjang = r * lebar
                bottom_left_x = ZMP_x - panjang / 2.0
                bottom_left_y = ZMP_y - lebar / 2.0

                rect.remove()  # hapus yang lama
                rect = patches.Rectangle((bottom_left_x, bottom_left_y),
                                         panjang, lebar,
                                         linewidth=2, edgecolor='blue', facecolor='lightblue')
                ax.add_patch(rect)

                ax.set_xlim(ZMP_x - panjang, ZMP_x + panjang)
                ax.set_ylim(ZMP_y - lebar,   ZMP_y + lebar)
                ax.set_title(f'Support Polygon (luas ≈ {luas:.4f})')

            # --- Update titik ZMP ---
            point_plot.set_data(ZMP_x, ZMP_y)
            label.set_position((ZMP_x, ZMP_y + 0.01 * lebar))
            label.set_text(f'ZMP ({ZMP_x:.2f}, {ZMP_y:.2f})')

            # Refresh tampilan
            fig.canvas.draw()
            fig.canvas.flush_events()
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("🛑 Dihentikan oleh pengguna.")
    finally:
        plt.ioff()
        plt.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    plot_dynamic_zmp_area()
