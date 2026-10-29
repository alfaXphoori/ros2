#!/usr/bin/env python3
"""
Tutorial 05: ROS 2 Production Lifecycle Node
Demonstrates managed states (Unconfigured -> Inactive -> Active -> Finalized)
ensuring safe hardware initialization and fail-safe shutdowns.

  ros2 run amr_adv05 lifecycle_laser_sensor
  ros2 lifecycle set /lifecycle_laser_sensor configure   # -> inactive, nothing on /scan_managed
  ros2 lifecycle set /lifecycle_laser_sensor activate    # -> active, LaserScan at 10 Hz
  ros2 lifecycle set /lifecycle_laser_sensor shutdown    # -> finalized, publishing stops

Resources (publisher + timer) are created in on_configure and released in
on_cleanup / on_shutdown, so a Finalized node never keeps publishing.
"""

import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.lifecycle import Node, State, TransitionCallbackReturn
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class LifecycleLaserSensor(Node):
    def __init__(self):
        super().__init__('lifecycle_laser_sensor')
        # Parameters are declared up front but only read in on_configure,
        # so `ros2 param set` before `configure` takes effect.
        self.declare_parameter('frame_id', 'lidar_link')
        self.declare_parameter('publish_rate', 10.0)   # Hz
        self.declare_parameter('num_beams', 360)
        self.declare_parameter('range_m', 2.5)         # simulated round room
        self.pub_scan = None
        self.timer = None
        self.get_logger().info('[LifecycleLaserSensor] Created in UNCONFIGURED state.')

    # ---- transition callbacks -------------------------------------------
    def on_configure(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('Configuring hardware connection and buffers...')
        self.frame_id = self.get_parameter('frame_id').value
        rate = float(self.get_parameter('publish_rate').value)
        self.num_beams = int(self.get_parameter('num_beams').value)
        self.range_m = float(self.get_parameter('range_m').value)
        if rate <= 0.0 or self.num_beams < 2:
            self.get_logger().error('publish_rate must be > 0 and num_beams >= 2')
            return TransitionCallbackReturn.FAILURE
        self.period = 1.0 / rate

        # A LifecyclePublisher drops publish() calls unless the node is Active
        self.pub_scan = self.create_lifecycle_publisher(
            LaserScan, '/scan_managed', qos_profile_sensor_data)
        # Timer exists but stays cancelled until on_activate
        self.timer = self.create_timer(self.period, self.publish_scan)
        self.timer.cancel()
        self.get_logger().info('Configured successfully. Transitioned to INACTIVE.')
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('Activating node: starting laser emission & timer...')
        self.timer.reset()
        # The base class activates every managed entity (our LifecyclePublisher)
        return super().on_activate(state)

    def on_deactivate(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().warn('Deactivating node: pausing laser emission...')
        self.timer.cancel()
        return super().on_deactivate(state)

    def on_cleanup(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().info('Cleaning up hardware resources...')
        self._release()
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: State) -> TransitionCallbackReturn:
        # shutdown can be requested from Unconfigured, Inactive *or Active*:
        # stop the timer and destroy the publisher, otherwise a Finalized
        # node would keep publishing.
        self.get_logger().info('Shutting down sensor node permanently.')
        self._release()
        return TransitionCallbackReturn.SUCCESS

    def on_error(self, state: State) -> TransitionCallbackReturn:
        self.get_logger().error('Error during a transition: releasing resources.')
        self._release()
        return TransitionCallbackReturn.SUCCESS

    def _release(self):
        if self.timer is not None:
            self.timer.cancel()
            self.destroy_timer(self.timer)
            self.timer = None
        if self.pub_scan is not None:
            # destroy_lifecycle_publisher also removes it from the managed entities
            self.destroy_lifecycle_publisher(self.pub_scan)
            self.pub_scan = None

    # ---- data ------------------------------------------------------------
    def make_scan(self) -> LaserScan:
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        # Full 360 deg scan: num_beams beams, last beam one increment before +pi
        msg.angle_increment = 2.0 * math.pi / self.num_beams
        msg.angle_min = -math.pi
        msg.angle_max = msg.angle_min + (self.num_beams - 1) * msg.angle_increment
        msg.scan_time = self.period
        msg.time_increment = self.period / self.num_beams
        msg.range_min = 0.12
        msg.range_max = 10.0
        msg.ranges = [self.range_m] * self.num_beams
        return msg

    def publish_scan(self):
        if self.pub_scan is None:
            return
        self.pub_scan.publish(self.make_scan())


def main(args=None):
    rclpy.init(args=args)
    node = LifecycleLaserSensor()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
