#!/usr/bin/env python3
"""
Week 15 Lab: multi-station warehouse patrol with the Nav2 NavigateToPose action.

  ros2 run amr_week15 waypoint_patrol --ros-args -p use_sim_time:=true
  ros2 run amr_week15 waypoint_patrol --ros-args -p use_sim_time:=true -p dwell_scale:=0.0

Each station is sent as one NavigateToPose goal. The script checks the final
GoalStatus of every goal (only STATUS_SUCCEEDED counts as arrived), cancels a
goal that exceeds `goal_timeout`, and exits with code 1 if any station failed.

Stations lie in free space of the real Week 12 map (outside the pillars at
(+-2, 2) and at least the 0.55 m inflation radius away from every obstacle;
see test/test_waypoints.py).
"""

import math
import sys

from action_msgs.msg import GoalStatus
from amr_week14.nav2_lifecycle_guard import describe, ensure_nav2_active
from nav2_msgs.action import NavigateToPose
import rclpy
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

PATROL_WAYPOINTS = [
    {'name': 'Station 1: Receiving Dock', 'x': 2.0, 'y': 3.5, 'yaw': 0.0, 'dwell': 3.0},
    {'name': 'Station 2: Storage Aisle B', 'x': 2.0, 'y': -2.0, 'yaw': -1.57, 'dwell': 3.0},
    {'name': 'Station 3: Quality Check', 'x': -2.0, 'y': -2.0, 'yaw': 3.14, 'dwell': 3.0},
    {'name': 'Station 4: Shipping Dock', 'x': -2.0, 'y': 3.5, 'yaw': 1.57, 'dwell': 3.0},
    {'name': 'Station 5: Charging Base', 'x': 0.0, 'y': 0.0, 'yaw': 0.0, 'dwell': 2.0},
]

STATUS_NAMES = {
    GoalStatus.STATUS_SUCCEEDED: 'SUCCEEDED',
    GoalStatus.STATUS_ABORTED: 'ABORTED',
    GoalStatus.STATUS_CANCELED: 'CANCELED',
    GoalStatus.STATUS_UNKNOWN: 'UNKNOWN',
}


def make_goal(wp, stamp, frame_id='map'):
    goal = NavigateToPose.Goal()
    goal.pose.header.frame_id = frame_id
    goal.pose.header.stamp = stamp
    goal.pose.pose.position.x = float(wp['x'])
    goal.pose.pose.position.y = float(wp['y'])
    goal.pose.pose.orientation.z = math.sin(wp['yaw'] / 2.0)
    goal.pose.pose.orientation.w = math.cos(wp['yaw'] / 2.0)
    return goal


class WaypointPatroller(Node):
    def __init__(self):
        super().__init__('waypoint_patroller')
        self.dwell_scale = self.declare_parameter('dwell_scale', 1.0).value
        self.goal_timeout = self.declare_parameter('goal_timeout', 120.0).value
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

    def sleep(self, seconds):
        """Sleep in node (sim) time while still processing callbacks."""
        end = self.get_clock().now().nanoseconds + seconds * 1e9
        while rclpy.ok() and self.get_clock().now().nanoseconds < end:
            rclpy.spin_once(self, timeout_sec=0.05)

    def wait_future(self, future, timeout_s):
        start = self.get_clock().now().nanoseconds
        while rclpy.ok() and not future.done():
            rclpy.spin_once(self, timeout_sec=0.1)
            if (self.get_clock().now().nanoseconds - start) * 1e-9 > timeout_s:
                return False
        return future.done()

    def navigate(self, wp):
        """Send one goal and return the final GoalStatus code."""
        send = self._action_client.send_goal_async(make_goal(wp, self.get_clock().now().to_msg()))
        if not self.wait_future(send, 10.0) or not send.result().accepted:
            self.get_logger().error(f"Goal for {wp['name']} was rejected")
            return GoalStatus.STATUS_UNKNOWN
        handle = send.result()
        result = handle.get_result_async()
        if not self.wait_future(result, self.goal_timeout):
            self.get_logger().error(f"{wp['name']}: no result after {self.goal_timeout:.0f} s, canceling")
            cancel = handle.cancel_goal_async()
            self.wait_future(cancel, 5.0)
            return GoalStatus.STATUS_CANCELED
        return result.result().status

    def wait_nav2_active(self, timeout_s=120.0):
        """bt_navigator rejects goals until it is ACTIVE: wait for every Nav2 lifecycle node
        (Week 14 guard, which also heals a lost lifecycle_manager reply)."""
        ok, states, healed = ensure_nav2_active(self, timeout=timeout_s)
        (self.get_logger().info if ok else self.get_logger().error)(describe(states, healed))
        return ok

    def run_patrol(self):
        self.get_logger().info('Waiting for Nav2 (bt_navigator active, /navigate_to_pose)...')
        if not self.wait_nav2_active() or not self._action_client.wait_for_server(timeout_sec=30.0):
            self.get_logger().error('Nav2 /navigate_to_pose is not available/active!')
            return False

        n = len(PATROL_WAYPOINTS)
        succeeded = 0
        patrol_start = self.get_clock().now()
        for idx, wp in enumerate(PATROL_WAYPOINTS, start=1):
            self.get_logger().info(
                f"[{idx}/{n}] Navigating to {wp['name']} (x={wp['x']:.2f}, y={wp['y']:.2f}, "
                f"yaw={wp['yaw']:.2f})")
            t0 = self.get_clock().now()
            status = self.navigate(wp)
            dt = (self.get_clock().now() - t0).nanoseconds * 1e-9
            name = STATUS_NAMES.get(status, str(status))
            if status == GoalStatus.STATUS_SUCCEEDED:
                succeeded += 1
                dwell = wp['dwell'] * self.dwell_scale
                self.get_logger().info(
                    f"[{idx}/{n}] {wp['name']}: {name} after {dt:.1f} s, dwelling {dwell:.1f} s")
                self.sleep(dwell)
            else:
                self.get_logger().error(f"[{idx}/{n}] {wp['name']}: {name} after {dt:.1f} s")

        total = (self.get_clock().now() - patrol_start).nanoseconds * 1e-9
        ok = succeeded == n
        summary = f'Patrol finished: {succeeded}/{n} stations SUCCEEDED in {total:.1f} s (sim time)'
        (self.get_logger().info if ok else self.get_logger().error)(summary)
        return ok


def main(args=None):
    rclpy.init(args=args)
    patroller = WaypointPatroller()
    ok = False
    try:
        ok = patroller.run_patrol()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        patroller.destroy_node()
        rclpy.try_shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
