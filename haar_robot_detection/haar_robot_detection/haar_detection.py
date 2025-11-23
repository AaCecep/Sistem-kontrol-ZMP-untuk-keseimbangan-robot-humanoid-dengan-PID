import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import time
import os

from ament_index_python.packages import get_package_share_directory


class HaarRobotDetector(Node):
    def __init__(self):
        super().__init__("haar_detection_node")

        self.get_logger().info("=== Node Deteksi Robot OP3 (Haar Cascade — ROS FIX) ===")

        # === Load Haar Cascade (pakai path dari share directory) ===
        pkg_share = get_package_share_directory("haar_robot_detection")
        cascade_path = os.path.join(pkg_share, "cascade.xml")

        self.robot_cascade = cv2.CascadeClassifier(cascade_path)
        if self.robot_cascade.empty():
            self.get_logger().error(f"Gagal memuat model cascade.xml di: {cascade_path}")
            raise SystemExit

        # Bridge konversi ROS ↔ OpenCV
        self.bridge = CvBridge()

        # Subscribe kamera
        self.subscription = self.create_subscription(
            Image,
            "/image_raw",
            self.image_callback,
            10
        )

        # Publisher status deteksi
        self.pub_status = self.create_publisher(String, "/robot_detection", 10)

        # Hitung FPS
        self.start_time = time.time()
        self.frame_count = 0

        self.get_logger().info("Node siap menerima stream /image_raw ...")

    def image_callback(self, msg):
        # Convert ROS Image → OpenCV BGR
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

        # Preprocessing (disamakan dengan Windows)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        # Deteksi Haar
        robots = self.robot_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=8,
            minSize=(80, 80)
        )

        # Hitung FPS
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0.0

        # Status deteksi
        status = "Robot Tidak Terdeteksi"
        color = (0, 0, 255)

        if len(robots) > 0:
            status = "Robot OP3 Terdeteksi"
            color = (0, 255, 0)
            for (x, y, w, h) in robots:
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        # Overlay
        cv2.putText(frame, status, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Tampilkan hasil
        cv2.imshow("Deteksi Robot Humanoid OP3 — ROS", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.get_logger().info("Keluar tampilan video.")
            rclpy.shutdown()

        # Publish hasil deteksi
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
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
