#!/usr/bin/env python3
"""Correlate one ROS 2 message across ros2_tracing (LTTng-UST) and two tcpdump captures.

Run inside lyrical-wire:exp-extra (needs python3-bt2, babeltrace2, tshark), see run_trace.sh.
Input  (--in):  A/ctf, A/A.raw.pcap, A/clock_*.txt, A/talker.log   (talker container)
                B/ctf, B/B.raw.pcap, B/clock_*.txt, B/listener.log (listener container)
Output (--res): trace_one_sample.csv, trace_stage_stats.csv, trace_env.txt,
                trace_babeltrace_excerpt.txt

Correlation key: rmw_publish.timestamp (talker) == RTPS INFO_TS of the DATA frame (both pcaps)
== rmw_take.source_timestamp (listener).  The frame's writerSN and its CDR string
"Hello World: N" give N.  rclcpp_publish/rcl_publish are matched to rmw_publish by message
pointer on the same thread; rcl_take/rclcpp_take/callback_start/callback_end are the next events
of that kind on the listener thread that emitted rmw_take.

Clocks: LTTng-UST timestamps are CLOCK_MONOTONIC (cycles, ns); babeltrace2/bt2 convert them to
realtime with the clock-class offset in the CTF metadata (ns_from_origin).  tcpdump timestamps
are CLOCK_REALTIME (software, nanosecond precision).  Both containers share the host clocks.
The offset in the metadata is compared with clock_offset.py's measurement before/after the run.
Stdlib + bt2 only.
"""
import argparse
import calendar
import csv
import os
import re
import statistics
import subprocess
import time

import bt2

WARMUP_BELOW = 5  # samples N < 5 are not used in the statistics


def kv(path):
    d = {}
    with open(path) as f:
        for line in f:
            if '=' in line:
                k, v = line.strip().split('=', 1)
                d[k] = v
    return d


def read_ctf(path):
    """List of dicts: name, t (ns_from_origin = realtime via metadata offset), cyc (monotonic ns),
    vtid, fields...  Also returns the clock-class offset in ns."""
    evs, offset = [], None
    for msg in bt2.TraceCollectionMessageIterator(path):
        if type(msg) is not bt2._EventMessageConst:
            continue
        ev = msg.event
        cs = msg.default_clock_snapshot
        if offset is None:
            cc = cs.clock_class
            offset = cc.offset.seconds * 1_000_000_000 + cc.offset.cycles * 1_000_000_000 // cc.frequency
        d = {'name': ev.name, 't': cs.ns_from_origin, 'cyc': cs.value}
        ctx = ev.common_context_field
        if ctx is not None and 'vtid' in ctx:
            d['vtid'] = int(ctx['vtid'])
        for k, v in ev.payload_field.items():
            d[k] = str(v) if isinstance(v, bt2._StringFieldConst) else (
                int(v) if isinstance(v, (bt2._IntegerFieldConst,)) else None)
        evs.append(d)
    return evs, offset


def frames(pcap):
    """{info_ts_ns: (time_ns, writerSN, N, frame_len)} for DATA frames carrying 'Hello World: N'."""
    out = subprocess.run(
        ['tshark', '-r', pcap, '-Y', 'frame contains "Hello World"', '-T', 'fields',
         '-E', 'separator=\t', '-e', 'frame.time_epoch', '-e', 'rtps.sm.seqNumber',
         '-e', 'rtps.info_ts.timestamp', '-e', 'frame.len', '-e', 'udp.payload'],
        capture_output=True, text=True, check=True).stdout
    res = {}
    for line in out.splitlines():
        ep, sn, ts, flen, data = line.split('\t')[:5]
        s, ns = ep.split('.')
        t_ns = int(s) * 1_000_000_000 + int(ns.ljust(9, '0')[:9])
        m = re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)\.(\d+)Z', ts)
        txt = bytes.fromhex(data.replace(':', '')).decode('latin1')
        n = int(re.search(r'Hello World: (\d+)', txt).group(1))
        sec = calendar.timegm(time.strptime(m.group(1), '%Y-%m-%dT%H:%M:%S'))
        res[sec * 1_000_000_000 + int(m.group(2).ljust(9, '0')[:9])] = (t_ns, int(sn.split(',')[0]), n, int(flen))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--res', required=True)
    ap.add_argument('--sample', type=int, default=10)
    ap.add_argument('--host-name', default='')
    a = ap.parse_args()
    A, B = os.path.join(a.inp, 'A'), os.path.join(a.inp, 'B')

    ea, off_a = read_ctf(os.path.join(A, 'ctf'))
    eb, off_b = read_ctf(os.path.join(B, 'ctf'))
    fa, fb = frames(os.path.join(A, 'A.raw.pcap')), frames(os.path.join(B, 'B.raw.pcap'))

    # talker: /chatter publisher handles
    pinit = next(e for e in ea if e['name'] == 'ros2:rcl_publisher_init' and e['topic_name'] == '/chatter')
    rmw_pub_h = pinit['rmw_publisher_handle']
    sinit = next(e for e in eb if e['name'] == 'ros2:rcl_subscription_init' and e['topic_name'] == '/chatter')
    rmw_sub_h = sinit['rmw_subscription_handle']

    samples = {}
    for i, e in enumerate(ea):
        if e['name'] != 'ros2:rmw_publish' or e['rmw_publisher_handle'] != rmw_pub_h:
            continue
        src = e['timestamp']
        if src not in fa or src not in fb:
            continue
        n = fa[src][2]
        s = {'N': n, 'writerSN': fa[src][1], 'frame_len': fa[src][3], 'src': src}
        # backwards on same thread: rcl_publish, rclcpp_publish with same message pointer
        for j in range(i - 1, max(i - 50, -1), -1):
            p = ea[j]
            if p.get('vtid') != e['vtid'] or p.get('message') != e['message']:
                continue
            if p['name'] == 'ros2:rcl_publish' and 'rcl_publish' not in s:
                s['rcl_publish'] = p['t']
            elif p['name'] == 'ros2:rclcpp_publish' and 'rclcpp_publish' not in s:
                s['rclcpp_publish'] = p['t']
        s['rmw_publish'] = e['t']
        s['source_timestamp'] = src
        s['frame_tx_A_eth0'] = fa[src][0]
        s['frame_rx_B_eth0'] = fb[src][0]
        samples[src] = s
    for i, e in enumerate(eb):
        if e['name'] != 'ros2:rmw_take' or e['rmw_subscription_handle'] != rmw_sub_h or not e['taken']:
            continue
        s = samples.get(e['source_timestamp'])
        if s is None:
            continue
        s['rmw_take'] = e['t']
        want = ['ros2:rcl_take', 'ros2:rclcpp_take', 'ros2:callback_start', 'ros2:callback_end']
        for p in eb[i + 1:i + 60]:
            if p.get('vtid') != e['vtid'] or not want:
                continue
            if p['name'] == want[0]:
                s[want.pop(0).split(':')[1]] = p['t']
            if p['name'] == 'ros2:rmw_take':
                break

    stages = ['rclcpp_publish', 'rcl_publish', 'source_timestamp', 'rmw_publish', 'frame_tx_A_eth0',
              'frame_rx_B_eth0', 'rmw_take', 'rcl_take', 'rclcpp_take', 'callback_start', 'callback_end']
    complete = sorted((s for s in samples.values() if all(k in s for k in stages)), key=lambda s: s['N'])
    os.makedirs(a.res, exist_ok=True)

    # one sample
    one = next(s for s in complete if s['N'] == a.sample)
    t0 = one['rclcpp_publish']
    with open(os.path.join(a.res, 'trace_one_sample.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['stage', 'host', 'timestamp_realtime_ns', 't_from_rclcpp_publish_ns', 'delta_from_prev_ns'])
        prev = None
        for k in stages:
            host = 'A' if stages.index(k) <= 4 else 'B'
            w.writerow([k, host, one[k], one[k] - t0, '' if prev is None else one[k] - prev])
            prev = one[k]
    # stats over N >= WARMUP_BELOW
    use = [s for s in complete if s['N'] >= WARMUP_BELOW]
    neg = []
    with open(os.path.join(a.res, 'trace_stage_stats.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['from', 'to', 'n', 'median_ns', 'min_ns', 'max_ns'])
        pairs = list(zip(stages[:-1], stages[1:])) + [('rclcpp_publish', 'callback_start'),
                                                       ('rmw_publish', 'rmw_take'),
                                                       ('frame_rx_B_eth0', 'callback_start')]
        for x, y in pairs:
            d = [s[y] - s[x] for s in use]
            neg += [(s['N'], x, y, s[y] - s[x]) for s in use if s[y] - s[x] < 0]
            w.writerow([x, y, len(d), int(statistics.median(d)), min(d), max(d)])

    # env
    ca_b, ca_a = kv(os.path.join(A, 'clock_before.txt')), kv(os.path.join(A, 'clock_after.txt'))
    cb_b, cb_a = kv(os.path.join(B, 'clock_before.txt')), kv(os.path.join(B, 'clock_after.txt'))
    env = os.path.join(a.res, 'trace_env.txt')
    with open(env, 'w') as f:
        f.write('# experiment 17 (run_trace.sh): environment, clocks, correlation summary\n')
        for fn in ('meta.txt', 'host_checks.txt'):
            p = os.path.join(a.inp, fn)
            if os.path.exists(p):
                f.write(open(p).read() + '\n')
        f.write('# clock alignment (ns). LTTng metadata clock offset = realtime - monotonic at session setup\n')
        f.write(f'A metadata offset          {off_a}\nB metadata offset          {off_b}\n')
        for lab, c in (('A before', ca_b), ('A after ', ca_a), ('B before', cb_b), ('B after ', cb_a)):
            f.write(f'{lab} clock_offset.py   {c["offset_ns"]} (+-{c["halfwidth_ns"]})\n')
        mx = max(abs(int(c['offset_ns']) - o) for c, o in ((ca_b, off_a), (ca_a, off_a), (cb_b, off_b), (cb_a, off_b)))
        f.write(f'max |measured - metadata| = {mx} ns (alignment error between LTTng and tcpdump timestamps)\n')
        f.write(f'samples with full chain: {len(complete)} (N={complete[0]["N"]}..{complete[-1]["N"]}); '
                f'stats use N>={WARMUP_BELOW}: n={len(use)}\n')
        f.write(f'negative stage durations: {neg if neg else "none"}\n')
        f.write(f'one sample: N={one["N"]} writerSN={one["writerSN"]} frame_len={one["frame_len"]} '
                f'source_timestamp(INFO_TS)={one["src"]}\n')
        f.write(f'/chatter rmw_publisher_handle=0x{rmw_pub_h:X} rmw_subscription_handle=0x{rmw_sub_h:X}\n')
        f.write('\n# lttng session (talker side)\n')
        f.write(open(os.path.join(A, 'lttng.log')).read())

    # babeltrace excerpt of the one sample (both traces), hostname scrubbed
    lo, hi = one['rclcpp_publish'] - 2000, one['callback_end'] + 2000
    with open(os.path.join(a.res, 'trace_babeltrace_excerpt.txt'), 'w') as f:
        f.write(f'# babeltrace2 output (realtime via metadata offset, UTC) for N={one["N"]}; '
                'only events between rclcpp_publish-2us and callback_end+2us\n')
        for side in (A, B):
            txt = subprocess.run(['babeltrace2', '--clock-gmt', '--clock-date', os.path.join(side, 'ctf')],
                                 capture_output=True, text=True, check=True).stdout
            f.write(f'## {os.path.basename(side)}\n')
            for line in txt.splitlines():
                m = re.match(r'\[(\d{4})-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)\.(\d{9})\]', line)
                if not m:
                    continue
                y, mo, d, hh, mm, ss, ns = (int(x) for x in m.groups())
                t = calendar.timegm((y, mo, d, hh, mm, ss)) * 1_000_000_000 + ns
                if lo <= t <= hi:
                    if a.host_name:
                        line = line.replace(a.host_name, '<host>')
                    f.write(line + '\n')
    print(open(os.path.join(a.res, 'trace_one_sample.csv')).read())
    print(open(os.path.join(a.res, 'trace_stage_stats.csv')).read())
    print(open(env).read().split('# lttng session')[0])


if __name__ == '__main__':
    main()
