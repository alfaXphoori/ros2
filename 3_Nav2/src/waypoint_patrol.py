#!/usr/bin/env python3

"""
waypoint_patrol.py
==================
Autonomous multi-waypoint patrol node for ROS 2 Navigation 2 (Nav2).
Supports both:
  1. Nav2 Simple Commander API (BasicNavigator)
  2. Native ROS 2 Action Client (/navigate_to_pose) as fallback

Controls the robot to navigate through a sequence of designated patrol points
in the warehouse with dwell/inspection time at each station.

Usage:
  python3 waypoint_patrol.py
  # OR
  ros2 run ce_nav2 waypoint_patrol.py --ros-args -p loops:=3
"""

import sys
import math
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus


# Default Warehouse Patrol Waypoints
PATROL_WAYPOINTS = [
    {
        'name': 'Station 1: Inbound Receiving Dock',
        'x': 2.5,
        'y': 3.5,
        'yaw': 0.0,
        'dwell_sec': 3.0
    },
    {
        'name': 'Station 2: Storage Rack Aisle B',
        'x': 3.5,
        'y': -2.5,
        'yaw': -1.5708,
        'dwell_sec': 3.0
    },
    {
        'name': 'Station 3: Quality Inspection Area',
        'x': -3.0,
        'y': -3.5,
        'yaw': 3.1415,
        'dwell_sec': 4.0
    },
    {
        'name': 'Station 4: Outbound Packaging Bay',
        'x': -3.0,
        'y': 3.5,
        'yaw': 1.5708,
        'dwell_sec': 3.0
    },
    {
        'name': 'Station 5: Charging Base / Origin',
        'x': 0.0,
        'y': 0.0,
        'yaw': 0.0,
        'dwell_sec': 2.0
    }
]


def euler_to_quaternion(yaw: float) -> Quaternion:
    q = Quaternion()
    q.w = math.cos(yaw * 0.5)
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw * 0.5)
    return q


def run_with_simple_commander(waypoints, total_loops):
    """Run waypoint navigation using Nav2 Simple Commander API"""
    from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

    navigator = BasicNavigator()
    print("\n🚀 [Simple Commander] Initializing BasicNavigator...")
    navigator.waitUntilNav2Active()

    print(f"🏁 Starting Patrol: {len(waypoints)} waypoints, {total_loops} loops\n")

    for loop in range(1, total_loops + 1):
        print(f"\n{'='*60}")
        print(f" 🔄 Patrol Cycle {loop}/{total_loops}")
        print(f"{'='*60}")

        for idx, wp in enumerate(waypoints, 1):
            goal_pose = PoseStamped()
            goal_pose.header.frame_id = 'map'
            goal_pose.header.stamp = navigator.get_clock().now().to_msg()
            goal_pose.pose.position.x = float(wp['x'])
            goal_pose.pose.position.y = float(wp['y'])
            goal_pose.pose.position.z = 0.0
            goal_pose.pose.orientation = euler_to_quaternion(wp['yaw'])

            print(f"\n📍 [{idx}/{len(waypoints)}] Navigating to: {wp['name']}")
            print(f"   Target: X={wp['x']:.2f}, Y={wp['y']:.2f}, Yaw={math.degrees(wp['yaw']):.1f}°")

            navigator.goToPose(goal_pose)

            while not navigator.isTaskComplete():
                feedback = navigator.getFeedback()
                if feedback:
                    dist = feedback.distance_remaining
                    eta = feedback.estimated_time_remaining.sec
                    print(f"   ⏳ Distance remaining: {dist:.2f} m | ETA: {eta}s   ", end='\r')
                time.sleep(0.5)

            result = navigator.getResult()
            print() # new line after \r
            if result == TaskResult.SUCCEEDED:
                print(f"   ✅ Arrived at {wp['name']}! Performing task for {wp['dwell_sec']}s...")
                time.sleep(wp['dwell_sec'])
            elif result == TaskResult.CANCELED:
                print(f"   ⚠️ Navigation to {wp['name']} was canceled.")
                return
            elif result == TaskResult.FAILED:
                print(f"   ❌ Navigation to {wp['name']} failed! Moving to next waypoint.")

    print("\n🎉 All patrol loops completed successfully!")


class WaypointActionPatroller(Node):
    """Fallback waypoint patrol using standard ROS 2 Action Client"""

    def __init__(self, waypoints, total_loops):
        super().__init__('waypoint_action_patroller')
        self.waypoints = waypoints
        self.total_loops = total_loops
        self.current_loop = 1
        self.current_wp_idx = 0
        self.goal_handle = None

        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        self.get_logger().info("=" * 60)
        self.get_logger().info(" 🤖 Nav2 Action Client Waypoint Patroller")
        self.get_logger().info(f"    Waypoints: {len(self.waypoints)}")
        self.get_logger().info(f"    Total Loops: {self.total_loops}")
        self.get_logger().info("=" * 60)

    def start_patrol(self):
        self.get_logger().info("Waiting for 'navigate_to_pose' action server...")
        if not self._action_client.wait_for_server(timeout_sec=15.0):
            self.get_logger().error("Action server /navigate_to_pose not available!")
            return False

        self.send_next_goal()
        return True

    def send_next_goal(self):
        if self.current_wp_idx >= len(self.waypoints):
            self.current_loop += 1
            self.current_wp_idx = 0
            if self.current_loop > self.total_loops:
                self.get_logger().info("🎉 All patrol cycles finished successfully!")
                rclpy.shutdown()
                return

        wp = self.waypoints[self.current_wp_idx]
        self.get_logger().info(f"\n[Loop {self.current_loop}/{self.total_loops}] Navigating to #{self.current_wp_idx + 1}: {wp['name']}")

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(wp['x'])
        goal_msg.pose.pose.position.y = float(wp['y'])
        goal_msg.pose.pose.orientation = euler_to_quaternion(wp['yaw'])

        send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.get_logger().error("Goal rejected by Nav2 server!")
            self.current_wp_idx += 1
            self.send_next_goal()
            return

        get_result_future = self.goal_handle.get_result_async()
        get_result_future.add_done_callback(self.get_result_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        dist = feedback.distance_remaining
        self.get_logger().info(f"  Distance remaining: {dist:.2f} m", throttle_duration_sec=2.0)

    def get_result_callback(self, future):
        status = future.result().status
        wp = self.waypoints[self.current_wp_idx]

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f"  ✅ Arrived at {wp['name']}! Pausing for {wp['dwell_sec']}s...")
            time.sleep(wp['dwell_sec'])
        else:
            self.get_logger().warn(f"  ⚠️ Navigation finished with status {status}")

        self.current_wp_idx += 1
        self.send_next_goal()


def main(args=None):
    rclpy.init(args=args)

    total_loops = 2

    # Check for Simple Commander first
    simple_commander_available = False
    try:
        from nav2_simple_commander.robot_navigator import BasicNavigator
        simple_commander_available = True
    except ImportError:
        pass

    if simple_commander_available:
        try:
            run_with_simple_commander(PATROL_WAYPOINTS, total_loops)
        except KeyboardInterrupt:
            print("\nPatrol interrupted by user.")
        finally:
            if rclpy.ok():
                rclpy.shutdown()
    else:
        # Fall back to Action Client node
        patroller = WaypointActionPatroller(PATROL_WAYPOINTS, total_loops)
        if patroller.start_patrol():
            try:
                rclpy.spin(patroller)
            except KeyboardInterrupt:
                pass
            finally:
                if rclpy.ok():
                    patroller.destroy_node()
                    rclpy.shutdown()


if __name__ == '__main__':
    main()
