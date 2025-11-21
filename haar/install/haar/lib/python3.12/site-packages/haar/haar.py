import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import time
import os
import numpy as np


class HaarRobotDetector(Node):
    def __init__(self):
        super().__init__('haar_robot_detector')

        self.get_logger().info("=== Node Deteksi Robot OP3 (Haar Cascade Saja) ===")

        # === Path model Haar Cascade ===
        cascade_path = os.path.expanduser("~/robotis_ws/src/haar/haar/cascade.xml")
        self.robot_cascade = cv2.CascadeClassifier(cascade_path)
        if self.robot_cascade.empty():
            self.get_logger().error(f"Gagal memuat model Haar Cascade di: {cascade_path}")
            raise SystemExit

        # === Bridge konversi ROS Image <-> OpenCV ===
        self.bridge = CvBridge()

        # === Subscribe kamera ===
        self.subscription = self.create_subscription(
            Image,
            '/image_raw',
            self.image_callback,
            10
        )

        # === Publisher status deteksi ===
        self.pub_status = self.create_publisher(String, '/robot_detection', 10)

        # === Variabel FPS ===
        self.start_time = time.time()
        self.frame_count = 0

        self.get_logger().info("Node aktif dan menunggu feed dari /image_raw ...")

    def image_callback(self, msg):
        # Konversi ROS -> OpenCV
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

        # === Preprocessing standar: grayscale saja ===
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # === ROI di bagian bawah frame ===
        height, width = gray.shape
        roi_y_start = int(height * 0.4)
        roi = gray[roi_y_start:height, 0:width]

        # === Deteksi Haar Cascade ===
        robots = self.robot_cascade.detectMultiScale(
            roi,
            scaleFactor=1.05,
            minNeighbors=8,
            minSize=(60, 60)
        )

        # === Hitung FPS ===
        self.frame_count += 1
        elapsed_time = time.time() - self.start_time
        fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0.0

        status = "Robot Tidak Terdeteksi"
        color = (0, 0, 255)

        # === Gambar bounding box ===
        if len(robots) > 0:
            status = "Robot OP3 Terdeteksi"
            color = (0, 255, 0)
            for (x, y, w, h) in robots:
                y += roi_y_start
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        # === Overlay teks ===
        cv2.putText(frame, status, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # === Tampilkan frame ===
        cv2.imshow("Deteksi Robot Humanoid OP3", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.get_logger().info("Keluar dari tampilan video.")
            rclpy.shutdown()

        # === Publish status ===
        msg_out = String()
        msg_out.data = status
        self.pub_status.publish(msg_out)

    def destroy_node(self):
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = HaarRobotDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Node dihentikan oleh pengguna.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
