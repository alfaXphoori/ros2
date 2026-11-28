#!/usr/bin/env python3
"""Subscriber for exp15 (run_sros2.sh, docs/03 §2.4): counts std_msgs/String on 'chatter'
(RELIABLE KEEP_LAST 10). Prints "subscription ready" once created, then one JSON line at exit:
t_first_recv_ns (CLOCK_REALTIME, first statement of the first callback), received, and
getrusage(RUSAGE_SELF) user/sys from the first sample to the end (cpu_user_s/cpu_sys_s).
Exits after --idle s without data (once something arrived) or after --timeout s.
usage: sec_sub.py [--idle 2] [--timeout 40] [--ros-args --enclave /listener]
"""
import argparse, json, resource, sys, time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from rclpy.utilities import remove_ros_args
from std_msgs.msg import String


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--idle', type=float, default=2.0)
    ap.add_argument('--timeout', type=float, default=40.0)
    a = ap.parse_args(remove_ros_args(sys.argv)[1:])
    rclpy.init(args=sys.argv)
    node = Node('sec_sub')
    st = {'t_first_recv_ns': None, 'received': 0}
    last = [None]
    ru0 = [None]

    def cb(_m):
        if st['t_first_recv_ns'] is None:
            st['t_first_recv_ns'] = time.clock_gettime_ns(time.CLOCK_REALTIME)
            r = resource.getrusage(resource.RUSAGE_SELF); ru0[0] = (r.ru_utime, r.ru_stime)
        st['received'] += 1
        last[0] = time.monotonic()
    node.create_subscription(String, 'chatter', cb, QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE))
    print('subscription ready', flush=True)
    t_giveup = time.monotonic() + a.timeout
    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0.05)
        now = time.monotonic()
        if (last[0] and now - last[0] > a.idle) or now > t_giveup:
            break
    r = resource.getrusage(resource.RUSAGE_SELF)
    if ru0[0]:
        st['cpu_user_s'] = round(r.ru_utime - ru0[0][0], 4); st['cpu_sys_s'] = round(r.ru_stime - ru0[0][1], 4)
    print(json.dumps(st), flush=True)
    node.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
