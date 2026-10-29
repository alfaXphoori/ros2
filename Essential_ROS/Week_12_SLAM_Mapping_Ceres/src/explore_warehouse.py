#!/usr/bin/env python3
"""
Week 12 Lab: scripted exploration drive for SLAM mapping.

Drives the robot through a fixed list of waypoints (map frame; the robot
spawns at the origin so map == odom at t=0) that covers the 10 x 10 m warehouse and closes a loop
around the two storage pillars, so SLAM Toolbox sees every wall and can
perform loop closure. It is a deterministic stand-in for teleop.

  ros2 run amr_week12 explore_warehouse --ros-args -p use_sim_time:=true

The robot pose is read from TF map -> base_footprint, i.e. the pose corrected by
SLAM Toolbox's scan matching. Wheel odometry alone drifts in yaw (wheel/caster
slip in Gazebo), and an open-loop odom route would end up driving into walls.
Falls back to /odom until the map frame exists.

Controller per waypoint: rotate towards the goal, then drive with a
proportional heading correction. A +-30 deg LiDAR sector check stops the robot
if anything is closer than 0.30 m. Exit code 0 only if every waypoint was reached.
"""

import math
import sys

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformException, TransformListener

# ('spin', turns) rotates in place; (x, y) drives to a point [m, map frame]
ROUTE = [
    ('spin', 1.0),
    (0.0, 3.3),           # between the pillars, look behind them
    ('spin', 1.0),
    (3.5, 3.5),           # north-east corner
    (3.5, -3.5),          # south-east corner
    (-3.5, -3.5),         # south-west corner
    (-3.5, 3.5),          # north-west corner
    (0.0, 3.5),           # back between the pillars -> loop closure
    (0.0, 0.0),           # home
]

MAX_V = 0.3        # m/s
MAX_W = 0.6        # rad/s
SPIN_W = 0.4       # rad/s, slow spins give SLAM more overlapping scans
GOAL_TOL = 0.10    # m
STOP_DIST = 0.30   # m, frontal safety distance
WAYPOINT_TIMEOUT = 90.0  # s (sim time)


def wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


def yaw_from_quat(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def go_to_point(x, y, yaw, gx, gy):
    """Return (v, w, reached) for a unicycle robot at (x, y, yaw) heading to (gx, gy)."""
    dx, dy = gx - x, gy - y
    dist = math.hypot(dx, dy)
    if dist < GOAL_TOL:
        return 0.0, 0.0, True
    err = wrap(math.atan2(dy, dx) - yaw)
    w = max(-MAX_W, min(MAX_W, 2.0 * err))
    if abs(err) > 0.35:          # turn in place first
        return 0.0, w, False
    v = min(MAX_V, 0.6 * dist) * math.cos(err)
    return v, w, False


class Explorer(Node):
    def __init__(self):
        super().__init__('explore_warehouse')
        self.pose = None
        self.pose_src = None
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.front = math.inf
        self.idx = 0
        self.reached = 0
        self.spin_acc = 0.0
        self.last_yaw = None
        self.wp_start = None
        self.t0 = None
        self.done = False
        self.ok = False
        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_subscription(Odometry, 'odom', self.on_odom, 10)
        self.create_subscription(LaserScan, 'scan', self.on_scan, qos_profile_sensor_data)
        self.timer = self.create_timer(0.1, self.step)
        self.get_logger().info(f'Exploration route with {len(ROUTE)} steps, waiting for /odom')

    def on_odom(self, msg):
        # fallback only, until SLAM publishes map -> odom
        if self.pose_src != 'map':
            p = msg.pose.pose
            self.pose = (p.position.x, p.position.y, yaw_from_quat(p.orientation))
            self.pose_src = 'odom'

    def update_map_pose(self):
        try:
            t = self.tf_buffer.lookup_transform('map', 'base_footprint', rclpy.time.Time())
        except TransformException:
            return
        tr = t.transform
        self.pose = (tr.translation.x, tr.translation.y, yaw_from_quat(tr.rotation))
        if self.pose_src != 'map':
            self.get_logger().info('Using SLAM pose (TF map -> base_footprint)')
        self.pose_src = 'map'

    def on_scan(self, msg):
        best = math.inf
        for i, r in enumerate(msg.ranges):
            a = wrap(msg.angle_min + i * msg.angle_increment)
            if abs(a) <= math.radians(30) and msg.range_min <= r <= msg.range_max:
                best = min(best, r)
        self.front = best

    def now_s(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def finish(self):
        self.pub.publish(Twist())
        elapsed = self.now_s() - self.t0
        self.ok = self.reached == len(ROUTE)
        msg = (f'Exploration finished: {self.reached}/{len(ROUTE)} steps completed '
               f'in {elapsed:.1f} s (sim time)')
        (self.get_logger().info if self.ok else self.get_logger().error)(msg)
        self.done = True

    def next_step(self, reached):
        if reached:
            self.reached += 1
        self.idx += 1
        self.wp_start = None

    def step(self):
        self.update_map_pose()
        if self.done or self.pose is None:
            return
        if self.t0 is None:
            self.t0 = self.now_s()
        if self.idx >= len(ROUTE):
            self.finish()
            return
        target = ROUTE[self.idx]
        if self.wp_start is None:
            self.wp_start = self.now_s()
            self.spin_acc, self.last_yaw = 0.0, self.pose[2]
            self.get_logger().info(f'[{self.idx + 1}/{len(ROUTE)}] {target}')
        if self.now_s() - self.wp_start > WAYPOINT_TIMEOUT:
            self.get_logger().error(f'Timeout on step {self.idx + 1} {target}, skipping')
            self.pub.publish(Twist())
            self.next_step(False)
            return

        cmd = Twist()
        x, y, yaw = self.pose
        if target[0] == 'spin':
            self.spin_acc += abs(wrap(yaw - self.last_yaw))
            self.last_yaw = yaw
            if self.spin_acc >= target[1] * 2.0 * math.pi:
                self.pub.publish(Twist())
                self.next_step(True)
                return
            cmd.angular.z = SPIN_W
        else:
            v, w, reached = go_to_point(x, y, yaw, *target)
            if reached:
                self.pub.publish(Twist())
                self.get_logger().info(f'    reached ({x:.2f}, {y:.2f})')
                self.next_step(True)
                return
            if v > 0.0 and self.front < STOP_DIST:
                self.get_logger().warn(f'Obstacle {self.front:.2f} m ahead, waiting',
                                       throttle_duration_sec=2.0)
                v = 0.0
            cmd.linear.x, cmd.angular.z = v, w
        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = Explorer()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ok = node.ok
        node.destroy_node()
        rclpy.try_shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
