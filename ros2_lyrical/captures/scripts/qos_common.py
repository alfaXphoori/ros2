"""Shared QoS argument parsing for qos_pub.py / qos_sub.py (docs/03 section 18, experiment 16)."""
import time

from rclpy.duration import Duration
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, LivelinessPolicy, QoSProfile,
                       ReliabilityPolicy)


def add_qos_args(ap):
    ap.add_argument('--reliability', choices=['reliable', 'best_effort'], default='reliable')
    ap.add_argument('--durability', choices=['volatile', 'transient_local'], default='volatile')
    ap.add_argument('--history', choices=['keep_last', 'keep_all'], default='keep_last')
    ap.add_argument('--depth', type=int, default=10)
    ap.add_argument('--liveliness', choices=['system_default', 'automatic', 'manual_by_topic'],
                    default='system_default')
    ap.add_argument('--lease', type=float, default=0.0, help='liveliness lease duration s (0 = default/infinite)')
    ap.add_argument('--deadline', type=float, default=0.0, help='s (0 = default/infinite)')
    ap.add_argument('--lifespan', type=float, default=0.0, help='s (0 = default/infinite)')
    ap.add_argument('--topic', default='qos_demo')


def profile(a):
    q = QoSProfile(
        depth=a.depth,
        history=HistoryPolicy.KEEP_LAST if a.history == 'keep_last' else HistoryPolicy.KEEP_ALL,
        reliability=ReliabilityPolicy.RELIABLE if a.reliability == 'reliable' else ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE if a.durability == 'volatile' else DurabilityPolicy.TRANSIENT_LOCAL,
    )
    if a.liveliness == 'automatic':
        q.liveliness = LivelinessPolicy.AUTOMATIC
    elif a.liveliness == 'manual_by_topic':
        q.liveliness = LivelinessPolicy.MANUAL_BY_TOPIC
    if a.lease > 0:
        q.liveliness_lease_duration = Duration(nanoseconds=int(a.lease * 1e9))
    if a.deadline > 0:
        q.deadline = Duration(nanoseconds=int(a.deadline * 1e9))
    if a.lifespan > 0:
        q.lifespan = Duration(nanoseconds=int(a.lifespan * 1e9))
    return q


T0 = time.monotonic()


def log(*args):
    """Line with seconds since process start (monotonic) so logs line up with pcap time roughly."""
    print(f'[t={time.monotonic() - T0:7.3f} wall={time.time():.3f}]', *args, flush=True)
