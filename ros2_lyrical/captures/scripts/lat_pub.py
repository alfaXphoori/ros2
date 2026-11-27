#!/usr/bin/env python3
"""Latency publisher for docs/03 section 10 (application-level end-to-end latency, rclpy).

Each message carries its sequence number and t_pub = clock_gettime_ns(CLOCK) taken
immediately before publish().  The subscriber (lat_sub.py) takes t_recv as the first
statement of its callback, so latency = t_recv - t_pub includes rclpy serialization,
rmw/DDS, the transport, and executor dispatch on the receiving side.

  small : std_msgs/String, data = "<seq>:<t_pub_ns>" padded with '.' to 64 characters
  image : sensor_msgs/Image 640x480 rgb8 (921 600 B), header.stamp = t_pub (sec/nanosec),
          header.frame_id = str(seq)

Clock: CLOCK_MONOTONIC by default.  Containers on one host share the kernel clock, so no
synchronisation is needed.  On two machines use --clock realtime and synchronise the
clocks (PTP/chrony); see run_latency.sh --help.
"""
import argparse
import sys
import time

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

CLOCKS = {'monotonic': time.CLOCK_MONOTONIC, 'realtime': time.CLOCK_REALTIME}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--payload', choices=['small', 'image'], default='small')
    ap.add_argument('--count', type=int, default=200)
    ap.add_argument('--rate', type=float, default=100.0, help='Hz')
    ap.add_argument('--reliability', choices=['reliable', 'best_effort'], default='reliable')
    ap.add_argument('--depth', type=int, default=10)
    ap.add_argument('--clock', choices=list(CLOCKS), default='monotonic')
    ap.add_argument('--match-timeout', type=float, default=15.0)
    ap.add_argument('--settle', type=float, default=1.0, help='s to wait after the match')
    ap.add_argument('--ack-timeout', type=float, default=5.0)
    ap.add_argument('--linger', type=float, default=1.0,
                    help='s to stay alive after the last publish/ack (lets the extra '
                         '<topic>/_buf_cpu writer of uint8[] messages finish delivery)')
    ap.add_argument('--topic', default='lat')
    ap.add_argument('--pub-out', default=None,
                    help='optional CSV of seq,t_pub_ns,t_after_publish_ns (publish() call cost)')
    a = ap.parse_args()
    clk = CLOCKS[a.clock]

    rclpy.init()
    node = Node('lat_pub')
    rel = ReliabilityPolicy.RELIABLE if a.reliability == 'reliable' else ReliabilityPolicy.BEST_EFFORT
    qos = QoSProfile(depth=a.depth, history=HistoryPolicy.KEEP_LAST, reliability=rel)

    if a.payload == 'small':
        from std_msgs.msg import String
        msg = String()
        pub = node.create_publisher(String, a.topic, qos)
    else:
        from sensor_msgs.msg import Image
        msg = Image(height=480, width=640, encoding='rgb8', is_bigendian=0, step=640 * 3)
        msg.data = bytes(i % 251 for i in range(640 * 480 * 3))
        pub = node.create_publisher(Image, a.topic, qos)

    # Readiness instead of a blind sleep: wait for the subscriber to be matched.
    t0 = time.monotonic()
    while pub.get_subscription_count() < 1:
        if time.monotonic() - t0 > a.match_timeout:
            print('lat_pub: no subscriber matched within %.1f s' % a.match_timeout, file=sys.stderr)
            node.destroy_node(); rclpy.shutdown(); sys.exit(2)
        rclpy.spin_once(node, timeout_sec=0.05)
    match_s = time.monotonic() - t0
    time.sleep(a.settle)

    after = [0] * a.count
    stamps = [0] * a.count
    period = 1.0 / a.rate
    start = time.monotonic() + 0.01
    for seq in range(a.count):
        target = start + seq * period
        d = target - time.monotonic()
        if d > 0:
            time.sleep(d)
        if a.payload == 'small':
            t = time.clock_gettime_ns(clk)
            msg.data = ('%d:%d:' % (seq, t)).ljust(64, '.')
        else:
            t = time.clock_gettime_ns(clk)
            msg.header.stamp.sec = t // 1_000_000_000
            msg.header.stamp.nanosec = t % 1_000_000_000
            msg.header.frame_id = str(seq)
        pub.publish(msg)
        after[seq] = time.clock_gettime_ns(clk)
        stamps[seq] = t
    late = time.monotonic() - (start + (a.count - 1) * period)

    acked = None
    if a.reliability == 'reliable':
        acked = pub.wait_for_all_acked(Duration(seconds=a.ack_timeout))
    # wait_for_all_acked() covers only the main writer; in Lyrical the image payload
    # travels on the separate <topic>/_buf_cpu writer (docs/03 section 3), so linger.
    t_end = time.monotonic() + a.linger
    while time.monotonic() < t_end:
        rclpy.spin_once(node, timeout_sec=0.05)
    if a.pub_out:
        with open(a.pub_out, 'w') as f:
            f.write('seq,t_pub_ns,t_after_publish_ns,publish_call_ns\n')
            for i in range(a.count):
                f.write('%d,%d,%d,%d\n' % (i, stamps[i], after[i], after[i] - stamps[i]))
    print('lat_pub: sent=%d match_s=%.3f end_lag_s=%.4f all_acked=%s'
          % (a.count, match_s, late, acked), flush=True)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
