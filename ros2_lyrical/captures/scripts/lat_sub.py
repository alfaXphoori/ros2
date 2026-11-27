#!/usr/bin/env python3
"""Latency subscriber for docs/03 section 10 (pairs with lat_pub.py).

t_recv = clock_gettime_ns(CLOCK) is the FIRST statement of the subscription callback;
the message is parsed afterwards.  Samples are kept in memory and written once at exit:
  <out>.csv        seq,t_pub_ns,t_recv_ns,latency_ns   (arrival order)
  <out>.meta.json  expected/received/duplicates/out_of_order/missing/bad_length ...

Exit conditions: all --count sequence numbers received, or no message for --idle s after
the first one, or --timeout s in total.
"""
import argparse
import json
import time

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

CLOCKS = {'monotonic': time.CLOCK_MONOTONIC, 'realtime': time.CLOCK_REALTIME}
IMAGE_BYTES = 640 * 480 * 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--payload', choices=['small', 'image'], default='small')
    ap.add_argument('--count', type=int, default=200)
    ap.add_argument('--reliability', choices=['reliable', 'best_effort'], default='reliable')
    ap.add_argument('--depth', type=int, default=10)
    ap.add_argument('--clock', choices=list(CLOCKS), default='monotonic')
    ap.add_argument('--idle', type=float, default=4.0)
    ap.add_argument('--timeout', type=float, default=60.0)
    ap.add_argument('--topic', default='lat')
    ap.add_argument('--out', required=True, help='path prefix, e.g. /out/run_00')
    a = ap.parse_args()
    clk = CLOCKS[a.clock]
    gettime = time.clock_gettime_ns

    rclpy.init()
    node = Node('lat_sub')
    rel = ReliabilityPolicy.RELIABLE if a.reliability == 'reliable' else ReliabilityPolicy.BEST_EFFORT
    qos = QoSProfile(depth=a.depth, history=HistoryPolicy.KEEP_LAST, reliability=rel)
    rows = []       # (seq, t_pub_ns, t_recv_ns); parsed in the callback so images are not kept
    bad_len = [0]
    last_rx = [None]

    if a.payload == 'small':
        from std_msgs.msg import String

        def cb(m):
            t_recv = gettime(clk)
            s, t, _ = m.data.split(':', 2)
            rows.append((int(s), int(t), t_recv))
            last_rx[0] = time.monotonic()
        node.create_subscription(String, a.topic, cb, qos)
    else:
        from sensor_msgs.msg import Image

        def cb(m):
            t_recv = gettime(clk)
            t_pub = m.header.stamp.sec * 1_000_000_000 + m.header.stamp.nanosec
            if len(m.data) != IMAGE_BYTES or m.height != 480 or m.width != 640:
                bad_len[0] += 1
            rows.append((int(m.header.frame_id), t_pub, t_recv))
            last_rx[0] = time.monotonic()
        node.create_subscription(Image, a.topic, cb, qos)

    ex = SingleThreadedExecutor()
    ex.add_node(node)
    t_start = time.monotonic()
    seen = set()
    n_seen = 0
    reason = 'timeout'
    while time.monotonic() - t_start < a.timeout:
        ex.spin_once(timeout_sec=0.1)
        while n_seen < len(rows):
            seen.add(rows[n_seen][0]); n_seen += 1
        if len(seen) >= a.count:
            reason = 'complete'; break
        if last_rx[0] is not None and time.monotonic() - last_rx[0] > a.idle:
            reason = 'idle'; break

    seqs = [r[0] for r in rows]
    ooo = sum(1 for i in range(1, len(seqs)) if seqs[i] < seqs[i - 1])
    uniq = set(seqs)
    with open(a.out + '.csv', 'w') as f:
        f.write('seq,t_pub_ns,t_recv_ns,latency_ns\n')
        for s, tp, tr in rows:
            f.write('%d,%d,%d,%d\n' % (s, tp, tr, tr - tp))
    meta = {
        'payload': a.payload, 'reliability': a.reliability, 'depth': a.depth, 'clock': a.clock,
        'expected': a.count, 'received': len(rows), 'unique': len(uniq),
        'duplicates': len(rows) - len(uniq), 'out_of_order': ooo,
        'missing': sorted(set(range(a.count)) - uniq), 'bad_length': bad_len[0],
        'exit_reason': reason,
    }
    with open(a.out + '.meta.json', 'w') as f:
        json.dump(meta, f)
    print('lat_sub: received=%d/%d ooo=%d bad_len=%d exit=%s'
          % (len(uniq), a.count, ooo, bad_len[0], reason), flush=True)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
