#!/usr/bin/env python3
"""QoS subscriber for docs/03 section 18 (experiment 16, QoS on the wire).

Subscribes to std_msgs/String on --topic with the QoS given on the command line for
--duration s and logs every sample (RECV q<seq>) and every QoS event with a monotonic
timestamp: requested incompatible QoS (rclpy default handler prints its own warning too),
liveliness changed (alive/not_alive counts), requested deadline missed.
--slow S sleeps S s inside each callback (a slow reader).
"""
import argparse
import time

import rclpy
from rclpy.event_handler import SubscriptionEventCallbacks
from rclpy.node import Node
from std_msgs.msg import String

from qos_common import add_qos_args, log, profile


def main():
    ap = argparse.ArgumentParser()
    add_qos_args(ap)
    ap.add_argument('--duration', type=float, default=5.0)
    ap.add_argument('--slow', type=float, default=0.0)
    a = ap.parse_args()

    rclpy.init()
    node = Node('qos_sub', enable_rosout=False, start_parameter_services=False)

    def on_msg(m):
        log('RECV', m.data)
        if a.slow > 0:
            time.sleep(a.slow)

    cbs = SubscriptionEventCallbacks(
        deadline=lambda e: log('EVENT requested_deadline_missed total', e.total_count),
        liveliness=lambda e: log('EVENT liveliness_changed alive', e.alive_count,
                                 'not_alive', e.not_alive_count,
                                 'alive_change', e.alive_count_change,
                                 'not_alive_change', e.not_alive_count_change),
    )   # incompatible_qos: rclpy's default handler (prints the standard warning)
    q = profile(a)
    node.create_subscription(String, a.topic, on_msg, q, event_callbacks=cbs)
    log('QOS', q)
    end = time.monotonic() + a.duration
    while time.monotonic() < end:
        rclpy.spin_once(node, timeout_sec=0.05)
    log('DONE')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
