#!/usr/bin/env python3
"""
Advanced Module 02: AprilTag (36h11) dock tracker -> geometry_msgs/PoseStamped.

  camera/image_raw + camera/camera_info  (qos_profile_sensor_data)
      -> cv2.aruco detection (DICT_APRILTAG_36h11) -> cv2.solvePnP(SOLVEPNP_IPPE_SQUARE)
      -> detected_dock_pose  (PoseStamped, header = the image header: same stamp & optical frame)

`detected_dock_pose` is the topic the Nav2 docking server (opennav_docking SimpleChargingDock with
use_external_detection_pose: true) subscribes to; module 03 uses this node unchanged.
Nothing is published when the tag is not in the image.

Run:  ros2 run amr_adv02 apriltag_dock_tracker --ros-args -p tag_size:=0.10 -p tag_id:=0
"""

import math

import numpy as np
import rclpy
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import PoseStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CameraInfo, Image

try:
    from amr_adv02 import vision_utils as vu
except ImportError:  # python3 src/apriltag_dock_tracker.py
    import vision_utils as vu


class AprilTagDockTracker(Node):
    def __init__(self):
        super().__init__('apriltag_dock_tracker')
        self.tag_id = self.declare_parameter('tag_id', 0).value          # -1: any id
        self.tag_size = self.declare_parameter('tag_size', 0.10).value   # metres (black border)
        self.bridge = CvBridge()
        self.K = None
        self.D = None
        self.last_q = None
        self.create_subscription(Image, 'camera/image_raw', self.image_callback,
                                 qos_profile_sensor_data)
        self.create_subscription(CameraInfo, 'camera/camera_info', self.info_callback,
                                 qos_profile_sensor_data)
        self.pub_dock_pose = self.create_publisher(PoseStamped, 'detected_dock_pose', 10)
        self.get_logger().info(f'AprilTag dock tracker: tag36h11 id={self.tag_id} '
                               f'size={self.tag_size} m -> detected_dock_pose')

    def info_callback(self, msg: CameraInfo):
        self.K = np.array(msg.k, dtype=float).reshape(3, 3)
        self.D = np.array(msg.d, dtype=float)

    def detect(self, cv_image):
        """Return (R, t) of the wanted tag in the camera frame, or None."""
        for tag_id, corners in vu.detect_tags(cv_image):
            if self.tag_id < 0 or tag_id == self.tag_id:
                return vu.estimate_tag_pose(corners, self.tag_size, self.K, self.D)
        return None

    def image_callback(self, msg: Image):
        if self.K is None:
            self.get_logger().warn('waiting for camera_info (camera matrix K)',
                                   throttle_duration_sec=5.0)
            return
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as e:
            self.get_logger().error(f'cv_bridge conversion error: {e}')
            return
        pose = self.detect(cv_image)
        if pose is None:
            self.get_logger().info('tag not visible', throttle_duration_sec=5.0)
            return
        R, t = pose
        if not (np.all(np.isfinite(R)) and np.all(np.isfinite(t))):
            self.get_logger().warn('non-finite pose estimate dropped')
            return
        out = PoseStamped()
        out.header = msg.header  # same stamp + optical frame as the image
        out.pose.position.x, out.pose.position.y, out.pose.position.z = (float(v) for v in t)
        # q and -q are the same rotation. A tag facing the camera is ~180 deg about x (w ~ 0),
        # so a fixed sign convention would flip from frame to frame; downstream filters (the
        # docking server averages poses) then average q with -q -> ~0 -> NaN. Keep continuity.
        q = vu.rotation_to_quaternion(R)
        if self.last_q is not None and sum(a * b for a, b in zip(q, self.last_q)) < 0.0:
            q = tuple(-v for v in q)
        self.last_q = q
        qx, qy, qz, qw = q
        out.pose.orientation.x, out.pose.orientation.y = qx, qy
        out.pose.orientation.z, out.pose.orientation.w = qz, qw
        self.pub_dock_pose.publish(out)
        # yaw of the tag normal seen from the camera (0 = facing the camera squarely)
        yaw = math.degrees(math.atan2(-R[0, 2], -R[2, 2]))
        self.get_logger().info(
            f'tag {self.tag_id}: x={t[0]:+.3f} y={t[1]:+.3f} z={t[2]:.3f} m  yaw={yaw:+.1f} deg',
            throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = AprilTagDockTracker()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
