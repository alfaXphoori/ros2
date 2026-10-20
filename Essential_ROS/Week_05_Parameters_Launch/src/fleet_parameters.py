#!/usr/bin/env python3
"""
Lab 1.4: Dynamic Parameter Node with Callback Validation
Demonstrates declaring ROS 2 parameters and intercepting changes via add_on_set_parameters_callback.
"""

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult


class FleetParametersNode(Node):
    def __init__(self):
        super().__init__('fleet_parameters')

        # Declare parameters with default values and descriptions
        self.declare_parameter('fleet_id', 'AMR_ALPHA_01')
        self.declare_parameter('max_linear_speed', 0.8)
        self.declare_parameter('safety_margin', 0.35)
        self.declare_parameter('enable_obstacle_stop', True)

        # Register callback for dynamic changes
        self.add_on_set_parameters_callback(self.parameters_callback)

        fleet_id = self.get_parameter('fleet_id').get_parameter_value().string_value
        max_speed = self.get_parameter('max_linear_speed').get_parameter_value().double_value
        margin = self.get_parameter('safety_margin').get_parameter_value().double_value

        self.get_logger().info(f'🤖 [FleetParametersNode] Initialized: ID={fleet_id}, MaxSpeed={max_speed}m/s, Margin={margin}m')

    def parameters_callback(self, params):
        result = SetParametersResult()
        result.successful = True

        for param in params:
            if param.name == 'max_linear_speed':
                if param.type_ not in (Parameter.Type.DOUBLE, Parameter.Type.INTEGER):
                    result.successful = False
                    result.reason = 'max_linear_speed must be a floating point number.'
                    return result
                if not (0.1 <= param.value <= 2.5):
                    result.successful = False
                    result.reason = f'Speed {param.value} is outside valid safety range [0.1, 2.5] m/s!'
                    return result
                self.get_logger().warn(f'⚡ max_linear_speed updated to: {param.value} m/s')

            elif param.name == 'safety_margin':
                if param.value < 0.1:
                    result.successful = False
                    result.reason = 'safety_margin cannot be smaller than 0.1 m!'
                    return result
                self.get_logger().info(f'🛡️ safety_margin updated to: {param.value} m')

            elif param.name == 'fleet_id':
                self.get_logger().info(f'🏷️ fleet_id changed to: "{param.value}"')

        return result


def main(args=None):
    rclpy.init(args=args)
    node = FleetParametersNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down Fleet Parameters Node...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
