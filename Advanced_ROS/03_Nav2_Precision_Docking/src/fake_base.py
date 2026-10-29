#!/usr/bin/env python3
"""
Advanced Module 03: kinematic fake differential-drive base (no simulator, no hardware).

  cmd_vel (geometry_msgs/Twist, or TwistStamped with -p stamped:=true)
      -> unicycle integration at `rate` Hz (velocity/acceleration limited)
      -> odom (nav_msgs/Odometry) + TF odom -> base_footprint

The pose it integrates is the ground truth of the lab, so docking accuracy can be measured
exactly. Commands older than cmd_timeout stop the robot (like diff_drive_controller).
"""

import math

import rclpy
from geometry_msgs.msg import TransformStamped, Twist, TwistStamped
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


def clamp(value, low, high):
    return max(low, min(high, value))


def step_toward(current, target, max_delta):
    return current + clamp(target - current, -max_delta, max_delta)


def integrate(x, y, yaw, v, w, dt):
    """Exact unicycle integration over dt (arc for w != 0)."""
    if abs(w) < 1e-9:
        return x + v * dt * math.cos(yaw), y + v * dt * math.sin(yaw), yaw
    r = v / w
    yaw2 = yaw + w * dt
    return (x + r * (math.sin(yaw2) - math.sin(yaw)),
            y - r * (math.cos(yaw2) - math.cos(yaw)),
            math.atan2(math.sin(yaw2), math.cos(yaw2)))


class FakeBase(Node):
    def __init__(self):
        super().__init__('fake_base')
        p = self.declare_parameter
        self.x = p('initial_x', 0.0).value
        self.y = p('initial_y', 0.0).value
        self.yaw = p('initial_yaw', 0.0).value
        self.rate = p('rate', 50.0).value
        self.cmd_timeout = p('cmd_timeout', 0.5).value
        self.max_v = p('max_linear_velocity', 0.5).value
        self.max_w = p('max_angular_velocity', 1.5).value
        self.max_acc_v = p('max_linear_acceleration', 1.0).value
        self.max_acc_w = p('max_angular_acceleration', 3.0).value
        self.odom_frame = p('odom_frame', 'odom').value
        self.base_frame = p('base_frame', 'base_footprint').value
        stamped = p('stamped', False).value

        self.v = self.w = 0.0
        self.cmd_v = self.cmd_w = 0.0
        self.last_cmd = None
        if stamped:
            self.create_subscription(TwistStamped, 'cmd_vel', lambda m: self.on_cmd(m.twist), 10)
        else:
            self.create_subscription(Twist, 'cmd_vel', self.on_cmd, 10)
        self.pub_odom = self.create_publisher(Odometry, 'odom', 10)
        self.tf = TransformBroadcaster(self)
        self.last_t = self.get_clock().now()
        self.create_timer(1.0 / self.rate, self.on_timer)
        self.get_logger().info(
            f'fake base at x={self.x:.3f} y={self.y:.3f} yaw={self.yaw:.3f}, '
            f'cmd_vel ({"TwistStamped" if stamped else "Twist"}) -> odom + TF '
            f'{self.odom_frame}->{self.base_frame}')

    def on_cmd(self, twist):
        self.cmd_v = clamp(twist.linear.x, -self.max_v, self.max_v)
        self.cmd_w = clamp(twist.angular.z, -self.max_w, self.max_w)
        self.last_cmd = self.get_clock().now()

    def on_timer(self):
        now = self.get_clock().now()
        dt = (now - self.last_t).nanoseconds * 1e-9
        self.last_t = now
        if dt <= 0.0:
            return
        if self.last_cmd is None or (now - self.last_cmd).nanoseconds * 1e-9 > self.cmd_timeout:
            self.cmd_v = self.cmd_w = 0.0
        self.v = step_toward(self.v, self.cmd_v, self.max_acc_v * dt)
        self.w = step_toward(self.w, self.cmd_w, self.max_acc_w * dt)
        self.x, self.y, self.yaw = integrate(self.x, self.y, self.yaw, self.v, self.w, dt)

        stamp = now.to_msg()
        qz, qw = math.sin(self.yaw / 2.0), math.cos(self.yaw / 2.0)
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = self.odom_frame
        t.child_frame_id = self.base_frame
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self.tf.sendTransform(t)

        odom = Odometry()
        odom.header = t.header
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = self.v
        odom.twist.twist.angular.z = self.w
        self.pub_odom.publish(odom)


def main(args=None):
    rclpy.init(args=args)
    node = FakeBase()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
