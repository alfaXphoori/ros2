#!/usr/bin/env python3
"""Publisher for exp15 (run_sros2.sh, docs/03 §17). std_msgs/String "Hello World: N" on 'chatter',
RELIABLE KEEP_LAST 10, published by a timer from the moment the node exists (no wait for a match,
like the demo talker). Prints one JSON line at exit:
  t_create_ns   CLOCK_REALTIME just after the publisher was created
  t_match_ns    CLOCK_REALTIME when get_subscription_count() first became > 0 (polled every 1 ms)
  published, published_after_match
  cpu_user_s/cpu_sys_s  getrusage(RUSAGE_SELF) over the window [match, end] (all threads of the
                         process, i.e. rclpy + rmw + Fast DDS incl. its crypto), and *_total_s for
                         the whole process lifetime.
usage: sec_pub.py --rate HZ --duration S  [--ros-args --enclave /talker]
"""
import argparse, json, resource, sys, time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from rclpy.utilities import remove_ros_args
from std_msgs.msg import String


def ru():
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime, r.ru_stime


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rate', type=float, default=1000.0)
    ap.add_argument('--duration', type=float, default=10.0, help='s of publishing after the match')
    ap.add_argument('--match-timeout', type=float, default=20.0)
    a = ap.parse_args(remove_ros_args(sys.argv)[1:])
    rclpy.init(args=sys.argv)
    node = Node('sec_pub')
    pub = node.create_publisher(String, 'chatter', QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE))
    st = {'t_create_ns': time.clock_gettime_ns(time.CLOCK_REALTIME), 't_match_ns': None,
          'published': 0, 'published_after_match': 0}
    msg = String()

    def tick():
        st['published'] += 1
        msg.data = 'Hello World: %d' % st['published']
        pub.publish(msg)
        if st['t_match_ns'] is not None:
            st['published_after_match'] += 1
    node.create_timer(1.0 / a.rate, tick)
    ru0 = None
    t_end = None
    t_giveup = time.monotonic() + a.match_timeout
    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.001)
        now = time.monotonic()
        if st['t_match_ns'] is None:
            if pub.get_subscription_count() > 0:
                st['t_match_ns'] = time.clock_gettime_ns(time.CLOCK_REALTIME)
                ru0 = ru(); t_end = now + a.duration
            elif now > t_giveup:
                break
        elif now >= t_end:
            break
    u1, s1 = ru()
    if ru0:
        st['cpu_user_s'] = round(u1 - ru0[0], 4); st['cpu_sys_s'] = round(s1 - ru0[1], 4)
    st['cpu_user_total_s'] = round(u1, 4); st['cpu_sys_total_s'] = round(s1, 4)
    print(json.dumps(st), flush=True)
    time.sleep(1.0)   # let the last samples be acknowledged
    node.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
