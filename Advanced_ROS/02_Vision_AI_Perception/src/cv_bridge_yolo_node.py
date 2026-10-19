#!/usr/bin/env python3
"""
Tutorial 02: ROS 2 Computer Vision & AI Perception Node
Subscribes to sensor_msgs/Image, converts to OpenCV format with cv_bridge,
performs object detection inference, and publishes 2D/3D detections.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge, CvBridgeError
import json


class YoloPerceptionNode(Node):
    def __init__(self):
        super().__init__('yolo_perception_node')

        self.bridge = CvBridge()

        # Subscribe to camera feed
        self.sub_camera = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        # Publish detected objects JSON / bounding boxes
        self.pub_detections = self.create_publisher(
            String,
            '/perception/detected_objects',
            10
        )

        self.get_logger().info('👁️ [YoloPerceptionNode] Vision & AI Perception Pipeline ready.')

    def image_callback(self, msg: Image):
        try:
            # Convert ROS Image to OpenCV BGR8
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as e:
            self.get_logger().error(f'cv_bridge conversion error: {e}')
            return

        height, width, _ = cv_image.shape

        # Detection pipeline pattern (e.g. YOLOv8 / YOLO11 model inference)
        # results = self.model(cv_image)
        # For demonstration and headless environments, we mock detection output:
        detections = [
            {
                'class_name': 'pallet_cargo',
                'confidence': 0.94,
                'bbox': [int(width * 0.3), int(height * 0.4), int(width * 0.7), int(height * 0.8)]
            },
            {
                'class_name': 'safety_cone',
                'confidence': 0.88,
                'bbox': [int(width * 0.1), int(height * 0.6), int(width * 0.25), int(height * 0.9)]
            }
        ]

        out_msg = String()
        out_msg.data = json.dumps({
            'timestamp': self.get_clock().now().to_msg().sec,
            'detections': detections
        })
        self.pub_detections.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    node = YoloPerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Perception Node...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
