#!/usr/bin/env python3
"""Row extraction and summary for run_rcvbuf_sweep.sh (docs/03 §9 and §11). Standard library only.

  rcvbuf_sweep.py row <run-prefix> <key=value>...      print the CSV header (if --header) or one CSV row
      <run-prefix> is out/<sweep>/runs/<run-id>; reads the files the shell script left there:
      .listener.log .talker.log .snmp{0,1}_{A,B}.txt .ss_B_ready.txt .ss_B_end.txt .ss_A.txt
      .shm_B.txt .tc_{A,B}.txt .tcpdump.log .exit.txt and .raw.pcap (via sweep_pcap_stats.py)
      key=value pairs (run_id, rep, arm, qos, shape, ...) are copied into the row first.
  rcvbuf_sweep.py header
  rcvbuf_sweep.py lost <out.csv> <runs.csv>      which images (frame_id f<k>) each run did NOT receive,
      read from runs/<run-id>.listener.log next to runs.csv
  rcvbuf_sweep.py summary <out.csv> <runs.csv>... [--only qos:arm,qos:arm] [--shape S]
      one row per (shape, qos, arm): mean/min/max of delivered images, loss %, median/min/max of
      Udp RcvbufErrors, DATA_FRAG on the wire, NACK_FRAG, etc. (n = number of runs)

Counters are deltas inside the container's own network namespace (snapshot before tcpdump / the
node started, snapshot after the node stopped), so they only contain this run.
"""
import csv, json, os, re, statistics, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = [
    # identity
    'run_id', 'start', 'rep', 'order', 'shape', 'qos', 'arm', 'profile_B', 'profile_A', 'req_bytes', 'n_pub',
    # buffers seen by the kernel (ss -uamn skmem) on the receiver user-data port, and the sender
    'rb_B_port', 'rb_B_all', 'drops_B_port', 'tb_A_max', 'rb_A_max', 'shm_files_B', 'udp_ports_B',
    # result
    'published', 'delivered',
    # receiver /proc/net/snmp deltas
    'B_InDatagrams', 'B_InErrors', 'B_RcvbufErrors', 'B_NoPorts', 'B_ReasmReqds', 'B_ReasmOKs', 'B_ReasmFails',
    # sender /proc/net/snmp deltas
    'A_OutDatagrams', 'A_SndbufErrors', 'A_FragCreates',
    # receiver capture
    'pcap_frames', 'tcpdump_dropped', 'datafrag_total', 'datafrag_unique', 'datafrag_retrans', 'nackfrag',
    'sn_seen', 'sn_complete', 'ip_frags_per_dgram', 'burst_ms_med', 'burst_ms_min', 'burst_ms_max',
    'dgram_us_med', 'gap_us_med', 'image_frame_bytes', 'image_frames', 'image_wire_us_1g',
    # qdisc stats (root qdisc on eth0) after the run
    'tcA_pkts', 'tcA_dropped', 'tcA_overlimits', 'tcB_pkts', 'tcB_dropped', 'tcB_overlimits',
    'exit_A', 'exit_B', 'wall_s', 'note',
    # added for docs/03 §13 and §15 (columns appended so older runs.csv files keep their meaning)
    'rmw', 'env_extra', 'sd_frames', 'sd_bytes', 'ds_frames', 'ds_bytes', 'tcp_sd_segs', 'tcp_sd_payload',
    'tcp_sd_retrans', 'acknack', 'heartbeat', 'lat_ms_med', 'lat_ms_max', 'lat_n',
]


def read(p):
    try:
        with open(p, errors='replace') as f:
            return f.read()
    except OSError:
        return None


def snmp(text):
    """{('Udp','RcvbufErrors'): int, ...} from a /proc/net/snmp dump"""
    out = {}
    if not text:
        return out
    lines = text.splitlines()
    for a, b in zip(lines, lines[1:]):
        ka, kb = a.split(), b.split()
        if (len(ka) > 1 and len(kb) == len(ka) and ka[0] == kb[0]
                and not ka[1].lstrip('-').isdigit() and kb[1].lstrip('-').isdigit()):
            for k, v in zip(ka[1:], kb[1:]):
                out[(ka[0].rstrip(':'), k)] = int(v)
    return out


def delta(a, b, key):
    if key in a and key in b:
        return b[key] - a[key]
    return ''


def ss_udp(text):
    """[(local_port, {'rb':..,'tb':..,'d':..}), ...] from `ss -uamn`"""
    res = []
    if not text:
        return res
    port = None
    for line in text.splitlines():
        m = re.search(r'skmem:\(([^)]*)\)', line)
        if m and port is not None:
            kv = {}
            for item in m.group(1).split(','):
                mm = re.match(r'([a-z]+)(\d+)', item)
                if mm:
                    kv[mm.group(1)] = int(mm.group(2))
            res.append((port, kv)); port = None
            continue
        f = line.split()
        if len(f) >= 5 and f[0] in ('UNCONN', 'ESTAB'):
            port = f[3].rsplit(':', 1)[-1]
    return res


def tc_root(text):
    """(sent_pkts, dropped, overlimits) of the first qdisc in `tc -s qdisc show dev eth0`"""
    if not text:
        return ('', '', '')
    m = re.search(r'Sent \d+ bytes (\d+) pkt \(dropped (\d+), overlimits (\d+)', text)
    return m.groups() if m else ('', '', '')


def row(prefix, kv, port):
    r = {k: '' for k in FIELDS}
    r.update(kv)
    lg = read(prefix + '.listener.log') or ''
    r['delivered'] = len(re.findall(r' got ', lg))
    tl = read(prefix + '.talker.log')
    r['published'] = len(re.findall(r'\bpublished \d+', tl)) if tl is not None else ''
    # delivery latency from the ROS log timestamps (same host clock in both containers):
    # time of the subscriber's 'got f<k>' line minus time of the publisher's 'published <k>' line,
    # which rclpy writes right after publish() returned.
    tp = {m.group(2): float(m.group(1)) for m in re.finditer(r'\[(\d+\.\d+)\] \[img_pub\]: published (\d+)', tl or '')}
    lat = [(float(m.group(1)) - tp[m.group(2)]) * 1e3
           for m in re.finditer(r'\[(\d+\.\d+)\] \[img_sub\]: got f(\d+) ', lg) if m.group(2) in tp]
    if lat:
        r['lat_ms_med'] = round(statistics.median(lat), 2); r['lat_ms_max'] = round(max(lat), 2); r['lat_n'] = len(lat)
    b0, b1 = snmp(read(prefix + '.snmp0_B.txt')), snmp(read(prefix + '.snmp1_B.txt'))
    for k in ('InDatagrams', 'InErrors', 'RcvbufErrors', 'NoPorts'):
        r['B_' + k] = delta(b0, b1, ('Udp', k))
    for k in ('ReasmReqds', 'ReasmOKs', 'ReasmFails'):
        r['B_' + k] = delta(b0, b1, ('Ip', k))
    a0, a1 = snmp(read(prefix + '.snmp0_A.txt')), snmp(read(prefix + '.snmp1_A.txt'))
    for k in ('OutDatagrams', 'SndbufErrors'):
        r['A_' + k] = delta(a0, a1, ('Udp', k))
    r['A_FragCreates'] = delta(a0, a1, ('Ip', 'FragCreates'))
    sb = ss_udp(read(prefix + '.ss_B_ready.txt'))
    r['rb_B_port'] = '/'.join(sorted({str(kv.get('rb')) for p, kv in sb if p == port})) or ''
    r['rb_B_all'] = '/'.join(sorted({str(kv.get('rb')) for p, kv in sb}, key=lambda x: int(x) if x.isdigit() else 0))
    r['udp_ports_B'] = ' '.join(sorted({p for p, kv in sb}, key=lambda x: int(x) if x.isdigit() else 0))
    se = ss_udp(read(prefix + '.ss_B_end.txt'))
    d = [kv.get('d', 0) for p, kv in se if p == port]
    r['drops_B_port'] = sum(d) if d else ''
    sa = ss_udp(read(prefix + '.ss_A.txt'))
    if sa:
        r['tb_A_max'] = max(kv.get('tb', 0) for p, kv in sa)
        r['rb_A_max'] = max(kv.get('rb', 0) for p, kv in sa)
    shm = read(prefix + '.shm_B.txt')
    r['shm_files_B'] = len([x for x in shm.split() if x.startswith('fastdds')]) if shm is not None else ''
    td = read(prefix + '.tcpdump.log') or ''
    m = re.search(r'(\d+) packets dropped by kernel', td)
    r['tcpdump_dropped'] = m.group(1) if m else ''
    r['tcA_pkts'], r['tcA_dropped'], r['tcA_overlimits'] = tc_root(read(prefix + '.tc_A.txt'))
    r['tcB_pkts'], r['tcB_dropped'], r['tcB_overlimits'] = tc_root(read(prefix + '.tc_B.txt'))
    ex = read(prefix + '.exit.txt') or ''
    m = re.search(r'A (\S+)', ex); r['exit_A'] = m.group(1) if m else ''
    m = re.search(r'B (\S+)', ex); r['exit_B'] = m.group(1) if m else ''
    pcap = prefix + '.raw.pcap'
    if os.path.exists(pcap) and os.path.getsize(pcap) > 24:
        src = kv.get('ip_sender', '172.20.0.3'); dst = kv.get('ip_receiver', '172.20.0.2')
        p = subprocess.run([sys.executable, os.path.join(HERE, 'sweep_pcap_stats.py'), pcap, '--src', src, '--dst', dst],
                           capture_output=True, text=True)
        if p.returncode == 0:
            st = json.loads(p.stdout)
            st['pcap_frames'] = st.pop('frames')
            for k, v in st.items():
                if k in r:
                    r[k] = '' if v is None else v
        else:
            r['note'] = (r.get('note', '') + ' pcap-parse-failed').strip()
    return r


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def fmt(x, nd=1):
    if x is None:
        return ''
    if abs(x - round(x)) < 1e-9:
        return str(int(round(x)))
    return f'{x:.{nd}f}'


def summary(out, files, only=None, shape=None):
    rows = []
    for fn in files:
        with open(fn, newline='') as f:
            rows += list(csv.DictReader(f))
    groups = {}
    for r in rows:
        if shape and r['shape'] != shape:
            continue
        if only and f"{r['qos']}:{r['arm']}" not in only:
            continue
        groups.setdefault((r['shape'], r['qos'], r['arm']), []).append(r)

    def order(k):
        shp = {'none': 0, 'tbf1g': 1, 'wifi': 2}.get(k[0], 9)
        a = k[2]
        rank = (0, 0) if a == 'noxml' else (1, int(a)) if a.isdigit() else (2, a)
        return (shp, k[1], rank)

    cols = ['shape', 'qos', 'arm', 'req_bytes', 'n', 'rb_eff_B', 'tb_A_max', 'images_per_run',
            'delivered_mean', 'delivered_min', 'delivered_max', 'loss_pct',
            'rcvbuferr_med', 'rcvbuferr_min', 'rcvbuferr_max', 'sockdrops_med', 'inerrors_med',
            'reasm_ok_mean', 'reasm_fails_max', 'datafrag_wire_mean', 'datafrag_wire_min', 'datafrag_wire_max',
            'sn_complete_min', 'nackfrag_mean', 'nackfrag_min', 'nackfrag_max', 'retrans_mean', 'retrans_min', 'retrans_max',
            'burst_ms_med', 'dgram_us_med', 'gap_us_med', 'image_wire_us_1g',
            'A_sndbuferr_max', 'tcA_pkts_med', 'tcA_dropped_sum', 'tcA_overlimits_med', 'tcpdump_dropped_max',
            'shm_files_B', 'lat_ms_med', 'lat_ms_max', 'sd_frames_per_img', 'sd_bytes_per_img', 'tcp_sd_payload_mean',
            'tcp_sd_retrans_mean', 'acknack_mean', 'heartbeat_mean', 'ds_frames_mean', 'rmw', 'run_ids']
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for k in sorted(groups, key=order):
            g = groups[k]

            def vals(c):
                return [v for v in (num(r.get(c)) for r in g) if v is not None]

            def st(c, fn):
                v = vals(c)
                return fn(v) if v else None
            dl, pb = vals('delivered'), vals('published')
            loss = (1 - sum(dl) / sum(pb)) * 100 if pb and sum(pb) and len(dl) == len(pb) else None
            w.writerow([k[0], k[1], k[2], g[0]['req_bytes'], len(g),
                        '/'.join(sorted({r['rb_B_port'] for r in g})), '/'.join(sorted({r['tb_A_max'] for r in g})),
                        fmt(st('published', statistics.mean)),
                        fmt(st('delivered', statistics.mean), 2), fmt(st('delivered', min)), fmt(st('delivered', max)),
                        fmt(loss, 1),
                        fmt(st('B_RcvbufErrors', statistics.median)), fmt(st('B_RcvbufErrors', min)), fmt(st('B_RcvbufErrors', max)),
                        fmt(st('drops_B_port', statistics.median)), fmt(st('B_InErrors', statistics.median)),
                        fmt(st('B_ReasmOKs', statistics.mean)), fmt(st('B_ReasmFails', max)),
                        fmt(st('datafrag_total', statistics.mean)), fmt(st('datafrag_total', min)), fmt(st('datafrag_total', max)),
                        fmt(st('sn_complete', min)),
                        fmt(st('nackfrag', statistics.mean)), fmt(st('nackfrag', min)), fmt(st('nackfrag', max)),
                        fmt(st('datafrag_retrans', statistics.mean)), fmt(st('datafrag_retrans', min)), fmt(st('datafrag_retrans', max)),
                        fmt(st('burst_ms_med', statistics.median), 3), fmt(st('dgram_us_med', statistics.median), 1),
                        fmt(st('gap_us_med', statistics.median), 2), fmt(st('image_wire_us_1g', statistics.median), 1),
                        fmt(st('A_SndbufErrors', max)), fmt(st('tcA_pkts', statistics.median)), fmt(st('tcA_dropped', sum)),
                        fmt(st('tcA_overlimits', statistics.median)), fmt(st('tcpdump_dropped', max)),
                        '/'.join(sorted({r['shm_files_B'] for r in g})),
                        fmt(st('lat_ms_med', statistics.median), 2), fmt(st('lat_ms_max', max), 2),
                        fmt(sum(vals('sd_frames')) / sum(pb), 1) if pb and sum(pb) and vals('sd_frames') else '',
                        fmt(sum(vals('sd_bytes')) / sum(pb), 0) if pb and sum(pb) and vals('sd_bytes') else '',
                        fmt(st('tcp_sd_payload', statistics.mean), 0), fmt(st('tcp_sd_retrans', statistics.mean)),
                        fmt(st('acknack', statistics.mean)), fmt(st('heartbeat', statistics.mean)),
                        fmt(st('ds_frames', statistics.mean)),
                        '/'.join(sorted({r.get('rmw') or '' for r in g})),
                        ' '.join(r['run_id'] for r in g)])
    print(f'wrote {out} ({len(groups)} groups, {sum(len(g) for g in groups.values())} runs)')


def main():
    a = sys.argv[1:]
    if not a or a[0] in ('-h', '--help'):
        print(__doc__); return 0
    if a[0] == 'header':
        csv.writer(sys.stdout).writerow(FIELDS); return 0
    if a[0] == 'row':
        kv = dict(x.split('=', 1) for x in a[2:])
        port = kv.pop('port', '7411')
        r = row(a[1], kv, port)
        csv.writer(sys.stdout).writerow([r.get(k, '') for k in FIELDS]); return 0
    if a[0] == 'lost':
        with open(a[2], newline='') as f:
            rows = list(csv.DictReader(f))
        d = os.path.join(os.path.dirname(os.path.abspath(a[2])), 'runs')
        with open(a[1], 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['run_id', 'order', 'shape', 'qos', 'arm', 'published', 'delivered', 'missing'])
            for r in rows:
                lg = read(os.path.join(d, r['run_id'] + '.listener.log')) or ''
                got = set(re.findall(r' got (f\d+) ', lg))
                n = int(r['published'] or r['n_pub'] or 0)
                w.writerow([r['run_id'], r['order'], r['shape'], r['qos'], r['arm'], r['published'], r['delivered'],
                            ' '.join(f'f{k}' for k in range(n) if f'f{k}' not in got)])
        print(f'wrote {a[1]}'); return 0
    if a[0] == 'summary':
        only = shape = None; files = []
        i = 2
        while i < len(a):
            if a[i] == '--only': only = set(a[i + 1].split(',')); i += 2
            elif a[i] == '--shape': shape = a[i + 1]; i += 2
            else: files.append(a[i]); i += 1
        summary(a[1], files, only, shape); return 0
    print(__doc__); return 2


if __name__ == '__main__':
    sys.exit(main())
