#!/usr/bin/env python3
import sys
import math
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus

PATROL_WAYPOINTS = [
    {'name': 'Station 1: Receiving Dock', 'x': 2.0, 'y': 2.0, 'yaw': 0.0, 'dwell': 3.0},
    {'name': 'Station 2: Storage Aisle B', 'x': 2.0, 'y': -2.0, 'yaw': -1.57, 'dwell': 3.0},
    {'name': 'Station 3: Quality Check', 'x': -2.0, 'y': -2.0, 'yaw': 3.14, 'dwell': 3.0},
    {'name': 'Station 4: Shipping Dock', 'x': -2.0, 'y': 2.0, 'yaw': 1.57, 'dwell': 3.0},
    {'name': 'Station 5: Charging Base', 'x': 0.0, 'y': 0.0, 'yaw': 0.0, 'dwell': 2.0}
]

class WaypointPatroller(Node):
    def __init__(self):
        super().__init__('waypoint_patroller')
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.get_logger().info('🤖 Nav2 Waypoint Patroller Node Initialized')

    def run_patrol(self):
        self.get_logger().info('Waiting for /navigate_to_pose action server...')
        if not self._action_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('Action server /navigate_to_pose not available!')
            return

        for idx, wp in enumerate(PATROL_WAYPOINTS):
            self.get_logger().info(f"📍 [{idx+1}/{len(PATROL_WAYPOINTS)}] Navigating to: {wp['name']}")
            self.get_logger().info(f"   Target: X={wp['x']:.2f}, Y={wp['y']:.2f}, Yaw={wp['yaw']:.2f}")

            goal_msg = NavigateToPose.Goal()
            goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
            goal_msg.pose.header.frame_id = 'map'
            goal_msg.pose.pose.position.x = wp['x']
            goal_msg.pose.pose.position.y = wp['y']
            half = wp['yaw'] * 0.5
            goal_msg.pose.pose.orientation.z = math.sin(half)
            goal_msg.pose.pose.orientation.w = math.cos(half)

            send_goal_future = self._action_client.send_goal_async(goal_msg)
            rclpy.spin_until_future_complete(self, send_goal_future)
            goal_handle = send_goal_future.result()

            if not goal_handle.accepted:
                self.get_logger().warn(f"Goal for {wp['name']} rejected!")
                continue

            get_result_future = goal_handle.get_result_async()
            rclpy.spin_until_future_complete(self, get_result_future)

            self.get_logger().info(f"✅ Arrived at {wp['name']}! Dwelling for {wp['dwell']}s...")
            time.sleep(wp['dwell'])

        self.get_logger().info('🎉 All patrol stations visited successfully!')

def main(args=None):
    rclpy.init(args=args)
    patroller = WaypointPatroller()
    try:
        patroller.run_patrol()
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        patroller.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
