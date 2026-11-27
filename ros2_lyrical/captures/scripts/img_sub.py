import sys, rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image
rel = ReliabilityPolicy.BEST_EFFORT if (len(sys.argv) > 1 and sys.argv[1] == 'be') else ReliabilityPolicy.RELIABLE
rclpy.init(); node = Node('img_sub')
node.create_subscription(Image, 'img', lambda m: node.get_logger().info(f'got {m.header.frame_id} {len(m.data)} B'), QoSProfile(depth=5, reliability=rel))
node.get_logger().info('subscription ready')   # run_experiments.sh waits for this line
try: rclpy.spin(node)
except Exception: pass
