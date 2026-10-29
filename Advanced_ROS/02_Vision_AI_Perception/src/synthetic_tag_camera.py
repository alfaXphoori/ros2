#!/usr/bin/env python3
"""
Advanced Module 02: synthetic pinhole camera that renders an AprilTag (36h11) at a KNOWN pose.

No GPU, no Gazebo, no real camera: every frame is drawn with OpenCV through the camera matrix K,
so the ground truth is exact and the tracker's error can be measured.

Publishes (qos_profile_sensor_data, same header on both):
  camera/image_raw     sensor_msgs/Image (bgr8)
  camera/camera_info   sensor_msgs/CameraInfo (K, plumb_bob D = 0)
  camera/tag_pose_ground_truth  geometry_msgs/PoseStamped (only while the tag is rendered)

Modes (parameter `mode`):
  static : tag pose given directly in the camera optical frame (tag_x, tag_y, tag_z, tag_yaw_deg)
  tf     : tag fixed in `world_frame` at tag_world = [x, y, z, yaw]; the camera pose is looked up
           from TF every frame (used by module 03: the robot drives, the image changes).

Run:  ros2 run amr_adv02 synthetic_tag_camera --ros-args -p tag_z:=0.8 -p tag_yaw_deg:=15.0
"""

import math

import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import CameraInfo, Image
from tf2_ros import Buffer, TransformException, TransformListener

try:
    from amr_adv02 import vision_utils as vu
except ImportError:  # python3 src/synthetic_tag_camera.py
    import vision_utils as vu


class SyntheticTagCamera(Node):
    def __init__(self):
        super().__init__('synthetic_tag_camera')
        p = self.declare_parameter
        self.width = p('width', 640).value
        self.height = p('height', 480).value
        self.fx = p('fx', 525.0).value
        self.fy = p('fy', 525.0).value
        self.cx = p('cx', 319.5).value
        self.cy = p('cy', 239.5).value
        self.frame_id = p('frame_id', 'camera_optical_link').value
        self.rate = p('rate', 10.0).value
        self.tag_id = p('tag_id', 0).value
        self.tag_size = p('tag_size', 0.10).value          # black border edge length, metres
        self.tag_visible = p('tag_visible', True).value
        self.draw_objects = p('draw_objects', True).value  # cone + pallet for the detector lab
        self.mode = p('mode', 'static').value
        self.tag_xyz = (p('tag_x', 0.10).value, p('tag_y', 0.05).value, p('tag_z', 0.80).value)
        self.tag_yaw = math.radians(p('tag_yaw_deg', 15.0).value)
        self.world_frame = p('world_frame', 'odom').value
        self.tag_world = list(p('tag_world', [1.35, 0.0, 0.15, math.pi]).value)

        self.K = vu.camera_matrix(self.fx, self.fy, self.cx, self.cy)
        self.bridge = CvBridge()
        self.pub_img = self.create_publisher(Image, 'camera/image_raw', qos_profile_sensor_data)
        self.pub_info = self.create_publisher(CameraInfo, 'camera/camera_info',
                                              qos_profile_sensor_data)
        self.pub_gt = self.create_publisher(PoseStamped, 'camera/tag_pose_ground_truth', 10)
        if self.mode == 'tf':
            self.tf_buffer = Buffer()
            self.tf_listener = TransformListener(self.tf_buffer, self)
        self.background = np.full((self.height, self.width, 3), 90, dtype=np.uint8)
        if self.draw_objects:
            vu.draw_scene_objects(self.background)
        self.timer = self.create_timer(1.0 / self.rate, self.on_timer)
        self.get_logger().info(
            f'Synthetic camera {self.width}x{self.height} fx={self.fx} mode={self.mode} '
            f'tag36h11 id={self.tag_id} size={self.tag_size} m visible={self.tag_visible}')

    def tag_pose_in_camera(self):
        """Return (R, t, stamp) of the tag in the optical frame, or None."""
        if self.mode == 'static':
            return (vu.tag_rotation_in_camera(self.tag_yaw), np.array(self.tag_xyz, dtype=float),
                    self.get_clock().now())
        try:
            tf = self.tf_buffer.lookup_transform(self.frame_id, self.world_frame, Time(),
                                                 timeout=Duration(seconds=0.0))
        except TransformException as e:
            self.get_logger().warn(f'no TF {self.world_frame}->{self.frame_id}: {e}',
                                   throttle_duration_sec=5.0)
            return None
        q = tf.transform.rotation
        R_cw = vu.quaternion_to_rotation(q.x, q.y, q.z, q.w)
        tr = tf.transform.translation
        t_cw = np.array([tr.x, tr.y, tr.z])
        x, y, z, yaw = self.tag_world
        # tag frame in the world: z_tag = outward normal (heading `yaw`), y_tag = world up
        z_axis = np.array([math.cos(yaw), math.sin(yaw), 0.0])
        y_axis = np.array([0.0, 0.0, 1.0])
        R_wt = np.column_stack([np.cross(y_axis, z_axis), y_axis, z_axis])
        R_ct = R_cw @ R_wt
        t_ct = R_cw @ np.array([x, y, z]) + t_cw
        return R_ct, t_ct, Time.from_msg(tf.header.stamp)

    def on_timer(self):
        pose = self.tag_pose_in_camera()
        if pose is None:
            return
        R, t, stamp = pose
        # re-read every frame: `ros2 param set /synthetic_tag_camera tag_visible false` hides the tag
        self.tag_visible = self.get_parameter('tag_visible').value
        stamp_msg = stamp.to_msg() if self.mode == 'tf' else self.get_clock().now().to_msg()
        if self.tag_visible:
            img = vu.render_tag(self.width, self.height, self.K, R, t, self.tag_size,
                                self.tag_id, background=self.background)
        else:
            img = self.background.copy()

        msg = self.bridge.cv2_to_imgmsg(img, encoding='bgr8')
        msg.header.stamp = stamp_msg
        msg.header.frame_id = self.frame_id
        info = CameraInfo()
        info.header = msg.header
        info.width, info.height = self.width, self.height
        info.distortion_model = 'plumb_bob'
        info.d = [0.0] * 5
        info.k = [float(v) for v in self.K.flatten()]
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.p = [self.fx, 0.0, self.cx, 0.0, 0.0, self.fy, self.cy, 0.0, 0.0, 0.0, 1.0, 0.0]
        self.pub_info.publish(info)
        self.pub_img.publish(msg)

        if self.tag_visible and t[2] > 0.0:
            gt = PoseStamped()
            gt.header = msg.header
            gt.pose.position.x, gt.pose.position.y, gt.pose.position.z = (float(v) for v in t)
            qx, qy, qz, qw = vu.rotation_to_quaternion(R)
            gt.pose.orientation.x, gt.pose.orientation.y = qx, qy
            gt.pose.orientation.z, gt.pose.orientation.w = qz, qw
            self.pub_gt.publish(gt)


def main(args=None):
    rclpy.init(args=args)
    node = SyntheticTagCamera()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
