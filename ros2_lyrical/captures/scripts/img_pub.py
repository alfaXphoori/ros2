import sys, time, rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
rel = ReliabilityPolicy.BEST_EFFORT if (len(sys.argv) > 1 and sys.argv[1] == 'be') else ReliabilityPolicy.RELIABLE
n_msgs = int(sys.argv[2]) if len(sys.argv) > 2 else 5
rclpy.init(); node = Node('img_pub')
pub = node.create_publisher(Image, 'img', QoSProfile(depth=5, reliability=rel, history=HistoryPolicy.KEEP_LAST))
msg = Image(height=480, width=640, encoding='rgb8', is_bigendian=0, step=640*3)
msg.data = bytes((i % 251 for i in range(640*480*3)))
# Discovery: wait until the subscriber is matched (timeout 15 s), but never start before
# 3.0 s after the publisher was created, which is the fixed delay the 2026-11-24 runs used.
t_start = time.time()
while pub.get_subscription_count() < 1 and time.time() - t_start < 15.0: time.sleep(0.05)
t_match = time.time() - t_start
if t_match < 3.0: time.sleep(3.0 - t_match)
node.get_logger().info(f'matched {pub.get_subscription_count()} subscription(s) after {t_match:.2f} s, '
                       f'publishing from {time.time() - t_start:.2f} s')
for k in range(n_msgs):
    msg.header.frame_id = f'f{k}'
    pub.publish(msg); node.get_logger().info(f'published {k}')
    t0 = time.time()
    while time.time() - t0 < 0.5: rclpy.spin_once(node, timeout_sec=0.05)
time.sleep(1.0); rclpy.shutdown()
