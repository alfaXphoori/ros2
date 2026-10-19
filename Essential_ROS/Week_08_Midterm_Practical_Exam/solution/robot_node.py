#!/usr/bin/env python3
"""
Week 08 Midterm Practical Exam: Sample Solution Node
Demonstrates an integrated AMR Controller:
- Publisher for velocity commands (/cmd_vel)
- Dynamic Parameter for max speed validation
- Subscriber for sensor temperature monitor
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32
from rcl_interfaces.msg import SetParametersResult, ParameterType


class MidtermRobotController(Node):
    def __init__(self):
        super().__init__('midterm_robot_controller')

        self.declare_parameter('max_speed', 0.6)
        self.max_speed = self.get_parameter('max_speed').value

        self.add_on_set_parameters_callback(self.param_callback)

        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub_temp = self.create_subscription(
            Float32, '/sensor/temperature', self.temp_callback, 10
        )

        self.timer = self.create_timer(0.2, self.control_loop)
        self.get_logger().info(f'✅ Midterm Solution Controller Running (MaxSpeed={self.max_speed}m/s)')

    def param_callback(self, params):
        result = SetParametersResult()
        result.successful = True
        for param in params:
            if param.name == 'max_speed':
                if not (0.1 <= param.value <= 1.5):
                    result.successful = False
                    result.reason = 'Speed out of safe limit [0.1, 1.5]'
                    return result
                self.max_speed = param.value
                self.get_logger().info(f'Max speed updated to: {self.max_speed}')
        return result

    def temp_callback(self, msg: Float32):
        if msg.data > 65.0:
            self.get_logger().warn(f'⚠️ High temperature detected: {msg.data}°C! Throttling robot.')

    def control_loop(self):
        cmd = Twist()
        cmd.linear.x = min(0.3, self.max_speed)
        cmd.angular.z = 0.0
        self.pub_cmd.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = MidtermRobotController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
