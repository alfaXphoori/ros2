#!/usr/bin/env python3
"""QoS publisher for docs/03 section 18 (experiment 16, QoS on the wire).

Publishes std_msgs/String "q<seq>" (seq = 1..count) on --topic with the QoS given on the
command line, then stays alive for --linger s so late joiners / HEARTBEATs can be captured.

  --wait-match         wait until >= 1 subscription is matched before publishing
  --assert-every S     (MANUAL_BY_TOPIC) call publisher.assert_liveliness() every S s ...
  --assert-for S       ... during the first S s of the linger phase, then stop (liveliness lost)
Prints one log line per publish and every QoS event (offered incompatible QoS, deadline missed,
liveliness lost) with a monotonic timestamp.
"""
import argparse
import time

import rclpy
from rclpy.event_handler import PublisherEventCallbacks
from rclpy.node import Node
from std_msgs.msg import String

from qos_common import add_qos_args, log, profile


def main():
    ap = argparse.ArgumentParser()
    add_qos_args(ap)
    ap.add_argument('--count', type=int, default=5)
    ap.add_argument('--rate', type=float, default=10.0, help='Hz')
    ap.add_argument('--wait-match', action='store_true')
    ap.add_argument('--match-timeout', type=float, default=10.0)
    ap.add_argument('--linger', type=float, default=5.0)
    ap.add_argument('--assert-every', type=float, default=0.0)
    ap.add_argument('--assert-for', type=float, default=0.0)
    a = ap.parse_args()

    rclpy.init()
    node = Node('qos_pub', enable_rosout=False, start_parameter_services=False)
    cbs = PublisherEventCallbacks(
        deadline=lambda e: log('EVENT offered_deadline_missed total', e.total_count),
        liveliness=lambda e: log('EVENT liveliness_lost total', e.total_count),
        incompatible_qos=lambda e: log('EVENT offered_incompatible_qos total', e.total_count,
                                       'last_policy', e.last_policy_kind),
    )
    q = profile(a)
    pub = node.create_publisher(String, a.topic, q, event_callbacks=cbs)
    log('QOS', q)
    if a.wait_match:
        end = time.monotonic() + a.match_timeout
        while pub.get_subscription_count() < 1 and time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.05)
        log('matched subscriptions', pub.get_subscription_count())
        t = time.monotonic() + 0.5
        while time.monotonic() < t:
            rclpy.spin_once(node, timeout_sec=0.05)
    for i in range(1, a.count + 1):
        pub.publish(String(data=f'q{i}'))
        log('PUB', i)
        t = time.monotonic() + 1.0 / a.rate
        while time.monotonic() < t:
            rclpy.spin_once(node, timeout_sec=max(0.0, t - time.monotonic()))
    t_lin = time.monotonic()
    nxt = t_lin
    while time.monotonic() < t_lin + a.linger:
        now = time.monotonic()
        if a.assert_every > 0 and now >= nxt and now < t_lin + a.assert_for:
            pub.assert_liveliness()
            log('ASSERT')
            nxt = now + a.assert_every
        rclpy.spin_once(node, timeout_sec=0.02)
    log('DONE')
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
