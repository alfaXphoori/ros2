#!/usr/bin/env python3
"""
Week 08 Midterm Practical Exam: reference solution for part 2 (hospital_robot_node.py)

Node `midterm_robot_controller`:
- max_speed (PARAMETER_DOUBLE, default 0.6 m/s), validated in [0.1, 1.5] by a
  set-parameters callback (out-of-range -> successful=False + reason)
- publishes geometry_msgs/Twist on /cmd_vel at 5 Hz with v = min(0.3, max_speed)
- subscribes std_msgs/Float32 /sensor/temperature; while the latest reading is
  > 65.0 degC it logs a warning and throttles v by THROTTLE_FACTOR (50 %)

Run:
  ros2 run amr_week08 hospital_robot_node
  python3 Essential_ROS/Week_08_Midterm_Practical_Exam/solution/hospital_robot_node.py
"""

import signal
import threading

import rclpy
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import ParameterDescriptor, ParameterType, SetParametersResult
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from std_msgs.msg import Float32

CRUISE_SPEED = 0.3          # m/s, v = min(CRUISE_SPEED, max_speed)
SPEED_LIMITS = (0.1, 1.5)   # m/s, allowed range of max_speed
TEMP_LIMIT = 65.0           # degC, above this the robot is throttled
THROTTLE_FACTOR = 0.5       # speed multiplier while overheated
CONTROL_PERIOD = 0.2        # s (5 Hz)


def commanded_speed(max_speed, overheated):
    """Linear speed the controller should publish."""
    v = min(CRUISE_SPEED, max_speed)
    return v * THROTTLE_FACTOR if overheated else v


class MidtermRobotController(Node):
    def __init__(self):
        super().__init__('midterm_robot_controller')

        self.declare_parameter(
            'max_speed', 0.6,
            ParameterDescriptor(type=ParameterType.PARAMETER_DOUBLE,
                                description='Maximum linear speed [m/s], allowed 0.1-1.5'))
        self.max_speed = self.get_parameter('max_speed').value
        self.overheated = False

        self.add_on_set_parameters_callback(self.param_callback)

        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub_temp = self.create_subscription(
            Float32, '/sensor/temperature', self.temp_callback, qos_profile_sensor_data)
        self.timer = self.create_timer(CONTROL_PERIOD, self.control_loop)
        self.get_logger().info(f'Midterm controller running (max_speed={self.max_speed} m/s)')

    def param_callback(self, params):
        for param in params:
            if param.name != 'max_speed':
                continue
            if param.type_ != param.Type.DOUBLE:
                return SetParametersResult(successful=False,
                                           reason='max_speed must be a double')
            low, high = SPEED_LIMITS
            if not (low <= param.value <= high):
                return SetParametersResult(
                    successful=False,
                    reason=f'max_speed {param.value} out of safe limit [{low}, {high}] m/s')
        # All values valid: apply them
        for param in params:
            if param.name == 'max_speed':
                self.max_speed = param.value
                self.get_logger().info(f'max_speed updated to {self.max_speed} m/s')
        return SetParametersResult(successful=True)

    def temp_callback(self, msg: Float32):
        overheated = msg.data > TEMP_LIMIT
        if overheated and not self.overheated:
            self.get_logger().warn(
                f'High temperature {msg.data:.1f} C > {TEMP_LIMIT} C: '
                f'throttling speed to {commanded_speed(self.max_speed, True):.2f} m/s')
        elif not overheated and self.overheated:
            self.get_logger().info(f'Temperature back to {msg.data:.1f} C: normal speed')
        self.overheated = overheated

    def control_loop(self):
        cmd = Twist()
        cmd.linear.x = commanded_speed(self.max_speed, self.overheated)
        cmd.angular.z = 0.0
        self.pub_cmd.publish(cmd)


def main(args=None):
    # Clean shutdown as in Week 2: SIGINT/SIGTERM only set a flag, the loop stops between
    # spin_once() calls (rclpy's own handler could shut the context down mid-callback).
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    node = MidtermRobotController()
    try:
        while not stop.is_set() and rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
    except ExternalShutdownException:
        pass
    finally:
        # stopping: ignore further signals (Python resets our handler at exit -> 2nd Ctrl+C = -2)
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal.SIG_IGN)
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
