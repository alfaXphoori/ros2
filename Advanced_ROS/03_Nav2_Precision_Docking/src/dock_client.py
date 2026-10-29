#!/usr/bin/env python3
"""
Advanced Module 03: DockRobot / UndockRobot action client that also MEASURES the docking error.

  ros2 run amr_adv03 dock_client                       # dock at home_dock, measure, undock
  ros2 run amr_adv03 dock_client --ros-args -p undock:=false

Actions are nav2_msgs/action/DockRobot and nav2_msgs/action/UndockRobot (ROS 2 Jazzy;
there is no opennav_docking_msgs package). The error is measured against the TRUE dock pose
(true_dock = [x, y, yaw] in odom, the ground truth of the fake base / synthetic camera),
not against the docking server's own estimate.
"""

import math
import sys
import time

import rclpy
from nav2_msgs.action import DockRobot, UndockRobot
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformException, TransformListener

DOCK_STATES = {0: 'NONE', 1: 'NAV_TO_STAGING_POSE', 2: 'INITIAL_PERCEPTION', 3: 'CONTROLLING',
               4: 'WAIT_FOR_CHARGE', 5: 'RETRY'}
DOCK_ERRORS = {0: 'NONE', 901: 'DOCK_NOT_IN_DB', 902: 'DOCK_NOT_VALID', 903: 'FAILED_TO_STAGE',
               904: 'FAILED_TO_DETECT_DOCK', 905: 'FAILED_TO_CONTROL', 906: 'FAILED_TO_CHARGE',
               999: 'UNKNOWN'}


def yaw_of(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def pose_error(robot_xyyaw, dock_xyyaw):
    """Return (position error m, lateral error m, longitudinal error m, yaw error rad).

    lateral/longitudinal are expressed in the dock frame (x into the dock)."""
    rx, ry, ryaw = robot_xyyaw
    dx, dy, dyaw = dock_xyyaw
    ex, ey = rx - dx, ry - dy
    lon = math.cos(dyaw) * ex + math.sin(dyaw) * ey
    lat = -math.sin(dyaw) * ex + math.cos(dyaw) * ey
    eyaw = math.atan2(math.sin(ryaw - dyaw), math.cos(ryaw - dyaw))
    return math.hypot(ex, ey), lat, lon, eyaw


class DockClient(Node):
    def __init__(self):
        super().__init__('dock_client')
        self.dock_id = self.declare_parameter('dock_id', 'home_dock').value
        self.true_dock = list(self.declare_parameter('true_dock', [1.0, 0.0, 0.0]).value)
        self.do_undock = self.declare_parameter('undock', True).value
        self.fixed_frame = self.declare_parameter('fixed_frame', 'odom').value
        self.base_frame = self.declare_parameter('base_frame', 'base_footprint').value
        self.dock_ac = ActionClient(self, DockRobot, 'dock_robot')
        self.undock_ac = ActionClient(self, UndockRobot, 'undock_robot')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.last_state = None

    def log(self, text):
        print(text, flush=True)

    def robot_pose(self, timeout=5.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                tf = self.tf_buffer.lookup_transform(self.fixed_frame, self.base_frame, Time())
                tr = tf.transform.translation
                return tr.x, tr.y, yaw_of(tf.transform.rotation)
            except TransformException:
                rclpy.spin_once(self, timeout_sec=0.1)
        return None

    def _run(self, client, goal, timeout, feedback_cb=None):
        if not client.wait_for_server(timeout_sec=30.0):
            raise RuntimeError(f'action server {client._action_name} not available')
        send = client.send_goal_async(goal, feedback_callback=feedback_cb)
        rclpy.spin_until_future_complete(self, send, timeout_sec=10.0)
        handle = send.result()
        if handle is None or not handle.accepted:
            raise RuntimeError('goal rejected')
        res = handle.get_result_async()
        rclpy.spin_until_future_complete(self, res, timeout_sec=timeout)
        if res.result() is None:
            handle.cancel_goal_async()
            raise RuntimeError('timed out waiting for the result')
        return res.result().result

    def _on_dock_feedback(self, fb):
        state = fb.feedback.state
        if state != self.last_state:
            self.last_state = state
            t = fb.feedback.docking_time
            self.log(f'  feedback: {DOCK_STATES.get(state, state):<20} '
                     f't={t.sec + t.nanosec * 1e-9:5.2f} s  retries={fb.feedback.num_retries}')

    def dock(self, timeout=90.0):
        goal = DockRobot.Goal()
        goal.use_dock_id = True
        goal.dock_id = self.dock_id
        goal.navigate_to_staging_pose = False  # no Nav2 planner/controller in this lab
        self.last_state = None
        start = self.robot_pose()
        self.log(f'DockRobot dock_id={self.dock_id}  start pose: '
                 f'x={start[0]:.3f} y={start[1]:.3f} yaw={math.degrees(start[2]):.1f} deg')
        t0 = time.monotonic()
        result = self._run(self.dock_ac, goal, timeout, self._on_dock_feedback)
        elapsed = time.monotonic() - t0
        self.log(f'DockRobot result: success={result.success} '
                 f'error_code={result.error_code} ({DOCK_ERRORS.get(result.error_code, "?")}) '
                 f'num_retries={result.num_retries}  ({elapsed:.1f} s)')
        return result

    def undock(self, timeout=60.0):
        goal = UndockRobot.Goal()
        goal.dock_type = 'simple_charging_dock'
        goal.max_undocking_time = 30.0
        t0 = time.monotonic()
        result = self._run(self.undock_ac, goal, timeout)
        self.log(f'UndockRobot result: success={result.success} error_code={result.error_code} '
                 f'({time.monotonic() - t0:.1f} s)')
        return result

    def report_error(self, label):
        pose = self.robot_pose()
        err, lat, lon, eyaw = pose_error(pose, self.true_dock)
        self.log(f'{label}: robot x={pose[0]:.4f} y={pose[1]:.4f} yaw={math.degrees(pose[2]):.2f} deg'
                 f' | true dock x={self.true_dock[0]:.3f} y={self.true_dock[1]:.3f}'
                 f' yaw={math.degrees(self.true_dock[2]):.2f} deg')
        self.log(f'{label}: error = {err * 1000:.1f} mm (lateral {lat * 1000:+.1f} mm, '
                 f'longitudinal {lon * 1000:+.1f} mm), yaw error = {math.degrees(eyaw):+.2f} deg')
        return err, lat, lon, eyaw


def main(args=None):
    rclpy.init(args=args)
    node = DockClient()
    ok = False
    try:
        # let TF fill up and the tracker see the tag
        node.robot_pose(timeout=10.0)
        end = time.monotonic() + 2.0
        while time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.1)
        result = node.dock()
        ok = result.success
        if ok:
            node.report_error('docked')
            if node.do_undock:
                ok = node.undock().success
                node.report_error('after undock')
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    except RuntimeError as e:
        node.get_logger().error(str(e))
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
