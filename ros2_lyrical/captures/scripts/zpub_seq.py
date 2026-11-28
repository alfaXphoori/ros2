# Sequence-numbered std_msgs/String publisher for experiment 11 (docs/03 §6): 10 Hz, "n=<k>".
import sys, time, rclpy
from rclpy.node import Node
from std_msgs.msg import String
n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
rclpy.init(); node = Node('zpub'); pub = node.create_publisher(String, 'seq', 10)
for k in range(n):
    pub.publish(String(data=f'n={k}')); node.get_logger().info(f'pub n={k}')
    t0 = time.time()
    while time.time() - t0 < 0.1: rclpy.spin_once(node, timeout_sec=0.02)
rclpy.shutdown()
