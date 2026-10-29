#!/usr/bin/env python3
"""
Week 05 Lab: Dynamic Parameter Node with two layers of validation

Layer 1 (rclpy, before any user code): the parameter TYPE is fixed by declare_parameter()
         -> setting max_linear_speed to an integer (1 instead of 1.0) is rejected by rclpy itself
         with "Wrong parameter type"; our callback never sees it.
Layer 2 (add_on_set_parameters_callback): engineering rules such as the safe speed range.

Accepted values are applied in a post-set callback and the active speed limit is published
(latched) on the `speed_limit` topic, so other nodes actually use the new value.
"""

import signal

import rclpy
from rcl_interfaces.msg import ParameterDescriptor, SetParametersResult
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile
from std_msgs.msg import Float64


def ignore_further_sigint():
    """Ctrl+C under `ros2 launch` arrives twice (terminal process group + launch forwarding it).
    Ignore later SIGINTs so they cannot interrupt the cleanup and kill us with a traceback."""
    signal.signal(signal.SIGINT, signal.SIG_IGN)


SPEED_RANGE = (0.1, 2.5)   # m/s
MIN_SAFETY_MARGIN = 0.1    # m


class FleetParametersNode(Node):
    def __init__(self):
        super().__init__('fleet_parameters')

        # Declare parameters with default values and descriptions (type is fixed from the default)
        self.declare_parameter('fleet_id', 'AMR_ALPHA_01',
                               ParameterDescriptor(description='Robot identifier in the fleet'))
        self.declare_parameter('max_linear_speed', 0.8, ParameterDescriptor(
            description='Speed limit [m/s]',
            additional_constraints=f'{SPEED_RANGE[0]} <= value <= {SPEED_RANGE[1]}'))
        self.declare_parameter('safety_margin', 0.35, ParameterDescriptor(
            description='Obstacle stop distance [m]',
            additional_constraints=f'value >= {MIN_SAFETY_MARGIN}'))
        self.declare_parameter('enable_obstacle_stop', True)

        self.fleet_id = self.get_parameter('fleet_id').value
        self.max_linear_speed = self.get_parameter('max_linear_speed').value
        self.safety_margin = self.get_parameter('safety_margin').value

        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.pub_speed_limit = self.create_publisher(Float64, 'speed_limit', latched)
        self.publish_speed_limit()

        # validate (may reject) -> rclpy stores the values -> apply (only after success)
        self.add_on_set_parameters_callback(self.validate_parameters)
        self.add_post_set_parameters_callback(self.apply_parameters)

        self.get_logger().info(
            f'🤖 [FleetParametersNode] Initialized: ID={self.fleet_id}, '
            f'MaxSpeed={self.max_linear_speed}m/s, Margin={self.safety_margin}m')

    def validate_parameters(self, params):
        """Reject unsafe values. Runs for all params of one request before anything changes."""
        for param in params:
            if param.name == 'max_linear_speed':
                low, high = SPEED_RANGE
                if not (low <= param.value <= high):
                    return SetParametersResult(
                        successful=False,
                        reason=f'Speed {param.value} is outside valid safety range '
                               f'[{low}, {high}] m/s!')
            elif param.name == 'safety_margin':
                if param.value < MIN_SAFETY_MARGIN:
                    return SetParametersResult(
                        successful=False,
                        reason=f'safety_margin cannot be smaller than {MIN_SAFETY_MARGIN} m!')
        return SetParametersResult(successful=True)

    def apply_parameters(self, params):
        """Called only after every parameter in the request was accepted and stored."""
        for param in params:
            if param.name == 'max_linear_speed':
                self.max_linear_speed = param.value
                self.publish_speed_limit()
                self.get_logger().warn(f'⚡ max_linear_speed updated to: {param.value} m/s')
            elif param.name == 'safety_margin':
                self.safety_margin = param.value
                self.get_logger().info(f'🛡️ safety_margin updated to: {param.value} m')
            elif param.name == 'fleet_id':
                self.fleet_id = param.value
                self.get_logger().info(f'🏷️ fleet_id changed to: "{param.value}"')

    def publish_speed_limit(self):
        self.pub_speed_limit.publish(Float64(data=float(self.max_linear_speed)))


def main(args=None):
    rclpy.init(args=args)
    node = FleetParametersNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        ignore_further_sigint()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
