# Subscriber for experiment 11 (docs/03 §14): logs every received "n=<k>" with the ROS log timestamp.
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
rclpy.init(); node = Node('zsub')
node.create_subscription(String, 'seq', lambda m: node.get_logger().info(f'got {m.data}'), 10)
node.get_logger().info('subscription ready')
try: rclpy.spin(node)
except Exception: pass
