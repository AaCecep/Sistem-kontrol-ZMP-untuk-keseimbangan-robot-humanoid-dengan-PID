import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data  # ✅ QoS untuk kamera
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

        # Load cascade dari share package
        pkg_share = get_package_share_directory("haar_robot_detection")
        cascade_path = os.path.join(pkg_share, "cascade.xml")

        self.robot_cascade = cv2.CascadeClassifier(cascade_path)
        if self.robot_cascade.empty():
            self.get_logger().error(f"Gagal memuat model cascade.xml di: {cascade_path}")
            raise SystemExit

        self.bridge = CvBridge()

        # ✅ Subscribe dengan QoS sensor_data (Best Effort)
        self.subscription = self.create_subscription(
            Image,
            "/image_raw",
            self.image_callback,
            qos_profile_sensor_data
        )

        self.pub_status = self.create_publisher(String, "/robot_detection", 10)

        self.start_time = time.time()
        self.frame_count = 0

        self.get_logger().info("Node siap menerima stream /image_raw ...")

    def image_callback(self, msg):
        try:
            # ✅ lebih aman: terima apa adanya dulu
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
        except Exception as e:
            self.get_logger().warn(f"Gagal konversi frame: {e}")
            return

        if frame is None or frame.size == 0:
            self.get_logger().warn("Frame kosong diterima.")
            return

        # Kalau frame 1 channel (grayscale), langsung pakai
        if len(frame.shape) == 2:
            gray = frame
        else:
            # Kalau frame 3 channel, ubah ke grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        gray = cv2.equalizeHist(gray)

        robots = self.robot_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=8,
            minSize=(80, 80)
        )

        self.frame_count += 1
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0.0

        status = "Robot Tidak Terdeteksi"
        color = (0, 0, 255)

        # kalau deteksi ada, gambar bbox di frame warna (kalau ada)
        if len(robots) > 0:
            status = "Robot OP3 Terdeteksi"
            color = (0, 255, 0)
            for (x, y, w, h) in robots:
                if len(frame.shape) == 2:
                    # kalau frame grayscale, bikin frame display BGR
                    disp = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    frame = disp
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        # Overlay teks
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        cv2.putText(frame, status, (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Deteksi Robot Humanoid OP3 — ROS", frame)
        cv2.waitKey(1)

        msg_out = String()
        msg_out.data = status
        self.pub_status.publish(msg_out)


def main(args=None):
    rclpy.init(args=args)
    node = HaarRobotDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
