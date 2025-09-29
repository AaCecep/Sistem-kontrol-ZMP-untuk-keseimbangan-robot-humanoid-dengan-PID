#!/home/robotis/mencoba/bin/python3
import rclpy
from rclpy.node import Node
import cv2
from ultralytics import YOLO
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from geometry_msgs.msg import PointStamped
import time

class OpenVINOYOLO(Node):
    def __init__(self):
        super().__init__('atom_openvino_yolo')
        self.bridge = CvBridge()
        self.image_pub = self.create_publisher(Image, '/openvino/image_processed', 10)
        self.image_sub = self.create_subscription(Image, '/usb_cam_node/image_raw', self.image_callback, 10)

        # Publisher untuk koordinat bola
        self.ball_pub = self.create_publisher(PointStamped, '/bola/koordinat', 10)

        # Load model
        self.model = YOLO('/home/robotis/robotis_ws/src/atom_openvino_yolo/atom_openvino_yolo/best_n_int8_openvino_model/')
        self.classNames = ['bola', 'gawang']

        self.fps_limit = 1.0 / 30
        self.last_time = time.time()
        self.get_logger().info('ATOM OpenVINO YOLO Node Initialized')

    def image_callback(self, msg):
        current_time = time.time()
        if current_time - self.last_time < self.fps_limit:
            return
        self.last_time = current_time

        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        height, width, _ = frame.shape

        results = self.model(frame)

        for r in results:
            boxes = r.boxes
            for box in boxes:
                confidence = box.conf[0]
                if confidence > 0.5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2

                    # Dapatkan label kelas
                    cls = int(box.cls[0])
                    class_name = self.classNames[cls]

                    if class_name == 'bola':
                        point_msg = PointStamped()
                        point_msg.header = msg.header  # gunakan header dari kamera
                        
                        # Normalisasi koordinat ke rentang [-1, 1]
                        point_msg.point.x = (center_x / width) * 2 - 1
                        point_msg.point.y = (center_y / height) * 2 - 1
                        point_msg.point.z = 0.0  
                        print(point_msg.point.x)
                        print(point_msg.point.y)
                        print(point_msg.point.z)
                        self.ball_pub.publish(point_msg)
                        self.get_logger().info(f"Published ball coordinates: ({point_msg.point.x:.2f}, {point_msg.point.y:.2f})")

                    # Visualisasi
                    radius = max((x2 - x1) // 2, (y2 - y1) // 2)
                    cv2.circle(frame, (center_x, center_y), radius, (0, 255, 0), 2)
                    label = f"{class_name} {confidence:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Publish hasil frame yang sudah diproses
        self.image_pub.publish(self.bridge.cv2_to_imgmsg(frame, 'bgr8'))

def main(args=None):
    rclpy.init(args=args)
    node = OpenVINOYOLO()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
