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

import signal
import threading

from geometry_msgs.msg import PoseStamped, TransformStamped
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
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
        self.closed = False
        # serialises the gz transport thread with close(): publishing on a destroyed
        # publisher from that thread crashed the process at shutdown (SIGSEGV)
        self.lock = threading.Lock()

        from gz.msgs10.pose_v_pb2 import Pose_V
        from gz.transport13 import Node as GzNode
        self.gz = GzNode()
        self.topic = f'/world/{self.world}/dynamic_pose/info'
        self.gz.subscribe(Pose_V, self.topic, self.on_poses)
        self.get_logger().info(f'Ground truth of model "{self.model}" from gz {self.topic} -> '
                               f'/ground_truth/pose + TF {self.base_frame} -> {self.world_frame}')

    def close(self):
        """Stop the gz callbacks from using ROS before the ROS publishers are destroyed."""
        with self.lock:   # waits for a callback that is publishing right now
            self.closed = True

    def on_poses(self, msg):
        """Gazebo transport thread: one Pose_V per physics publish."""
        with self.lock:
            if self.closed:
                return
            self.count += 1
            if self.count % self.decimation:
                return
            try:
                self.publish(msg)
            except Exception as err:  # noqa: B902 - never raise into the gz thread
                # SIGINT shuts the rclpy context down before main() reaches close()
                if self.context.ok():
                    self.get_logger().error(f'ground truth publish failed: {err}')

    def publish(self, msg):
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
    # Own signal handling: SIGINT/SIGTERM only set a flag that the loop below checks between
    # spin_once() calls, so the context stays valid until the gz callbacks are stopped
    # (close) and the node is destroyed. With rclpy's handler the context was shut down while
    # spin() built its wait set (RCLError, exit code 1) and while the gz thread was still
    # publishing (SIGSEGV); a KeyboardInterrupt can also land inside a pybind call.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    node = GroundTruthTF()
    try:
        while not stop.is_set() and rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
    except ExternalShutdownException:
        pass
    finally:
        # stopping: ignore further signals (Python resets our handler at exit -> 2nd Ctrl+C = -2)
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal.SIG_IGN)
        node.close()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
