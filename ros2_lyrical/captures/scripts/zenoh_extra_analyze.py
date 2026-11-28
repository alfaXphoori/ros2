#!/usr/bin/env python3
"""Analysis for run_zenoh_extra.sh (docs/03 §14, experiments 11-12). Standard library only.

  zenoh_extra_analyze.py kill  <out/zenoh_extra/kill>   [--csv out.csv]   one row per repetition
  zenoh_extra_analyze.py image <out/zenoh_extra/image>  [--csv out.csv]   one row per run (qos)

kill: from <id>.events.txt (host epoch of kill / sub2_start / restart / router_listening / pub_end), the ROS log
timestamps of <id>.pub.log ('pub n=K'), <id>.sub.log and <id>.sub2.log ('got n=K') and the subscriber-side
capture <id>.raw.pcap (TCP flags per connection; pcap time = host clock, same as the events):
  received / published, missing n, messages received while the router was down, the TCP events between the
  subscriber and the router address 172.20.0.2:7447 (SYN, RST, FIN with times relative to the kill), the period of
  reconnect attempts, time from router restart to the first SYN-ACK from the new router, whether the
  publisher->subscriber TCP connection saw FIN/RST, and when the subscriber started during the outage got its
  first message (relative to the restart).
image: TCP payload publisher(172.20.0.4) -> subscriber(172.20.0.3) reassembled per connection, then split into
Zenoh batches (u16 little-endian length prefix); counts batches by transport message id (low 5 bits of the first
byte: 0x05 FRAME, 0x06 FRAGMENT, 0x04 KEEP_ALIVE ...), FRAGMENT batch sizes and 'M' (more) flag, TCP segments as
seen by tcpdump on the receiver veth (GSO/GRO: can be larger than the MSS) and the sender's Tcp OutSegs /
RetransSegs from /proc/net/snmp (counts MSS-sized segments).
"""
import csv, glob, os, re, statistics, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sweep_pcap_stats import frames, ip_udp  # noqa: E402
from rcvbuf_sweep import snmp, read  # noqa: E402

ROUTER, SUB, PUB, SUB2 = '172.20.0.2', '172.20.0.3', '172.20.0.4', '172.20.0.5'


def tcp_pkts(path):
    """[(t_abs, src, sport, dst, dport, flags, seq, payload)]; t_abs = epoch seconds"""
    f = open(path, 'rb'); hdr = f.read(24); f.close()
    end = '<' if hdr[:4] in (b'\xd4\xc3\xb2\xa1', b'\x4d\x3c\xb2\xa1') else '>'
    nano = hdr[:4] in (b'\x4d\x3c\xb2\xa1', b'\xa1\xb2\x3c\x4d')
    data = open(path, 'rb').read(); off = 24; out = []
    while off + 16 <= len(data):
        ts, tu, incl, _ = struct.unpack(end + 'IIII', data[off:off + 16])
        pkt = data[off + 16:off + 16 + incl]; off += 16 + incl
        d = ip_udp(pkt)
        if not d or d['proto'] != 6 or len(d['l4']) < 20:
            continue
        th = d['l4']; sp, dp, seq = struct.unpack('>HHI', th[:8]); fl = th[13]; doff = (th[12] >> 4) * 4
        out.append((ts + (tu / 1e9 if nano else tu / 1e6), d['src'], sp, d['dst'], dp, fl, seq, th[doff:]))
    return out


def logts(text, pat):
    return [(float(m.group(1)), int(m.group(2))) for m in re.finditer(r'\[(\d+\.\d+)\] \[\w+\]: ' + pat, text or '')]


def flags(f):
    return ''.join(n for b, n in ((2, 'S'), (16, 'A'), (4, 'R'), (1, 'F')) if f & b) or '.'


def kill(d, out_csv):
    rows = []
    for ev in sorted(glob.glob(os.path.join(d, 'kill_*.events.txt'))):
        p = ev[:-len('.events.txt')]; rid = os.path.basename(p)
        E = {k: float(v) for k, v in (l.split() for l in open(ev) if l.strip())}
        tk, tr = E['kill'], E['restart']
        pub = logts(read(p + '.pub.log'), r'pub n=(\d+)')
        sub = logts(read(p + '.sub.log'), r'got n=(\d+)')
        sub2 = logts(read(p + '.sub2.log'), r'got n=(\d+)')
        got = {n for _, n in sub}; pubn = {n for _, n in pub}
        missing = sorted(pubn - got)
        down = [n for t, n in sub if tk <= t < tr]
        pkts = tcp_pkts(p + '.raw.pcap') if os.path.exists(p + '.raw.pcap') else []
        r_ev = [(t - tk, s, sp, dd, dp, flags(f)) for t, s, sp, dd, dp, f, seq, pl in pkts
                if ROUTER in (s, dd) and 7447 in (sp, dp) and (f & 0x07)]
        syn_out = [x[0] for x in r_ev if x[1] == SUB and x[5] == 'S' and x[0] > 0]
        conn_port = {}                     # sub source port -> first SYN time (one connect() each)
        for x in r_ev:
            if x[1] == SUB and x[5] == 'S' and x[0] > 0:
                conn_port.setdefault(x[2], x[0])
        synack_new = [x[0] for x in r_ev if x[1] == ROUTER and x[5] == 'SA' and x[0] > tr - tk]
        rst = [(round(x[0], 3), x[1]) for x in r_ev if 'R' in x[5] and x[0] > 0]
        fin = [(round(x[0], 3), x[1]) for x in r_ev if 'F' in x[5] and x[0] > 0]
        ps = [(t - tk, flags(f)) for t, s, sp, dd, dp, f, seq, pl in pkts if {s, dd} == {SUB, PUB} and (f & 0x05)]
        data_down = sum(1 for t, s, sp, dd, dp, f, seq, pl in pkts if s == PUB and dd == SUB and pl and tk <= t < tr)
        gaps = [round(b - a, 3) for a, b in zip(syn_out, syn_out[1:])]
        rows.append({
            'run_id': rid, 'down_s': round(tr - tk, 2), 'published': len(pubn), 'received': len(got),
            'missing_n': ' '.join(map(str, missing)),
            'received_while_router_down': len(down),
            'pub_sub_tcp_FIN_RST': ' '.join(f'{t:.3f}{fl}' for t, fl in ps) or 'none',
            'pub_to_sub_data_segs_while_down': data_down,
            'sub_SYN_to_router_after_kill_s': ' '.join(f'{x:.3f}' for x in syn_out),
            'syn_period_s': ' '.join(map(str, gaps)),
            'sub_connect_attempts': len(conn_port),
            'sub_connect_first_syn_s': ' '.join(f'{t:.3f}' for t in sorted(conn_port.values())),
            'router_RST_s': ' '.join(f'{t}{"<" if s == ROUTER else ">"}' for t, s in rst) or 'none',
            'router_FIN_s': ' '.join(f'{t}{"<" if s == ROUTER else ">"}' for t, s in fin) or 'none',
            'restart_s': round(tr - tk, 3),
            'synack_new_router_after_restart_s': round(synack_new[0] - (tr - tk), 3) if synack_new else '',
            'router_listening_after_restart_s': round(E.get('router_listening', tr) - tr, 3),
            'sub2_start_s': round(E['sub2_start'] - tk, 3),
            'sub2_received': len(sub2),
            'sub2_first_got_after_restart_s': round(sub2[0][0] - tr, 3) if sub2 else '',
            'sub2_got_before_restart': sum(1 for t, _ in sub2 if t < tr),
        })
    write(rows, out_csv)


def batches(stream):
    out = []; i = 0
    while i + 2 <= len(stream):
        n = struct.unpack('<H', stream[i:i + 2])[0]
        b = stream[i + 2:i + 2 + n]
        if len(b) < n:
            break
        out.append(b); i += 2 + n
    return out, len(stream) - i


def image(d, out_csv):
    rows = []
    for ex in sorted(glob.glob(os.path.join(d, 'image_*.exit.txt'))):
        p = ex[:-len('.exit.txt')]; rid = os.path.basename(p)
        pkts = tcp_pkts(p + '.raw.pcap')
        conns = {}
        for t, s, sp, dd, dp, f, seq, pl in pkts:
            if s == PUB and dd == SUB:
                c = conns.setdefault((sp, dp), {'segs': {}, 'n': 0, 'bytes': 0, 'sizes': [], 'syn': None})
                if f & 0x02:
                    c['syn'] = seq
                if pl:
                    c['n'] += 1; c['bytes'] += len(pl); c['sizes'].append(len(pl)); c['segs'].setdefault(seq, pl)
        best = max(conns.items(), key=lambda kv: kv[1]['bytes'])
        c = best[1]
        base = c['syn'] + 1 if c['syn'] is not None else min(c['segs'])
        stream = bytearray(); nxt = base
        for seq in sorted(c['segs'], key=lambda s: (s - base) & 0xffffffff):
            pl = c['segs'][seq]; o = (seq - nxt) & 0xffffffff
            if o > 0x7fffffff:   # overlap with what we have
                pl = pl[(nxt - seq) & 0xffffffff:]
                o = 0
            if o:
                break            # hole: stop (capture gap)
            stream += pl; nxt = (nxt + len(pl)) & 0xffffffff
        bl, rest = batches(bytes(stream))
        ids = {}
        for b in bl:
            ids[b[0] & 0x1f] = ids.get(b[0] & 0x1f, 0) + 1
        frag = [b for b in bl if b and b[0] & 0x1f == 0x06]
        last = [b for b in frag if not b[0] & 0x40]
        fsz = [len(b) + 2 for b in frag]
        lg = read(p + '.sub.log') or ''; pl_ = read(p + '.pub.log') or ''
        s0, s1 = snmp(read(p + '.snmp0_pub.txt')), snmp(read(p + '.snmp1_pub.txt'))
        r0, r1 = snmp(read(p + '.snmp0_sub.txt')), snmp(read(p + '.snmp1_sub.txt'))
        qos = rid.rsplit('_', 1)[-1]
        pubn = len(re.findall(r'published \d+', pl_)); got = len(re.findall(r' got ', lg))
        rows.append({
            'run_id': rid, 'qos': qos, 'published': pubn, 'delivered': got,
            'data_conn': f'{PUB}:{best[0][0]}->{SUB}:{best[0][1]}', 'other_conns_pub_to_sub': len(conns) - 1,
            'tcp_payload_bytes': c['bytes'], 'tcpdump_segs': c['n'],
            'tcpdump_seg_max': max(c['sizes']), 'tcpdump_seg_med': statistics.median(c['sizes']),
            'stream_bytes_reassembled': len(stream), 'unparsed_tail': rest,
            'batches': len(bl), 'batch_ids': ' '.join(f'0x{k:02x}:{v}' for k, v in sorted(ids.items())),
            'fragment_batches': len(frag), 'fragment_last_M0': len(last),
            'fragment_batches_per_msg': round(len(frag) / len(last), 2) if last else '',
            'fragment_batch_bytes_max': max(fsz) if fsz else '', 'fragment_batch_bytes_med': statistics.median(fsz) if fsz else '',
            'payload_per_image': round(c['bytes'] / pubn) if pubn else '',
            'overhead_per_image_vs_921652': round(c['bytes'] / pubn - 921652) if pubn else '',
            'pub_Tcp_OutSegs': s1.get(('Tcp', 'OutSegs'), 0) - s0.get(('Tcp', 'OutSegs'), 0),
            'pub_Tcp_RetransSegs': s1.get(('Tcp', 'RetransSegs'), 0) - s0.get(('Tcp', 'RetransSegs'), 0),
            'sub_Tcp_InSegs': r1.get(('Tcp', 'InSegs'), 0) - r0.get(('Tcp', 'InSegs'), 0),
        })
    write(rows, out_csv)


def write(rows, out_csv):
    if not rows:
        print('no runs found'); return
    w = csv.DictWriter(open(out_csv, 'w', newline='') if out_csv else sys.stdout, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
    if out_csv:
        print(f'wrote {out_csv} ({len(rows)} rows)')


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ('kill', 'image'):
        print(__doc__); sys.exit(2)
    oc = a[a.index('--csv') + 1] if '--csv' in a else None
    (kill if a[0] == 'kill' else image)(a[1], oc)
