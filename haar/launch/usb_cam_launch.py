from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='usb_cam',
            executable='usb_cam_node_exe',
            name='usb_cam',
            output='screen',
            parameters=[{
                # === Device Kamera ===
                'video_device': '/dev/video0',

                # === Resolusi & FPS ===
                'image_width': 640,
                'image_height': 480,
                'framerate': 30.0,

                # === Format Paling Stabil (anti crash) ===
                # MJPEG sering crash saat mmap -> gunakan YUYV dulu
                'pixel_format': 'yuyv',

                # === PENGATURAN AGAR GAMBAR TERANG ===
                # Matikan auto exposure
                'auto_exposure': False,

                # Exposure manual (nilai 200–400 sangat terang)
                # 300 = recommended
                'exposure_time_absolute': 300,  

                # Naikkan brightness (default 50)
                'brightness': 150,

                # Gain untuk menambah cahaya (default -1 / tidak diset)
                'gain': 80,

                # White balance auto (biarkan aktif)
                'white_balance_automatic': True,

                # (Opsional, kalau kamera support)
                'focus_automatic_continuous': False,
            }]
        )
    ])
