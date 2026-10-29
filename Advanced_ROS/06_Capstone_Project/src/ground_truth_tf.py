#!/usr/bin/env python3
"""
Advanced Module 06: Gazebo ground truth -> ROS (for the virtual charger camera and for KPIs).

  ros2 run amr_adv06 ground_truth_tf --ros-args -p use_sim_time:=true

Subscribes DIRECTLY to Gazebo transport (Python bindings gz.transport13 / gz.msgs10) on
/world/<world>/dynamic_pose/info (gz.msgs.Pose_V, ~60 Hz, sim-time stamps) and picks the robot
model. Why not ros_gz_bridge? Pose_V -> tf2_msgs/TFMessage through the bridge drops the entity
names and the stamps (frame_id/child_frame_id/stamp arrive empty), so the robot entry cannot be
identified reliably.

Publishes
  /ground_truth/pose  geometry_msgs/PoseStamped  TRUE pose of base_footprint, frame `sim_world`
  TF base_footprint -> sim_world (the INVERSE of the true pose)
      sim_world hangs below base_footprint so the TF tree stays a tree (base_footprint already
      has the parent odom). Any node can now ask TF for camera_optical_link <- sim_world, i.e.
      where the world really is as seen by the camera - this is what lets the amr_adv02
      synthetic_tag_camera render the charger AprilTag from the robot's TRUE pose, exactly
      like a real camera would see it (independent of AMCL / odometry errors).
"""

import threading

from geometry_msgs.msg import PoseStamped, TransformStamped
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from tf2_ros import TransformBroadcaster

try:
    from amr_adv06.capstone_config import invert_transform
except ImportError:  # python3 src/ground_truth_tf.py
    from capstone_config import invert_transform


class GroundTruthTF(Node):
    def __init__(self):
        super().__init__('ground_truth_tf')
        self.model = self.declare_parameter('model', 'diff_drive_robot').value
        self.world = self.declare_parameter('world', 'warehouse').value
        self.world_frame = self.declare_parameter('world_frame', 'sim_world').value
        self.base_frame = self.declare_parameter('base_frame', 'base_footprint').value
        self.decimation = int(self.declare_parameter('decimation', 2).value)  # 60 Hz -> 30 Hz

        self.pub_pose = self.create_publisher(PoseStamped, 'ground_truth/pose', 10)
        self.tf_pub = TransformBroadcaster(self)
        self.count = 0
        self.lock = threading.Lock()

        from gz.msgs10.pose_v_pb2 import Pose_V
        from gz.transport13 import Node as GzNode
        self.gz = GzNode()
        topic = f'/world/{self.world}/dynamic_pose/info'
        self.gz.subscribe(Pose_V, topic, self.on_poses)
        self.get_logger().info(f'Ground truth of model "{self.model}" from gz {topic} -> '
                               f'/ground_truth/pose + TF {self.base_frame} -> {self.world_frame}')

    def on_poses(self, msg):
        """Gazebo transport thread: one Pose_V per physics publish."""
        with self.lock:
            self.count += 1
            if self.count % self.decimation:
                return
        for pose in msg.pose:
            if pose.name == self.model:
                break
        else:
            return
        stamp = rclpy.time.Time(seconds=msg.header.stamp.sec,
                                nanoseconds=msg.header.stamp.nsec).to_msg()
        p, o = pose.position, pose.orientation
        out = PoseStamped()
        out.header.stamp = stamp
        out.header.frame_id = self.world_frame
        out.pose.position.x, out.pose.position.y, out.pose.position.z = p.x, p.y, p.z
        out.pose.orientation.x, out.pose.orientation.y = o.x, o.y
        out.pose.orientation.z, out.pose.orientation.w = o.z, o.w
        self.pub_pose.publish(out)

        t_inv, q_inv = invert_transform((p.x, p.y, p.z), (o.x, o.y, o.z, o.w))
        tf = TransformStamped()
        tf.header.stamp = stamp
        tf.header.frame_id = self.base_frame
        tf.child_frame_id = self.world_frame
        tf.transform.translation.x, tf.transform.translation.y, tf.transform.translation.z = t_inv
        (tf.transform.rotation.x, tf.transform.rotation.y,
         tf.transform.rotation.z, tf.transform.rotation.w) = q_inv
        self.tf_pub.sendTransform(tf)


def main(args=None):
    rclpy.init(args=args)
    node = GroundTruthTF()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
